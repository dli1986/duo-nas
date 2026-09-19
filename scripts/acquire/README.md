# acquire/

Personal audio acquisition helper (yt-dlp based). Output always goes to `<repo root>/music/` (gitignored, private) — resolved relative to this script's own location, not the current working directory, so it lands in the right place regardless of which directory you run it from.

Never re-expose the acquired full tracks to the public `duo-li` website — private/personal use only (see README.md at repo root for the reasoning).

## Usage

Uses the single project-level virtual environment at the repo root (`duo-nas/.venv`), same convention as the other WSL projects (`nanoGPT-learning`, `llama2.c`) — one venv for all of `scripts/`, not one per script folder:

```bash
cd ~/duo-nas                     # native WSL filesystem, not /mnt/c
python3 -m venv .venv            # first time only
source .venv/bin/activate
pip install -r requirements.txt
python scripts/acquire/acquire.py "<url>"
```

Also requires `ffmpeg` on PATH (system package, not pip-installed) for audio extraction — already present on this WSL Ubuntu image.

Downloads the best available audio track, converts to mp3 (VBR 0), embeds metadata + thumbnail as ID3 tags, saves into `<repo root>/music/` (this is what `docker-compose.yml` mounts read-only into Navidrome — a file anywhere else won't get picked up by the library scan).

## Known caveat

YouTube URLs specifically may hit 403/bot-detection errors with yt-dlp — this repo's sibling project `../../../Subtitle` (YutubeDownloadWithBilingualSubtitle) already solved this with a PO-token workaround; see its `docs/troubleshooting/` if this script 403s on a YouTube link. Non-YouTube sources (Bilibili, SoundCloud, Bandcamp, etc.) generally don't need that workaround.

**Windows-side note**: run `acquire.py` from WSL, not the Windows-side `.venv` — Bilibili
downloads have been observed returning `412 Precondition Failed` from this machine's
Windows network path but working fine from WSL (likely something in the corporate
network/proxy path mangling requests on the Windows side specifically).

## Batch downloads

Append one URL per line to `batch_urls.txt` (any number, any time — tracking query params
like `?spm_id_from=...&vd_source=...` are fine, they get ignored), then run:

```bash
bash scripts/acquire/batch_acquire.sh
```

It downloads everything in `batch_urls.txt`, skipping URLs already recorded (by BV id) in
`batch_done.txt`. Safe to re-run any time — already-downloaded entries are skipped, only
new ones (and any that failed last time) get attempted. Keep appending to `batch_urls.txt`
as you find more songs, and re-run whenever you want to catch up on the backlog.

