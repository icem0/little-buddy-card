#!/usr/bin/env bash
# verify.sh — Pre-drop sanity check for Little Buddy Card.
#
# PURPOSE: Run this before adding the card to a dashboard. Catches:
#   - missing dist bundle
#   - missing/empty placeholder assets
#   - dist not rebuilt after src changes
#   - missing GitHub release (for HACS update path)
#   - manifest version drift
#
# EXIT: 0 = ready, 1 = issues found (printed in human-readable form).
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
errors=0

ok()   { echo "  ✓ $1"; }
warn() { echo "  ⚠ $1"; err() { errors=$((errors+1)); }; }
err()  { echo "  ✗ $1"; errors=$((errors+1)); }

echo "Little Buddy Card — verify"
echo "───────────────────────────"

# 1. dist bundle
echo
echo "[1] Build artefacts"
bundle="custom_components/little_buddy_card/dist/little-buddy-card.js"
if [[ -s "$bundle" ]]; then
  size=$(stat -c%s "$bundle" 2>/dev/null || stat -f%z "$bundle")
  ok "$bundle exists (${size} bytes)"
  if (( size < 20000 )); then
    warn "bundle looks small (<20KB) — was the build minified?"
  fi
else
  err "$bundle missing or empty — run: npm run build"
fi

# 2. mtime: bundle newer than src?
src_mtime=$(find custom_components/little_buddy_card/src -type f -name '*.ts' -printf '%T@\n' 2>/dev/null | sort -nr | head -1)
bundle_mtime=$(stat -c%Y "$bundle" 2>/dev/null || stat -f%m "$bundle")
if [[ -n "${src_mtime:-}" && -n "${bundle_mtime:-}" ]]; then
  if (( $(printf "%.0f" "$src_mtime") > bundle_mtime )); then
    err "src/ is newer than bundle — re-run: npm run build"
  else
    ok "bundle is up-to-date with src/"
  fi
fi

# 3. placeholder assets
echo
echo "[2] Placeholder assets"
missing_pets=0
for lvl in 1 2 3 4 5; do
  for mood in happy sad hungry thirsty sleepy angry playful; do
    f="custom_components/little_buddy_card/assets/pets/level_${lvl}/${mood}.png"
    if [[ ! -s "$f" ]]; then
      err "missing/empty: $f"
      missing_pets=$((missing_pets+1))
    fi
  done
done
if [[ $missing_pets -eq 0 ]]; then
  ok "all 35 pet placeholders present"
else
  err "$missing_pets pet placeholders missing — run: python3 scripts/download_placeholder_assets.py"
fi

missing_trees=0
for stage in seed sprout sapling young_tree full_grown; do
  f="custom_components/little_buddy_card/assets/trees/${stage}.png"
  if [[ ! -s "$f" ]]; then
    err "missing/empty: $f"
    missing_trees=$((missing_trees+1))
  fi
done
if [[ $missing_trees -eq 0 ]]; then
  ok "all 5 tree placeholders present"
else
  err "$missing_trees tree placeholders missing — run: python3 scripts/download_placeholder_assets.py"
fi

# 4. manifest
echo
echo "[3] Manifest"
version=$(python3 -c "import json;print(json.load(open('custom_components/little_buddy_card/manifest.json'))['version'])" 2>/dev/null || echo "unknown")
ok "manifest version: $version"
if [[ "$version" == "0.0.0" ]]; then
  err "manifest version still 0.0.0 — did you forget to bump?"
fi

# 5. hacs.json vs. manifest consistency
echo
echo "[4] HACS manifest consistency"
hacs_filename=$(python3 -c "import json;print(json.load(open('hacs.json'))['filename'])" 2>/dev/null || echo "")
hacs_zip=$(python3 -c "import json;print(json.load(open('hacs.json')).get('zip_release',False))" 2>/dev/null || echo "False")
if [[ -n "$hacs_filename" ]]; then
  ok "hacs.json filename: $hacs_filename"
  if [[ "$hacs_zip" == "True" ]]; then
    if [[ "$hacs_filename" == *.zip ]]; then
      ok "hacs.json: zip_release=true + filename ends .zip — HACS will use ZIP download path"
      if [[ -s "dist/$hacs_filename" ]]; then
        ok "dist/$hacs_filename exists ($(stat -c%s "dist/$hacs_filename") bytes)"
      else
        err "dist/$hacs_filename missing — run: npm run zip"
      fi
    else
      err "hacs.json: zip_release=true but filename '$hacs_filename' does not end in .zip"
    fi
  fi
else
  err "hacs.json missing 'filename'"
fi

# 6. GitHub release (informational)
echo
echo "[5] GitHub release (informational)"
release_json=$(curl -sS --max-time 8 "https://api.github.com/repos/icem0/little-buddy-card/releases/tags/v${version}" 2>/dev/null || true)
if echo "$release_json" | python3 -c "import sys,json;d=json.load(sys.stdin);sys.exit(0 if d.get('id') else 1)" 2>/dev/null; then
  asset_names=$(echo "$release_json" | python3 -c "import sys,json;d=json.load(sys.stdin);print(' '.join(a['name'] for a in d.get('assets',[])))")
  ok "v${version} release live, assets: $asset_names"
  if [[ "$hacs_zip" == "True" && "$hacs_filename" != "" ]]; then
    if echo " $asset_names " | grep -q " $hacs_filename "; then
      ok "ZIP asset '$hacs_filename' is attached to release"
    else
      err "Release v${version} is missing the ZIP asset '$hacs_filename' that hacs.json points to"
    fi
  fi
else
  warn "v${version} release not found on GitHub — HACS users won't see an update"
fi

# 6. HA helpers (optional)
echo
echo "[5] HA helpers (optional)"
helpers_file="examples/package/little_buddy_helpers.yaml"
if [[ -s "$helpers_file" ]]; then
  ok "helpers package present: $helpers_file"
else
  warn "helpers package missing"
fi

echo
if (( errors == 0 )); then
  echo "✅ All checks passed — card is ready to drop into a dashboard."
  exit 0
else
  echo "❌ $errors issue(s) found — fix and re-run."
  exit 1
fi
