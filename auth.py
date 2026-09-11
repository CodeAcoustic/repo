#!/usr/bin/env python3
"""Connect your YouTube Music account, automatically from your browser or by manual paste.

Usage:
  auth.py           auto-read your login from installed browsers, else manual
  auth.py --manual  skip auto-detection and paste request headers yourself
"""

import glob
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

DIR = Path(__file__).resolve().parent
BROWSER_JSON = DIR / "browser.json"

UA_FALLBACK = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

CURL_HEADER_RE = re.compile(r"""(?:-H|--header)(?:\s+|=)(['"])(.*?)\1""", re.S)


def build_browser_headers(cookie):
    return {
        "cookie": cookie,
        "user-agent": UA_FALLBACK,
        "x-goog-authuser": "0",
        "origin": "https://music.youtube.com",
        "authorization": "SAPISIDHASH placeholder",
    }


def verify():
    from ytmusicapi import YTMusic

    last_err = None
    for attempt in range(3):
        try:
            yt = YTMusic(str(BROWSER_JSON))
            count = len(yt.get_liked_songs(limit=None)["tracks"])
            print(f"[+] Connected! Found {count} liked songs. Run ./sync to download them.")
            return True
        except Exception as e:
            last_err = str(e)
            if attempt < 2:
                time.sleep(5)
    err = last_err
    if len(err) > 200:
        err = err[:200] + "..."
    print(f"[-] Saved browser.json, but couldn't verify it: {err}")
    return False


# --- auto connection -------------------------------------------------------


def firefox_family_cookies(patterns=None):
    """Read unencrypted cookies.sqlite from Firefox-family browsers (incl. Flatpak)."""
    patterns = patterns or [
        "~/.mozilla/firefox/*/cookies.sqlite",
        "~/.config/zen/*/cookies.sqlite",
        "~/.config/librewolf/*/cookies.sqlite",
        "~/.config/waterfox/*/cookies.sqlite",
        "~/.var/app/*/.mozilla/firefox/*/cookies.sqlite",
        "~/.var/app/*/.mozilla/*/*/cookies.sqlite",
        "~/.var/app/*/.librewolf/*/*/cookies.sqlite",
        "~/.var/app/*/.waterfox/*/*/cookies.sqlite",
    ]
    paths = set()
    for pat in patterns:
        paths.update(glob.glob(str(Path(pat).expanduser())))

    seen = {}
    for path in paths:
        try:
            con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
            rows = con.execute("SELECT host, name, value FROM moz_cookies").fetchall()
            con.close()
        except Exception:
            continue
        for host, name, value in rows:
            host = host.lower()
            if (
                (host.endswith("youtube.com") or host.endswith("google.com"))
                and not name.startswith("ST-")
            ):
                seen[name] = value

    if seen and "__Secure-3PAPISID" in seen:
        return "; ".join(f"{k}={v}" for k, v in seen.items())
    return None


def chrome_family_cookies():
    """Read cookies via browser_cookie3 (handles Chrome-family decryption)."""
    try:
        import browser_cookie3 as bc
    except Exception:
        return None
    for name in ("chrome", "chromium", "edge", "brave", "opera", "vivaldi"):
        fn = getattr(bc, name, None)
        if fn is None:
            continue
        try:
            jar = fn()
        except Exception:
            continue
        pairs = [
            f"{c.name}={c.value}"
            for c in jar
            if (c.domain or "").lstrip(".").endswith(("youtube.com", "google.com"))
            and not c.name.startswith("ST-")
        ]
        if pairs and any("__Secure-3PAPISID" in p or "__Secure-3PSID" in p for p in pairs):
            return "; ".join(pairs)
    return None


def normalize_browser_json():
    d = json.loads(BROWSER_JSON.read_text(encoding="utf-8"))
    d["authorization"] = "SAPISIDHASH placeholder"
    d.setdefault("x-goog-authuser", "0")
    d.setdefault("origin", "https://music.youtube.com")
    BROWSER_JSON.write_text(json.dumps(d, indent=4), encoding="utf-8")


def auto_connect():
    print("[sync] Looking for your YouTube login in installed browsers...")
    cookie = None
    for reader in (firefox_family_cookies, chrome_family_cookies):
        cookie = reader()
        if cookie:
            break
    if not cookie:
        print("[sync] Couldn't find a logged-in browser. Falling back to manual paste.")
        return False

    BROWSER_JSON.write_text(json.dumps(build_browser_headers(cookie), indent=4), encoding="utf-8")
    if verify():
        return True
    print("[sync] That browser login didn't work. Falling back to manual paste.")
    return False


# --- manual connection -----------------------------------------------------


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


def manual_connect():
    steps()
    try:
        first = input("Paste your Request Headers (then Enter, Ctrl-D): ").strip()
    except EOFError:
        sys.exit("[!] No input given. Run './sync auth' again in an interactive terminal.")
    if not first:
        sys.exit("[!] Nothing pasted. Please try again.")
    text = read_paste(first)

    if "…" in text:
        print("[!] Warning: the pasted text contains a '...' truncation marker - make sure")
        print("    you copied the full Request Headers panel.")

    first_line = text.splitlines()[0].strip()
    if first_line.startswith("curl") and "__Secure-3PAPISID" in text:
        headers = parse_curl(text)
        if "cookie" not in headers:
            sys.exit("[!] No Cookie header found in that curl command. Please try again.")
        BROWSER_JSON.write_text(
            json.dumps(build_browser_headers(headers["cookie"]), indent=4), encoding="utf-8"
        )
    elif "__Secure-3PAPISID" in text:
        from ytmusicapi import setup

        try:
            setup(filepath=str(BROWSER_JSON), headers_raw=text)
            normalize_browser_json()
        except Exception as e:
            sys.exit(f"[!] Could not parse those headers: {e}")
    else:
        sys.exit("[!] That doesn't look like YouTube request headers. Please try again.")

    verify()


def main():
    if "--manual" not in sys.argv:
        if auto_connect():
            return
        print()
    manual_connect()


if __name__ == "__main__":
    main()