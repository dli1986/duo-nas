# export-music/

Pulls track metadata from MusicBrainz (free, no token needed) and can write it straight into `../../../duo-li/content/music/*.mdx` (assumes `duo-li` is cloned as a sibling of `duo-nas` — see root README's "Directory layout" section).

Catalog entries here are metadata-only by design — they reflect what the owner is interested in/appreciates, and don't require a matching locally-acquired audio file. When a matching file does exist in `../../music/`, that's a bonus, not a requirement.

## Usage

```bash
source ../../.venv/bin/activate
pip install -r requirements.txt   # first time only — adds opencc for the script-variant retry

# just look up and print, no file written
python musicbrainz_lookup.py "辛晓琪" "两两相忘"

# look up AND write duo-li/content/music/<slug>.mdx
python musicbrainz_lookup.py "辛晓琪" "两两相忘" --write liang-liang-xiang-wang --tags "国语" "Chinese Music"
```

`--write` refuses to overwrite an existing file — delete it first if you really want to redo one.

## Matching Chinese-language songs reliably

MusicBrainz's search ranks by text-match relevance, not data completeness, and its Chinese-language entries are inconsistently scripted (Simplified vs Traditional) — the naive "take the first search result" approach silently returned empty composer/lyricist for real songs (辛晓琪《倆倆相忘》, 巫啟賢《紅塵來去一場夢》) simply because the top-ranked hit happened to be an under-linked recording, or the script didn't match at all. Fixed by:

1. Fetching all 5 search candidates and scoring each by "has a linked work" + "has a populated length," keeping the best one instead of always trusting `candidates[0]`
2. If the first attempt returns nothing (or nothing scores well), automatically retrying with the artist/title converted Simplified→Traditional and Traditional→Simplified (via `opencc`)

Still not perfect — if a song genuinely isn't in MusicBrainz well-linked in *either* script, you'll get partial data (or a clean "not found" error) and have to fill in the rest by hand.
