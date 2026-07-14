#!/usr/bin/env python3
"""
Build a HACS release asset: dist/little-buddy-card.zip containing the
complete custom_components/ tree (manifest, frontend bundle, brand, __init__.py).

This ZIP is what HACS's "Download" button fetches when installing the
Integration. HACS unpacks it into config/custom_components/little_buddy_card/.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "little-buddy-card.zip")
CC = os.path.join(ROOT, "custom_components", "little_buddy_card")
MANIFEST = os.path.join(CC, "manifest.json")
BUNDLE = os.path.join(CC, "frontend", "little-buddy-card.js")


def main():
    if not os.path.exists(MANIFEST):
        print(f"✗ {MANIFEST} missing")
        return 1
    if not os.path.exists(BUNDLE):
        print(f"✗ {BUNDLE} missing — run: npm run build")
        return 1

    os.makedirs(DIST, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)

    written = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for dirpath, _, files in os.walk(CC):
            for f in files:
                src = os.path.join(dirpath, f)
                arc = os.path.relpath(src, ROOT)
                zf.write(src, arcname=arc)
                written += 1

    size = os.path.getsize(OUT)
    print(f"✅ {OUT}")
    print(f"   {written} files, {size:,} bytes ({size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
