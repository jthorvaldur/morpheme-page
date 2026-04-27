#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DIST="$ROOT/dist"

echo "=== morpheme-page build ==="
echo ""

# Clean and recreate dist/
rm -rf "$DIST"
mkdir -p "$DIST"
echo "[1/5] Cleaned dist/"

# Copy site/ contents (html, css/, js/) to dist/
if [ -d "$ROOT/site" ]; then
  # Copy all files from site/ preserving structure
  cp -R "$ROOT/site/"* "$DIST/" 2>/dev/null || true
  echo "[2/5] Copied site/ -> dist/"
else
  echo "[2/5] No site/ directory found, skipping"
fi

# Copy viz/*.html to dist/viz/ (exclude maps/ subdirectory — local only)
if [ -d "$ROOT/viz" ]; then
  mkdir -p "$DIST/viz"
  cp "$ROOT/viz/"*.html "$DIST/viz/" 2>/dev/null || true
  # Don't copy viz/maps/ — those are local/personal analysis
  VIZ_COUNT=$(ls -1 "$DIST/viz/"*.html 2>/dev/null | wc -l | tr -d ' ')
  echo "[3/5] Copied $VIZ_COUNT visualizations -> dist/viz/"
else
  echo "[3/5] No viz/ directory found, skipping"
fi

# Copy data/*.json to dist/data/
if [ -d "$ROOT/data" ]; then
  mkdir -p "$DIST/data"
  cp "$ROOT/data/"*.json "$DIST/data/" 2>/dev/null || true
  DATA_COUNT=$(ls -1 "$DIST/data/"*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "[4/5] Copied $DATA_COUNT data files -> dist/data/"
else
  echo "[4/5] No data/ directory found, skipping"
fi

# Template replacements in dist/index.html
if [ -f "$DIST/index.html" ]; then
  # Count decompositions
  if [ -f "$DIST/data/decompositions.json" ]; then
    DECOMP_COUNT=$(python3 -c "
import json, sys
with open('$DIST/data/decompositions.json') as f:
    data = json.load(f)
if isinstance(data, list):
    print(len(data))
else:
    print(0)
" 2>/dev/null || echo "0")
  else
    DECOMP_COUNT="0"
  fi

  # Current date in YYYY-MM-DD format
  LAST_UPDATED=$(date +%Y-%m-%d)

  # Replace template variables
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/{{DECOMPOSITION_COUNT}}/$DECOMP_COUNT/g" "$DIST/index.html"
    sed -i '' "s/{{LAST_UPDATED}}/$LAST_UPDATED/g" "$DIST/index.html"
  else
    sed -i "s/{{DECOMPOSITION_COUNT}}/$DECOMP_COUNT/g" "$DIST/index.html"
    sed -i "s/{{LAST_UPDATED}}/$LAST_UPDATED/g" "$DIST/index.html"
  fi

  echo "[5/5] Replaced templates: DECOMPOSITION_COUNT=$DECOMP_COUNT, LAST_UPDATED=$LAST_UPDATED"
else
  echo "[5/5] No index.html found, skipping template replacements"
fi

echo ""
echo "=== Build complete ==="
echo ""

# Print summary
echo "dist/ contents:"
if command -v tree &>/dev/null; then
  tree "$DIST" --noreport
else
  find "$DIST" -type f | sort | sed "s|$DIST/|  |"
fi

TOTAL_FILES=$(find "$DIST" -type f | wc -l | tr -d ' ')
echo ""
echo "Total files: $TOTAL_FILES"
