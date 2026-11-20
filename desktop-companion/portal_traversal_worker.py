"""Portal Traversal Worker — proves a funder application form page-by-page.

Doctrine: a static fetch only sees page 1 plus whatever the form embeds in its
initial HTML/JSON. That is METADATA discovery. This worker performs INTERACTIVE
traversal: it opens the live portal, records the controls on the current page,
fills required non-submission inputs with clearly-marked safe test values,
clicks Next, and repeats until no further page is reachable.

Hard rules:
  * NEVER click Submit / Send / Finish. Submission words are blacklisted.
  * Test values are obviously synthetic so nothing can be mistaken for a filing.
  * Results are posted back to the `portal-traverse` edge function, which sets
    the opportunity's traversal status (metadata_only / partially / fully).

Usage:
    python portal_traversal_worker.py --run-id <uuid> --url <portal url>
It is normally launched by Unk from a `portal_traverse_via_browser`
desktop action request.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_TOKEN = os.environ.get("MCP_SYSTEM_TOKEN") or os.environ.get("SUPABASE_ANON_KEY", "")

SUBMIT_WORDS = re.compile(r"\b(submit|send|finish|complete application|pay|donate)\b", re.I)
NEXT_WORDS = re.compile(r"\b(next|continue|proceed|forward)\b", re.I)

TEST_TEXT = "TEST — NOT A SUBMISSION"
TEST_EMAIL = "traversal-test@example.invalid"
TEST_PHONE = "0000000000"
TEST_NUMBER = "1"
MAX_PAGES = 25


def post_result(payload: dict) -> None:
    url = f"{SUPABASE_URL}/functions/v1/portal-traverse"
    body = json.dumps({"action": "result", **payload}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SERVICE_TOKEN}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        print(res.read().decode()[:500])


async def describe_controls(page, page_index: int) -> list[dict]:
    """Record every real input control visible on the current screen."""
    js = """
    () => {
      const out = [];
      const nodes = document.querySelectorAll('input, textarea, select');
      nodes.forEach((el, i) => {
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
          const wrap = el.closest('label, .form-line, .field, li, div');
          if (wrap) label = (wrap.innerText || '').trim().split('\\n')[0];
        }
        out.push({
          label: (label || el.getAttribute('aria-label') || el.name || `field_${i + 1}`).slice(0, 200),
          name: el.name || null,
          type: el.tagName.toLowerCase() === 'select' ? 'select' :
                el.tagName.toLowerCase() === 'textarea' ? 'textarea' : type,
          required: el.required || el.getAttribute('aria-required') === 'true',
          options: el.tagName.toLowerCase() === 'select'
            ? Array.from(el.options).map(o => o.text.trim()).filter(Boolean) : [],
          max_chars: el.maxLength && el.maxLength > 0 ? el.maxLength : null,
        });
      });
      return out;
    }
    """
    controls = await page.evaluate(js)
    for c in controls:
        c["screen"] = f"Page {page_index}"
        c["discovery_source"] = "portal_traversal"
    return controls


async def fill_required(page) -> None:
    """Satisfy required non-submission controls with obviously synthetic values."""
    inputs = await page.query_selector_all("input, textarea, select")
    for el in inputs:
        try:
            tag = (await el.evaluate("e => e.tagName.toLowerCase()")) or ""
            typ = ((await el.get_attribute("type")) or tag).lower()
            if typ in ("hidden", "submit", "button", "image", "file"):
                continue
            required = await el.evaluate(
                "e => e.required || e.getAttribute('aria-required') === 'true'"
            )
            if not required:
                continue
            if tag == "select":
                opts = await el.evaluate("e => Array.from(e.options).map(o => o.value)")
                real = [o for o in opts if o]
                if real:
                    await el.select_option(real[0])
            elif typ in ("checkbox", "radio"):
                await el.check(timeout=2000)
            elif typ == "email":
                await el.fill(TEST_EMAIL)
            elif typ in ("number", "tel"):
                await el.fill(TEST_PHONE if typ == "tel" else TEST_NUMBER)
            elif typ == "date":
                await el.fill("2026-01-01")
            else:
                await el.fill(TEST_TEXT)
        except Exception:
            continue


async def find_next(page):
    """Return a Next/Continue control, never a submission control."""
    candidates = await page.query_selector_all(
        "button, input[type=button], a[role=button], .form-pagebreak-next"
    )
    for el in candidates:
        try:
            text = ((await el.inner_text()) or (await el.get_attribute("value")) or "").strip()
        except Exception:
            text = ""
        if not text:
            continue
        if SUBMIT_WORDS.search(text):
            continue
        if NEXT_WORDS.search(text):
            return el, text
    return None, None


async def traverse(url: str) -> dict:
    from playwright.async_api import async_playwright

    pages_log: list[dict] = []
    all_controls: list[dict] = []
    complete = False
    error = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            for index in range(1, MAX_PAGES + 1):
                await page.wait_for_timeout(1500)
                controls = await describe_controls(page, index)
                all_controls.extend(controls)
                pages_log.append({"page": index, "url": page.url, "controls": len(controls)})
                await fill_required(page)
                nxt, label = await find_next(page)
                if not nxt:
                    complete = True
                    break
                before = page.url + str(len(controls))
                await nxt.click()
                await page.wait_for_timeout(2500)
                after = page.url + str(len(await describe_controls(page, index)))
                if before == after:
                    # Page did not advance — required validation likely blocked us.
                    pages_log.append({"page": index, "blocked_by": label, "advanced": False})
                    break
        except Exception as exc:  # noqa: BLE001
            error = str(exc)[:500]
        finally:
            await browser.close()

    return {
        "pages_seen": len([p for p in pages_log if "controls" in p]),
        "pages_total": len([p for p in pages_log if "controls" in p]) if complete else None,
        "controls": all_controls,
        "pages": pages_log,
        "complete": complete,
        "error": error,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--url", required=True)
    args = ap.parse_args()

    import asyncio

    result = asyncio.run(traverse(args.url))
    result["run_id"] = args.run_id
    print(json.dumps({k: v for k, v in result.items() if k != "controls"}, indent=2))
    post_result(result)
    return 0 if not result.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())
