#!/usr/bin/env bash
# deploy.sh — Build the card and deploy assets to Home Assistant.
#
# PURPOSE: After editing source or pulling newer assets, run this once and
# the card is updated. Copies dist + asset folders into
# /config/www/community/little-buddy-card/ which is served by HA at
# /local/little-buddy-card/.
#
# USAGE:
#   bash scripts/deploy.sh                 # uses HA_PATH=/config/www
#   HA_PATH=/custom/path bash deploy.sh    # override target
#   DRY_RUN=1 bash deploy.sh               # print actions, do not copy
#
# EXIT: 0 on success, 1 if HA path is missing.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

HA_PATH="${HA_PATH:-/config/www/community/little-buddy-card}"
DRY_RUN="${DRY_RUN:-0}"

echo "→ Repo:    $REPO_DIR"
echo "→ Target:  $HA_PATH"

# --- 1. Build ---
echo "→ Building card (npm run build)…"
if ! npm run build --silent; then
  echo "✗ Build failed." >&2
  exit 1
fi

# --- 2. Sanity ---
if [[ ! -s dist/little-buddy-card.js ]]; then
  echo "✗ dist/little-buddy-card.js is missing or empty." >&2
  exit 1
fi

# --- 3. Ensure target exists ---
if [[ ! -d "$HA_PATH" && "$DRY_RUN" != "1" ]]; then
  if ! mkdir -p "$HA_PATH"; then
    echo "✗ Cannot create $HA_PATH." >&2
    echo "  Set HA_PATH=/your/target or create the directory first." >&2
    exit 1
  fi
fi

# --- 4. Copy ---
copy() {
  local src="$1" label="$2"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] would copy: $src → $HA_PATH/"
  else
    cp -r "$src" "$HA_PATH/"
    echo "  ✓ $label: $(du -sh "$HA_PATH/${src##*/}" 2>/dev/null | cut -f1)"
  fi
}

echo "→ Copying to $HA_PATH …"
copy "dist"                       "card bundle"
copy "assets/pets"                "pet placeholders (35)"
copy "assets/trees"               "tree placeholders (5)"

# --- 5. Summary ---
echo
echo "✅ Deploy complete."
echo "   Card served at:  /local/little-buddy-card/little-buddy-card.js"
echo "   Pet images:      /local/little-buddy-card/pets/level_{1-5}/{mood}.{png,gif}"
echo "   Tree images:     /local/little-buddy-card/trees/{stage}.{png,gif}"
echo
echo "Next: in HA, Settings → Developer Tools → YAML → 'Reload all YAML files'"
echo "      then hard-refresh your dashboard (Ctrl+Shift+R)."
