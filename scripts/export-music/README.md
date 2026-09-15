# export-music/

Pulls track metadata from the public, free APIs (MusicBrainz, Discogs, ListenBrainz) for songs in the personal catalog, and writes `../../../duo-li/content/music/*.mdx` files (same frontmatter pattern as `content/knowledge`/`content/reading`) — assumes `duo-li` is cloned as a sibling of `duo-nas` (see root README's "Directory layout" section).

Catalog entries here are metadata-only by design — they reflect what the owner is interested in/appreciates, and don't require a matching locally-acquired audio file. When a matching file does exist in `../../music/`, that's a bonus, not a requirement.

Nothing scripted here yet — so far `content/music/si-shi-gu-ren-lai.mdx` was written by hand using `musicbrainz_lookup.py`'s output as the source of truth.
