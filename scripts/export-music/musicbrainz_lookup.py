#!/usr/bin/env python3
"""Look up a recording on MusicBrainz (search -> recording detail -> linked work's
composer/lyricist) and print structured JSON, using only the public, free API.

Usage:
    python musicbrainz_lookup.py "<artist>" "<track title>"
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://musicbrainz.org/ws/2"
# MusicBrainz requires a descriptive User-Agent identifying the app + contact.
USER_AGENT = "duo-nas-music-export/0.1 (https://github.com/dli1986/duo-li)"


def _get(url: str, retries: int = 5) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            # MusicBrainz returns 503 "server is currently busy" under load — transient, not a rate-limit block.
            if exc.code == 503 and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def search_recording(artist: str, title: str) -> list[dict]:
    query = f'recording:"{title}" AND artist:"{artist}"'
    url = f"{API_ROOT}/recording/?" + urllib.parse.urlencode(
        {"query": query, "fmt": "json", "limit": 5}
    )
    return _get(url).get("recordings", [])


def recording_detail(mbid: str) -> dict:
    url = f"{API_ROOT}/recording/{mbid}?" + urllib.parse.urlencode(
        {"inc": "work-rels+artist-rels+releases", "fmt": "json"}
    )
    return _get(url)


def work_detail(mbid: str) -> dict:
    url = f"{API_ROOT}/work/{mbid}?" + urllib.parse.urlencode(
        {"inc": "artist-rels", "fmt": "json"}
    )
    return _get(url)


def lookup(artist: str, title: str) -> dict:
    candidates = search_recording(artist, title)
    if not candidates:
        raise SystemExit(f"No MusicBrainz recording found for {artist!r} / {title!r}")

    best = candidates[0]
    detail = recording_detail(best["id"])

    result = {
        "recording_mbid": detail["id"],
        "title": detail["title"],
        "artist": ", ".join(a["name"] for a in detail.get("artist-credit", [])),
        "length_ms": detail.get("length"),
        "releases": [r["title"] for r in detail.get("releases", [])][:5],
        "composer": [],
        "lyricist": [],
        "work_mbid": None,
    }

    for rel in detail.get("relations", []):
        if rel.get("target-type") == "work":
            work = work_detail(rel["work"]["id"])
            result["work_mbid"] = work["id"]
            for wrel in work.get("relations", []):
                role = wrel.get("type")
                name = wrel.get("artist", {}).get("name")
                if not name:
                    continue
                if role == "composer":
                    result["composer"].append(name)
                elif role == "lyricist":
                    result["lyricist"].append(name)
            break  # first linked work is enough for our purposes

    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python musicbrainz_lookup.py "<artist>" "<track title>"')
        sys.exit(1)
    print(json.dumps(lookup(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
