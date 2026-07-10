#!/usr/bin/env bash
# release.sh — Create a HACS-compatible GitHub Release for Little Buddy Card
# Usage: bash scripts/release.sh [patch|minor|major]
# Default: patch
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# --- Config ---
GITHUB_USER="icem0"
REPO_NAME="little-buddy-card"
ASSET_FILE="dist/little-buddy-card.js"
MANIFEST="manifest.json"
PACKAGE="package.json"

# --- Bump type ---
BUMP_TYPE="${1:-patch}"
if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major)$ ]]; then
  echo "Usage: bash scripts/release.sh [patch|minor|major]"
  exit 1
fi

# --- Get GitHub token from git credentials ---
TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: No GitHub token found in ~/.git-credentials"
  echo "Run: git config --global credential.helper store"
  echo "Then: echo 'https://USERNAME:TOKEN@github.com' > ~/.git-credentials"
  exit 1
fi

# --- Current version ---
CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['version'])")
echo "Current version: $CURRENT_VERSION"

# --- Bump version ---
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
case "$BUMP_TYPE" in
  major)  MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor)  MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch)  PATCH=$((PATCH + 1)) ;;
esac
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
NEW_TAG="v${NEW_VERSION}"
echo "New version: $NEW_VERSION (tag: $NEW_TAG)"

# --- Build ---
echo "Building dist..."
npm run build

# --- Bump version in files ---
python3 -c "
import json
for f in ['$MANIFEST', '$PACKAGE']:
    data = json.load(open(f))
    data['version'] = '$NEW_VERSION'
    with open(f, 'w') as fh:
        json.dump(data, fh, indent=2)
        fh.write('\n')
"
echo "Version bumped in manifest.json + package.json"

# --- Git commit + tag ---
git add "$MANIFEST" "$PACKAGE" "$ASSET_FILE"
git commit -m "release: v$NEW_VERSION"
git tag "$NEW_TAG"
echo "Committed and tagged $NEW_TAG"

# --- Push ---
git push origin main
git push origin "$NEW_TAG"
echo "Pushed to GitHub"

# --- Create GitHub Release ---
echo "Creating GitHub Release..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_USER/$REPO_NAME/releases" \
  -d "$(python3 -c "
import json
print(json.dumps({
    'tag_name': '$NEW_TAG',
    'name': 'v$NEW_VERSION',
    'body': 'Release v$NEW_VERSION\n\nBuilt dist/little-buddy-card.js included.',
    'draft': False,
    'prerelease': False,
    'make_latest': 'true'
}))
")")

RELEASE_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")
if [[ -z "$RELEASE_ID" ]]; then
  echo "ERROR: Failed to create release: $RESPONSE"
  exit 1
fi
echo "Release created (id=$RELEASE_ID)"

# --- Upload asset ---
echo "Uploading $ASSET_FILE..."
curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/javascript" \
  --data-binary @"$ASSET_FILE" \
  "https://uploads.github.com/repos/$GITHUB_USER/$REPO_NAME/releases/$RELEASE_ID/assets?name=little-buddy-card.js"

echo ""
echo "✅ Release v$NEW_VERSION complete!"
echo "   HACS will detect this as an update."
echo "   Download: https://github.com/$GITHUB_USER/$REPO_NAME/releases/download/$NEW_TAG/little-buddy-card.js"
