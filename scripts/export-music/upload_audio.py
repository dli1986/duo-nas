"""Upload a local audio file (mp3) to the Cloudflare R2 bucket for the duo-li Music module.

Usage:
    python upload_audio.py AUDIO_PATH --slug my-song

Prints the resulting public URL. Requires a .env (or exported env vars) with
R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_URL —
see duo-nas/.env.example.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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


def upload_audio_to_r2(local_path: Path, slug: str) -> str:
    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key = os.environ["R2_ACCESS_KEY_ID"]
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    bucket = os.environ.get("R2_BUCKET", "duo-li-media")
    public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")

    key = f"music/{slug}.mp3"
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )
    client.upload_file(str(local_path), bucket, key, ExtraArgs={"ContentType": "audio/mpeg"})
    return f"{public_url}/{key}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_path", type=Path, help="Local path to the source mp3")
    parser.add_argument("--slug", required=True, help="Music entry slug, e.g. si-shi-gu-ren-lai")
    args = parser.parse_args()

    if not args.audio_path.exists():
        print(f"error: {args.audio_path} does not exist", file=sys.stderr)
        sys.exit(1)

    _load_env_file()
    required_env = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_URL"]
    missing = [key for key in required_env if not os.environ.get(key)]
    if missing:
        print(f"error: missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    url = upload_audio_to_r2(args.audio_path, args.slug)
    print(url)


if __name__ == "__main__":
    main()
