#!/usr/bin/env bash
# deploy.sh — Build the card and deploy assets to Home Assistant.
#
# HACS 2026-summer: for category=INTEGRATION (which Lovelace cards are),
# HACS downloads the entire custom_components/<domain>/ directory from the
# repo into www/community/<repo>/. So this script rsyncs that one dir.
#
# USAGE:
#   bash scripts/deploy.sh                 # uses HA_PATH=/config/www
#   HA_PATH=/custom/path bash deploy.sh    # override target
#   DRY_RUN=1 bash deploy.sh               # print actions, do not copy
#
# EXIT: 0 on success, 1 if HA path is missing or build failed.
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
BUNDLE="custom_components/little_buddy_card/dist/little-buddy-card.js"
if [[ ! -s "$BUNDLE" ]]; then
  echo "✗ $BUNDLE is missing or empty." >&2
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
# HACS lays out the custom_components/<domain>/ tree flat under
# www/community/<repo>/. We mirror that here.
copy() {
  local src="$1" label="$2"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] would copy: $src/ → $HA_PATH/"
  else
    cp -r "$src" "$HA_PATH/"
    echo "  ✓ $label: $(du -sh "$HA_PATH/${src##*/}" 2>/dev/null | cut -f1)"
  fi
}

echo "→ Copying custom_components/little_buddy_card/ → $HA_PATH …"
copy "custom_components/little_buddy_card/dist" "card bundle"
copy "custom_components/little_buddy_card/assets" "pet + tree placeholders (40)"

# --- 5. Summary ---
echo
echo "✅ Deploy complete."
echo "   Bundle:       /local/little-buddy-card/dist/little-buddy-card.js"
echo "   Pet sprites:  /local/little-buddy-card/assets/pets/level_{1-5}/{mood}.png"
echo "   Tree sprites: /local/little-buddy-card/assets/trees/{stage}.png"
echo
echo "Next: in HA, hard-refresh your dashboard (Ctrl+Shift+R)."
