# export-photos/

Turns a local photo into a live entry on the Photography page: extracts EXIF,
generates an optimized WebP thumbnail, uploads it to the Cloudflare R2 bucket,
and writes the corresponding `content/photos/<slug>.mdx` file into the sibling
`duo-li` repo.

No "download original" feature is provided or planned — only the resized WebP
thumbnail ever leaves this machine.

## Where to keep original photos

Keep full-resolution source photos in `duo-nas/photos/` (gitignored,
local-only — mirrors `duo-nas/music/` for original audio: bare folder name =
the original-media library). **Do not** use a folder that syncs to any cloud
service (OneDrive, Google Drive, iCloud, etc.), especially a work/corporate-
managed account — that defeats the point of "only the thumbnail ever leaves
this machine" by handing the original to that cloud provider instead.
`photos/` is just a plain local folder with no upload/sync of its own; treat
it as this machine's "NAS" storage for photos.

Generated WebP thumbnails are written to `duo-nas/photos-generated/`
(also gitignored) — kept in a separate folder so originals and derived
output never mix.

## Setup

Uses the same repo-root venv as every other script under `scripts/` (do **not** create a separate venv in this folder — see root README's Setup section):

```bash
cd ../..                    # duo-nas repo root
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt   # first time only
cd scripts/export-photos
```

Fill in the R2 section of `duo-nas/.env` (copy from `.env.example` if you
haven't already) with real credentials from the Cloudflare dashboard
(R2 > Manage API Tokens for the access key pair):

```
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=duo-li-media
R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

## Usage

```bash
python upload_photo.py ~/Pictures/kyoto-alley.jpg \
  --slug kyoto-alley \
  --title "Kyoto Alley" \
  --location "Kyoto, Japan" \
  --tags travel street \
  --date-taken 2024-05-01   # optional, overrides EXIF DateTimeOriginal
```

This will:

1. Read EXIF (camera, lens, date, focal length, aperture, shutter speed, ISO)
   from the source file.
2. Resize to a max dimension of 2400px and re-encode as WebP (quality 82),
   written locally to `photos-generated/<slug>.webp` (gitignored — working
   file only, not the same folder as the originals).
3. Upload the WebP to `R2_BUCKET` under key `photos/<slug>.webp` (R2's own
   key namespace — unrelated to the local folder names above) via the
   S3-compatible API, and build the public URL from `R2_PUBLIC_URL`.
4. Write `../../../duo-li/content/photos/<slug>.mdx` with a frontmatter
   matching `PhotoFrontmatter` in duo-li's `src/lib/photos.ts`. Refuses to
   overwrite an existing file for the same slug.

After running, `cd` into `duo-li`, review the generated `.mdx`, then
`npm run build`, commit, and push as usual.

### Known rough edge

If this is run from the WSL-side clone, the `.mdx` lands in the WSL-side
`duo-li` clone, not the Windows-side authoring copy — same friction as the
music pipeline. Mirror the file over manually (or `git pull` in WSL after
pushing from Windows, then re-run there) until this gets a real fix.
