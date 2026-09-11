#!/usr/bin/env python3
"""Connect your YouTube Music account by pasting the Request Headers panel."""

import json
import re
import sys
from pathlib import Path

FROM_YT = __import__("ytmusicapi")

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
    print("   4. Open its Headers tab and find the 'Request Headers' panel.")
    print("      Chrome/Edge: click the copy icon (two squares) at the panel's top-right.")
    print("      Firefox: right-click inside the panel -> Copy.")
    print("   5. Paste it below, then press Enter and Ctrl-D to finish.")
    print()
    print("  Tip: copy the whole Request Headers panel, not just the cookie - the cookie")
    print("  alone is truncated or missing protected values and won't work.")
    print()


def read_paste(first):
    lines = [first]
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)


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
    verify()


def normalize_browser_json():
    d = json.loads(BROWSER_JSON.read_text(encoding="utf-8"))
    d["authorization"] = "SAPISIDHASH placeholder"
    d.setdefault("x-goog-authuser", "0")
    d.setdefault("origin", "https://music.youtube.com")
    BROWSER_JSON.write_text(json.dumps(d, indent=4), encoding="utf-8")


def verify():
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
        print("    If the message mentions 'Sign in', the headers were incomplete - copy the")
        print("    whole Request Headers panel and run './sync auth' again.")


def main():
    steps()
    first = input("Paste your Request Headers (then Enter, Ctrl-D): ").strip()
    if not first:
        sys.exit("[!] Nothing pasted. Please try again.")
    text = read_paste(first)

    if "…" in text:
        print("[!] Warning: the pasted text contains a '...' truncation marker - make sure")
        print("    you copied the full Request Headers panel.")

    # Fast path: a whole 'curl ...' command was pasted instead.
    first_line = text.splitlines()[0].strip()
    if first_line.startswith("curl") and "__Secure-3PAPISID" in text:
        headers = parse_curl(text)
        if "cookie" not in headers:
            sys.exit("[!] No Cookie header found in that curl command. Please try again.")
        cookie = headers["cookie"]
        headers = {
            "cookie": cookie,
            "user-agent": headers.get("user-agent", UA_FALLBACK),
            "x-goog-authuser": headers.get("x-goog-authuser", "0"),
            "origin": headers.get("origin") or "https://music.youtube.com",
            "authorization": "SAPISIDHASH placeholder",
        }
    elif "__Secure-3PAPISID" in text:
        # Raw Request Headers block - use ytmusicapi's own battle-tested parser.
        try:
            FROM_YT.setup(filepath=str(BROWSER_JSON), headers_raw=text)
            normalize_browser_json()
        except SystemExit:
            raise
        except Exception as e:
            sys.exit(f"[!] Could not parse those headers: {e}")
    else:
        sys.exit("[!] That doesn't look like YouTube request headers. Please try again.")

    verify()


if __name__ == "__main__":
    main()