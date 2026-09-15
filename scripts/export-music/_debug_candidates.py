import sys

sys.path.insert(0, "scripts/export-music")
import musicbrainz_lookup as m

candidates = m.search_recording("梅艳芳", "似是故人來")
for c in candidates:
    print(
        c["id"],
        c.get("title"),
        [a.get("name") for a in c.get("artist-credit", [])],
        c.get("length"),
        [r.get("title") for r in c.get("releases", [])][:3],
    )
