#!/usr/bin/env python3
"""Look up a recording on MusicBrainz (search -> recording detail -> linked work's
composer/lyricist) and print structured JSON, using only the public, free API.
Optionally writes the result straight into the sibling duo-li repo's content/music/.

Usage:
    python musicbrainz_lookup.py "<artist>" "<track title>"
    python musicbrainz_lookup.py "<artist>" "<track title>" --write <slug> [--tags tag1 tag2 ...]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from opencc import OpenCC

    _s2t = OpenCC("s2t").convert
    _t2s = OpenCC("t2s").convert
except ImportError:
    # degrade gracefully: script still works, just without the Simplified<->Traditional retry
    _s2t = _t2s = None

API_ROOT = "https://musicbrainz.org/ws/2"
# MusicBrainz requires a descriptive User-Agent identifying the app + contact.
USER_AGENT = "duo-nas-music-export/0.1 (https://github.com/dli1986/duo-li)"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_duo_li_dir() -> Path:
    # Local clone folder name doesn't match the GitHub repo name (duo-li) on this machine —
    # override with DUO_LI_REPO_DIR if your setup differs.
    override = os.environ.get("DUO_LI_REPO_DIR")
    if override:
        return Path(override)
    for candidate in ("Duo-digital-garden", "duo-li"):
        path = REPO_ROOT.parent / candidate
        if (path / "package.json").exists():
            return path
    return REPO_ROOT.parent / "duo-li"


DUO_LI_MUSIC_DIR = _resolve_duo_li_dir() / "content" / "music"


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


def search_recording(artist: str, title: str, limit: int = 5) -> list[dict]:
    query = f'recording:"{title}" AND artist:"{artist}"'
    url = f"{API_ROOT}/recording/?" + urllib.parse.urlencode(
        {"query": query, "fmt": "json", "limit": limit}
    )
    return _get(url).get("recordings", [])


def recording_detail(mbid: str) -> dict:
    url = f"{API_ROOT}/recording/{mbid}?" + urllib.parse.urlencode(
        {"inc": "artist-credits+work-rels+artist-rels+releases", "fmt": "json"}
    )
    return _get(url)


def work_detail(mbid: str) -> dict:
    url = f"{API_ROOT}/work/{mbid}?" + urllib.parse.urlencode(
        {"inc": "artist-rels", "fmt": "json"}
    )
    return _get(url)


def _score(detail: dict) -> int:
    """Higher is better: a recording linked to a work (has composer/lyricist data) and
    with a populated length is a more complete MusicBrainz entry than a bare, unlinked one."""
    has_work = any(r.get("target-type") == "work" for r in detail.get("relations", []))
    has_length = detail.get("length") is not None
    return (2 if has_work else 0) + (1 if has_length else 0)


def _best_candidate_detail(artist: str, title: str, limit: int = 5) -> dict | None:
    """MusicBrainz's search ranking is text-match relevance, not data completeness — the
    top hit is often NOT the recording with composer/lyricist linked. Fetch details for
    every candidate and keep the best-scoring one instead of blindly trusting candidates[0]."""
    candidates = search_recording(artist, title, limit=limit)
    if not candidates:
        return None

    scored = []
    for c in candidates:
        detail = recording_detail(c["id"])
        scored.append((_score(detail), detail))
        time.sleep(1)  # MusicBrainz asks for ~1 unauthenticated request/sec

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[0][1]


def lookup(artist: str, title: str) -> dict:
    """Search MusicBrainz, retrying with Simplified<->Traditional Chinese script variants
    if the first attempt comes back empty or without a linked work. MusicBrainz's Chinese-
    language coverage is inconsistently scripted — a Cantopop/Mandopop song might only be
    catalogued in Traditional even when your source video title used Simplified, or vice
    versa (hit this for real with both 辛晓琪/辛曉琪 and 两两相忘/倆倆相忘)."""
    attempts = [(artist, title)]
    if _s2t:
        attempts.append((_s2t(artist), _s2t(title)))
    if _t2s:
        attempts.append((_t2s(artist), _t2s(title)))

    detail = None
    for a, t in attempts:
        candidate = _best_candidate_detail(a, t)
        if candidate is None:
            continue
        if detail is None:
            detail = candidate
        if _score(candidate) == 3:  # work + length both present — good enough, stop early
            detail = candidate
            break

    if detail is None:
        raise SystemExit(
            f"No MusicBrainz recording found for {artist!r} / {title!r} "
            f"(tried {len(attempts)} script variant(s))"
        )

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


def _yaml_str(value: str) -> str:
    # JSON string syntax is valid YAML flow-scalar syntax too — a cheap, correct way to
    # escape quotes/special characters without pulling in a YAML-writing dependency.
    return json.dumps(value, ensure_ascii=False)


def write_mdx(entry: dict, slug: str, tags: list[str]) -> Path:
    DUO_LI_MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    path = DUO_LI_MUSIC_DIR / f"{slug}.mdx"
    if path.exists():
        raise SystemExit(f"{path} already exists — remove it first if you want to overwrite")

    mb_url = f"https://musicbrainz.org/recording/{entry['recording_mbid']}"

    lines = [
        "---",
        f"title: {_yaml_str(entry['title'])}",
        f"slug: {_yaml_str(slug)}",
        f"artist: {_yaml_str(entry['artist'])}",
    ]
    if entry["lyricist"]:
        lines.append(f"lyricist: {_yaml_str('、'.join(entry['lyricist']))}")
    if entry["composer"]:
        lines.append(f"composer: {_yaml_str('、'.join(entry['composer']))}")
    lines.append("tags:")
    for tag in tags:
        lines.append(f"  - {_yaml_str(tag)}")
    lines.append(f"musicbrainzUrl: {_yaml_str(mb_url)}")
    lines.append("---")
    lines.append("")
    lines.append("_Personal notes: to be added._")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artist")
    parser.add_argument("title")
    parser.add_argument("--write", metavar="SLUG", help="also write duo-li/content/music/<SLUG>.mdx")
    parser.add_argument("--tags", nargs="*", default=[], help="tags for the MDX entry, space-separated")
    args = parser.parse_args()

    result = lookup(args.artist, args.title)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.write:
        written = write_mdx(result, args.write, args.tags)
        print(f"\nWrote {written}")

