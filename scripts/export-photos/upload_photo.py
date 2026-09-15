"""Prepare a photo for the duo-li Photography module.

Given a local photo file, this script:
  1. Reads EXIF metadata (camera, lens, date, focal length, aperture, shutter, ISO).
  2. Generates an optimized WebP thumbnail (long edge capped, no originals kept/uploaded).
  3. Uploads the WebP to the Cloudflare R2 bucket (S3-compatible API).
  4. Writes content/photos/<slug>.mdx into the sibling duo-li repo, matching the
     PhotoFrontmatter schema in duo-li's src/lib/photos.ts.

Usage:
    python upload_photo.py PHOTO_PATH --slug my-photo --title "My Photo" \
        [--location "Kyoto, Japan"] [--tags travel street] [--date-taken 2024-05-01]

Requires a .env (or exported env vars) with R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_URL — see duo-nas/.env.example.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

import boto3
from PIL import ExifTags, Image

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


DUO_LI_PHOTOS_DIR = _resolve_duo_li_dir() / "content" / "photos"

MAX_DIMENSION = 2400
WEBP_QUALITY = 82

# Exif IFD pointer tag (holds FNumber, ExposureTime, ISO, LensModel, DateTimeOriginal, etc.)
EXIF_IFD_TAG = 0x8769


def _load_env_file() -> None:
    """Best-effort .env loader so this works without python-dotenv installed."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _rational_to_str(value, kind: str) -> str | None:
    if value is None:
        return None
    try:
        frac = Fraction(value.numerator, value.denominator) if hasattr(value, "numerator") else Fraction(value)
    except (ZeroDivisionError, ValueError):
        return None

    if kind == "fnumber":
        f = float(frac)
        text = f"{f:.1f}".rstrip("0").rstrip(".")
        return f"f/{text}"
    if kind == "exposure":
        if frac >= 1:
            return f"{float(frac):g}s"
        reduced = frac.limit_denominator(8000)
        return f"1/{reduced.denominator}s" if reduced.numerator == 1 else f"{reduced.numerator}/{reduced.denominator}s"
    if kind == "focal_length":
        f = float(frac)
        return f"{f:.0f}mm" if f == int(f) else f"{f:.1f}mm"
    return str(frac)


def extract_exif(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    with Image.open(path) as img:
        exif = img.getexif()
        if not exif:
            return result

        tag_names = {v: k for k, v in ExifTags.TAGS.items()}

        make = exif.get(tag_names.get("Make", -1))
        model = exif.get(tag_names.get("Model", -1))
        if make or model:
            camera = " ".join(part for part in [make, model] if part).strip()
            if camera:
                result["camera"] = camera

        exif_ifd = exif.get_ifd(EXIF_IFD_TAG) if EXIF_IFD_TAG in exif else {}

        lens = exif_ifd.get(tag_names.get("LensModel", -1))
        if lens:
            result["lens"] = str(lens)

        date_original = exif_ifd.get(tag_names.get("DateTimeOriginal", -1))
        if date_original:
            # EXIF format: "YYYY:MM:DD HH:MM:SS"
            date_part = str(date_original).split(" ")[0]
            result["dateTaken"] = date_part.replace(":", "-")

        fnumber = exif_ifd.get(tag_names.get("FNumber", -1))
        aperture = _rational_to_str(fnumber, "fnumber")
        if aperture:
            result["aperture"] = aperture

        exposure = exif_ifd.get(tag_names.get("ExposureTime", -1))
        shutter = _rational_to_str(exposure, "exposure")
        if shutter:
            result["shutterSpeed"] = shutter

        focal_length = exif_ifd.get(tag_names.get("FocalLength", -1))
        focal = _rational_to_str(focal_length, "focal_length")
        if focal:
            result["focalLength"] = focal

        iso = exif_ifd.get(tag_names.get("ISOSpeedRatings", -1))
        if iso:
            result["iso"] = str(iso)

    return result


def make_thumbnail(src: Path, dest: Path) -> None:
    with Image.open(src) as img:
        img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="WEBP", quality=WEBP_QUALITY, method=6)


def upload_to_r2(local_path: Path, key: str) -> str:
    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key = os.environ["R2_ACCESS_KEY_ID"]
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    bucket = os.environ.get("R2_BUCKET", "duo-li-media")
    public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")

    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )
    client.upload_file(
        str(local_path),
        bucket,
        key,
        ExtraArgs={"ContentType": "image/webp"},
    )
    return f"{public_url}/{key}"


def write_mdx(slug: str, title: str, image_url: str, exif: dict[str, str], location: str | None,
              tags: list[str], date_taken: str | None) -> Path:
    DUO_LI_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    dest = DUO_LI_PHOTOS_DIR / f"{slug}.mdx"
    if dest.exists():
        raise FileExistsError(f"{dest} already exists, refusing to overwrite")

    def _yaml_str(value: str) -> str:
        # JSON string syntax is valid YAML flow-scalar syntax too — cheap, correct escaping
        # without a YAML-writing dependency. ensure_ascii=False keeps CJK text readable.
        return json.dumps(value, ensure_ascii=False)

    frontmatter_lines = [
        "---",
        f"title: {_yaml_str(title)}",
        f"slug: {_yaml_str(slug)}",
    ]
    resolved_date = date_taken or exif.get("dateTaken")
    if resolved_date:
        frontmatter_lines.append(f"dateTaken: {_yaml_str(resolved_date)}")
    if location:
        frontmatter_lines.append(f"location: {_yaml_str(location)}")
    for key in ("camera", "lens", "focalLength", "aperture", "shutterSpeed", "iso"):
        if exif.get(key):
            frontmatter_lines.append(f"{key}: {_yaml_str(exif[key])}")
    frontmatter_lines.append(f"tags: [{', '.join(_yaml_str(t) for t in tags)}]")
    frontmatter_lines.append(f"imageUrl: {_yaml_str(image_url)}")
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    dest.write_text("\n".join(frontmatter_lines), encoding="utf-8")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo_path", type=Path, help="Local path to the source photo")
    parser.add_argument("--slug", required=True, help="URL slug, e.g. kyoto-alley")
    parser.add_argument("--title", required=True, help="Display title")
    parser.add_argument("--location", default=None)
    parser.add_argument("--date-taken", default=None, help="Overrides EXIF date, format YYYY-MM-DD")
    parser.add_argument("--tags", nargs="*", default=[])
    args = parser.parse_args()

    if not args.photo_path.exists():
        print(f"error: {args.photo_path} does not exist", file=sys.stderr)
        sys.exit(1)

    _load_env_file()
    required_env = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_URL"]
    missing = [key for key in required_env if not os.environ.get(key)]
    if missing:
        print(f"error: missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading EXIF from {args.photo_path} ...")
    exif = extract_exif(args.photo_path)
    for key, value in exif.items():
        print(f"  {key}: {value}")

    thumbnail_path = REPO_ROOT / "photos-generated" / f"{args.slug}.webp"
    print(f"Generating thumbnail (max {MAX_DIMENSION}px, WebP q={WEBP_QUALITY}) -> {thumbnail_path}")
    make_thumbnail(args.photo_path, thumbnail_path)

    key = f"photos/{args.slug}.webp"
    print(f"Uploading to R2 bucket as {key} ...")
    image_url = upload_to_r2(thumbnail_path, key)
    print(f"  public URL: {image_url}")

    dest = write_mdx(
        slug=args.slug,
        title=args.title,
        image_url=image_url,
        exif=exif,
        location=args.location,
        tags=args.tags,
        date_taken=args.date_taken,
    )
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
