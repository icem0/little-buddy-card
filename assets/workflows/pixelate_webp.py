#!/usr/bin/env python3
"""
Post-Processing: Convert WanAnimate WebP output to Pixel Art.
Nearest-neighbor downscale + K-Means color quantize.

This is the MISSING step in v14 — WanAnimate produces photorealistic video
(49k colors), but our master is pixel art (164 colors). This script bridges
the gap: takes the animated WebP, quantizes each frame to N colors, and
re-saves as animated WebP with pixel-art aesthetic.
"""

import sys
from PIL import Image, ImageSequence
import numpy as np

def pixelate_webp(input_path, output_path, target_size=(256, 256), n_colors=32, fps=16):
    """
    Convert animated WebP to pixel art.
    
    Args:
        input_path: source animated WebP (from WanAnimate)
        output_path: destination animated WebP (pixelated)
        target_size: downscale target (pixel art is low-res)
        n_colors: number of colors in palette (pixel art uses few)
        fps: frames per second for output
    """
    src = Image.open(input_path)
    frames = []
    
    for i, frame in enumerate(ImageSequence.Iterator(src)):
        # 1. Convert to RGB
        rgb = frame.convert("RGB")
        
        # 2. Nearest-neighbor downscale (preserves hard pixel edges)
        small = rgb.resize(target_size, Image.NEAREST)
        
        # 3. Color quantize via K-Means
        arr = np.array(small).reshape(-1, 3).astype(np.float32)
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
        labels = kmeans.fit_predict(arr)
        quantized = kmeans.cluster_centers_[labels].astype(np.uint8)
        pixel_art = quantized.reshape(target_size[1], target_size[0], 3)
        
        # 4. Back to PIL, scale up with NEAREST for crisp pixels
        pixel_img = Image.fromarray(pixel_art, "RGB")
        pixel_img = pixel_img.resize((512, 512), Image.NEAREST)  # display size
        
        frames.append(pixel_img)
        if i % 10 == 0:
            print(f"  Frame {i}: quantized to {n_colors} colors")
    
    # Save as animated WebP
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),
        loop=0,
        lossless=True,
        format="WEBP",
    )
    print(f"\n✅ Saved: {output_path} ({len(frames)} frames, {target_size} internal, {n_colors} colors)")

if __name__ == "__main__":
    inp = sys.argv[1] if len(sys.argv) > 1 else "/root/little-buddy-card/assets/temp/katharina_hop_v9.webp"
    out = sys.argv[2] if len(sys.argv) > 2 else "/root/little-buddy-card/assets/temp/katharina_hop_pixelated.webp"
    tsize = tuple(map(int, (sys.argv[3] if len(sys.argv) > 3 else "256,256").split(",")))
    ncol = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    
    pixelate_webp(inp, out, target_size=tsize, n_colors=ncol)
