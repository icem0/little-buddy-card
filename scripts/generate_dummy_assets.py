#!/usr/bin/env python3
"""
Generate static placeholder PNGs for the Little Buddy Card.

WHY: The animated GIF asset pipeline (ASSET-7/8/9) runs in parallel and is
not ready for the dev loop. To keep the card renderable without 404 noise,
we ship small static dummy PNGs (colored block + label) that the card can
load instead of the final pixel-art sprites.

The card reads `config.asset_ext` (default 'png' in dev builds). When the
real GIF/art pipeline lands, flip `asset_ext` to 'gif' and drop the real
assets at the same paths under /local/little-buddy-card/.

Run:  python3 scripts/generate_dummy_assets.py
Output: assets/pets/level_1..5/<mood>.png  (35)
        assets/trees/<stage>.png           (5)
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOODS = ["happy", "sad", "hungry", "thirsty", "sleepy", "angry", "playful"]
LEVELS = [1, 2, 3, 4, 5]
TREES = ["seed", "sprout", "sapling", "young_tree", "full_grown"]

# Mood -> base color (hex). Tree -> green shades.
MOOD_COLORS = {
    "happy": (255, 209, 102),
    "sad": (120, 160, 220),
    "hungry": (240, 150, 90),
    "thirsty": (90, 190, 220),
    "sleepy": (160, 150, 200),
    "angry": (230, 100, 90),
    "playful": (140, 220, 140),
}
TREE_COLORS = {
    "seed": (150, 120, 80),
    "sprout": (120, 180, 100),
    "sapling": (90, 190, 90),
    "young_tree": (70, 170, 80),
    "full_grown": (50, 150, 70),
}


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _label(draw, text, w, h):
    font = _font(max(10, h // 8))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2), text, fill=(20, 20, 20), font=font)


def make_tile(path, color, label, size=128):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGBA", (size, size), color + (255,))
    d = ImageDraw.Draw(img)
    # simple border to mimic a sprite frame
    d.rectangle([2, 2, size - 3, size - 3], outline=(0, 0, 0, 120), width=2)
    _label(d, label, size, size)
    img.save(path)
    return path


def main():
    pets = os.path.join(ROOT, "assets", "pets")
    trees = os.path.join(ROOT, "assets", "trees")
    count = 0

    for lvl in LEVELS:
        for mood in MOODS:
            color = MOOD_COLORS[mood]
            label = f"L{lvl}\n{mood}"
            p = os.path.join(pets, f"level_{lvl}", f"{mood}.png")
            make_tile(p, color, label)
            count += 1

    for stage in TREES:
        color = TREE_COLORS[stage]
        p = os.path.join(trees, f"{stage}.png")
        make_tile(p, color, stage)
        count += 1

    print(f"✅ {count} dummy PNGs written under {os.path.join(ROOT,'assets')}")


if __name__ == "__main__":
    main()
