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
if [[ -s dist/little-buddy-card.js ]]; then
  size=$(stat -c%s dist/little-buddy-card.js 2>/dev/null || stat -f%z dist/little-buddy-card.js)
  ok "dist/little-buddy-card.js exists (${size} bytes)"
  if (( size < 20000 )); then
    warn "dist looks small (<20KB) — was the build minified?"
  fi
else
  err "dist/little-buddy-card.js missing or empty — run: npm run build"
fi

# 2. mtime: dist newer than src?
src_mtime=$(find src -type f -name '*.ts' -printf '%T@\n' 2>/dev/null | sort -nr | head -1)
dist_mtime=$(stat -c%Y dist/little-buddy-card.js 2>/dev/null || stat -f%m dist/little-buddy-card.js)
if [[ -n "${src_mtime:-}" && -n "${dist_mtime:-}" ]]; then
  if (( $(printf "%.0f" "$src_mtime") > dist_mtime )); then
    err "src/ is newer than dist/ — re-run: npm run build"
  else
    ok "dist is up-to-date with src/"
  fi
fi

# 3. placeholder assets
echo
echo "[2] Placeholder assets"
missing_pets=0
for lvl in 1 2 3 4 5; do
  for mood in happy sad hungry thirsty sleepy angry playful; do
    f="assets/pets/level_${lvl}/${mood}.png"
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
  f="assets/trees/${stage}.png"
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
version=$(python3 -c "import json;print(json.load(open('manifest.json'))['version'])" 2>/dev/null || echo "unknown")
ok "manifest version: $version"
if [[ "$version" == "0.0.0" ]]; then
  err "manifest version still 0.0.0 — did you forget to bump?"
fi

# 5. GitHub release (informational)
echo
echo "[4] GitHub release (informational)"
release_json=$(curl -sS --max-time 8 "https://api.github.com/repos/icem0/little-buddy-card/releases/tags/v${version}" 2>/dev/null || true)
if echo "$release_json" | python3 -c "import sys,json;d=json.load(sys.stdin);sys.exit(0 if d.get('id') else 1)" 2>/dev/null; then
  asset=$(echo "$release_json" | python3 -c "import sys,json;d=json.load(sys.stdin);print((d.get('assets') or [{}])[0].get('name','(no asset)'))")
  ok "v${version} release live, asset: $asset"
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
