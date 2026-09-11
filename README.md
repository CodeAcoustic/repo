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
git clone https://github.com/CodeAcoustic/repo.git
cd repo
./sync setup
```

`./sync setup` holds your hand through it:

1. Creates a Python virtual environment and installs `ytmusicapi` + `yt-dlp`
2. Walks you through copying the **Request Headers** of one request from
   `music.youtube.com` and pasting it here
3. Tests the connection and tells you how many liked songs it found

The result is saved to `browser.json`, which is git-ignored.

### Getting your Request Headers (any browser)

1. Open `https://music.youtube.com` and log in
2. Press `F12` → **Network** tab → reload the page (`Ctrl+R`)
3. Click the first `music.youtube.com` request at the top of the list
4. Open its **Headers** tab and find the **Request Headers** panel:
   - Chrome/Edge: click the copy icon (two stacked squares) at the panel's top-right
   - Firefox: right-click inside the panel → **Copy**
5. Paste it into the terminal, press `Enter`, then `Ctrl-D` to finish

> **Important:** copy the whole Request Headers panel. Copying just the cookie or
> `document.cookie` misses/truncates YouTube's protected cookies (`__Secure-3PSID`,
> `HSID`, …) and the connection will look signed-out.

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

- `browser.json` contains your login cookie — it's git-ignored, never commit or
  share it. Don't paste browser.json content into GitHub issues.
- Cookies can expire. If downloads stop working, run `./sync auth` to reconnect
  with a fresh cookie.