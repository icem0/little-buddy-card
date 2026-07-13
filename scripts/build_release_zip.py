#!/usr/bin/env python3
"""
Build a HACS release asset: dist/little-buddy-card.zip containing only the
runtime payload (the bundle + the 40 placeholder sprites), nothing else.

The bundle now lives at the repo root (little-buddy-card.js) — HACS-Plugin
downloads it from there into www/community/little-buddy-card/.

This ZIP is a convenience/fallback for manual install, not required for the
normal HACS-Plugin path (which uses the root .js directly).
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "little-buddy-card.zip")
BUNDLE = os.path.join(ROOT, "little-buddy-card.js")
ASSETS = os.path.join(ROOT, "assets")


def main():
    if not os.path.exists(BUNDLE):
        print(f"✗ {BUNDLE} missing — run: npm run build")
        return 1

    os.makedirs(DIST, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)

    written = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Bundle at top level (wget+unzip gives the .js without prefix).
        zf.write(BUNDLE, arcname="little-buddy-card.js")
        written += 1
        # 40 sprites flat under assets/ (matches /local/little-buddy-card/).
        for sub in ("pets", "trees"):
            for dirpath, _, files in os.walk(os.path.join(ASSETS, sub)):
                for f in files:
                    src = os.path.join(dirpath, f)
                    arc = os.path.relpath(src, ASSETS)
                    zf.write(src, arcname=f"assets/{arc}")
                    written += 1

    size = os.path.getsize(OUT)
    print(f"✅ {OUT}")
    print(f"   {written} files, {size:,} bytes ({size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
