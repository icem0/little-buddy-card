from PIL import Image
import glob, os

SPRITES = "/root/little-buddy-card/assets/sprites"

def analyze(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    nw = 0; total = 0
    distinct = set()
    for x in range(0, w, 2):
        for y in range(0, h, 2):
            c = px[x, y]
            distinct.add(c)
            total += 1
            if all(ch > 240 for ch in c):
                nw += 1
    return w, h, 100.0 * nw / total, len(distinct)

pets = sorted(glob.glob(os.path.join(SPRITES, "pet_*.png")))
trees = sorted(glob.glob(os.path.join(SPRITES, "tree_*.png")))

print("FILE | WxH | near_white% | distinct_colors")
print("--- PETS ---")
pet_nonwhite = []
for p in pets:
    w, h, nw, d = analyze(p)
    flag = "" if nw > 50 else "  <-- LOW WHITE (non-white bg?)"
    if nw <= 50: pet_nonwhite.append((os.path.basename(p), nw))
    print(f"{os.path.basename(p)} | {w}x{h} | {nw:.1f}% | {d}{flag}")

print("--- TREES ---")
tree_white = []
tree_nonwhite = []
for t in trees:
    w, h, nw, d = analyze(t)
    flag = "" if nw > 50 else "  <-- NON-WHITE BG"
    if nw > 50:
        tree_white.append((os.path.basename(t), round(nw,1)))
    else:
        tree_nonwhite.append((os.path.basename(t), round(nw,1)))
    print(f"{os.path.basename(t)} | {w}x{h} | {nw:.1f}% | {d}{flag}")

print()
print(f"PET non-white-bg count: {len(pet_nonwhite)} -> {pet_nonwhite}")
print(f"TREE white-bg count: {len(tree_white)} -> {tree_white}")
print(f"TREE non-white-bg count: {len(tree_nonwhite)} -> {tree_nonwhite}")
