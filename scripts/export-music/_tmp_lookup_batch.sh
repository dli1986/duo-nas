#!/bin/bash
# One-off batch metadata lookup helper — not meant to be a permanent script.
cd ~/duo-nas
source .venv/bin/activate

pairs=(
  "汪峰|硬币"
  "张国荣|有谁共鸣"
  "张信哲|别让情两难"
  "张信哲|用情"
  "张国荣|共同渡过"
  "张学友|望月"
  "张清芳|大雨的夜里"
  "张清芳|花雨夜"
  "汪峰|光明"
  "陶喆|寂寞的季节"
)

for pair in "${pairs[@]}"; do
  IFS='|' read -r artist title <<< "$pair"
  echo "### $artist - $title"
  python scripts/export-music/musicbrainz_lookup.py "$artist" "$title" 2>&1
  echo
done
