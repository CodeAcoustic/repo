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

`./sync setup` is fully automatic — **no copy-paste needed**:

1. Creates a Python virtual environment and installs `ytmusicapi` + `yt-dlp`
2. Reads your YouTube login straight from your installed browser
   (Chrome, Chromium, Edge, Brave, Firefox, Waterfox, LibreWolf — including Flatpak)
3. Tests the connection and tells you how many liked songs it found

The login is saved to `browser.json`, which is git-ignored.

To auto-connect you just need to be **already logged into YouTube/Google** in one of
your browsers. Everything else is handled.

### No browser login found?

`./sync setup` falls back to asking you to paste the **Request Headers** panel:

1. Open `https://music.youtube.com` and log in
2. Press `F12` → **Network** tab → reload the page (`Ctrl+R`)
3. Click the first `music.youtube.com` request at the top of the list
4. Open its **Headers** tab and find the **Request Headers** panel:
   - Chrome/Edge: click the copy icon (two stacked squares) at the panel's top-right
   - Firefox: right-click inside the panel → **Copy**
5. Paste it into the terminal, press `Enter`, then `Ctrl-D` to finish

> Copy the whole panel, not just the cookie — a partial cookie (e.g. from
> `document.cookie`) misses YouTube's protected cookies and looks signed-out.

## Usage

```bash
./sync                 # download all new liked songs
./sync auth            # reconnect automatically from your browser
./sync auth --manual   # reconnect by pasting Request Headers yourself
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
- Auto-connect reads cookies from your own browsers only; on Linux it may ask to
  unlock your login keyring (that's how Chrome-family cookies are decrypted).
- Cookies can expire. If downloads stop working, run `./sync auth` to reconnect.