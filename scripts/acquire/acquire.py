#!/usr/bin/env python3
"""Minimal audio acquisition: given a URL, download the best available audio into <repo>/music/.

Usage:
    python acquire.py "<url>"
    (works from any directory — output always lands in the repo root's music/,
     which is what docker-compose mounts into Navidrome, not wherever you happened to run this from)

Requires: pip install yt-dlp
"""

import sys
from pathlib import Path

import yt_dlp

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MUSIC_DIR = REPO_ROOT / "music"


def acquire(url: str) -> None:
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{MUSIC_DIR}/%(title)s.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python acquire.py <url>")
        sys.exit(1)
    acquire(sys.argv[1])

