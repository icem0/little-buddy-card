#!/usr/bin/env python3
"""
gen_littlebuddy_sprites.py — Generate 35 distinct Little-Buddy pet sprites via
the ComfyUI-Direct API at SwarmUI.

Context (task t_5692390d, parent t_99cd9b1a):
  - SwarmUI @ 192.168.178.53:7801, ComfyUI-Direct backend
  - Base : RDXL_Pixel_Art_-_Pony_2.safetensors
  - LoRA : littlebuddy_pixel_00001_.safetensors  (loaded via ComfyUI LoraLoader
           node — SwarmUI WebAPI LoRA index does NOT know this LoRA)
  - Workflow template: assets/workflows/littlebuddy_sprite_gen_v1_api.json
    (8 nodes, positive prompt has a {pose} placeholder, SaveImage at node 8)
  - Sprite target: 64x64, nearest-neighbor downscale (no smoothing)
  - Identity token "littlebuddy" stays fixed; species + palette vary per sprite.

Outputs: assets/sprites/pet_01.png .. pet_35.png

Usage:
  python3 gen_littlebuddy_sprites.py --count 1     # smoke test (pet_01 only)
  python3 gen_littlebuddy_sprites.py --count 35    # full batch (default)
  python3 gen_littlebuddy_sprites.py --start 5 --count 35   # resume from index 5
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

# 35 (species, palette) combos — species varies identity-flavor, palette varies color.
SPECIES = [
    "cat", "dog", "fox", "rabbit", "bear", "dragon", "wolf", "tiger", "panda",
    "owl", "frog", "hamster", "penguin", "chick", "deer", "raccoon", "hedgehog",
    "lion", "monkey", "pig", "cow", "horse", "seal", "turtle", "bat", "squid",
    "sloth", "axolotl", "chameleon", "duck", "mouse", "snake", "crab", "octopus",
    "koala",
]
PALETTES = [
    "warm orange and cream", "cool blue and white", "mint green and pink",
    "lavender and gold", "red and black", "teal and yellow", "purple and silver",
    "peach and brown", "sky blue and coral", "forest green and tan",
    "rose and ivory", "navy and cyan", "maroon and beige", "lime and violet",
    "coral and mint", "indigo and peach", "charcoal and amber", "pink and slate",
    "emerald and cream", "royal blue and gold", "cherry and white", "olive and rust",
    "periwinkle and rose", "sand and turquoise", "plum and sage", "cobalt and ivory",
    "brick and cream", "seafoam and lilac", "mahogany and gold", "steel and coral",
    "honey and moss", "dusty rose and teal", "cream and cocoa", "sky and marigold",
    "violet and mint",
]
POSES = [
    "standing, idle pose, both feet planted, neutral expression",
    "happy expression, small smile, slight bounce",
    "sad expression, head tilted down",
    "angry expression, slight stomp",
    "sleepy expression, eyes half closed, slight sway",
    "thirsty expression, looking up, tongue slightly out",
    "hungry expression, looking at viewer, eager",
    "playful expression, one paw up, wagging",
    "walking forward, one foot in front of the other, mid-step",
    "sitting pose, weight on haunches",
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
        # ensure exact square; crop center if non-square, then NN shrink
        if im.width != im.height:
            s = min(im.width, im.height)
            left = (im.width - s) // 2
            top = (im.height - s) // 2
            im = im.crop((left, top, left + s, top + s))
        im = im.resize((target, target), Image.NEAREST)
    return im


def build_manifest(existing):
    with open(MANIFEST, "w") as f:
        json.dump(existing, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=35)
    ap.add_argument("--start", type=int, default=1,
                    help="1-based start index (for resume)")
    ap.add_argument("--no-downscale", action="store_true",
                    help="keep ComfyUI native res instead of 64px")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    wf_template = load_workflow()
    client_id = f"hermes_gen_{int(time.time())}"

    manifest = {}
    if os.path.exists(MANIFEST):
        try:
            manifest = json.load(open(MANIFEST))
        except Exception:
            manifest = {}

    done = 0
    failed = []
    end = min(args.start + args.count - 1, 35)
    for i in range(args.start, end + 1):
        species = SPECIES[i - 1]
        palette = PALETTES[i - 1]
        pose = POSES[(i - 1) % len(POSES)]
        wf = json.loads(json.dumps(wf_template))  # deep copy
        base_pos = wf["3"]["inputs"]["text"]
        wf["3"]["inputs"]["text"] = (
            f"pixel art, littlebuddy, 32x32 chibi creature, {species}, "
            f"{palette} palette, white background, masterpiece, highly detailed, "
            f"sharp pixels, no smoothing, {pose}"
        )
        wf["6"]["inputs"]["seed"] = random.randint(1, 2**31 - 1)
        wf["8"]["inputs"]["filename_prefix"] = f"pet_{i:02d}"

        try:
            pid = submit_prompt(wf, client_id)
            hist = wait_for_output(pid)
            imgs = hist["outputs"]["8"]["images"]
            first = imgs[0]
            raw = fetch_image(first["filename"], first.get("subfolder", ""))
            im = downscale_to_target(raw) if not args.no_downscale else Image.open(BytesIO(raw)).convert("RGBA")
            out_path = os.path.join(OUT_DIR, f"pet_{i:02d}.png")
            im.save(out_path, "PNG")
            manifest[f"pet_{i:02d}.png"] = {
                "index": i, "species": species, "palette": palette,
                "pose": pose, "seed": wf["6"]["inputs"]["seed"],
                "prompt_id": pid, "size": im.size,
            }
            build_manifest(manifest)
            done += 1
            print(f"[OK] pet_{i:02d}.png  species={species}  palette={palette}  "
                  f"size={im.size}  ({done}/{args.count})")
        except Exception as e:
            failed.append(i)
            print(f"[FAIL] pet_{i:02d}.png  species={species}  -> {type(e).__name__}: {e}")
            continue

    print("\n=== SUMMARY ===")
    print(f"generated: {done}/{args.count}  failed: {len(failed)} {failed}")
    print(f"output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
