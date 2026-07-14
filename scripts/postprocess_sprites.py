#!/usr/bin/env python3
"""
postprocess_sprites.py — Post-process the 40 Little-Buddy LoRA sprites.

Pipeline (per sprite):
  1. load RGBA (64x64, fully opaque from gen pipeline)
  2. KEY the background: 8-connected flood-fill grown from all 4 border rows/cols
     with a per-edge color-tolerance. Anything reached = background -> alpha 0.
     This is robust to multi-colored borders (e.g. tree_03 red/black/tan corners)
     because every background region touches the border and is seeded directly.
  3. UNIFY palette: build ONE global palette from the union of all creature colors
     across the 40 sprites (exact if <=256 colors, else median-cut to 256) and map
     every sprite onto it (dither=NONE). Shared palette => coherent set; also snaps
     the accidental downscale-gradient noise = artifact removal.
  4. NN-UPSCALE 64 -> 128 so the release sprites match the repo's existing
     128px transparent placeholder convention (ready to drop into /local/...).
  5. Export:
       assets/release/pets/pet_XX.png     (128, indexed PNG, transparent bg)
       assets/release/trees/tree_XX.png   (128, indexed PNG, transparent bg)
       assets/release/littlebuddy_atlas.png (8x5 grid sprite sheet, 1024x640)
       assets/release/littlebuddy_atlas.json (name -> [x,y,w,h] map)
       assets/release/contact_sheet.png   (labeled, gray-bg, for human eyeball pass)
       assets/release/RELEASE_MANIFEST.json (per-sprite metadata + regen flags)

Regen-needed heuristic: if the keyed creature area is < 6% of the 64x64 canvas
(near-blank sprite), flag regen_needed=True.

Usage:
  python3 postprocess_sprites.py
"""
import os
import json
import collections
import math

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO, "assets", "sprites")
OUT_DIR = os.path.join(REPO, "assets", "release")
MANIFEST_SRC = os.path.join(SRC_DIR, "_manifest.json")

TARGET = 128          # upscaled output size (repo convention)
NATIVE = 64           # source size
KEY_TOL = 60          # RGB euclidean tolerance for border flood-fill
MIN_CREATURE_FRAC = 0.06  # below this (of 64x64) -> flag regen

# ---------------------------------------------------------------- keying
def key_background(im, tol=KEY_TOL):
    """Flood background from the border. Returns RGBA with bg -> alpha 0."""
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    visited = [[False] * w for _ in range(h)]
    bg = [[False] * w for _ in range(h)]
    queue = []

    def push(x, y):
        if 0 <= x < w and 0 <= y < h and not visited[y][x]:
            visited[y][x] = True
            queue.append((x, y))

    # seed: all border pixels
    for x in range(w):
        push(x, 0); push(x, h - 1)
    for y in range(h):
        push(0, y); push(w - 1, y)

    while queue:
        x, y = queue.pop()
        bg[y][x] = True
        cr, cg, cb, ca = px[x, y]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or visited[ny][nx]:
                    continue
                nr, ng, nb, na = px[nx, ny]
                d = math.sqrt((cr - nr) ** 2 + (cg - ng) ** 2 + (cb - nb) ** 2)
                if d <= tol:
                    push(nx, ny)

    # apply alpha: bg -> 0, also zero RGB on bg so quantize has clean black bg
    out = rgba.copy()
    opx = out.load()
    for y in range(h):
        for x in range(w):
            if bg[y][x]:
                opx[x, y] = (0, 0, 0, 0)
    return out


def creature_frac(rgba):
    px = rgba.load()
    w, h = rgba.size
    n = sum(1 for y in range(h) for x in range(w) if px[x, y][3] > 0)
    return n / (w * h)


# ---------------------------------------------------------------- palette
def build_global_palette(sprite_rgbs):
    """sprite_rgbs: list of PIL 'RGB' images (bg already zeroed). Returns
    (pal_img, n_colors) where pal_img is a 'P' mode 1x1 image carrying the palette."""
    # count distinct creature colors
    distinct = set()
    for im in sprite_rgbs:
        px = im.load()
        w, h = im.size
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                if r == 0 and g == 0 and b == 0:
                    continue
                distinct.add((r, g, b))
    n_colors = len(distinct)
    colors = min(256, n_colors)
    # stack for median-cut palette estimation
    stack = Image.new("RGB", (NATIVE, NATIVE * len(sprite_rgbs)))
    for i, im in enumerate(sprite_rgbs):
        stack.paste(im, (0, i * NATIVE))
    q = stack.convert("P", palette=Image.ADAPTIVE, colors=colors)
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(q.getpalette())
    return pal_img, n_colors, colors


def quantize_to_palette(rgb_im, pal_img):
    """Map an 'RGB' (bg zeroed) image onto the fixed palette -> indexed RGBA."""
    q = rgb_im.quantize(palette=pal_img, dither=Image.NONE)  # 'P'
    # find palette index closest to (0,0,0) = our transparent bg color
    pal = q.getpalette()
    best_i, best_d = 0, 1e9
    for i in range(256):
        r, g, b = pal[i * 3:i * 3 + 3]
        d = (r - 0) ** 2 + (g - 0) ** 2 + (b - 0) ** 2
        if d < best_d:
            best_d, best_i = d, i
    q.info["transparency"] = best_i
    return q.convert("RGBA")


# ---------------------------------------------------------------- sheets
def make_atlas(sprites, cols=8, cell=TARGET):
    rows = math.ceil(len(sprites) / cols)
    atlas = Image.new("RGBA", (cols * cell, rows * cell), (0, 0, 0, 0))
    mapping = {}
    for idx, (name, im) in enumerate(sprites):
        r, c = divmod(idx, cols)
        x, y = c * cell, r * cell
        atlas.paste(im, (x, y))
        mapping[name] = [x, y, cell, cell]
    return atlas, mapping


def make_contact_sheet(sprites, cols=8, cell=TARGET, bg=(90, 90, 100, 255)):
    rows = math.ceil(len(sprites) / cols)
    sheet = Image.new("RGBA", (cols * cell, rows * cell), bg)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    d = ImageDraw.Draw(sheet)
    for idx, (name, im) in enumerate(sprites):
        r, c = divmod(idx, cols)
        x, y = c * cell, r * cell
        # checker behind transparent so alpha reads clearly
        for yy in range(0, cell, 16):
            for xx in range(0, cell, 16):
                if ((xx // 16) + (yy // 16)) % 2 == 0:
                    d.rectangle([x + xx, y + yy, x + xx + 15, y + yy + 15],
                                fill=(60, 60, 70, 255))
        sheet.alpha_composite(im, (x, y))
        if font:
            d.text((x + 3, y + 3), name.replace(".png", ""), fill=(255, 255, 0, 255), font=font)
    return sheet


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    src_manifest = {}
    if os.path.exists(MANIFEST_SRC):
        src_manifest = json.load(open(MANIFEST_SRC))

    pet_files = sorted(f for f in os.listdir(SRC_DIR) if f.startswith("pet_") and f.endswith(".png"))
    tree_files = sorted(f for f in os.listdir(SRC_DIR) if f.startswith("tree_") and f.endswith(".png"))
    all_files = [(f, "pets") for f in pet_files] + [(f, "trees") for f in tree_files]

    keyed = {}        # name -> RGBA (native 64)
    rgb_for_pal = []  # 'RGB' bg-zeroed for palette build
    fracs = {}
    for fname, kind in all_files:
        im = Image.open(os.path.join(SRC_DIR, fname)).convert("RGBA")
        k = key_background(im)
        keyed[fname] = k
        rgb_for_pal.append(k.convert("RGB"))
        fracs[fname] = creature_frac(k)

    pal_img, n_colors, used_colors = build_global_palette(rgb_for_pal)

    pets_out, trees_out = [], []
    release_manifest = {
        "meta": {
            "source": "assets/sprites/* (LoRA littlebuddy_pixel_00001_ @0.8)",
            "native_size": NATIVE,
            "output_size": TARGET,
            "key_tolerance": KEY_TOL,
            "upscale": "nearest-neighbor 64->128",
            "palette": {
                "mode": "global-shared",
                "distinct_creature_colors": n_colors,
                "palette_size": used_colors,
                "method": "exact" if n_colors <= 256 else "median-cut-256",
            },
        },
        "sprites": {},
    }

    for fname, kind in all_files:
        k = keyed[fname]
        rgb = k.convert("RGB")
        qi = quantize_to_palette(rgb, pal_img)        # indexed RGBA
        up = qi.resize((TARGET, TARGET), Image.NEAREST)  # NN upscale, stays indexed-color
        out_dir = os.path.join(OUT_DIR, kind)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, fname)
        # save as indexed PNG with transparency
        up_idx = up.convert("P", palette=Image.ADAPTIVE, colors=256)
        # carry transparency index over
        up_idx.info["transparency"] = qi.info.get("transparency", 0)
        up_idx.save(out_path, "PNG")
        # also keep a clean RGBA copy for sheets
        up_rgba = up
        if kind == "pets":
            pets_out.append((fname, up_rgba))
        else:
            trees_out.append((fname, up_rgba))

        meta = dict(src_manifest.get(fname, {}))
        frac = fracs[fname]
        regen = frac < MIN_CREATURE_FRAC
        meta.update({
            "output_size": [TARGET, TARGET],
            "output_path": os.path.relpath(out_path, REPO),
            "creature_area_frac": round(frac, 4),
            "transparent_background": True,
            "regen_needed": regen,
        })
        release_manifest["sprites"][fname] = meta

    # sprite sheet (pets + trees combined, ordered)
    combined = pets_out + trees_out
    atlas, mapping = make_atlas(combined, cols=8, cell=TARGET)
    atlas_path = os.path.join(OUT_DIR, "littlebuddy_atlas.png")
    atlas.save(atlas_path, "PNG")
    json.dump(mapping, open(os.path.join(OUT_DIR, "littlebuddy_atlas.json"), "w"), indent=2)

    contact = make_contact_sheet(combined, cols=8, cell=TARGET)
    contact_path = os.path.join(OUT_DIR, "contact_sheet.png")
    contact.save(contact_path, "PNG")

    json.dump(release_manifest, open(os.path.join(OUT_DIR, "RELEASE_MANIFEST.json"), "w"), indent=2)

    regen = [f for f, _ in all_files if release_manifest["sprites"][f]["regen_needed"]]
    print(f"OK  processed {len(all_files)} sprites")
    print(f"    palette: {used_colors} colors ({'exact' if n_colors<=256 else 'median-cut-256'}), distinct creature colors={n_colors}")
    print(f"    pets  -> {os.path.join(OUT_DIR,'pets')}")
    print(f"    trees -> {os.path.join(OUT_DIR,'trees')}")
    print(f"    atlas -> {atlas_path}")
    print(f"    sheet -> {contact_path}")
    print(f"    regen_needed ({len(regen)}): {regen}")


if __name__ == "__main__":
    main()
