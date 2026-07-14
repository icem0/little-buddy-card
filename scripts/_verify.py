import os, glob
from PIL import Image
import numpy as np

OUT = "assets/sprites"
files = sorted(glob.glob(os.path.join(OUT, "pet_*.png")))
expected = [f"pet_{i:02d}.png" for i in range(1, 36)]

print("count:", len(files))
missing = [e for e in expected if not os.path.exists(os.path.join(OUT, e))]
print("missing:", missing)

problems = []
for f in expected:
    p = os.path.join(OUT, f)
    if not os.path.exists(p):
        problems.append((f, "MISSING"))
        continue
    im = Image.open(p)
    if im.size != (64, 64):
        problems.append((f, f"size={im.size}"))
        continue
    a = np.asarray(im.convert("RGB")).astype(int)
    # white-ish background detection
    white = (a[:, :, 0] > 240) & (a[:, :, 1] > 240) & (a[:, :, 2] > 240)
    nonwhite = int((~white).sum())
    if nonwhite < 100:
        problems.append((f, f"TOO_BLANK nonwhite={nonwhite}"))
    # check not a single flat color
    if len(np.unique(a.reshape(-1, 3), axis=0)) < 5:
        problems.append((f, "FLAT_COLOR"))

print("problems:", problems if problems else "NONE")
print("all 35 distinct PNGs present & valid:", len(files) == 35 and not problems)
