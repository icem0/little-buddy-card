from PIL import Image
import glob, os

SPRITES = "/root/little-buddy-card/assets/sprites"
trees = sorted(glob.glob(os.path.join(SPRITES, "tree_*.png")))

for t in trees:
    im = Image.open(t).convert("RGB")
    px = im.load()
    w, h = im.size
    # sample a 4x4 grid of corner-ish + center
    samples = {
        "tl": px[0,0], "tr": px[w-1,0], "bl": px[0,h-1], "br": px[w-1,h-1],
        "center": px[w//2,h//2]
    }
    # count how many pixels are "near-white" (>240 all channels)
    nw = sum(1 for x in range(0,w,2) for y in range(0,h,2)
             if all(c > 240 for c in px[x,y]))
    total = (w//2)*(h//2)
    print(os.path.basename(t), samples, f"near-white%={100*nw/total:.1f}")
