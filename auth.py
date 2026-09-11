#!/usr/bin/env python3
"""Connect your YouTube Music account by pasting one 'Copy as cURL' command."""

import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
BROWSER_JSON = DIR / "browser.json"

UA_FALLBACK = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

CURL_HEADER_RE = re.compile(r"""(?:-H|--header)(?:\s+|=)(['"])(.*?)\1""", re.S)


def steps():
    print()
    print("  How to get it (takes ~30 seconds):")
    print("   1. Open https://music.youtube.com in your browser and log in.")
    print("   2. Press F12, open the Network tab, then reload the page (Ctrl+R).")
    print("   3. Click the first 'music.youtube.com' request at the top of the list.")
    print("   4. Right-click it -> Copy -> Copy as cURL.")
    print("   5. Paste the whole command here (it starts with 'curl').")
    print()
    print("  Tip: use 'Copy as cURL', not 'Copy value' on the Cookie header - DevTools")
    print("  truncates long cookie values with '...' and the cut-off cookie won't work.")
    print()


def parse_curl(text):
    headers = {}
    for m in CURL_HEADER_RE.finditer(text):
        raw = m.group(2).replace("\\'", "'").replace('\\"', '"')
        if ": " in raw:
            key, _, value = raw.partition(": ")
            headers[key.strip().lower()] = value.strip()
    return headers


def save_and_verify(headers):
    BROWSER_JSON.write_text(json.dumps(headers, indent=4), encoding="utf-8")
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
        print("    If the message mentions 'Sign in', the cookie was incomplete - re-copy it")
        print("    with 'Copy as cURL' and run './sync auth' again.")


def main():
    steps()
    text = input("Paste your cURL command and press Enter: ").strip()
    if not text:
        sys.exit("[!] Nothing pasted. Please try again.")

    if "…" in text or "..." in text.replace("...cURL", ""):
        print("[!] Warning: the pasted text contains truncation markers ('...').")
        print("    Make sure you copied the full line with 'Copy as cURL'.")

    if "__Secure-3PAPISID" in text and ("-H" in text or "--header" in text):
        headers = parse_curl(text)
        if "cookie" not in headers:
            sys.exit("[!] No Cookie header found in that cURL command. Please try again.")
        cookie = headers["cookie"]
        headers = {
            "cookie": cookie,
            "user-agent": headers.get("user-agent", UA_FALLBACK),
            "x-goog-authuser": headers.get("x-goog-authuser", "0"),
            "origin": headers.get("origin") or "https://music.youtube.com",
            "authorization": "SAPISIDHASH placeholder",
        }
        if "x-goog-visitor-id" in headers:
            pass  # ytmusicapi fetches visitor id itself when missing
    elif "__Secure-3PAPISID" in text:
        cookie = text
        if "__Secure-3PSID" not in cookie:
            print("\n[!] Heads up: this looks like the Console (document.cookie) version, which")
            print("    is missing the protected cookies. Use 'Copy as cURL' instead.")
        headers = {
            "cookie": cookie,
            "user-agent": UA_FALLBACK,
            "x-goog-authuser": "0",
            "origin": "https://music.youtube.com",
            "authorization": "SAPISIDHASH placeholder",
        }
    else:
        sys.exit("[!] That doesn't look like a YouTube cURL command. Please try again.")

    save_and_verify(headers)


if __name__ == "__main__":
    main()