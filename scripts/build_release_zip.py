#!/usr/bin/env python3
"""
Build a HACS release asset: dist/little-buddy-card.zip containing only the
runtime payload (the bundle + the 40 placeholder sprites), nothing else.

HACS for category=INTEGRATION (incl. Lovelace cards, in HACS 2026-summer)
downloads the contents of custom_components/<domain>/ from the repo tree
into www/community/<repo>/. This ZIP is therefore a *convenience* /
fallback for users who prefer manual install via wget + unzip, not a
required install path.

For the normal HACS install path see .github/workflows/release.yml — the
custom_components/ tree is the source of truth.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "little-buddy-card.zip")
CC = os.path.join(ROOT, "custom_components", "little_buddy_card")


def main():
    bundle = os.path.join(CC, "dist", "little-buddy-card.js")
    if not os.path.exists(bundle):
        print(f"✗ {bundle} missing — run: npm run build")
        return 1

    os.makedirs(DIST, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)

    written = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # The bundle at the top level (so users can wget+unzip and get
        # the .js without a custom_components/ prefix).
        zf.write(bundle, arcname="little-buddy-card.js")
        written += 1
        # All 40 sprites flat at the top of the zip (matches the path
        # scheme the card expects at /local/little-buddy-card/).
        for sub in ("pets", "trees"):
            for dirpath, _, files in os.walk(os.path.join(CC, "assets", sub)):
                for f in files:
                    src = os.path.join(dirpath, f)
                    arc = os.path.relpath(src, os.path.join(CC, "assets"))
                    zf.write(src, arcname=f"assets/{arc}")
                    written += 1

    size = os.path.getsize(OUT)
    print(f"✅ {OUT}")
    print(f"   {written} files, {size:,} bytes ({size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
