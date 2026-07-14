from PIL import Image
import os, hashlib

d = "/root/little-buddy-card/assets/sprites"
sizes = {}
blanks = []
hashes = {}
for f in sorted(os.listdir(d)):
    if not f.endswith(".png"):
        continue
    p = os.path.join(d, f)
    im = Image.open(p).convert("RGBA")
    sz = im.size
    sizes.setdefault(sz, []).append(f)
    cols = set(im.getdata())
    if len(cols) <= 1:
        blanks.append(f)
    h = hashlib.md5(open(p, "rb").read()).hexdigest()
    hashes.setdefault(h, []).append(f)

dupe_groups = {k: v for k, v in hashes.items() if len(v) > 1}
print("SIZES:", sizes)
print("BLANKS:", blanks)
print("DUPE_GROUPS:", dupe_groups)
print("TOTAL_PNG:", len([f for f in os.listdir(d) if f.endswith('.png')]))
