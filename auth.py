#!/usr/bin/env python3
"""Connect your YouTube Music account with one paste of your browser cookie."""

import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
BROWSER_JSON = DIR / "browser.json"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def steps():
    print()
    print("  How to get your cookie (takes ~30 seconds):")
    print("   1. Open https://music.youtube.com in your browser and log in.")
    print("   2. Press F12, open the Network tab, then reload the page (Ctrl+R).")
    print("   3. Click the first 'music.youtube.com' request at the top of the list.")
    print("   4. Under 'Request Headers', right-click the 'Cookie:' line and choose")
    print("      'Copy value'.")
    print("   5. Paste that cookie here.")
    print()
    print("  Note: copying from the Console (document.cookie) does NOT work — it's")
    print("  missing the protected cookies YouTube needs to verify you're signed in.")
    print()


def get_cookie():
    steps()
    cookie = input("Paste your cookie and press Enter: ").strip().strip('"')
    if not cookie or "__Secure-3PAPISID" not in cookie:
        sys.exit("[!] That doesn't look like a YouTube cookie. Please try again.")
    if "__Secure-3PSID" not in cookie:
        print("\n[!] Heads up: this looks like the Console (document.cookie) version, which is")
        print("    usually missing the protected cookies. Please use the Network-tab method above,")
        print("    then run './sync auth' again if this fails.")
    return cookie


def main():
    cookie = get_cookie()

    BROWSER_JSON.write_text(
        json.dumps(
            {
                "cookie": cookie,
                "x-goog-authuser": "0",
                "user-agent": UA,
                "origin": "https://music.youtube.com",
                "authorization": "SAPISIDHASH placeholder",
            },
            indent=4,
        ),
        encoding="utf-8",
    )

    try:
        from ytmusicapi import YTMusic

        yt = YTMusic(str(BROWSER_JSON))
        count = len(yt.get_liked_songs(limit=None)["tracks"])
        print(f"[+] Connected! Found {count} liked songs. Run ./sync to download them.")
    except Exception as e:
        err = str(e)
        if len(err) > 200:
            err = err[:200] + "..."
        print(f"[-] Saved browser.json, but couldn't verify it: {err}")
        print("    If the message mentions 'Sign in', your cookie was missing the protected")
        print("    cookies — copy it from the Network tab (see steps above), not the Console,")
        print("    then run './sync auth' again.")


if __name__ == "__main__":
    main()