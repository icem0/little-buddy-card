#!/usr/bin/env python3
"""
katharina_dataset_v3 — CharTurn-LoRA via ComfyUI pass-through

Quirk #6 Fix: SwarmUI's WebAPI kennt CharTurn-LoRA nicht.
Wir nutzen /ComfyBackendDirect/prompt mit LoraLoader-Node.

Pipeline:
  CheckpointLoaderSimple → LoraLoader (CharTurn 0.7) → CLIPTextEncode →
  EmptyLatentImage → KSampler → VAEDecode → SaveImage

12 verschiedene Winkel via CharTurn-Trigger-Wörter
"""

import os, sys, time, urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
CHARTURN_LORA = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
CHARTURN_WEIGHT = 0.7

DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"

PROMPT_BASE = (
    "score_9, score_8_up, score_7_up, score_6_up, source_anime, "
    "masterpiece, best quality, amazing quality, "
    "pixel art, cute childlike small girl, "
    "(blonde_braids:1.3), "
    "(bright crimson red dress:1.4), (long_dress:1.2), white peter pan collar, "
    "short puffy sleeves, white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "(chibi proportions:1.1), large round head, tiny limbs, "
    "(neutral gray soft shadow under feet:1.2), "
    "pure white background, no scenery, isolated character, "
    "turnaround sheet, character design sheet, multiple views, model sheet reference"
)

NEG = (
    "score_1, score_2, score_3, source_pony, source_furry, source_hentai, "
    "grass, ground, outdoor, ground line, floor, dirt, soil, sand, gravel, "
    "landscape, scenery, environment, platform, pedestal, square, stage, "
    "horizon, sky, trees, plants, flowers, bushes, "
    "green shadow, green tint, blue shadow, colored shadow, tinted shadow, "
    "shorts, mini skirt, crop top, short dress, mini dress, "
    "white dress, blue dress, green dress, yellow dress, black dress, purple dress, pink dress, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "multiple girls, second character, additional character, additional figure, "
    "scaled character, resized character, size difference, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "no braids, loose hair, hair down, ponytail, bun, "
    "black hair, brown hair, "
    "three legs, extra leg, extra limb, deformed legs, fused legs, bad anatomy, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, "
    "blurry, deformed, noise, watermark, text, signature, "
    "3d, realistic, photo, "
    "fighting, leaping, jumping, raised arms, dynamic pose, "
    "back turned, from behind, rear view, "
    "wings, halo, tail, animal ears, fantasy, "
    "necklace, earrings, makeup, lipstick, high heels"
)

FRAMES = [
    ("02_front",       "single character facing forward, front view, looking at viewer"),
    ("03_3quarter_r",  "single character in 3/4 view from the right, head turned right"),
    ("04_3quarter_l",  "single character in 3/4 view from the left, head turned left"),
    ("05_side_r",      "single character in side view from the right, profile"),
    ("06_side_l",      "single character in side view from the left, profile"),
    ("07_back_3q",     "single character in 3/4 view from behind, slight head turn"),
    ("08_back",        "single character back view, facing away, back of braids visible"),
    ("09_top_down",    "single character from above, high angle, top-down view"),
    ("10_low_angle",   "single character from below, low angle, looking up"),
    ("11_4q_dynamic",  "single character, dynamic 3/4 pose with slight movement"),
    ("12_leaning",     "single character in 3/4 view, slight body lean to the right"),
    ("13_full_body",   "single character, full body turnaround, all proportions visible"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_workflow(seed, prompt, neg):
    """ComfyUI pass-through Workflow mit LoraLoader für CharTurn."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL}
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": CHARTURN_LORA,
                "strength_model": CHARTURN_WEIGHT,
                "strength_clip": CHARTURN_WEIGHT,
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 1]}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": neg, "clip": ["2", 1]}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "seed": seed,
                "steps": 28,
                "cfg": 7.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "denoise": 1.0,
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]}
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": "katharina_v3"}
        }
    }


def submit_and_wait(workflow, timeout=300):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")
    prompt_id = r.json().get("prompt_id")

    # Wait
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if prompt_id in data:
                entry = data[prompt_id]
                status = entry.get("status", {})
                if status.get("completed"):
                    if "outputs" in entry and entry["outputs"]:
                        return entry
                    return None
        time.sleep(3)
    raise TimeoutError(f"Prompt {prompt_id} timeout")


def find_output(history, prefix):
    outputs = history.get("outputs", {})
    for nid, out in outputs.items():
        if "images" in out:
            for img in out["images"]:
                fname = img.get("filename", "")
                if "katharina_v3" in fname or prefix in fname:
                    return img
    for nid, out in outputs.items():
        if "images" in out:
            return out["images"][0]
    return None


def download(img_info, save_to):
    fname = img_info["filename"]
    subfolder = img_info.get("subfolder", "")
    img_type = img_info.get("type", "output")
    params = urllib.parse.urlencode({"filename": fname, "subfolder": subfolder, "type": img_type})
    url = f"{HOST}/ComfyBackendDirect/view?{params}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_dataset_v3 (CharTurn-LoRA via ComfyUI pass-through) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"LoRA: {CHARTURN_LORA} (weight {CHARTURN_WEIGHT})")
    print(f"Resolution: 1024x1024, Steps 28, Cfg 7.5")
    print(f"12 verschiedene Winkel via CharTurn-Trigger")
    print()

    if not do_submit:
        print("Run with --submit to generate.")
        sys.exit(0)

    os.makedirs(DATASET_DIR, exist_ok=True)

    for i, (idx_name, frame_suffix) in enumerate(FRAMES):
        seed = 100 + i * 7
        out_png = f"{DATASET_DIR}/{idx_name}.png"
        out_txt = f"{DATASET_DIR}/{idx_name}.txt"
        full_prompt = PROMPT_BASE + ", " + frame_suffix
        print(f"\n[{i+1}/{len(FRAMES)}] {idx_name} (seed {seed})")
        print(f"  View: {frame_suffix[:80]}")

        try:
            wf = build_workflow(seed, full_prompt, NEG)
            # Cache-Bypass (Quirk #15): seed minimal variieren falls cache-hit
            history = submit_and_wait(wf)
            if history is None:
                print(f"  ✗ Cache-Hit, retry mit seed+1000")
                wf["6"]["inputs"]["seed"] = seed + 1000
                history = submit_and_wait(wf)
                if history is None:
                    print(f"  ✗ Auch Retry gecacht")
                    continue
            img_info = find_output(history, idx_name)
            if not img_info:
                print(f"  ✗ No image in output")
                continue
            size = download(img_info, out_png)
            print(f"  ✓ {out_png} ({size//1024} KB)")
            with open(out_txt, "w") as f:
                f.write(full_prompt + "\n")
            print(f"  ✓ {out_txt}")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print()
    print(f"=== FERTIG ===")
    n_pngs = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".png")])
    n_txts = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".txt")])
    print(f"  Bilder:  {n_pngs}")
    print(f"  Captions: {n_txts}")
