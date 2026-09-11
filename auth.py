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
    print("  How to get your cookie (takes ~20 seconds):")
    print("   1. Open https://music.youtube.com in your browser and log in.")
    print("   2. Press F12 to open DevTools, then click the Console tab.")
    print("   3. Type this and press Enter:")
    print("        copy(document.cookie)")
    print("   4. Now paste the cookie here.")
    print()


def get_cookie():
    steps()
    cookie = input("Paste your cookie and press Enter: ").strip().strip('"')
    if not cookie or "__Secure-3PAPISID" not in cookie:
        sys.exit("[!] That doesn't look like a YouTube cookie. Please try again.")
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
        print(f"[-] Saved browser.json, but couldn't verify it: {e}")
        print("    If this keeps failing, log out and back in, then run './sync auth' again.")


if __name__ == "__main__":
    main()