#!/usr/bin/env bash
# verify.sh — Pre-drop sanity check for Little Buddy Card (v0.9.5+ Integration-Category structure).
#
# Checks:
#   - bundle at custom_components/little_buddy_card/frontend/little-buddy-card.js
#   - manifest.json present + integration_type
#   - hacs.json minimal (no filename/content_in_root, those belong to Plugin-Category)
#   - brand/ has icon.png + dark_icon.png
#   - GitHub release for current version
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"
errors=0

ok()   { echo "  ✓ $1"; }
warn() { echo "  ⚠ $1"; }
err()  { echo "  ✗ $1"; errors=$((errors+1)); }

echo "Little Buddy Card — verify (Integration-Category structure)"
echo "─────────────────────────────────────────────────────────────"

# 1. bundle
echo
echo "[1] Build artefacts"
bundle="custom_components/little_buddy_card/frontend/little-buddy-card.js"
if [[ -s "$bundle" ]]; then
  size=$(stat -c%s "$bundle" 2>/dev/null || stat -f%z "$bundle")
  ok "$bundle exists (${size} bytes)"
else
  err "$bundle missing or empty — run: npm run build"
fi

# 2. mtime
src_mtime=$(find src -type f -name '*.ts' -printf '%T@\n' 2>/dev/null | sort -nr | head -1)
bundle_mtime=$(stat -c%Y "$bundle" 2>/dev/null || stat -f%m "$bundle" 2>/dev/null)
if [[ -n "${src_mtime:-}" && -n "${bundle_mtime:-}" ]]; then
  if (( $(printf "%.0f" "$src_mtime") > bundle_mtime )); then
    err "src/ is newer than bundle — re-run: npm run build"
  else
    ok "bundle is up-to-date with src/"
  fi
fi

# 3. manifest.json
echo
echo "[2] Integration manifest"
manifest="custom_components/little_buddy_card/manifest.json"
if [[ -s "$manifest" ]]; then
  version=$(python3 -c "import json;print(json.load(open('$manifest'))['version'])" 2>/dev/null || echo "unknown")
  domain=$(python3 -c "import json;print(json.load(open('$manifest'))['domain'])" 2>/dev/null || echo "unknown")
  itype=$(python3 -c "import json;print(json.load(open('$manifest')).get('integration_type',''))" 2>/dev/null || echo "")
  ok "manifest version: $version, domain: $domain"
  if [[ "$itype" != "lovelace" ]]; then
    err "manifest.integration_type must be 'lovelace', got '$itype'"
  else
    ok "manifest.integration_type: lovelace"
  fi
else
  err "$manifest missing"
fi

# 4. brand
echo
echo "[3] Brand assets"
for f in icon.png dark_icon.png; do
  p="custom_components/little_buddy_card/brand/$f"
  if [[ -s "$p" ]]; then
    ok "$p present"
  else
    err "$p missing"
  fi
done

# 5. hacs.json
echo
echo "[4] hacs.json"
hacs_file="hacs.json"
if [[ -s "$hacs_file" ]]; then
  hname=$(python3 -c "import json;print(json.load(open('$hacs_file')).get('name',''))")
  hfilename=$(python3 -c "import json;print(json.load(open('$hacs_file')).get('filename',''))" 2>/dev/null)
  hroot=$(python3 -c "import json;print(json.load(open('$hacs_file')).get('content_in_root',''))" 2>/dev/null)
  if [[ -n "$hname" ]]; then ok "name: $hname"; else err "name missing"; fi
  if [[ -z "$hfilename" ]]; then ok "no filename (correct for Integration-Category)"; else warn "filename set ($hfilename) — not needed for Integration"; fi
  if [[ -z "$hroot" ]]; then ok "no content_in_root (correct for Integration-Category)"; else warn "content_in_root set — not needed for Integration"; fi
else
  err "$hacs_file missing"
fi

# 6. ZIP
echo
echo "[5] Release ZIP"
if [[ -s "dist/little-buddy-card.zip" ]]; then
  zsize=$(stat -c%s "dist/little-buddy-card.zip")
  ok "dist/little-buddy-card.zip exists ($zsize bytes)"
  if unzip -l "dist/little-buddy-card.zip" 2>/dev/null | grep -q "custom_components/little_buddy_card/manifest.json"; then
    ok "ZIP contains manifest.json"
  else
    err "ZIP missing manifest.json"
  fi
  if unzip -l "dist/little-buddy-card.zip" 2>/dev/null | grep -q "custom_components/little_buddy_card/frontend/little-buddy-card.js"; then
    ok "ZIP contains frontend bundle"
  else
    err "ZIP missing frontend bundle"
  fi
else
  warn "dist/little-buddy-card.zip not built — run: npm run zip"
fi

# 7. GitHub release
echo
echo "[6] GitHub release (informational)"
release_json=$(curl -sS --max-time 8 "https://api.github.com/repos/icem0/little-buddy-card/releases/tags/v${version}" 2>/dev/null || true)
if echo "$release_json" | python3 -c "import sys,json;d=json.load(sys.stdin);sys.exit(0 if d.get('id') else 1)" 2>/dev/null; then
  ok "v${version} release live"
else
  warn "v${version} release not found on GitHub yet"
fi

echo
if (( errors == 0 )); then
  echo "✅ All checks passed — card is ready to drop into a dashboard."
  exit 0
else
  echo "❌ $errors issue(s) found — fix and re-run."
  exit 1
fi
