#!/usr/bin/env python3
"""
Generate 5 distinct tree sprites via the littlebuddy pixel-art LoRA.

MIRRORS the proven pet-sprite recipe (scripts/gen_littlebuddy_sprites.py, task
t_5692390d) so the output is visually consistent with the existing pet sprites:
  - SwarmUI @ 192.168.178.53:7801, ComfyUI-Direct backend
  - Base : RDXL_Pixel_Art_-_Pony_2.safetensors
  - LoRA : littlebuddy_pixel_00001_.safetensors  (ComfyUI LoraLoader node)
  - Workflow template: assets/workflows/littlebuddy_sprite_gen_v1_api.json
  - Sprite target: 64x64, center-crop + nearest-neighbor downscale (NO bg removal)
  - KEEP white/light background (matches pet sprites' convention)
  - Identity token "littlebuddy" fixed; tree shape + palette vary per sprite.

Outputs: assets/sprites/tree_01.png .. tree_05.png  (merged into _manifest.json)

Author: Helga (kanban t_56b44faa)
"""
import argparse
import json
import os
import sys
import time
import random

import requests
from PIL import Image
from io import BytesIO

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
HOST = "http://192.168.178.53:7801"
WORKFLOW = os.path.join(REPO, "assets", "workflows", "littlebuddy_sprite_gen_v1_api.json")
OUT_DIR = os.path.join(REPO, "assets", "sprites")
SPRITE_TARGET = 64
MANIFEST = os.path.join(OUT_DIR, "_manifest.json")

# 5 tree variants: (shape descriptor, color palette) — shape varies identity-flavor,
# palette varies color. "littlebuddy" stays fixed for LoRA identity consistency.
TREES = [
    ("round bushy tree, lush green canopy, thick brown trunk",
     "forest green and tan"),
    ("tall slender pine tree, dark green needles, conifer",
     "emerald and cream"),
    ("autumn tree, orange and red leaves, small brown trunk",
     "maroon and beige"),
    ("small bonsai sapling, light green leaves, tiny pot",
     "mint green and pink"),
    ("blossom tree, pink flowers, soft green foliage, spring",
     "rose and ivory"),
]
POSES = [
    "standing upright, centered, neutral",
    "standing upright, centered, slight breeze",
    "standing upright, centered, full spread",
    "standing upright, centered, compact",
    "standing upright, centered, flowering",
]


def load_workflow():
    with open(WORKFLOW) as f:
        return json.load(f)


def submit_prompt(wf, client_id):
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt",
                      json={"prompt": wf, "client_id": client_id}, timeout=60)
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait_for_output(prompt_id, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data:
                return data[prompt_id]
        time.sleep(3)
    raise TimeoutError(f"prompt {prompt_id} did not finish in {timeout}s")


def fetch_image(filename, subfolder, img_type="output"):
    r = requests.get(f"{HOST}/ComfyBackendDirect/view",
                     params={"filename": filename, "subfolder": subfolder,
                             "type": img_type}, timeout=60)
    r.raise_for_status()
    return r.content


def downscale_to_target(raw_bytes, target=SPRITE_TARGET):
    im = Image.open(BytesIO(raw_bytes)).convert("RGBA")
    if im.width != target or im.height != target:
        if im.width != im.height:
            s = min(im.width, im.height)
            left = (im.width - s) // 2
            top = (im.height - s) // 2
            im = im.crop((left, top, left + s, top + s))
        im = im.resize((target, target), Image.NEAREST)
    return im


def build_manifest(merge):
    with open(MANIFEST, "w") as f:
        json.dump(merge, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, default=None,
                    help="1-based index to (re)generate a single tree")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    wf_template = load_workflow()
    client_id = f"helga_tree_{int(time.time())}"

    manifest = {}
    if os.path.exists(MANIFEST):
        try:
            manifest = json.load(open(MANIFEST))
        except Exception:
            manifest = {}

    idxs = [args.only] if args.only else list(range(1, len(TREES) + 1))
    done = 0
    failed = []
    for i in idxs:
        shape, palette = TREES[i - 1]
        pose = POSES[i - 1]
        wf = json.loads(json.dumps(wf_template))
        base_pos = wf["3"]["inputs"]["text"]
        wf["3"]["inputs"]["text"] = (
            f"pixel art, littlebuddy, 32x32 chibi tree, {shape}, "
            f"{palette} palette, white background, masterpiece, highly detailed, "
            f"sharp pixels, no smoothing, {pose}"
        )
        wf["6"]["inputs"]["seed"] = random.randint(1, 2**31 - 1)
        wf["8"]["inputs"]["filename_prefix"] = f"tree_{i:02d}"

        try:
            pid = submit_prompt(wf, client_id)
            hist = wait_for_output(pid)
            imgs = hist["outputs"]["8"]["images"]
            first = imgs[0]
            raw = fetch_image(first["filename"], first.get("subfolder", ""))
            im = downscale_to_target(raw)
            out_path = os.path.join(OUT_DIR, f"tree_{i:02d}.png")
            im.save(out_path, "PNG")
            manifest[f"tree_{i:02d}.png"] = {
                "index": i, "shape": shape, "palette": palette,
                "pose": pose, "seed": wf["6"]["inputs"]["seed"],
                "prompt_id": pid, "size": list(im.size),
            }
            build_manifest(manifest)
            done += 1
            print(f"[OK] tree_{i:02d}.png  shape={shape}  palette={palette}  "
                  f"size={im.size}  ({done}/{len(idxs)})")
        except Exception as e:
            failed.append(i)
            print(f"[FAIL] tree_{i:02d}.png  shape={shape}  -> {type(e).__name__}: {e}")
            continue

    print("\n=== SUMMARY ===")
    print(f"generated: {done}/{len(idxs)}  failed: {len(failed)} {failed}")
    print(f"output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
