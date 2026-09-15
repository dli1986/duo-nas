import sys
sys.path.insert(0, "scripts/export-music")
import musicbrainz_lookup as m
import json

w = m.work_detail("bdbd403d-dc98-4ba0-b4ff-336d508ad647")
print(json.dumps(w.get("relations", []), ensure_ascii=False, indent=2))
