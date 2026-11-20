"""Autonomous paperwork form filler for Unk.

Design contract (this is the fix for the "forms keep opening on Jason's
desktop" problem):

  * Unk fills every non-signature / non-certification / non-payment /
    non-CAPTCHA / non-MFA field HEADLESSLY. Jason's screen is never touched
    for the ordinary case.
  * A visible window is opened ONLY when `allow_human_gate=True` is passed by
    the cloud, and the cloud only passes it once per gate (it tracks
    `human_gate_opened_at`). That is the duplicate-window suppression.
  * Every run returns a structured receipt: fields_completed, fields_blocked
    (each with a reason code), whether the draft saved, and the screenshot.

Reason codes returned in `fields_blocked[].reason_code` / `blocker_reason_code`:
    signature_required, legal_certification_required, payment_approval_required,
    captcha_required, mfa_required, missing_fact, login_required,
    selector_drift, portal_unreachable, save_draft_unavailable
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from meta_browser_publisher import (  # reuse the hardened browser plumbing

    PROFILE_DIR,
    UNK_CHROMIUM_ARGS,
    _ensure_playwright_ready,
    _release_locked_profile,
    _screenshot_path,
)
# --- Unk window policy: never flash a console window, never steal focus ---
try:
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args
    _install_quiet_subprocess()
except Exception:  # policy module missing -> behave as before
    def _win_browser_args(base=None, **_kw):
        return list(base or [])


# --- Human-only gate detection ---------------------------------------------
# Each entry: (reason_code, [css selectors that prove the gate is present])
GATE_PROBES: list[tuple[str, list[str]]] = [
    ("captcha_required", [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        "iframe[src*='challenges.cloudflare.com']",
        "div.g-recaptcha",
        "div[class*='captcha']",
    ]),
    ("signature_required", [
        "canvas[class*='signature']",
        "canvas[id*='signature']",
        "iframe[src*='docusign']",
        "iframe[src*='hellosign']",
        "iframe[src*='adobesign']",
        "[data-testid*='signature']",
    ]),
    ("payment_approval_required", [
        "iframe[src*='js.stripe.com']",
        "iframe[title*='card number' i]",
        "input[name*='cardnumber' i]",
        "input[autocomplete='cc-number']",
    ]),
    ("mfa_required", [
        "input[autocomplete='one-time-code']",
        "input[name*='otp' i]",
        "input[id*='verification_code' i]",
        "input[name*='mfa' i]",
    ]),
    ("login_required", [
        "input[type='password']",
    ]),
]

# Field labels that are legal certifications — never auto-checked, even when a
# value is supplied by the cloud.
CERTIFICATION_HINTS = (
    "certif", "under penalt", "perjur", "i attest", "attestation",
    "i declare", "authorized signer", "signature of", "notar",
)


def _detect_gates(page) -> list[dict]:
    found: list[dict] = []
    for reason_code, selectors in GATE_PROBES:
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=800):
                    found.append({"reason_code": reason_code, "selector": sel})
                    break
            except Exception:
                continue
    return found


def _is_certification(field: dict) -> bool:
    text = f"{field.get('label') or ''} {field.get('key') or ''}".lower()
    return any(h in text for h in CERTIFICATION_HINTS)


def _resolve(page, field: dict):
    """Return the first matching, visible locator for a field, or None."""
    selectors = list(field.get("selectors") or [])
    label = (field.get("label") or "").strip()
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                return loc
        except Exception:
            continue
    if label:
        for getter in ("get_by_label", "get_by_placeholder"):
            try:
                loc = getattr(page, getter)(label, exact=False).first
                if loc.count() > 0 and loc.is_visible(timeout=800):
                    return loc
            except Exception:
                continue
    return None


def _fill_one(page, loc, field: dict) -> str:
    """Fill a single control. Returns 'filled' or a reason code."""
    value = field.get("value")
    kind = (field.get("kind") or "text").lower()
    try:
        if kind in ("checkbox", "radio"):
            if value in (True, "true", "yes", "1"):
                loc.check(timeout=4000)
            return "filled"
        if kind == "select":
            loc.select_option(str(value), timeout=4000)
            return "filled"
        if kind == "file":
            loc.set_input_files(str(value), timeout=15000)
            return "filled"
        loc.fill(str(value), timeout=5000)
        return "filled"
    except Exception:
        return "selector_drift"


def _save_draft(page, save_selectors: list[str], notes: list[str]) -> bool:
    candidates = list(save_selectors) + [
        "button:has-text('Save draft')",
        "button:has-text('Save Draft')",
        "button:has-text('Save and continue')",
        "button:has-text('Save & Continue')",
        "button:has-text('Save')",
        "input[type='submit'][value*='Save' i]",
        "[data-testid*='save']",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=800):
                loc.click(timeout=6000)
                time.sleep(2.0)
                notes.append(f"saved_draft_via:{sel}")
                return True
        except Exception:
            continue
    notes.append("save_draft_unavailable")
    return False


def autofill(
    url: str,
    fields: Optional[list] = None,
    attachments: Optional[list] = None,
    save_selectors: Optional[list] = None,
    allow_human_gate: bool = False,
    task_id: Optional[str] = None,
    **_ignored: Any,
) -> dict:
    """Fill a paperwork form autonomously and return a receipt.

    `allow_human_gate=False` (the default) means: never show a window. This is
    the mode the continuous queue uses on every ordinary pass.
    """
    fields = list(fields or [])
    attachments = list(attachments or [])
    notes: list[str] = []
    receipt: dict = {
        "ok": False,
        "task_id": task_id,
        "url": url,
        "fields_completed": [],
        "fields_blocked": [],
        "gates_detected": [],
        "saved_draft": False,
        "blocker_reason_code": None,
        "next_automatic_action": None,
        "screenshot_path": None,
        "notes": notes,
        "human_window_opened": bool(allow_human_gate),
    }

    ready, ready_err = _ensure_playwright_ready(notes)
    if not ready:
        receipt["blocker_reason_code"] = "portal_unreachable"
        receipt["error"] = ready_err or "playwright_not_ready"
        return receipt

    from playwright.sync_api import sync_playwright  # type: ignore

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            _release_locked_profile(notes)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=not allow_human_gate,
                viewport={"width": 1400, "height": 1000},
                args=_win_browser_args(UNK_CHROMIUM_ARGS, visible_required=bool(allow_human_gate)),
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as exc:
                receipt["blocker_reason_code"] = "portal_unreachable"
                receipt["error"] = str(exc)[:300]
                context.close()
                return receipt
            time.sleep(2.5)

            gates = _detect_gates(page)
            receipt["gates_detected"] = gates
            gate_codes = {g["reason_code"] for g in gates}

            # A login wall means nothing else on the page is trustworthy.
            if "login_required" in gate_codes:
                shot = _screenshot_path("paperwork_login_required")
                try:
                    page.screenshot(path=str(shot))
                    receipt["screenshot_path"] = str(shot)
                except Exception:
                    pass
                receipt["blocker_reason_code"] = "login_required"
                receipt["next_automatic_action"] = (
                    "retry after session repair; queue will not reopen this form"
                )
                context.close()
                return receipt

            # Fill everything that is not a human-only gate.
            for field in fields:
                key = field.get("key") or field.get("label") or "?"
                value = field.get("value")

                if _is_certification(field):
                    receipt["fields_blocked"].append({
                        "field": key, "reason_code": "legal_certification_required"})
                    continue
                if field.get("human_only_reason"):
                    receipt["fields_blocked"].append({
                        "field": key, "reason_code": field["human_only_reason"]})
                    continue
                if value in (None, ""):
                    receipt["fields_blocked"].append({
                        "field": key, "reason_code": "missing_fact"})
                    continue

                loc = _resolve(page, field)
                if loc is None:
                    receipt["fields_blocked"].append({
                        "field": key, "reason_code": "selector_drift"})
                    continue
                outcome = _fill_one(page, loc, field)
                if outcome == "filled":
                    receipt["fields_completed"].append(key)
                else:
                    receipt["fields_blocked"].append({
                        "field": key, "reason_code": outcome})

            # Attach documents to any file inputs that are still empty.
            for att in attachments:
                sel = att.get("selector") or "input[type='file']"
                path = att.get("path")
                if not path or not Path(str(path)).exists():
                    receipt["fields_blocked"].append({
                        "field": att.get("key") or sel, "reason_code": "missing_fact"})
                    continue
                try:
                    page.locator(sel).first.set_input_files(str(path), timeout=20000)
                    receipt["fields_completed"].append(att.get("key") or sel)
                except Exception:
                    receipt["fields_blocked"].append({
                        "field": att.get("key") or sel, "reason_code": "selector_drift"})

            receipt["saved_draft"] = _save_draft(page, list(save_selectors or []), notes)

            shot = _screenshot_path("paperwork_receipt")
            try:
                page.screenshot(path=str(shot))
                receipt["screenshot_path"] = str(shot)
            except Exception:
                pass

            # Decide the blocker for the run as a whole. Human-only gates win.
            for code in ("signature_required", "legal_certification_required",
                         "payment_approval_required", "captcha_required",
                         "mfa_required"):
                if code in gate_codes or any(
                    b["reason_code"] == code for b in receipt["fields_blocked"]
                ):
                    receipt["blocker_reason_code"] = code
                    break
            else:
                if any(b["reason_code"] == "missing_fact"
                       for b in receipt["fields_blocked"]):
                    receipt["blocker_reason_code"] = "missing_fact"
                elif any(b["reason_code"] == "selector_drift"
                         for b in receipt["fields_blocked"]):
                    receipt["blocker_reason_code"] = "selector_drift"

            if receipt["blocker_reason_code"] is None:
                receipt["next_automatic_action"] = "advance task to complete"
            elif receipt["blocker_reason_code"] == "selector_drift":
                receipt["next_automatic_action"] = "auto-retry with refreshed selectors"
            else:
                receipt["next_automatic_action"] = (
                    "hold for human gate; auto-resume when cleared"
                )

            receipt["ok"] = True
            context.close()
            return receipt
    except Exception as exc:
        receipt["blocker_reason_code"] = "portal_unreachable"
        receipt["error"] = str(exc)[:300]
        return receipt


def dry_run(url: str, fields: Optional[list] = None, **_ignored: Any) -> dict:
    """Plan-only pass: classify every field without touching a browser."""
    fields = list(fields or [])
    plan_fill, plan_block = [], []
    for field in fields:
        key = field.get("key") or field.get("label") or "?"
        if _is_certification(field):
            plan_block.append({"field": key, "reason_code": "legal_certification_required"})
        elif field.get("human_only_reason"):
            plan_block.append({"field": key, "reason_code": field["human_only_reason"]})
        elif field.get("value") in (None, ""):
            plan_block.append({"field": key, "reason_code": "missing_fact"})
        else:
            plan_fill.append(key)
    return {
        "ok": True,
        "mode": "dry_run",
        "url": url,
        "fields_completed": plan_fill,
        "fields_blocked": plan_block,
        "saved_draft": False,
        "human_window_opened": False,
        "blocker_reason_code": (plan_block[0]["reason_code"] if plan_block else None),
        "next_automatic_action": (
            "execute autofill headlessly" if not plan_block
            else "execute autofill headlessly, then hold only the blocked fields"
        ),
    }
