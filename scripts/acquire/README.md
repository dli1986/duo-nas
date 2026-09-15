# acquire/

Personal audio acquisition helper (yt-dlp based). Output goes to `../../music/` (gitignored, private).

Never re-expose the acquired full tracks to the public `duo-li` website — private/personal use only (see README.md at repo root for the reasoning).

## Usage

Uses its own virtual environment (`duo-nas/.venv`), same convention as the other WSL projects (`nanoGPT-learning`, `llama2.c`):

```bash
cd ~/duo-nas                     # native WSL filesystem, not /mnt/c
python3 -m venv .venv            # first time only
source .venv/bin/activate
pip install -r scripts/acquire/requirements.txt
python scripts/acquire/acquire.py "<url>"
```

Also requires `ffmpeg` on PATH (system package, not pip-installed) for audio extraction — already present on this WSL Ubuntu image.

Downloads the best available audio track, converts to mp3 (VBR 0), embeds metadata + thumbnail as ID3 tags, saves into `./music/`.

## Known caveat

YouTube URLs specifically may hit 403/bot-detection errors with yt-dlp — this repo's sibling project `../../../Subtitle` (YutubeDownloadWithBilingualSubtitle) already solved this with a PO-token workaround; see its `docs/troubleshooting/` if this script 403s on a YouTube link. Non-YouTube sources (Bilibili, SoundCloud, Bandcamp, etc.) generally don't need that workaround.
