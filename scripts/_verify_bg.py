from PIL import Image
import glob, os
from collections import Counter

SPRITES = "/root/little-buddy-card/assets/sprites"

def modal_bg(path, sample_step=2):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    cnt = Counter()
    for x in range(0, w, sample_step):
        for y in range(0, h, sample_step):
            cnt[px[x, y]] += 1
    return cnt.most_common(3)

print("=== PETS (sample 3) ===")
for p in sorted(glob.glob(os.path.join(SPRITES, "pet_*.png")))[:3]:
    print(os.path.basename(p), modal_bg(p))

print("=== TREES (all) ===")
for t in sorted(glob.glob(os.path.join(SPRITES, "tree_*.png"))):
    name = os.path.basename(t)
    top = modal_bg(t)
    # is the dominant color near-white?
    dom = top[0][0]
    is_white = all(c > 240 for c in dom)
    print(f"{name} dominant={dom} near_white={is_white} top3={top}")
