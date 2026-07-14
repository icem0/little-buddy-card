from PIL import Image
import glob, os

SPRITES = "/root/little-buddy-card/assets/sprites"
OUT = "/root/little-buddy-card/assets/_contact_sheet.png"

pets = sorted(glob.glob(os.path.join(SPRITES, "pet_*.png")))
trees = sorted(glob.glob(os.path.join(SPRITES, "tree_*.png")))
all_ = pets + trees  # 40 total

cols = 8
cell = 64
rows = (len(all_) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), (200, 200, 200))
for i, p in enumerate(all_):
    im = Image.open(p).convert("RGB")
    r, c = divmod(i, cols)
    sheet.paste(im, (c * cell, r * cell))

# label row dividers: pets = rows 0-4 cols0-6, trees = last 5 in row 4
sheet.save(OUT)
print("WROTE", OUT, sheet.size, "sprites:", len(all_))
