#!/usr/bin/env python3
"""Minimal audio acquisition: given a URL, download the best available audio into ./music/.

Usage:
    python acquire.py "<url>"

Requires: pip install yt-dlp
"""

import sys

import yt_dlp

MUSIC_DIR = "music"


def acquire(url: str) -> None:
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
