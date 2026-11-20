"""
Meta Autofix Handlers (dry-run first)
=====================================
Companion-side executors for the autofix_kinds produced by the
`unk-meta-autopilot` edge worker.

Doctrine (mem://preferences/unk-meta-autofix-doctrine.md):
  • Use Jason's local browser session only — never a headless bot elsewhere.
  • Never post content from these handlers. Setup/config repair ONLY.
  • Always log a screenshot + a structured result to CONFIG_DIR.
  • Escalate to Jason ONLY for the 5 forced-human categories:
      1. 2FA / security prompt
      2. Password manager unlock
      3. Legal certification / final submission
      4. Payment / paid signup approval
      5. Live ID / selfie / manual identity verification

Live execution is gated behind META_AUTOPILOT_ENABLED=true.
Until dry-run passes, every handler returns a structured plan + evidence
of what it *would* do, without touching Meta.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from meta_credentials import CONFIG_DIR

AUTOFIX_LOG = CONFIG_DIR / "meta_autofix_history.jsonl"
SCREENSHOT_DIR = CONFIG_DIR / "meta_autofix_screenshots"


def _enabled() -> bool:
    return (os.environ.get("META_AUTOPILOT_ENABLED", "false").lower()
            in ("1", "true", "yes", "on"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(record: dict) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with AUTOFIX_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def _dry_screenshot_stub(action_type: str) -> str:
    """Write a tiny placeholder file so the log carries a real path even in
    dry-run mode. Real handlers will replace this with an actual Playwright
    screenshot (page.screenshot(path=...)) when META_AUTOPILOT_ENABLED=true.
    """
    try:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        p = SCREENSHOT_DIR / f"{action_type}_{uuid.uuid4().hex[:8]}.dryrun.txt"
        p.write_text(
            f"dry-run screenshot placeholder for {action_type} @ {_now()}\n",
            encoding="utf-8",
        )
        return str(p)
    except Exception:
        return ""


# 5 forced-human escalation categories — the ONLY reasons a handler is
# allowed to bail back to Jason.
FORCED_HUMAN = {
    "twofactor_prompt",
    "password_manager_unlock",
    "legal_certification",
    "payment_approval",
    "identity_verification",
}


def _dry(action_type: str, planned_steps: list[str],
         *, escalation_hint: str | None = None,
         extra: dict | None = None) -> dict:
    shot = _dry_screenshot_stub(action_type)
    rec = {
        "ts": _now(),
        "action_type": action_type,
        "dry_run": True,
        "enabled": _enabled(),
        "planned_steps": planned_steps,
        "screenshot_path": shot,
        "escalation_hint": escalation_hint,
        "extra": extra or {},
    }
    _log(rec)
    return {
        "ok": True,
        "dry_run": True,
        "action_type": action_type,
        "planned_steps": planned_steps,
        "screenshot_path": shot,
        "escalation_hint": escalation_hint,
        "note": ("Handler is scaffolded. Set META_AUTOPILOT_ENABLED=true "
                 "to execute against the live browser session."),
    }


# ---------------------------------------------------------------------------
# Individual autofix action types
# ---------------------------------------------------------------------------

def handle_meta_refresh_user_token(payload: dict) -> dict:
    steps = [
        "Locate Jason's default Chrome profile (already signed in to Facebook).",
        "Open https://developers.facebook.com/tools/explorer/ in that profile.",
        "Select the JFLI app and click 'Get User Access Token'.",
        "Escalate → twofactor_prompt if 2FA challenge appears.",
        "Copy the long-lived user token, POST to companion → meta_credentials.set_user_token().",
        "Call meta_publisher.refresh_long_lived_token() to exchange for 60-day token.",
        "POST refreshed token back to server via desktop_action_results.",
    ]
    return _dry("meta_refresh_user_token", steps,
                escalation_hint="twofactor_prompt")


def handle_meta_add_missing_scopes(payload: dict) -> dict:
    missing = payload.get("missing_scopes") or []
    steps = [
        "Open Facebook Login for Business config for JFLI app.",
        f"Add missing scopes: {missing or '[from doctor report]'}",
        "Trigger consent dialog in Jason's browser.",
        "Escalate → twofactor_prompt if security prompt appears.",
        "Escalate → legal_certification if Meta shows the 'Data Use Checkup' certification step.",
        "Re-run meta-setup-doctor to verify scopes now report present.",
    ]
    return _dry("meta_add_missing_scopes", steps,
                escalation_hint="legal_certification",
                extra={"missing_scopes": missing})


def handle_meta_remove_deprecated_scopes(payload: dict) -> dict:
    deprecated = payload.get("deprecated_scopes") or [
        "manage_pages", "publish_pages", "publish_actions",
        "read_insights", "user_managed_groups",
    ]
    steps = [
        "Open App Dashboard → Permissions & Features (or Login for Business config).",
        f"Un-check deprecated scopes: {deprecated}",
        "Save. This should require NO Meta review because we are only removing.",
        "Re-run meta-setup-doctor; deprecated_scopes list should be empty.",
    ]
    return _dry("meta_remove_deprecated_scopes", steps,
                extra={"deprecated_scopes": deprecated})


def handle_meta_repair_app_config(payload: dict) -> dict:
    profile = payload.get("business_profile") or {}
    steps = [
        "Open https://developers.facebook.com/apps/<APP_ID>/settings/basic/",
        "Set Privacy Policy URL: https://jfortitude.com/legal/privacy",
        "Set Terms of Service URL: https://jfortitude.com/legal/terms",
        "Set Data Deletion Instructions URL: https://jfortitude.com/legal/data-deletion",
        "Set App Category: Education",
        "Upload 1024×1024 app icon from business profile media (fallback: JFLI logo).",
        "Escalate → legal_certification if 'Data Use Checkup' or 'App Review' certification is required.",
        "Save. Re-run meta-setup-doctor to verify app_config_missing is empty.",
    ]
    return _dry("meta_repair_app_config", steps,
                escalation_hint="legal_certification",
                extra={"business_profile_keys": list(profile.keys())})


def handle_meta_manual_repair_step(payload: dict) -> dict:
    intent = payload.get("intent") or "Unspecified generic local repair."
    steps = [
        f"Interpret intent: {intent}",
        "Attempt safest local action inside Jason's browser session.",
        "If action requires posting content → REFUSE (autopilot never posts).",
        "If action requires any of the 5 forced-human categories → escalate.",
        "Otherwise perform, screenshot, log.",
    ]
    return _dry("meta_manual_repair_step", steps,
                extra={"intent": intent})


def _search_web(query: str, max_results: int = 8) -> list[str]:
    """Return candidate URLs from public search endpoints.

    Multi-engine: if one endpoint rate-limits or changes markup, the next one
    is tried. Raises only when EVERY engine fails, so a search failure is never
    silently reported as a successful dry-run.
    """
    try:
        import requests
        from urllib.parse import unquote, quote_plus
    except Exception as exc:
        raise RuntimeError(f"requests_missing: {exc}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    engines = [
        ("post", "https://html.duckduckgo.com/html/"),
        ("post", "https://lite.duckduckgo.com/lite/"),
        ("get", "https://search.marcia.cc/search?q=" + quote_plus(query)),
        ("get", "https://www.bing.com/search?q=" + quote_plus(query)),
    ]
    errors: list[str] = []
    for method, endpoint in engines:
        try:
            if method == "post":
                r = requests.post(endpoint, data={"q": query, "kl": "us-en"},
                                  headers=headers, timeout=30)
            else:
                r = requests.get(endpoint, headers=headers, timeout=30)
            r.raise_for_status()
        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")
            continue

        text = r.text
        urls: list[str] = []
        for m in re.finditer(r'uddg=([^"&]+)', text):
            try:
                decoded = unquote(m.group(1))
                if decoded.startswith("http") and decoded not in urls:
                    urls.append(decoded)
            except Exception:
                continue
        if not urls:
            for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"', text):
                href = m.group(1)
                if any(b in href for b in ("duckduckgo.com", "bing.com", "microsoft.com",
                                           "go.microsoft", "w3.org")):
                    continue
                if href not in urls:
                    urls.append(href)
        if urls:
            return urls[:max_results]
        errors.append(f"{endpoint}: no_results")

    raise RuntimeError("all_search_engines_failed: " + " | ".join(errors[:4]))


_RFP_IDENTITY_STOPWORDS = {
    "a", "an", "and", "application", "for", "fund", "funding", "grant",
    "of", "opportunity", "program", "rfp", "the", "to", "with",
}

_KNOWN_OFFICIAL_RFP_URLS = {
    # Official funder guidance, not the account-registration surface.
    "proliteracy": [
        "https://www.proliteracy.org/grants-funding/literacy-opportunity-fund/",
    ],
}


def _identity_tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", str(value).lower())
        if len(token) > 1 and token not in _RFP_IDENTITY_STOPWORDS
    }


def _candidate_identity_matches(expected: str, candidate: str) -> bool:
    """Require material opportunity/funder overlap before trusting a fuzzy hit."""
    expected_tokens = _identity_tokens(expected)
    candidate_tokens = _identity_tokens(candidate)
    if not expected_tokens or not candidate_tokens:
        return False
    overlap = expected_tokens & candidate_tokens
    if len(expected_tokens) <= 2:
        return len(overlap) >= 1
    return len(overlap) >= 2


def _trusted_payload_urls(payload: dict) -> list[str]:
    """Carry forward explicit canonical URLs without exposing account secrets."""
    values: list[object] = []
    for key in (
        "official_url", "source_url", "rfp_url", "guidelines_url",
        "application_url", "canonical_url", "source_urls",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            values.extend(value)
        elif value:
            values.append(value)
    out: list[str] = []
    for value in values:
        url = str(value).strip()
        if re.match(r"^https?://", url, re.I) and url not in out:
            out.append(url)
    return out


def _search_grants_gov(title: str) -> list[str]:
    """Resolve a matching official grants.gov opportunity.

    Grants.gov search is fuzzy. Never accept its first result until the returned
    title/agency/number materially matches the requested opportunity identity.
    """
    try:
        import requests
    except Exception as exc:
        raise RuntimeError(f"requests_missing: {exc}")
    try:
        r = requests.post(
            "https://api.grants.gov/v1/api/search2",
            json={"keyword": title[:180], "rows": 10,
                  "oppStatuses": "forecasted|posted|closed"},
            timeout=30,
        )
        r.raise_for_status()
        hits = (r.json().get("data") or {}).get("oppHits") or []
        matched = None
        for hit in hits:
            identity = " ".join(str(hit.get(key) or "") for key in (
                "title", "agency", "agencyCode", "number",
            ))
            if _candidate_identity_matches(title, identity):
                matched = hit
                break
        if not matched:
            return []

        opp_id = matched.get("id")
        if not opp_id:
            return []
        out: list[str] = []
        d = requests.post(
            "https://api.grants.gov/v1/api/fetchOpportunity",
            json={"opportunityId": int(opp_id)},
            timeout=30,
        )
        if d.ok:
            data = (d.json() or {}).get("data") or {}
            for folder in data.get("synopsisAttachmentFolders") or []:
                for att in folder.get("synopsisAttachments") or []:
                    if att.get("id"):
                        out.append(
                            "https://www.grants.gov/grantsws/rest/opportunity/att/"
                            f"download/{att['id']}"
                        )
            link = ((data.get("synopsis") or {}).get("fundingDescLinkUrl") or "")
            if link.startswith("http"):
                out.append(link)
        out.append(f"https://www.grants.gov/search-results-detail/{opp_id}")
        return out
    except Exception:
        return []


def _pick_best_rfp_url(urls: list[str], funder_name: str) -> str | None:
    """Prefer PDFs, RFP/guidelines pages, and the funder's own domain."""
    if not urls:
        return None
    funder_slug = re.sub(r"[^a-z0-9]", "", funder_name.lower())[:20]
    score = lambda u: (
        (1 if u.lower().endswith(".pdf") else 0) * 4
        + (1 if re.search(r"(rfp|nofo|guidelines?|application|solicitation|funding|grant)", u, re.I) else 0) * 2
        + (1 if funder_slug and funder_slug in u.lower() else 0) * 2
        + (1 if "grants.gov" in u.lower() else 0)
        - (1 if "duckduckgo" in u.lower() or "google.com" in u.lower() else 0)
    )
    ranked = sorted(urls, key=score, reverse=True)
    return ranked[0]


def handle_grant_rfp_locate(payload: dict) -> dict:
    """Locate the official RFP/NOFO URL for a grant opportunity.

    Executed on the desktop because search engines and funder sites are more
    tolerant of a real user's IP/browser fingerprint than a cloud IP. If a URL
    is found, it is returned in the action result so the server-side worker can
    call read-rfp and unlock drafting.
    """
    funder = str(payload.get("funder_name") or "").strip()
    title = str(payload.get("title") or "").strip()
    opportunity_id = str(payload.get("opportunity_id") or "").strip()
    acquisition_job_id = str(payload.get("acquisition_job_id") or "").strip()

    query_parts = [p for p in [funder, title] if p]
    if not query_parts:
        return {"ok": False, "error": "missing_funder_and_title",
                "opportunity_id": opportunity_id}

    query = " ".join(query_parts) + " RFP application 2026"
    planned_steps = [
        f"Search DuckDuckGo for: {query}",
        "Rank candidates by PDF / RFP / funder-domain signals.",
        "Return the best URL to the server worker.",
        "Server will call read-rfp and update the opportunity.",
    ]

    identity = " ".join(query_parts)
    urls: list[str] = _trusted_payload_urls(payload)
    search_error: str | None = None

    # Known official funder guidance is preferable to a fuzzy registry search.
    funder_key = re.sub(r"[^a-z0-9]", "", funder.lower())
    for key, known_urls in _KNOWN_OFFICIAL_RFP_URLS.items():
        if key in funder_key:
            for url in known_urls:
                if url not in urls:
                    urls.append(url)

    # Grants.gov search is useful only when the returned opportunity identity
    # actually matches. Its first fuzzy hit is never accepted on rank alone.
    if not urls:
        try:
            urls.extend(_search_grants_gov(identity))
        except Exception as e:
            search_error = f"grants_gov: {e}"

    # Open-web candidates must also carry material funder/title identity in
    # their URL. A plausible-looking but unrelated grant URL fails closed.
    if not urls:
        try:
            discovered = _search_web(query, max_results=8)
            urls = [
                url for url in discovered
                if _candidate_identity_matches(identity, url)
            ]
            if discovered and not urls:
                search_error = (
                    f"{search_error + ' | ' if search_error else ''}"
                    "search_results_failed_identity_check"
                )
        except Exception as e:
            search_error = f"{search_error + ' | ' if search_error else ''}{e}"

    best = _pick_best_rfp_url(urls, funder) if urls else None

    if not best:
        # Report the REAL failure. Never return a fake successful dry-run —
        # the server worker must be able to see that this job needs another path.
        rec = {
            "ts": _now(),
            "action_type": "grant_rfp_locate",
            "dry_run": False,
            "ok": False,
            "search_query": query,
            "error": search_error or "no_search_results",
            "opportunity_id": opportunity_id,
            "acquisition_job_id": acquisition_job_id,
        }
        _log(rec)
        return {
            "ok": False,
            "action_type": "grant_rfp_locate",
            "error": search_error or "no_search_results",
            "search_query": query,
            "opportunity_id": opportunity_id,
            "acquisition_job_id": acquisition_job_id,
            "escalation_hint": "manual_search_required",
        }

    rec = {
        "ts": _now(),
        "action_type": "grant_rfp_locate",
        "dry_run": False,
        "enabled": True,
        "planned_steps": planned_steps,
        "search_query": query,
        "found_url": best,
        "candidates": urls,
        "opportunity_id": opportunity_id,
        "acquisition_job_id": acquisition_job_id,
    }
    _log(rec)
    return {
        "ok": True,
        "action_type": "grant_rfp_locate",
        "found_url": best,
        "candidates": urls,
        "search_query": query,
        "opportunity_id": opportunity_id,
        "acquisition_job_id": acquisition_job_id,
        "note": "URL found. Server worker will call read-rfp automatically.",
    }




def handle_invoke_edge_function(payload: dict) -> dict:
    """Dry-run planner for calling a server-side edge function
    (e.g. meta-pages-sync). Real execution will POST from the companion using
    the enrolled device key so results are attributable in audit."""
    fn = payload.get("edge_function") or payload.get("function") or ""
    body = payload.get("body") or {}
    steps = [
        f"Target edge function: {fn or '[missing]'}",
        f"Body keys: {list(body.keys())}",
        "POST to https://<project>.functions.supabase.co/<fn> with device auth headers.",
        "Capture response JSON and attach to desktop_action_results.",
        "Never invoke publisher functions from this path.",
    ]
    if not fn:
        return {"ok": False, "error": "missing_edge_function",
                "dry_run": True, "planned_steps": steps}
    return _dry("invoke_edge_function", steps,
                extra={"edge_function": fn, "body_keys": list(body.keys())})


# ---------------------------------------------------------------------------
# Public registry consumed by unk_companion.py
# ---------------------------------------------------------------------------

AUTOFIX_ACTION_HANDLERS: dict[str, Callable[[dict], dict]] = {
    "meta_refresh_user_token": handle_meta_refresh_user_token,
    "meta_add_missing_scopes": handle_meta_add_missing_scopes,
    "meta_remove_deprecated_scopes": handle_meta_remove_deprecated_scopes,
    "meta_repair_app_config": handle_meta_repair_app_config,
    "meta_manual_repair_step": handle_meta_manual_repair_step,
    "grant_rfp_locate": handle_grant_rfp_locate,
    "invoke_edge_function": handle_invoke_edge_function,
}


def dispatch_browser_session(payload: dict, *, action_type: str | None = None) -> dict:
    """Router for capability=browser_session. Selects by action_type."""
    resolved = (action_type or payload.get("action_type") or "").strip()
    fn = AUTOFIX_ACTION_HANDLERS.get(resolved)
    if not fn:
        return {"ok": False, "error": "unsupported_action_type",
                "action_type": resolved,
                "supported": sorted(AUTOFIX_ACTION_HANDLERS.keys())}
    try:
        result = fn(payload)
    except Exception as e:  # pragma: no cover
        return {"ok": False, "error": "handler_crash",
                "action_type": resolved, "detail": str(e)}
    # After the batch executes in real mode, autopilot itself re-triggers
    # meta-setup-doctor via the workday orchestrator. Handlers just report.
    return result


def dispatch_invoke_edge_function(payload: dict) -> dict:
    """Router for capability=invoke_edge_function (server-side setup calls)."""
    return handle_invoke_edge_function(payload)


def recent_autofix_history(limit: int = 50) -> dict:
    if not AUTOFIX_LOG.exists():
        return {"ok": True, "history": []}
    try:
        lines = AUTOFIX_LOG.read_text(encoding="utf-8").splitlines()[-limit:]
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return {"ok": True, "history": out, "enabled": _enabled()}
    except Exception as e:
        return {"ok": False, "error": "read_failed", "detail": str(e)}
