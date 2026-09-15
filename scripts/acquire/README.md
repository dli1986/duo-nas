# acquire/

Personal audio acquisition helper (yt-dlp based). Output goes to `../../music/` (gitignored, private).

Never re-expose the acquired full tracks to the public `duo-li` website — private/personal use only (see README.md at repo root for the reasoning).

## Usage

```bash
pip install -r requirements.txt
cd ../..              # run from duo-nas/ root so output lands in ./music/
python scripts/acquire/acquire.py "<url>"
```

Downloads the best available audio track, converts to mp3 (VBR 0), embeds metadata + thumbnail as ID3 tags.

## Known caveat

YouTube URLs specifically may hit 403/bot-detection errors with yt-dlp — this repo's sibling project `../../../Subtitle` (YutubeDownloadWithBilingualSubtitle) already solved this with a PO-token workaround; see its `docs/troubleshooting/` if this script 403s on a YouTube link. Non-YouTube sources (Bilibili, SoundCloud, Bandcamp, etc.) generally don't need that workaround.
