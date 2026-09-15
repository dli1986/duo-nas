# duo-nas

Private media backend for the [duo-li](../Duo-digital-garden) personal site. Runs on a local machine / mini-PC / NAS — **never** deployed to Vercel, and never called live by the public website at runtime.

## Why a separate repo

`duo-li` (the Next.js site on Vercel) is a fully static, stateless deploy. This repo is the opposite: stateful, long-running, self-hosted, holds private originals. Keeping them as two independent repos means:

- Vercel only ever builds `duo-li` — it has no knowledge this repo exists
- This stack can move from "running on a dev laptop" to "running on a mini-PC/NAS" without touching the site's deploy at all
- No git submodule bookkeeping (pointer/version drift) for a single-maintainer project

## How the two repos talk to each other

They don't, at runtime. The only handoff is **exported artifacts**:

```
duo-nas (private, local)                    duo-li (public, Vercel)
├─ originals (music/, photos/ — local-only, gitignored, never synced
│  to any cloud service, incl. corporate OneDrive/Drive/iCloud)
├─ generated (photos-generated/ — thumbnails, local working copy before R2 upload)
├─ state/ (Postgres, Navidrome index/cache)
└─ export scripts
        │
        ├─► optimized thumbnails/audio  ──►  Cloudflare R2 (public CDN)
        └─► JSON/MDX metadata           ──►  git push to duo-li content/
                                                   │
                                                   ▼
                                          Vercel rebuilds as usual
```

No API from this repo is ever called by a website visitor's browser. No database or admin service from this repo is exposed to the public internet. Personal remote access (if any) goes through Tailscale, not port-forwarding.

## Planned components (not all built yet)

- `docker-compose.yml` — Postgres (metadata) + Navidrome (private streaming for personal/family use only)
- `scripts/acquire/` — yt-dlp-based audio acquisition helpers (private archive only, never re-exposed publicly as full tracks), saves originals into `music/`
- `scripts/export-photos/` — built: reads a photo from `photos/` (local-only originals, see that folder's README note), extracts EXIF, generates an optimized WebP thumbnail into `photos-generated/` (no originals ever uploaded), pushes it to Cloudflare R2, writes `content/photos/*.mdx` for the `duo-li` repo
- `scripts/export-music/` — pulls metadata from MusicBrainz for cataloged tracks, writes `content/music/*.mdx` for the `duo-li` repo (catalog entries are metadata-only and don't require a matching playable file)

## What real NAS hardware actually needs to run this

Just an OS + Docker + Docker Compose. That's it. Everything stateful (Postgres data, Navidrome index, the actual music/photo files) lives under `DUONAS_STATE_DIR` / `DUONAS_MUSIC_DIR` (see `.env`), which you point at an external/attached drive — the drive is the only thing that has to be "big." The compute side (this repo, the containers) is intentionally tiny and disposable: if the box dies, a fresh OS + `git clone` + `docker compose up` on new hardware gets you back to where you were, as long as the external drive survives. That's the whole point of separating state (drive) from compute (containers) — see the Gemini-derived design notes in project memory for the fuller reasoning.

## Directory layout: clone `duo-li` as a sibling

Export scripts write into the `duo-li` site repo (`content/music/*.mdx`, `content/knowledge/*.mdx`, optimized photos, etc.), so they assume a fixed relative layout — both repos cloned side by side under the same parent directory:

```
some-parent-dir/
├── duo-nas/    (this repo)
└── duo-li/     (github.com/dli1986/duo-li — the Next.js site)
```

On the current dev machine this looks like:

```
Windows: C:\Users\dli\Projects\MyTest\duo-nas          (authoring copy, no docker/python run here)
         C:\Users\dli\Projects\MyTest\Duo-digital-garden (authoring copy of duo-li)

WSL:     ~/duo-nas   (runtime copy — origin = the Windows duo-nas path)
         ~/duo-li    (runtime copy — origin = the Windows Duo-digital-garden path)
```

Both WSL copies sync the same way: `git pull` from their `origin` (the Windows-side path), then re-run whatever needs re-running (`docker compose up -d`, an export script, etc.). Setting up a fresh machine? Clone both repos next to each other first, under whatever name you like, as long as they're siblings — the export scripts use a relative path (`../duo-li/content/...`) to reach the site repo, they don't hardcode any absolute path.

## Setup on a new machine

Starting point: any machine with Docker + Docker Compose installed (Docker Desktop, Rancher Desktop, or a bare Linux install with `docker` + the `compose` plugin all work identically — this repo doesn't care which).

```bash
git clone https://github.com/dli1986/duo-nas.git
cd duo-nas

cp .env.example .env
# edit .env:
#   - set a real POSTGRES_PASSWORD
#   - if you have an external drive mounted, point DUONAS_STATE_DIR / DUONAS_MUSIC_DIR at it
#     (e.g. DUONAS_MUSIC_DIR=/mnt/usb1/music) — otherwise leave the ./state, ./music defaults

docker compose up -d
```

First-run admin setup (one-time, per machine): open `http://localhost:4533`, create the Navidrome admin account through the web UI (no CLI flow for this — it's a one-screen form).

For the acquisition/export scripts (Python), same convention on every machine — one dedicated venv for the whole repo, never system-wide pip and never a separate venv per script folder:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Also needs `ffmpeg` on PATH (system package — `apt install ffmpeg` / `brew install ffmpeg`, not pip).

**Windows-side note**: other projects on this machine historically share one large venv
(`C:\Users\dli\Projects\MyTest\MyTest\Scripts\activate.bat`) — that's a pre-existing
convention from before this repo existed and isn't being changed globally right now, but
`duo-nas` itself always uses its own repo-root `.venv` per the above, kept consistent with
the WSL side. Don't install this repo's dependencies into the shared `MyTest` venv, and
don't create ad-hoc venvs inside individual `scripts/*` subfolders.

### Running under WSL2 (if Docker only runs inside a WSL distro, e.g. Rancher Desktop)

Clone this repo a second time *inside* the WSL distro's own native filesystem (e.g. `~/duo-nas`), not under `/mnt/c/...` — bind-mounting a Windows path into Docker volumes has real I/O overhead for things like Postgres. The Windows-side checkout stays the "authoring" copy (edit + commit there); the WSL-native checkout is the "runtime" copy:

```bash
# inside the WSL distro
git clone /mnt/c/path/to/duo-nas ~/duo-nas   # or the GitHub URL directly
cd ~/duo-nas && git pull                     # re-run this after every commit on the Windows side
```

## Status

Running (on the current dev machine, WSL): Postgres + Navidrome, both `127.0.0.1`-only. One real track acquired via `scripts/acquire/acquire.py`, imported into Navidrome, playback verified. `scripts/export-music/musicbrainz_lookup.py` verified against the live MusicBrainz API. `scripts/export-photos/upload_photo.py` verified end-to-end (EXIF extract → WebP thumbnail → Cloudflare R2 upload → MDX written into `duo-li`) with one real photo. Both Windows and WSL sides now use a single repo-root `.venv` (`pip install -r requirements.txt`) — no more per-script venvs. Postgres schema/usage beyond Navidrome's own tables: not started yet.

