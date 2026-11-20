"""
Meta Autopilot — guardrailed auto-publish for Unk.

Operating rule:
  - Routine content  -> auto-publish via meta_publisher
  - Sensitive content -> hold for Jason (written to hold queue, NOT posted)
  - Failed content   -> auto-retried inside meta_publisher (3x backoff)
  - Repeated failure -> escalation alert appended to alert queue

Sensitivity triggers (any match = HOLD):
  legal, money, medical, political, minors, partner names,
  paid sponsor reports, signature/contract asks.

Triggers are intentionally conservative — false-positives just mean Jason
reviews one extra post, false-negatives are the real cost.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from meta_credentials import CONFIG_DIR
from meta_publisher import (
    publish_text,
    publish_photo,
    publish_video,
    publish_reel,
    _log as publisher_log,
)

HOLD_QUEUE = CONFIG_DIR / "meta_autopilot_holds.jsonl"
ALERT_QUEUE = CONFIG_DIR / "meta_autopilot_alerts.jsonl"
HISTORY_LOG = CONFIG_DIR / "meta_autopilot_history.jsonl"

# Track repeated failures keyed by source_id so we only alert on N+ in a row.
FAILURE_STATE = CONFIG_DIR / "meta_autopilot_failures.json"
REPEAT_FAILURE_THRESHOLD = 2  # after this many failures of the same source -> alert


# ---------------------------------------------------------------------------
# Sensitivity classifier
# ---------------------------------------------------------------------------

# Word-boundary patterns keep us from flagging substrings like "minors" inside
# unrelated words. All matching is case-insensitive.
_PATTERNS: dict[str, list[str]] = {
    "legal_claim": [
        r"\blawsuit\b", r"\bsue[ds]?\b", r"\battorney(s)?\b", r"\blawyer(s)?\b",
        r"\bsettlement\b", r"\bcourt order\b", r"\bsubpoena\b", r"\bdefamation\b",
        r"\bcease and desist\b", r"\bcopyright (claim|strike)\b",
        r"\bguarantee[ds]?\b", r"\bofficial(ly)? (recognized|certified)\b",
    ],
    "money_claim": [
        r"\b\$\s?\d{1,3}(,\d{3})+\b",          # $25,000 ; $1,000,000
        r"\b\$\s?\d{4,}\b",                    # $5000+
        r"\b\d+\s*%\s*(return|roi|guaranteed)\b",
        r"\bguaranteed (income|return|payout|profit)\b",
        r"\brefund(ed|ing)?\b", r"\bchargeback\b",
        r"\b(raise[ds]?|raised)\s+\$",
        r"\b(grant|award) of \$",
    ],
    "medical_claim": [
        r"\bcure[ds]?\b", r"\btreat(s|ed|ment)\b", r"\bdiagnos(e|is|ed)\b",
        r"\bclinical(ly)? proven\b", r"\bFDA[- ]approved\b",
        r"\bhypertension\b", r"\bblood pressure\b", r"\bdepression\b",
        r"\banxiety disorder\b", r"\bmental illness\b", r"\bprescription\b",
        r"\bmedication\b", r"\bdiabet(es|ic)\b",
    ],
    "political": [
        r"\bvot(e|ing|er)\b", r"\bballot\b", r"\belection\b",
        r"\bcandidate\b", r"\bcampaign for\b",
        r"\b(democrat|republican|gop|liberal|conservative|progressive)\b",
        r"\bendors(e|ed|ing) (the |a )?candidate\b",
        r"\bPresident [A-Z][a-z]+\b", r"\bGovernor [A-Z][a-z]+\b",
        r"\bMayor [A-Z][a-z]+\b",
    ],
    "minors": [
        r"\bminor(s)?\b", r"\bchild(ren)?\b", r"\bkid(s)?\b",
        r"\bstudent(s)?\b", r"\byouth\b", r"\bteen(s|ager(s)?)?\b",
        r"\b(under|below)\s*1[0-8]\b", r"\bunderage\b",
        r"\bcamp(er|ers)?\b",
    ],
    "partner_named": [
        # Live JFLI partners that require Jason's eyes before public mention.
        r"\bBAMA\b", r"\bBlack Archives( of Mid-America)?\b",
        r"\bSoul of Santa\b", r"\bDo Good Foundation\b",
        r"\bMissouri Humanities\b", r"\bKauffman( Foundation)?\b",
        r"\bBloch\b", r"\bRESET\b(?! framework)",  # RESET program partner mention
    ],
    "paid_sponsor": [
        r"#ad\b", r"#sponsored\b", r"\bsponsored by\b", r"\bpaid partnership\b",
        r"\bin partnership with\b", r"\bbrought to you by\b",
        r"\bsponsor report\b",
    ],
    "signature_or_contract": [
        r"\bsign(ed|ing|ature)?\b", r"\bcontract\b", r"\bagreement\b",
        r"\bMOU\b", r"\bLOI\b", r"\bletter of intent\b",
        r"\bDocuSign\b", r"\bnotari(ze|zed)\b",
    ],
}

_COMPILED = {
    label: [re.compile(p, re.IGNORECASE) for p in pats]
    for label, pats in _PATTERNS.items()
}


def classify(text: str) -> dict:
    """Return {sensitive: bool, reasons: [...]} for a piece of post text."""
    if not text:
        return {"sensitive": False, "reasons": []}
    reasons: list[str] = []
    for label, patterns in _COMPILED.items():
        for pat in patterns:
            m = pat.search(text)
            if m:
                reasons.append(f"{label}: {m.group(0)!r}")
                break  # one match per category is enough
    return {"sensitive": bool(reasons), "reasons": reasons}


# ---------------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------------

def _append_jsonl(path: Path, record: dict) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_failure_state() -> dict:
    if not FAILURE_STATE.exists():
        return {}
    try:
        return json.loads(FAILURE_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_failure_state(state: dict) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        FAILURE_STATE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def _record_failure(source_id: str, error: dict) -> int:
    state = _load_failure_state()
    entry = state.get(source_id, {"count": 0})
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_error"] = error
    entry["last_at"] = _now()
    state[source_id] = entry
    _save_failure_state(state)
    return entry["count"]


def _clear_failure(source_id: str) -> None:
    state = _load_failure_state()
    if source_id in state:
        del state[source_id]
        _save_failure_state(state)


# ---------------------------------------------------------------------------
# Autopilot entry point
# ---------------------------------------------------------------------------

VALID_FORMATS = {"text", "photo", "video", "reel"}


def autopilot_publish(
    *,
    message: str,
    format: str = "text",
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
    link: Optional[str] = None,
    title: Optional[str] = None,
    source_id: Optional[str] = None,
    force: bool = False,
) -> dict:
    """Autopilot dispatcher.

    Returns one of:
      {ok: True, status: 'published', post_id, format, ...}
      {ok: False, status: 'held', hold_id, reasons[...]}
      {ok: False, status: 'failed_alerted', source_id, failure_count, error}
      {ok: False, status: 'failed', source_id, failure_count, error}
    """
    source_id = source_id or f"auto_{uuid.uuid4().hex[:12]}"
    fmt = (format or "text").lower()
    if fmt not in VALID_FORMATS:
        return {"ok": False, "status": "rejected",
                "error": "invalid_format", "format": fmt}

    # Sensitivity gate — combine message + title for classification.
    text_to_scan = " ".join(filter(None, [message, title]))
    verdict = classify(text_to_scan)

    if verdict["sensitive"] and not force:
        hold_id = f"hold_{uuid.uuid4().hex[:12]}"
        record = {
            "hold_id": hold_id, "source_id": source_id, "ts": _now(),
            "format": fmt, "message": message, "title": title, "link": link,
            "image_path": image_path, "video_path": video_path,
            "reasons": verdict["reasons"],
        }
        _append_jsonl(HOLD_QUEUE, record)
        _append_jsonl(HISTORY_LOG,
                      {"ts": _now(), "source_id": source_id, "action": "held",
                       "reasons": verdict["reasons"]})
        publisher_log("autopilot_hold", source_id=source_id,
                      reasons=verdict["reasons"], format=fmt)
        return {"ok": False, "status": "held", "hold_id": hold_id,
                "source_id": source_id, "reasons": verdict["reasons"]}

    # Publish via underlying publisher (which already retries 3x w/ backoff).
    if fmt == "text":
        res = publish_text(message, link=link)
    elif fmt == "photo":
        if not image_path:
            return {"ok": False, "status": "rejected", "error": "missing_image_path"}
        res = publish_photo(image_path, caption=message)
    elif fmt == "video":
        if not video_path:
            return {"ok": False, "status": "rejected", "error": "missing_video_path"}
        res = publish_video(video_path, description=message, title=title)
    else:  # reel
        if not video_path:
            return {"ok": False, "status": "rejected", "error": "missing_video_path"}
        res = publish_reel(video_path, description=message)

    if res.get("ok"):
        _clear_failure(source_id)
        _append_jsonl(HISTORY_LOG, {
            "ts": _now(), "source_id": source_id, "action": "published",
            "format": fmt, "post_id": res.get("post_id") or res.get("video_id"),
        })
        return {"ok": True, "status": "published", "format": fmt,
                "source_id": source_id,
                "post_id": res.get("post_id") or res.get("video_id"),
                "result": res}

    # Failure path
    err = {k: res.get(k) for k in ("error", "status", "body", "detail") if k in res}
    count = _record_failure(source_id, err)
    _append_jsonl(HISTORY_LOG, {
        "ts": _now(), "source_id": source_id, "action": "failed",
        "format": fmt, "failure_count": count, "error": err,
    })
    if count >= REPEAT_FAILURE_THRESHOLD:
        alert = {
            "ts": _now(), "source_id": source_id, "format": fmt,
            "failure_count": count, "error": err,
            "message_excerpt": (message or "")[:280],
            "severity": "high" if count >= REPEAT_FAILURE_THRESHOLD + 1 else "medium",
        }
        _append_jsonl(ALERT_QUEUE, alert)
        publisher_log("autopilot_alert", **alert)
        return {"ok": False, "status": "failed_alerted",
                "source_id": source_id, "failure_count": count, "error": err}
    return {"ok": False, "status": "failed",
            "source_id": source_id, "failure_count": count, "error": err}


# ---------------------------------------------------------------------------
# Queue inspection
# ---------------------------------------------------------------------------

def _tail_jsonl(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
        out: list[dict] = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out
    except Exception:
        return []


def list_holds(limit: int = 50) -> dict:
    return {"ok": True, "holds": _tail_jsonl(HOLD_QUEUE, limit)}


def list_alerts(limit: int = 50) -> dict:
    return {"ok": True, "alerts": _tail_jsonl(ALERT_QUEUE, limit)}


def list_history(limit: int = 100) -> dict:
    return {"ok": True, "history": _tail_jsonl(HISTORY_LOG, limit)}


def release_hold(hold_id: str) -> dict:
    """Approve a held post. Reads from HOLD_QUEUE, publishes with force=True,
    and rewrites the queue without the released entry."""
    if not HOLD_QUEUE.exists():
        return {"ok": False, "error": "no_holds"}
    try:
        lines = HOLD_QUEUE.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return {"ok": False, "error": "hold_read_failed", "detail": str(e)}
    target = None
    keep: list[str] = []
    for ln in lines:
        try:
            rec = json.loads(ln)
        except Exception:
            keep.append(ln)
            continue
        if rec.get("hold_id") == hold_id and target is None:
            target = rec
        else:
            keep.append(ln)
    if not target:
        return {"ok": False, "error": "hold_not_found", "hold_id": hold_id}
    # Rewrite queue without this entry
    try:
        HOLD_QUEUE.write_text("\n".join(keep) + ("\n" if keep else ""),
                              encoding="utf-8")
    except Exception:
        pass
    res = autopilot_publish(
        message=target.get("message") or "",
        format=target.get("format") or "text",
        image_path=target.get("image_path"),
        video_path=target.get("video_path"),
        link=target.get("link"),
        title=target.get("title"),
        source_id=target.get("source_id"),
        force=True,
    )
    _append_jsonl(HISTORY_LOG, {
        "ts": _now(), "source_id": target.get("source_id"),
        "action": "released", "hold_id": hold_id, "result_status": res.get("status"),
    })
    return {"ok": res.get("ok", False), "released": hold_id, "result": res}
