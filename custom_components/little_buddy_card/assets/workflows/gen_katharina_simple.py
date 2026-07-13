#!/usr/bin/env python3
"""
Generate a NEW simple pixel-art input image for Katharina.
Replaces the old master with too much "folklore"/playful detail.

Design:
- Solid flat background (single color)
- Centered chibi girl, blonde braids, red dress
- Minimal details: simple face (2 eyes, small smile), 2 braids, dress
- 32x32 internal grid scaled to 512x512 with NEAREST (crisp pixels)
- No patterns, no decorations, symmetric
"""

from PIL import Image, ImageDraw

def generate_katharina_simple(output_path, grid=32, scale=16):
    """Generate simple pixel-art Katharina on a grid, scaled up with NEAREST."""
    # Palette
    BG = (220, 225, 230)      # light gray-blue flat bg
    SKIN = (255, 220, 190)    # skin
    HAIR = (250, 220, 120)    # blonde
    DRESS = (220, 60, 60)     # red
    OUTLINE = (40, 40, 50)    # dark outline
    WHITE = (255, 255, 255)
    BLACK = (20, 20, 20)

    # Create grid (grid x grid), start all BG
    img = Image.new("RGB", (grid, grid), BG)
    px = img.load()

    def setp(x, y, color):
        if 0 <= x < grid and 0 <= y < grid:
            px[x, y] = color

    cx = grid // 2  # center x

    # ── Hair (top) ──
    for x in range(cx-6, cx+6):
        setp(x, 4, HAIR)
        setp(x, 5, HAIR)
    for x in range(cx-5, cx+5):
        setp(x, 6, HAIR)

    # ── Face (skin) ──
    for y in range(7, 14):
        for x in range(cx-4, cx+4):
            setp(x, y, SKIN)

    # ── Braids (sides) ──
    for y in range(7, 16):
        setp(cx-5, y, HAIR)
        setp(cx-6, y, HAIR)
        setp(cx+5, y, HAIR)
        setp(cx+6, y, HAIR)
    # braid tips
    setp(cx-6, 16, HAIR)
    setp(cx+6, 16, HAIR)

    # ── Eyes ──
    setp(cx-2, 10, BLACK)
    setp(cx+2, 10, BLACK)

    # ── Smile (small) ──
    setp(cx-1, 12, OUTLINE)
    setp(cx, 12, OUTLINE)
    setp(cx+1, 12, OUTLINE)

    # ── Body / Dress (red triangle-ish) ──
    for y in range(14, 24):
        width = (y - 14) // 2 + 3  # widens downward
        for x in range(cx-width, cx+width):
            setp(x, y, DRESS)

    # ── Arms (skin, simple) ──
    setp(cx-6, 16, SKIN)
    setp(cx+6, 16, SKIN)
    setp(cx-7, 17, SKIN)
    setp(cx+7, 17, SKIN)

    # ── Legs (simple, skin) ──
    for y in range(24, 28):
        setp(cx-2, y, SKIN)
        setp(cx+2, y, SKIN)

    # ── Shoes (dark) ──
    setp(cx-3, 28, OUTLINE)
    setp(cx-2, 28, OUTLINE)
    setp(cx+2, 28, OUTLINE)
    setp(cx+3, 28, OUTLINE)

    # Scale up with NEAREST for crisp pixels
    big = img.resize((grid * scale, grid * scale), Image.NEAREST)
    big.save(output_path)
    print(f"✅ Generated: {output_path} ({grid}x{grid} grid, {grid*scale}x{grid*scale} output)")
    return big


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/root/little-buddy-card/assets/katharina_master.png"
    generate_katharina_simple(out)
