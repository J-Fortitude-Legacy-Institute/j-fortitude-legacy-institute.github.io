"""Portal Login Worker — executes `browser_portal_login` desktop actions.

Handles the three action types the Grant Engine portal broker dispatches:

  * portal_register_account  — create the funder-portal account for the
    canonically authorized applicant entity.
  * portal_session_login     — sign in and open the application.
  * portal_session_resume    — resume the SAME session after a human cleared a
    verification checkpoint.

Hard rules (non-negotiable):
  * NEVER accept legal terms / privacy agreements / attestations.
  * NEVER certify, sign, or attest under penalties of perjury.
  * NEVER authorize or make a payment.
  * NEVER final-submit an application.
  * Credentials are fetched one-time from the portal credential vault, held in
    memory only, and NEVER printed, logged, or written to disk.

Human-only checkpoints (CAPTCHA, SMS/authenticator approval, emailed code)
pause the run through the existing vault checkpoint path; the same browser
profile is reused on resume so work continues exactly where it stopped.

Usage (normally launched by Unk from a desktop action request):
    python portal_login_worker.py --mode register --payload-file <json>
    python portal_login_worker.py --mode login    --payload-file <json>
    python portal_login_worker.py --mode resume   --payload-file <json>
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"
SERVICE_TOKEN = os.environ.get("MCP_SYSTEM_TOKEN") or os.environ.get("SUPABASE_ANON_KEY", "")
ANON_TOKEN = os.environ.get("SUPABASE_ANON_KEY", "")
DEVICE_ID = os.environ.get("UNK_DEVICE_ID", "")
DEVICE_KEY = os.environ.get("UNK_DEVICE_KEY", "")

def _reject_wrong_project_jwt(token: str) -> bool:
    """Refuse a project-bound anon JWT from any project other than owner K.

    Public sb_publishable keys are opaque; backend auth remains authoritative
    for those. This check only rejects independently identifiable wrong-project
    JWT credentials before any portal request uses them.
    """
    if not token or not token.startswith("eyJ") or token.count(".") != 2:
        return False
    try:
        segment = token.split(".")[1]
        payload = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        return payload.get("ref") != "kwbegsybeyyxfmavjswv"
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        return True


PROFILE_ROOT = Path.home() / "Documents" / "JFLI" / "portal_profiles"
RECEIPT_DIR = Path.home() / "Documents" / "JFLI" / "portal_receipts"

# Never click anything matching these.
FORBIDDEN_WORDS = re.compile(
    r"\b(submit|sign\s*and\s*submit|final\s*submit|certify|certification|signature|e-?sign|"
    r"sign(?!\s*(?:in|up|on)\b)|attest|agree|accept|i\s+consent|pay|payment|checkout|purchase|authorize)\b",
    re.I,
)
SAVE_WORDS = re.compile(r"\b(save|save\s+(and\s+)?(continue|draft|progress)|save\s+for\s+later)\b", re.I)
NEXT_WORDS = re.compile(r"\b(next|continue|proceed|forward)\b", re.I)

CAPTCHA_HINTS = ("recaptcha", "hcaptcha", "captcha", "cf-turnstile", "are you a robot")
SMS_HINTS = ("verification code", "one-time code", "authenticator", "text message", "sms code", "approve the sign-in")
EMAIL_HINTS = ("verify your email", "confirmation email", "check your inbox", "email verification")

PAY_GOV_FORM_1023 = "704509645"


# --------------------------------------------------------------------------
# Edge function IO
# --------------------------------------------------------------------------

def _post(fn: str, body: dict, timeout: int = 90) -> dict:
    if _reject_wrong_project_jwt(SERVICE_TOKEN):
        return {"ok": False, "error": "noncanonical_portal_credential_project"}
    url = f"{SUPABASE_URL}/functions/v1/{fn}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SERVICE_TOKEN}",
            "X-MCP-System-Token": SERVICE_TOKEN,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode()
    except urllib.error.HTTPError as exc:  # keep the status, drop nothing secret
        raw = exc.read().decode()[:1000]
        return {"ok": False, "http_status": exc.code, "error": raw}
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": raw[:500]}


def vault(action: str, **body) -> dict:
    return _post("portal-credential-vault", {"action": action, **body})


def device_session(action: str, **body) -> dict:
    """Use the enrolled Ground Zero identity; never serialize its key."""
    if not DEVICE_ID or not DEVICE_KEY:
        return {"ok": False, "error": "device_credentials_unavailable"}
    if _reject_wrong_project_jwt(ANON_TOKEN):
        return {"ok": False, "error": "noncanonical_portal_credential_project"}
    url = f"{SUPABASE_URL}/functions/v1/portal-worker-session"
    req = urllib.request.Request(
        url,
        data=json.dumps({"action": action, **body}).encode(),
        headers={
            "Content-Type": "application/json",
            "apikey": ANON_TOKEN,
            "Authorization": f"Bearer {ANON_TOKEN}",
            "X-Device-Id": DEVICE_ID,
            "X-Device-Key": DEVICE_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            raw = res.read().decode()
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()[:1000]
        return {"ok": False, "http_status": exc.code, "error": raw}
    try:
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": raw[:500]}


def redact(value: object) -> str:
    """Never emit a secret. Only its shape."""
    s = "" if value is None else str(value)
    return f"<redacted:{len(s)}>"


def registration_profile_gaps(url: str, profile: dict) -> list[str]:
    """Return explicit facts required by the known multi-step ProLiteracy form."""
    u = (url or "").lower()
    if "grantinterface.com" not in u or "urlkey=prolit" not in u:
        return []

    requirements = {
        "contact_phone": ("contact_phone", "phone"),
        "city": ("city", "contact_city"),
        "postal_code": ("postal_code", "zip"),
        "country": ("country",),
        "contact_prefix": ("contact_prefix", "prefix"),
        "contact_title": ("contact_title", "business_title"),
        "executive_officer_response": ("executive_officer_response", "is_executive_officer"),
    }

    def present(keys: tuple[str, ...]) -> bool:
        for key in keys:
            if key in profile and profile.get(key) is not None and str(profile.get(key)).strip() != "":
                return True
        return False

    return [label for label, keys in requirements.items() if not present(keys)]


# --------------------------------------------------------------------------
# Page inspection
# --------------------------------------------------------------------------

CONTROL_JS = """
() => {
  const out = [];
  document.querySelectorAll('input, textarea, select').forEach((el, i) => {
    const type = (el.getAttribute('type') || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'image'].includes(type)) return;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return;
    let label = '';
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l) label = l.innerText.trim();
    }
    if (!label) {
      const wrap = el.closest('label, .field, li, div');
      if (wrap) label = (wrap.innerText || '').trim().split('\\n')[0];
    }
    out.push({
      label: (label || el.getAttribute('aria-label') || el.name || `field_${i + 1}`).slice(0, 200),
      name: el.name || null,
      key: el.name || el.id || null,
      type: el.tagName.toLowerCase() === 'select' ? 'select'
          : el.tagName.toLowerCase() === 'textarea' ? 'textarea' : type,
      required: el.required || el.getAttribute('aria-required') === 'true',
      options: el.tagName.toLowerCase() === 'select'
        ? Array.from(el.options).map(o => o.text.trim()).filter(Boolean) : [],
      max_chars: el.maxLength && el.maxLength > 0 ? el.maxLength : null,
    });
  });
  return out;
}
"""


async def describe_controls(page, screen: str) -> list[dict]:
    controls = await page.evaluate(CONTROL_JS)
    for c in controls:
        c["screen"] = screen
        c["discovery_source"] = "portal_traversal"
    return controls


async def detect_human_checkpoint(page) -> str | None:
    """Return a checkpoint kind when only a person can proceed."""
    try:
        html = (await page.content()).lower()
    except Exception:  # noqa: BLE001
        return None
    if any(h in html for h in CAPTCHA_HINTS):
        return "captcha"
    if any(h in html for h in SMS_HINTS):
        return "sms_2fa"
    if any(h in html for h in EMAIL_HINTS):
        return "email_verification"
    return None


async def click_safe(page, matcher: re.Pattern) -> str | None:
    """Click a control matching `matcher` — never one matching FORBIDDEN_WORDS."""
    els = await page.query_selector_all("button, input[type=button], input[type=submit], a[role=button], a")
    for el in els:
        try:
            text = ((await el.inner_text()) or (await el.get_attribute("value")) or "").strip()
        except Exception:  # noqa: BLE001
            continue
        if not text or FORBIDDEN_WORDS.search(text):
            continue
        if matcher.search(text):
            try:
                await el.click(timeout=5000)
                await page.wait_for_timeout(2000)
                return text[:80]
            except Exception:  # noqa: BLE001
                continue
    return None


async def fill_by_label(page, label_pattern: str, value: str) -> bool:
    """Fill the first visible field whose label/name/placeholder matches."""
    rx = re.compile(label_pattern, re.I)
    els = await page.query_selector_all("input, textarea, select")
    for el in els:
        try:
            typ = ((await el.get_attribute("type")) or "").lower()
            if typ in ("hidden", "submit", "button", "image", "file", "checkbox", "radio"):
                continue
            meta = " ".join(
                filter(
                    None,
                    [
                        await el.get_attribute("name") or "",
                        await el.get_attribute("id") or "",
                        await el.get_attribute("aria-label") or "",
                        await el.get_attribute("placeholder") or "",
                        await el.evaluate(
                            "e => { const l = e.id && document.querySelector(`label[for=\"${e.id}\"]`);"
                            " return l ? l.innerText : (e.closest('label')?.innerText || ''); }"
                        )
                        or "",
                    ],
                )
            )
            if not rx.search(meta):
                continue
            if (await el.evaluate("e => e.tagName.toLowerCase()")) == "select":
                continue
            existing = await el.input_value()
            if existing and existing.strip():
                return True
            await el.fill(value)
            return True
        except Exception:  # noqa: BLE001
            continue
    return False


# --------------------------------------------------------------------------
# Browser session (persistent profile => same session resumes)
# --------------------------------------------------------------------------

async def open_context(playwright, profile_key: str, headless: bool):
    profile = PROFILE_ROOT / re.sub(r"[^a-zA-Z0-9_-]", "_", profile_key or "default")
    profile.mkdir(parents=True, exist_ok=True)
    ctx = await playwright.chromium.launch_persistent_context(
        str(profile),
        headless=headless,
        viewport={"width": 1280, "height": 1800},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    return ctx, page


# --------------------------------------------------------------------------
# Mirroring captured schema back through the canonical section-sync path
# --------------------------------------------------------------------------

def mirror_sections(opportunity_id: str | None, organization_id: str | None, controls: list[dict]) -> dict:
    if not opportunity_id or not controls:
        return {"mirrored": False, "reason": "no_opportunity_or_controls"}
    cap = _post(
        "portal-section-sync",
        {
            "action": "capture",
            "opportunity_id": opportunity_id,
            "organization_id": organization_id,
            "controls": controls,
        },
    )
    pre = _post(
        "portal-section-sync",
        {"action": "prefill", "opportunity_id": opportunity_id, "organization_id": organization_id},
    )
    return {
        "mirrored": bool(cap.get("ok")),
        "sections": cap.get("sections_upserted") or cap.get("sections") or None,
        "fields": cap.get("fields_upserted") or None,
        "prefilled": pre.get("filled") if isinstance(pre, dict) else None,
        "prefill_human_only_skipped": pre.get("human_only_skipped") if isinstance(pre, dict) else None,
        "capture_error": None if cap.get("ok") else cap.get("error"),
    }


# --------------------------------------------------------------------------
# Pay.gov Form 1023
# --------------------------------------------------------------------------

def is_pay_gov_1023(url: str) -> bool:
    u = (url or "").lower()
    return "pay.gov" in u and PAY_GOV_FORM_1023 in u


async def fill_form_1023(page, plan: dict, receipts: list[dict]) -> dict:
    """Populate current Parts I-X + Schedule H from the live form_1023 workspace.

    Stops before the authorized-signer certification, the $600 user fee, and
    final submit. Those remain human-only, every time.
    """
    filled = 0
    skipped_human_only = 0
    unmatched: list[str] = []
    pages_seen: list[dict] = []
    sections = plan.get("sections") or []

    for screen_index in range(1, 40):
        await page.wait_for_timeout(1200)
        checkpoint = await detect_human_checkpoint(page)
        if checkpoint:
            return {
                "filled": filled,
                "human_only_skipped": skipped_human_only,
                "unmatched": unmatched[:40],
                "pages": pages_seen,
                "checkpoint": checkpoint,
            }
        controls = await describe_controls(page, f"Pay.gov screen {screen_index}")
        pages_seen.append({"screen": screen_index, "url": page.url, "controls": len(controls)})

        for sec in sections:
            if sec.get("human_only"):
                skipped_human_only += 1
                continue
            answer = (sec.get("answer_draft") or "").strip()
            if not answer:
                continue
            line_ref = str(sec.get("line_ref") or "").strip()
            label = str(sec.get("title") or "").strip()
            pattern = re.escape(line_ref) if line_ref else re.escape(label[:40])
            if not pattern:
                continue
            if await fill_by_label(page, pattern, answer[:5000]):
                filled += 1
                receipts.append(
                    {
                        "kind": "form_1023_field_filled",
                        "part": sec.get("part_code"),
                        "line_ref": line_ref or None,
                        "section_key": sec.get("section_key"),
                        "chars": len(answer),
                    }
                )
            else:
                unmatched.append(f"{sec.get('part_code')} {line_ref or label}"[:80])

        saved = await click_safe(page, SAVE_WORDS)
        if saved:
            receipts.append({"kind": "progress_saved", "control": saved, "screen": screen_index})
        advanced = await click_safe(page, NEXT_WORDS)
        if not advanced:
            break

    return {
        "filled": filled,
        "human_only_skipped": skipped_human_only,
        "unmatched": unmatched[:40],
        "pages": pages_seen,
        "checkpoint": None,
    }


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------

async def run_register(payload: dict, headless: bool) -> dict:
    from playwright.async_api import async_playwright

    receipt_id = payload.get("registration_receipt_id")
    account_id = payload.get("portal_account_id")
    url = payload.get("portal_url") or ""
    profile = payload.get("registration_profile") or {}
    opportunity_id = payload.get("opportunity_id")
    org = payload.get("organization_id")
    receipts: list[dict] = []

    session_id = payload.get("portal_session_id")
    if not session_id:
        return {"ok": False, "error": "device_session_required"}

    missing_fields = registration_profile_gaps(url, profile)
    if missing_fields:
        return {
            "ok": False,
            "mode": "register",
            "error": "registration_profile_incomplete",
            "checkpoint": "human_action",
            "human_action_required": True,
            "missing_fields": missing_fields,
            "registration_confirmed": False,
            "registration_receipt_id": receipt_id,
            "portal_account_id": account_id,
            "never_submitted": True,
            "never_accepted_terms": True,
            "never_certified": True,
        }

    creds = device_session("fetch", portal_session_id=session_id)
    if not creds.get("username"):
        return {"ok": False, "error": "credential_fetch_failed", "detail": creds.get("error")}

    username, password = creds["username"], creds["password"]
    controls: list[dict] = []
    checkpoint = None
    error = None
    registration_confirmed = False

    async with async_playwright() as p:
        ctx, page = await open_context(p, f"account-{account_id}", headless)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            await click_safe(page, re.compile(r"\b(register|create (?:(?:a|an|new) )?account|sign up|new user)\b", re.I))
            await page.wait_for_timeout(1500)

            await fill_by_label(page, r"user\s*name|login|username", username)
            await fill_by_label(page, r"e-?mail", str(profile.get("contact_email") or creds.get("recovery_email") or ""))
            await fill_by_label(page, r"\bpassword\b", password)
            await fill_by_label(page, r"confirm.*password|password.*confirm", password)
            for key, pattern in (
                ("legal_organization_name", r"organi[sz]ation|entity|nonprofit"),
                ("ein", r"\bein\b|tax id|employer identification"),
                ("address", r"address|street"),
                ("state", r"\bstate\b"),
                ("contact_name", r"contact name|full name|your name"),
                ("contact_phone", r"phone"),
            ):
                val = profile.get(key)
                if val:
                    await fill_by_label(page, pattern, str(val))

            receipts.append({"kind": "registration_form_filled", "url": page.url, "credential": redact(username)})

            checkpoint = await detect_human_checkpoint(page)
            before_submit_url = page.url
            clicked = None
            if not checkpoint:
                clicked = await click_safe(page, re.compile(r"\b(create account|register|sign up)\b", re.I))
                if clicked:
                    receipts.append({"kind": "registration_control_clicked", "control": clicked})
                    await page.wait_for_timeout(4000)
                    checkpoint = await detect_human_checkpoint(page)
                else:
                    error = "registration_control_not_found"
                    receipts.append({"kind": "registration_control_not_found"})

            page_text = ((await page.locator("body").inner_text()) or "").lower()
            success_markers = (
                "account created",
                "registration complete",
                "welcome",
                "check your email",
                "verify your email",
            )
            password_still_visible = bool(await page.query_selector("input[type=password]"))
            registration_confirmed = bool(clicked) and not checkpoint and (
                page.url != before_submit_url or any(marker in page_text for marker in success_markers)
            ) and not password_still_visible
            if not checkpoint and not registration_confirmed:
                error = error or "registration_outcome_unverified"

            controls = await describe_controls(page, "Registration")
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:400]
        finally:
            await ctx.close()

    del password  # noqa: F821 — never persisted anywhere

    progress = device_session(
        "record_login",
        portal_session_id=session_id,
        success=registration_confirmed,
        needs_human=bool(checkpoint),
        failure_reason=error or (checkpoint and f"checkpoint:{checkpoint}"),
    )
    mirror = mirror_sections(opportunity_id, org, controls)
    return {
        "ok": bool(registration_confirmed or checkpoint) and not error,
        "mode": "register",
        "registration_confirmed": registration_confirmed,
        "registration_receipt_id": receipt_id,
        "portal_account_id": account_id,
        "checkpoint": checkpoint,
        "human_action_required": bool(checkpoint),
        "progress": progress,
        "mirror": mirror,
        "receipts": receipts,
        "error": error,
        "never_submitted": True,
        "never_accepted_terms": True,
        "never_certified": True,
    }


async def run_login(payload: dict, headless: bool, resume: bool) -> dict:
    from playwright.async_api import async_playwright

    session_id = payload.get("portal_session_id")
    receipts: list[dict] = []
    creds = device_session("fetch", portal_session_id=session_id)
    already_issued = "already" in str(creds.get("error", "")).lower()
    if not creds.get("username") and not (resume and already_issued):
        return {"ok": False, "error": "credential_fetch_failed", "detail": creds.get("error")}

    url = creds.get("portal_url") or payload.get("portal_url") or ""
    target = payload.get("target_application_url")
    username = creds.get("username")
    password = creds.get("password")

    controls: list[dict] = []
    checkpoint = None
    error = None
    signed_in = False
    form_1023 = None

    async with async_playwright() as p:
        ctx, page = await open_context(p, f"session-{payload.get('portal_account_id') or session_id}", headless)
        try:
            await page.goto(target or url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)

            needs_login = bool(await page.query_selector("input[type=password]"))
            if needs_login and username and password:
                await fill_by_label(page, r"user\s*name|login|e-?mail|username", username)
                await fill_by_label(page, r"password", password)
                clicked = await click_safe(page, re.compile(r"\b(sign in|log ?in|continue)\b", re.I))
                receipts.append({"kind": "sign_in_control_clicked", "control": clicked, "credential": redact(username)})
                await page.wait_for_timeout(4000)
            elif not needs_login:
                receipts.append({"kind": "existing_session_reused", "url": page.url})

            checkpoint = await detect_human_checkpoint(page)
            signed_in = not checkpoint and not await page.query_selector("input[type=password]")

            if signed_in and target and page.url != target:
                await page.goto(target, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
                checkpoint = await detect_human_checkpoint(page)

            if signed_in and is_pay_gov_1023(target or url):
                plan = vault("worker_form_1023_plan")
                if plan.get("ok"):
                    form_1023 = await fill_form_1023(page, plan, receipts)
                    checkpoint = checkpoint or form_1023.get("checkpoint")
                    form_1023["stopped_before"] = [
                        "authorized_signer_certification",
                        "user_fee_payment_600",
                        "final_submit",
                    ]
                    form_1023["upload_packet"] = plan.get("upload_packet")
                else:
                    form_1023 = {"error": plan.get("error"), "filled": 0}

            if signed_in:
                controls = await describe_controls(page, "Application")
                saved = await click_safe(page, SAVE_WORDS)
                if saved:
                    receipts.append({"kind": "progress_saved", "control": saved})
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:400]
        finally:
            await ctx.close()

    password = None  # never persisted

    progress = device_session(
        "record_login",
        portal_session_id=session_id,
        success=bool(signed_in),
        needs_human=bool(checkpoint),
        failure_reason=error or (checkpoint and f"checkpoint:{checkpoint}"),
    )

    mirror = mirror_sections(payload.get("opportunity_id"), payload.get("organization_id"), controls)
    return {
        "ok": bool(signed_in) and not error,
        "mode": "resume" if resume else "login",
        "portal_session_id": session_id,
        "signed_in": signed_in,
        "checkpoint": checkpoint,
        "human_action_required": bool(checkpoint),
        "form_1023": form_1023,
        "progress": progress,
        "mirror": mirror,
        "receipts": receipts,
        "error": error,
        "never_submitted": True,
        "never_accepted_terms": True,
        "never_certified": True,
        "never_paid": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["register", "login", "resume"])
    ap.add_argument("--payload-file", required=True)
    ap.add_argument("--headed", action="store_true", help="show the browser (human checkpoints)")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    import asyncio

    headless = not args.headed
    if args.mode == "register":
        result = asyncio.run(run_register(payload, headless))
    else:
        result = asyncio.run(run_login(payload, headless, resume=args.mode == "resume"))

    try:
        RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = payload.get("portal_session_id") or payload.get("registration_receipt_id") or "run"
        (RECEIPT_DIR / f"{stamp}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    print(json.dumps(result, indent=2)[:8000])
    return 0 if result.get("ok") or result.get("human_action_required") else 1


if __name__ == "__main__":
    sys.exit(main())
