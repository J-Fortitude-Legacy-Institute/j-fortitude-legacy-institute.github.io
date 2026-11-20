"""
Unk Meta Media Engine — one-time credential capture.

Run this once on the PC that will publish to Facebook / Instagram through the
Meta Graph API. It stores:
  - non-sensitive config (app_id, page_id, provider) in a 0600 JSON file
  - secrets (app_secret, page_access_token) in the OS keyring when available,
    otherwise in 0600-protected files under ~/.unk_companion/

Never paste these values into ChatGPT or any web chat. This script keeps them
local to this machine.
"""

import getpass
import json
import os
import webbrowser
from pathlib import Path

try:
    import keyring
except ImportError:
    keyring = None

SERVICE = "jfortitude_meta_media_engine"
CONFIG_DIR = Path.home() / ".unk_companion"
CONFIG_FILE = CONFIG_DIR / "meta_media_engine.json"


def save_secret(name: str, value: str):
    if keyring:
        keyring.set_password(SERVICE, name, value)
    else:
        CONFIG_DIR.mkdir(exist_ok=True)
        fallback_file = CONFIG_DIR / f"{name}.secret"
        fallback_file.write_text(value, encoding="utf-8")
        os.chmod(fallback_file, 0o600)


def main():
    print("\n=== Unk Meta Media Engine Key Capture ===")
    print("Do NOT paste these keys into ChatGPT.")
    print("This stores them locally on this computer.\n")

    print("Opening Meta Developer Apps page...")
    webbrowser.open("https://developers.facebook.com/apps/")

    input("\nCreate/open your Meta app, then press ENTER here...")

    app_id = input("Paste Meta App ID: ").strip()
    app_secret = getpass.getpass("Paste Meta App Secret: ").strip()

    print("\nNow open Graph API Explorer / Access Token Tool.")
    webbrowser.open("https://developers.facebook.com/tools/explorer/")
    input("Generate/copy your Page Access Token, then press ENTER...")

    page_access_token = getpass.getpass("Paste Page Access Token: ").strip()
    page_id = input("Paste Facebook Page ID: ").strip()

    CONFIG_DIR.mkdir(exist_ok=True)

    public_config = {
        "provider": "meta",
        "app_id": app_id,
        "page_id": page_id,
        "secret_store": "system_keyring" if keyring else "local_600_files",
        "service": SERVICE,
    }

    # Save the non-sensitive configuration
    CONFIG_FILE.write_text(
        json.dumps(public_config, indent=2),
        encoding="utf-8",
    )
    os.chmod(CONFIG_FILE, 0o600)

    # Store secrets separately
    save_secret("META_APP_SECRET", app_secret)
    save_secret("META_PAGE_ACCESS_TOKEN", page_access_token)

    print("\n✓ Meta credentials captured successfully.")
    print(f"Public config saved to: {CONFIG_FILE}")

    if keyring:
        print("✓ Secrets stored securely in the system keyring.")
    else:
        print("⚠ keyring not available.")
        print("Secrets were written to local 0600-protected files.")
        print("Install 'keyring' for more secure storage.")

    print("\nUnk is now configured to use the Meta Media Engine.")
    print("No secrets were written to the public configuration file.")


if __name__ == "__main__":
    main()
