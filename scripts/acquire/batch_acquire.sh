#!/bin/bash
cd ~/duo-nas
source .venv/bin/activate
while IFS= read -r url; do
  echo "=== $url ==="
  python scripts/acquire/acquire.py "$url" 2>&1 | tail -5
done < scripts/acquire/batch_urls.txt
