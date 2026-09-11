# ytmusic-sync

Download all your YouTube Music **liked songs** as MP3s, organized into
`Artist/Album/Track.mp3` folders. Incremental — rerun it anytime to grab just the
new likes.

## Requirements

- Python 3.8+
- **FFmpeg** (for MP3 conversion + metadata). Install it with your package
  manager, e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS,
  or `winget install ffmpeg` on Windows.

## First-run setup

```bash
git clone https://github.com/YOUR_USERNAME/ytmusic-sync.git
cd ytmusic-sync
./sync setup
```

`./sync setup` does everything for you:

1. Creates a Python virtual environment and installs `ytmusicapi` + `yt-dlp`
2. Starts the YouTube Music authentication flow — just paste the request headers
   from `music.youtube.com` (DevTools → Network → the `browse` request → copy
   headers). It saves them to `browser.json`, which is git-ignored.

## Usage

```bash
./sync            # download all new liked songs
./sync auth       # re-authenticate if your session expires
```

## How it works

- Reads your liked list from YouTube Music
- Downloads each song with `yt-dlp` and converts it to 192 kbps MP3 with embedded
  thumbnail + tags (requires FFmpeg)
- Saves tracks under `Artist/Album/Track.mp3`
- Tracks what's already downloaded in `.downloaded_songs.json`, so reruns are fast

## Notes / Troubleshooting

- Auth files (`browser.json`, `oauth.json`) are private — never commit or share them.
- If downloads stop working, your auth may have expired: run `./sync auth`.