#!/bin/bash
# Append URLs to batch_urls.txt any time; re-run this whenever you want to catch up.
# Already-downloaded URLs (tracked by BV id in batch_done.txt) are skipped automatically.
cd ~/duo-nas
source .venv/bin/activate

URLS_FILE="scripts/acquire/batch_urls.txt"
DONE_FILE="scripts/acquire/batch_done.txt"
touch "$DONE_FILE"

while IFS= read -r url; do
  [ -z "$url" ] && continue
  case "$url" in \#*) continue ;; esac

  # Key the done-list on the BV id, not the full URL — the same video can show up with
  # different tracking query params (?spm_id_from=..., ?vd_source=...) across pastes.
  id=$(echo "$url" | grep -oE 'BV[0-9A-Za-z]+' | head -1)
  if [ -z "$id" ]; then
    echo "=== SKIP (couldn't parse a BV id): $url ==="
    continue
  fi

  if grep -qxF "$id" "$DONE_FILE"; then
    echo "=== SKIP (already downloaded): $id ==="
    continue
  fi

  echo "=== $id : $url ==="
  output=$(python scripts/acquire/acquire.py "$url" 2>&1)
  status=$?
  echo "$output" | tail -5

  if [ $status -eq 0 ]; then
    echo "$id" >> "$DONE_FILE"
  else
    echo "=== FAILED (will retry next run): $id ==="
  fi
done < "$URLS_FILE"
