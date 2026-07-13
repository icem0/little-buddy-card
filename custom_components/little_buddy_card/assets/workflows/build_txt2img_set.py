#!/usr/bin/env python3
"""
txt2img Workflow Builder — Katharina Character Set (v1)
Generates a set of consistent character images for LoRA training.

Strategy (per User 2026-07-10):
- Base: RDXL_Pixel_Art_-_Pony_2 (SDXL pixel art)
- LoRA: littlebuddy_pixel_00001_.safetensors (character consistency)
- 800x800 (higher res than 512 training, SDXL native ~1024 but 800 works)
- Multiple seeds + pose variations for training diversity

Usage:
    python3 build_txt2img_set.py            # prints plan, no gen
    python3 build_txt2img_set.py --submit   # generates all images
    python3 build_txt2img_set.py --submit --seed 42  # single image test
"""

import requests
import json
import sys
import os
import base64
import time

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/training/candidate_set"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
CHAR_LORA = "littlebuddy_pixel_00001_.safetensors"

# Pose variations for training diversity (subtle, no action words)
POSES = [
    "standing on the ground, both feet planted, idle pose, arms at sides",
    "standing, weight shifted to one foot, slight head tilt, calm pose",
    "sitting on a small stool, hands in lap, relaxed",
    "standing, one hand raised waving, gentle smile",
    "standing, both arms slightly out for balance, soft stance",
    "turned slightly to the side, three-quarter view, casual",
    "standing, looking up with curious expression, hands behind back",
    "standing, gentle hop mid-air, both feet barely off ground",
]

INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii girl, "
    "blonde hair in two long braids, (bright crimson red long dress:1.4) "
    "with puffy sleeves and white collar, white socks, black mary jane shoes, "
    "big round innocent eyes, sweet innocent, white background, masterpiece, highly detailed"
)

NEGATIVE = (
    "muted, blurry, deformed, fighting, action pose, multiple girls, adult, "
    "schürze, apron, handtasche, bag, purse, cross, crucifix, religious, kruzifix, "
    "nurse, uniform, costume, wings, halo, tail, animal ears, fantasy, "
    "white dress, blue dress, green dress, bun, ponytail, short hair, "
    "black hair, brown hair, blue hair, pink hair, folk pattern, ornaments, "
    "decorative, busy background, complex details"
)


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def generate(sid, prompt_suffix, seed, lora_weight=0.8):
    payload = {
        "session_id": sid,
        "images": 1,
        "model": BASE_MODEL,
        "prompt": f"{INSTANCE_PROMPT}, {prompt_suffix}",
        "negativeprompt": NEGATIVE,
        "width": 800,
        "height": 800,
        "steps": 28,
        "cfgscale": 7.5,
        "sampler": "euler_ancestral",
        "seed": seed,
        "LoRAs": [CHAR_LORA],
        "LoRA Weights": [str(lora_weight)],
        "LoRA Tenc Weights": [str(lora_weight)],
    }
    r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=180)
    if r.status_code == 200:
        data = r.json()
        if "images" in data:
            return data["images"][0]
    raise Exception(f"Gen failed: {r.status_code} {r.text[:200]}")


def download(sid, img_path, save_path):
    url = f"{HOST}/{img_path}"
    r = requests.get(url, timeout=30)
    with open(save_path, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    single_seed = None
    for a in sys.argv[1:]:
        if a == "--submit":
            continue
        if a == "--seed":
            idx = sys.argv.index(a)
            if idx + 1 < len(sys.argv):
                single_seed = int(sys.argv[idx + 1])

    os.makedirs(OUT_DIR, exist_ok=True)

    if not do_submit:
        print(f"Plan: {len(POSES)} poses × 800×800, base={BASE_MODEL}, lora={CHAR_LORA}")
        print(f"Output: {OUT_DIR}/")
        for i, p in enumerate(POSES):
            print(f"  [{i}] {p[:60]}...")
        print("\nRun with --submit to generate.")
        sys.exit(0)

    sid = get_session()
    print(f"Session: {sid[:16]}...")

    if single_seed is not None:
        # Single test image
        path = generate(sid, POSES[0], single_seed)
        save = os.path.join(OUT_DIR, f"test_seed{single_seed}.png")
        download(sid, path, save)
        print(f"Saved: {save}")
    else:
        # Full set
        for i, pose in enumerate(POSES):
            seed = 1000 + i * 7
            print(f"[{i+1}/{len(POSES)}] Generating pose {i} (seed {seed})...")
            try:
                path = generate(sid, pose, seed)
                save = os.path.join(OUT_DIR, f"katharina_{i:02d}_pose.png")
                size = download(sid, path, save)
                print(f"  ✓ {save} ({size//1024} KB)")
            except Exception as e:
                print(f"  ✗ {e}")
            time.sleep(1)
        print(f"\n✅ Set complete: {OUT_DIR}")
