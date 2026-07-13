#!/usr/bin/env python3
"""
build_release_zip.py — Bundle the card + assets into a HACS-ready ZIP.

HACS for Lovelace cards (HacsCategory.INTEGRATION with content_in_root=true)
downloads the asset(s) attached to the latest GitHub release. To ship the
card JS + all 40 placeholder sprites, we create a single ZIP that has
everything in the repository root, matching the paths the Card resolves at
runtime (/local/little-buddy-card/...).

OUTPUT: dist/little-buddy-card.zip containing:
  - little-buddy-card.js       (built bundle)
  - assets/pets/level_*/...    (35 pet sprites)
  - assets/trees/...           (5 tree sprites)
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "little-buddy-card.zip")

REQUIRED = [
    "dist/little-buddy-card.js",
    "assets/pets",
    "assets/trees",
]


def main():
    missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print(f"✗ Missing required paths: {missing}")
        print("  Run: npm run build && python3 scripts/download_placeholder_assets.py")
        return 1

    if os.path.exists(OUT):
        os.remove(OUT)

    written = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1) the bundle
        bundle = "dist/little-buddy-card.js"
        zf.write(os.path.join(ROOT, bundle), arcname="little-buddy-card.js")
        written += 1
        # 2) pets
        for dirpath, _, files in os.walk(os.path.join(ROOT, "assets", "pets")):
            for f in files:
                src = os.path.join(dirpath, f)
                arc = os.path.relpath(src, os.path.join(ROOT, "assets"))
                zf.write(src, arcname=f"assets/{arc}")
                written += 1
        # 3) trees
        for dirpath, _, files in os.walk(os.path.join(ROOT, "assets", "trees")):
            for f in files:
                src = os.path.join(dirpath, f)
                arc = os.path.relpath(src, os.path.join(ROOT, "assets"))
                zf.write(src, arcname=f"assets/{arc}")
                written += 1

    size = os.path.getsize(OUT)
    print(f"✅ {OUT}")
    print(f"   {written} files, {size:,} bytes ({size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
