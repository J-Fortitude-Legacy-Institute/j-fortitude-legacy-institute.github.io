# Unk Desktop Companion (Phase 3)

Single-file Python companion that runs on your Windows PC, pairs with the JFLI
platform via a one-time enrollment code, and executes **only** approved
desktop actions filed through the Change Gate.

## Install

```powershell
python -m pip install requests pillow keyring playwright
python -m playwright install chromium
```

`pillow` is only needed for `capture_screenshot`. `playwright` is required for
browser-based Facebook Page publishing. `keyring` stores credentials
in Windows Credential Manager instead of a 0600 file under
`%USERPROFILE%\.unk-companion\`.

## First run (enrollment)

1. On the platform: open **/grant-engine/desktop-command** → *Generate
   enrollment code*. Code is valid 15 minutes, one use.
2. On the PC:

   ```powershell
   python .\unk_companion.py
   ```

   Paste the 8-character code when prompted.

If the window closes after you press Enter, run it from an already-open
PowerShell window instead:

```powershell
cd $env:USERPROFILE\Downloads
python .\unk_companion.py --enroll
```

The companion also writes the exact error to
`%USERPROFILE%\.unk-companion\companion.log` and now pauses before closing on
startup/enrollment errors.

If Facebook publishing reports `playwright_not_installed`, run `setup_unk.ps1`
again or use **Update & Restart** from Desktop Command. Newer builds also try a
local Playwright/Chromium repair before failing a publish job.

## Normal run

```powershell
python .\unk_companion.py            # heartbeat loop, polls every 15s
python .\unk_companion.py --status   # one-shot heartbeat, print JSON, exit
python .\unk_companion.py --enroll   # force re-enrollment
```

## Permission profile (edit at top of `unk_companion.py`)

| Knob | Default |
| --- | --- |
| `ALLOWED_ROOTS` | `~/Documents/JFLI`, `~/Documents/Bot-Fresh`, `~/Documents/Grants`, `~/Documents/BAMA`, `~/Downloads/Unk`, `~/.unk-companion` |
| `ALLOWED_EXECUTABLES` | `python`, `python.exe`, `pythonw.exe`, `Bot-Fresh.py`, `notepad.exe` |
| `URL_ALLOWLIST` | TradingView, Coinbase, Google Drive/Docs/Calendar/Mail/Meet, BAMA, JFLI, Facebook/Meta Page publishing surfaces, Grants.gov, Submittable, Instrumentl, Kauffman, MO Humanities, lovable.app/dev |
| `URL_HARD_BLOCKLIST_SUBSTRINGS` | IRS, EFTPS, SAM.gov, major banks (Chase/WF/BofA/USBank), brokerages (Fidelity/Schwab/Vanguard/E\*Trade/Robinhood/TD/IB), payroll (Gusto/ADP/Paychex), QuickBooks Online, Stripe dashboard |
| `OPEN_FILE_DENY_EXT` | `.exe .bat .cmd .com .scr .pif .msi .msp .ps1 .psm1 .vbs .vbe .js .wsf .jar .reg .lnk` |
| `POLL_SECONDS` | 15 |

Anything outside these is refused at the companion, regardless of what the
server sent. Hard-block wins over allow-list.

## Supported capabilities

### Tier 1 — read + narrow write
| capability | payload | risk |
| --- | --- | --- |
| `capture_screenshot` | — | low |
| `read_file` | `{path, max_bytes?}` | low |
| `write_file` | `{path, content}` | medium |
| `launch_process` | `{executable, args[], cwd?}` | medium |
| `run_check` | `{executable, args[]}` | low |

### Tier 2 — open and show
| capability | payload | risk |
| --- | --- | --- |
| `open_url` | `{url}` (must match `URL_ALLOWLIST`, never `URL_HARD_BLOCKLIST_SUBSTRINGS`) | low |
| `connector_escort` | `{provider?, account_email?, url?, checklist?}` opens Lovable and copies the connector checklist; OAuth consent stays human-only | low |
| `open_file` | `{path}` (path allow-list + extension deny-list) | low |
| `reveal_in_explorer` | `{path}` | low |
| `read_clipboard` | — | low |
| `write_clipboard` | `{text}` (≤ 8000 chars) | low |

### Tier 3 — paperwork (medium risk, approval required for write ops)
| capability | payload | risk |
| --- | --- | --- |
| `append_to_file` | `{path, content}` append-only, ≤ 1 MB per call | medium |
| `download_url_to_folder` | `{url, folder?, filename?}` ≤ 25 MB | medium |

### Tier 3 — Meta / Facebook publishing
| capability | payload | risk |
| --- | --- | --- |
| `browser_publish_facebook` | `{job_id, page_slug, message, image_url?, video_url?}` | medium |

### Tier 3 — cloud (runs server-side, no companion needed)
These do **not** run inside the companion. They dispatch through
`supabase/functions/cloud-action-dispatch/index.ts` and the platform's
connected Google / Microsoft connector accounts.

| capability | payload | risk |
| --- | --- | --- |
| `calendar_create_event` | `{summary, start, end, description?, location?, attendees?, calendar_id?}` | medium |
| `email_draft` | `{provider: "google"\|"outlook", to, subject, body, cc?, bcc?}` | medium |

### Tier 4 / Tier 5 — not implemented
Send-for-real email, form submission, file delete/move, anything banking /
brokerage / IRS / payroll. Human-only by design.

Unknown capabilities return `{ok:false, error:"unsupported_capability"}` — they
never execute.

## Run as a self-healing background service

Run `setup_unk.ps1` once from the extracted folder. It installs:

- `UnkSupervisor` — the local watchdog that owns `unk_companion.py`.
- `UnkSupervisorKeepAlive` — a second scheduled task that runs every 5 minutes and restarts/recreates `UnkSupervisor` if Windows stops it or its liveness marker goes stale.
- A Startup-folder fallback that runs the same keepalive script after sign-in.
- If you use **Run installer as admin**, `UnkSupervisorBootKeepAlive` is also added at Windows startup to repair/start the supervisor as early as Windows allows.

Do **not** point Task Scheduler directly at `unk_companion.py`; the supervisor must be the single owner. Logs go to `%USERPROFILE%\.unk-companion\supervisor.log`, `companion.log`, and `keepalive.log`.

## Infrastructure Recovery (Ground Zero doctrine)

The platform now recognizes four *classes* of failure. Each has its own recovery path:

| Class     | Recovery path                                                                                     |
| --------- | ------------------------------------------------------------------------------------------------- |
| Software  | Supervisor restarts the process (`unk_supervisor.py`, backoff ladder).                            |
| Browser   | Companion repairs Playwright/Chromium in place before failing a publish job.                      |
| Power     | BIOS auto-power-on + supervisor auto-launch. Logged as `power_return` in `infrastructure_events`. |
| Internet  | Companion keeps retrying; nothing to restart locally. Logged when connectivity returns.           |

To make **power recovery** work on Ground Zero (no human required):

1. **BIOS / UEFI** → look for a setting named
   *"Restore on AC Power Loss"*, *"AC Power Recovery"*, or
   *"After Power Failure"* → set it to **Power On**.
2. **Windows autostart** — `install_supervisor.ps1` registers the supervisor,
   the keepalive task, the Startup fallback, and—when run as admin—the boot
   keepalive task. The supervisor then launches `unk_companion.py`, which
   unlocks the browser profile and resumes the autonomous sweep.
3. On next boot the supervisor detects a short system uptime combined with a
   stale liveness marker and posts a `power_return` event. The platform stores
   it as a `power` failure class in `infrastructure_events` and shows it on
   **/grant-engine/desktop-heartbeat**.

**Strongly recommended:** a small UPS (battery backup) on the PC + router.
Even a modest unit rides through storm blinks, prevents corrupted browser
profiles, and gives Windows time to shut down cleanly during longer outages.
