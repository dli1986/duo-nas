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
├─ originals (RAW photos, FLAC/audio)
├─ Postgres (metadata, relationships)
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
- `scripts/acquire/` — yt-dlp-based audio acquisition helpers (private archive only, never re-exposed publicly as full tracks)
- `scripts/export-photos/` — RAW → optimized WebP/AVIF thumbnails + EXIF/XMP-preserving originals, pushed to R2
- `scripts/export-music/` — pulls metadata from MusicBrainz / Discogs / ListenBrainz for cataloged tracks, writes `content/music/*.mdx` for the `duo-li` repo (catalog entries are metadata-only and don't require a matching playable file)

## Status

Scaffold only — nothing is running yet. Being built incrementally.
