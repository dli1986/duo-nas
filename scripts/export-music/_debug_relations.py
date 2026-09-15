import sys
sys.path.insert(0, "scripts/export-music")
import musicbrainz_lookup as m
import json

d = m.recording_detail("ceffab1e-3441-4484-8354-f2a77066c746")
work_rels = [r for r in d.get("relations", []) if r.get("target-type") == "work"]
print(json.dumps(work_rels, ensure_ascii=False, indent=2))
