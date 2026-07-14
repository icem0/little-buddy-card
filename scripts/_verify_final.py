import os, glob, hashlib, json
from collections import defaultdict

SPRITES = "/root/little-buddy-card/assets/sprites"

try:
    from PIL import Image
except ImportError:
    print("PIL_MISSING")
    raise SystemExit(1)

files = sorted(glob.glob(os.path.join(SPRITES, "*.png")))
pets = sorted(glob.glob(os.path.join(SPRITES, "pet_*.png")))
trees = sorted(glob.glob(os.path.join(SPRITES, "tree_*.png")))
others = [f for f in files if not (os.path.basename(f).startswith("pet_") or os.path.basename(f).startswith("tree_"))]

print(f"TOTAL_PNG={len(files)} PET={len(pets)} TREE={len(trees)} OTHER={len(others)}")

# Dimensions + content + hashes
sizes = defaultdict(int)
hashes = defaultdict(list)
issues = []
dims = set()
for f in files:
    im = Image.open(f).convert("RGB")
    w, h = im.size
    dims.add((w, h))
    sizes[(w, h)] += 1
    # distinct color count (proxy for content)
    cols = im.getcolors(maxcolors=10**7)
    ncols = len(cols) if cols else 0
    if ncols < 4:
        issues.append(f"{os.path.basename(f)}: looks flat ({ncols} colors)")
    hsh = hashlib.md5(open(f, "rb").read()).hexdigest()
    hashes[hsh].append(os.path.basename(f))

print("DIMENSIONS:", dict(sizes))
dupes = {h: names for h, names in hashes.items() if len(names) > 1}
print("DUPLICATES:", dupes)
print("ISSUES:", issues)

# baseline color stats to compare pet vs tree style
def avg_bg(im):
    # sample corner pixels (assume white bg convention)
    px = im.load()
    w, h = im.size
    corners = [px[0,0], px[w-1,0], px[0,h-1], px[w-1,h-1]]
    return corners

pet_bg = avg_bg(Image.open(pets[0]).convert("RGB"))
tree_bg = avg_bg(Image.open(trees[0]).convert("RGB"))
print("PET0_CORNERS:", pet_bg)
print("TREE0_CORNERS:", tree_bg)

result = {
    "total": len(files), "pet": len(pets), "tree": len(trees), "other": len(others),
    "dimensions": {f"{k[0]}x{k[1]}": v for k, v in sizes.items()},
    "duplicates": dupes,
    "issues": issues,
}
print("JSON:", json.dumps(result))
