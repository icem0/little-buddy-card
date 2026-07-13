#!/usr/bin/env python3
"""
Download free placeholder images for Little Buddy Card dev loop.

WHY: The real pixel-art pipeline (ASSET-1..6) runs in parallel and is not
ready. To keep the card renderable and visually distinguishable during
development, this script pulls 40 free placeholder images (variations of
dogs via placedog.net, seeded per file) and writes them to the expected
asset paths inside the HACS custom_components/ tree.

Once the real character art lands, simply overwrite the same files (or run
`scripts/generate_dummy_assets.py` to fall back to flat placeholders).
"""
import os
import sys
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "custom_components", "little_buddy_card", "assets")

MOODS = ["happy", "sad", "hungry", "thirsty", "sleepy", "angry", "playful"]
LEVELS = [1, 2, 3, 4, 5]
TREES = ["seed", "sprout", "sapling", "young_tree", "full_grown"]

SIZE = 128
SOURCE = "https://placedog.net"
TIMEOUT = 8
WORKERS = 8


def fetch(url: str, dest: str, timeout: int = TIMEOUT) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "little-buddy-card-dev/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if len(data) < 200:
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        print(f"  ! {dest}: {e}", file=sys.stderr)
        return False


def _job(args):
    url, dest, label = args
    return (label, dest, fetch(url, dest))


def main():
    jobs = []
    for lvl in LEVELS:
        for mood in MOODS:
            seed = f"l{lvl}-{mood}"
            url = f"{SOURCE}/{SIZE}/{SIZE}?id={seed}"
            dest = os.path.join(ASSETS, "pets", f"level_{lvl}", f"{mood}.png")
            jobs.append((url, dest, f"pet L{lvl}/{mood}"))
    for stage in TREES:
        seed = f"tree-{stage}"
        url = f"{SOURCE}/{SIZE}/{SIZE}?id={seed}"
        dest = os.path.join(ASSETS, "trees", f"{stage}.png")
        jobs.append((url, dest, f"tree/{stage}"))

    ok = fail = 0
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for label, dest, success in ex.map(_job, jobs):
            if success:
                ok += 1
                print(f"  ✓ {label}")
            else:
                fail += 1
                print(f"  ✗ {label}")

    print(f"\n✅ Downloaded {ok} placeholder images ({fail} failures).")
    if fail:
        print("   Run scripts/generate_dummy_assets.py for flat fallbacks.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
