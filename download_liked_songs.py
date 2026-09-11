#!/usr/bin/env python3
"""Download your YouTube Music liked songs into Artist/Album/Track.mp3 folders."""

import json
import sys
from pathlib import Path

import yt_dlp
from ytmusicapi import YTMusic

DIR = Path(__file__).resolve().parent
AUTH = DIR / "oauth.json" if (DIR / "oauth.json").exists() else DIR / "browser.json"
DB_FILE = DIR / ".downloaded_songs.json"


def load_db():
    try:
        return set(json.loads(DB_FILE.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_db(ids):
    DB_FILE.write_text(json.dumps(sorted(ids), indent=2), encoding="utf-8")


def clean(name):
    if not name:
        return "Unknown"
    return "".join("_" if c in r'\/:*?"<>|' else c for c in name).strip()


def file_on_disk(title, artists, album):
    artist = clean(artists[0]["name"] if artists else "Unknown Artist")
    album_name = clean(album["name"] if album else "Unknown Album")
    title_clean = clean(title)
    album_dir = DIR / artist / album_name
    if not album_dir.is_dir():
        return False
    return any(p.suffix and clean(p.stem) == title_clean for p in album_dir.iterdir())


def download(video_id, title, artists, album):
    artist = clean(artists[0]["name"] if artists else "Unknown Artist")
    album_name = clean(album["name"] if album else "Unknown Album")
    out_dir = DIR / artist / album_name
    out_dir.mkdir(parents=True, exist_ok=True)

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / f"{clean(title)}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://music.youtube.com/watch?v={video_id}"])


def main():
    if not AUTH.exists():
        sys.exit("No auth file found.\nConnect your account first:  ./sync setup")

    yt = YTMusic(str(AUTH))
    tracks = yt.get_liked_songs(limit=None)["tracks"]
    downloaded = load_db()
    todo = [t for t in tracks if t["videoId"] not in downloaded and not file_on_disk(t["title"], t.get("artists"), t.get("album"))]

    print(f"[*] {len(tracks)} liked songs, {len(downloaded)} already saved, {len(todo)} to download.")

    for i, t in enumerate(todo, 1):
        artist = t["artists"][0]["name"] if t.get("artists") else "Unknown"
        print(f"[{i}/{len(todo)}] {artist} - {t['title']}", flush=True)
        try:
            download(t["videoId"], t["title"], t.get("artists"), t.get("album"))
            downloaded.add(t["videoId"])
            save_db(downloaded)
        except Exception as e:
            print(f"    [!] {e}")

    print(f"[+] Done. {len(downloaded)} songs in local library.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)