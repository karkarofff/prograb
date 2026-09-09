<p align="center">
  <img src="prograb_logo.png" width="140" alt="ProGrab logo">
</p>

<h1 align="center">ProGrab</h1>

<p align="center">
  A clean, modern video downloader for Windows — paste a link, pick a quality, done.
</p>

<p align="center">
  🇫🇷 <a href="README.fr.md">Version française</a>
</p>

---

## What is it?

ProGrab is a minimal GUI around the excellent [yt-dlp](https://github.com/yt-dlp/yt-dlp): paste a video URL, see the thumbnail/title/duration, pick a quality, and watch the download button itself turn into a progress bar.

<img width="741" height="660" alt="prograb" src="https://github.com/user-attachments/assets/4ac3f352-ba9f-4f60-aa4e-540dccb28945" />


## Features

- 🎯 **Simple flow** — paste, analyze, download. The big button becomes the progress bar (percent, size, speed, ETA), click it mid-download to cancel, and it turns green when done.
- 🎞 **Real MP4s** — video downloads are forced to H.264 + AAC whenever available, so files play everywhere (old TVs included), not just in VLC.
- 🎵 **MP3 mode** — audio-only extraction, converted to MP3.
- - 📝 **Transcript mode** — grabs the video's subtitles (manual ones preferred, auto-generated as fallback) and converts them to a clean .txt file: no timestamps, no duplicate lines, just readable text. Great for feeding videos to AI tools or skimming a talk.
- 🔁 **Self-maintaining** — on first launch, ProGrab fetches its own tools (yt-dlp, ffmpeg, deno) into its data folder, then **yt-dlp updates itself silently at every startup**. When sites change, the app heals on its own. ProGrab also notifies you when a new version of itself is available.
- 🌑 **Modern dark UI** — CustomTkinter, rounded everything, no clutter.
- Your quality choice is remembered as the default across sessions.

## Installation

Download `ProGrab.exe` from the [Releases](../../releases) page and run it. On first launch it downloads its components (~200 MB, one time).

> **SmartScreen note**: Windows may warn about an unsigned executable — normal for a small independent project. Click *More info* then *Run anyway*. The full source code is readable in this repository.

### From source

```
pip install customtkinter pillow
python prograb.py
```

### Build the exe yourself

```
pip install pyinstaller customtkinter pillow
pyinstaller --onefile --noconsole --collect-all customtkinter --icon prograb.ico --add-data "prograb.ico;." --name ProGrab prograb.py
```

## ⚠️ Legal notice

Downloading videos from YouTube and most platforms **violates their Terms of Service** and may infringe copyright depending on the content and your jurisdiction. ProGrab is provided for **personal, educational and fair-use purposes only** (e.g. backing up your own content, offline access to freely-licensed material). You are solely responsible for how you use it. The author does not endorse piracy.

## Requirements

- Windows 10 / 11

## License

MIT — the app itself. yt-dlp, ffmpeg and deno belong to their respective projects and licenses.

---

<p align="center">
  Developed by <a href="https://github.com/karkarofff">Karkarofff</a> — also check out <a href="https://github.com/karkarofff/probox">ProBox</a> and <a href="https://github.com/karkarofff/prokill">ProKill</a>
</p>
