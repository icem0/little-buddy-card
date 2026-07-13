#!/usr/bin/env python3
"""
katharina_characterset_v2 — Multi-View via Pony CharTurn LoRA

ComfyUI pass-through workflow. Nutzt das neue Pony CharTurn LoRA für echte
Multi-View/Turnaround-Generierung (Workaround: SwarmUI LoRA-Index kennt das
LoRA nicht, ComfyUI LoraLoader schon).

Setup:
  - Base: RDXL_Pixel_Art_-_Pony_2.safetensors (Pony-SDXL pixel art)
  - LoRA: Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors
  - Weight 0.7 (Author-Empfehlung: Main 0.7, Secondary 0.15)
  - Resolution: 1536x1024 (Author-Empfehlung für CharTurn Layout)
  - KSampler: euler_ancestral, steps 28, cfg 7.5, seed 100
  - Master: katharina_master.png (rote Kleid, blonde Zöpfe, kindlich)

Output: 1 Bild (Contact-Sheet) mit 6 Katharina-Views + 1 Detail-Ansicht
"""

import os
import sys
import json
import time
import shutil
import urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
SID = None  # Refresh per call

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
LORA_NAME = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
LORA_WEIGHT = 0.7
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v2"
TEMP_OUT = "/root/little-buddy-card/assets/temp"

# Katharina's definitive Feature-Spec (single source of truth)
INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii small girl, "
    "blonde hair in two long braids, "
    "(bright crimson red simple dress:1.4), white collar, puffy short sleeves, "
    "white socks, black mary jane shoes, "
    "big round innocent eyes, small button nose, plump cheeks, sweet innocent smile, "
    "childlike proportions, large round head, small body, tiny limbs, "
    "white background, no scenery, simple plain background, isolated character, "
    "masterpiece, best quality, highly detailed, sharp focus"
)

NEGATIVE = (
    "nsfw, nude, naked, exposed, undressed, topless, cleavage, lingerie, underwear, "
    "suggestive, sensual, erotic, seductive, mature, adult, "
    "developed body, curvy, voluptuous, large breasts, "
    "18, 20, 25, old, beautiful woman, attractive, hot, "
    "folklore, folk, traditional, bavarian, dirndl, tracht, costume, "
    "wreath, flower crown, embroidered, dirndl, "
    "apron, schürze, handtasche, bag, purse, religious, cross, crucifix, kruzifix, "
    "wings, halo, tail, animal ears, cat ears, bunny ears, fantasy, "
    "no braids, loose hair, hair down, hair open, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, multicolored hair, "
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, two-tone dress, striped dress, patterned dress, "
    "muted, blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "realistic, photo, 3d, multiple girls, fighting, action pose, dynamic, "
    "busy background, scenery, landscape, gradient background, dark background, "
    "colored background, off-white background, gray background, "
    "back turned, from behind, rear view, bent over, looking over shoulder"
)

# 6 View-Slots — MIT CharTurn-Trigger ("turnaround", "character sheet", "multiple views")
# Author: "use at least 2 Turn LoRA, the main one weight around 0.7, and the secondary one weight around 0.15"
# Wir haben nur die Haupt-LoRA, also CharTurn via Trigger-Wörter erzwingen
VIEWS = [
    ("01_front", "front view, looking at viewer, standing straight, both arms at sides, turnaround sheet, multiple views"),
    ("02_3quarter_left", "three quarter view from the left, slight turn, gentle smile, head slightly tilted, character design sheet"),
    ("03_side_right", "side view facing right, profile, standing still, calm expression, model sheet reference"),
    ("04_back_3quarter", "three quarter view from behind, mostly back, slight head turn to the right, turnaround"),
    ("05_low_angle", "slight low angle view, looking up at the character, gentle pose, character reference"),
    ("06_top_down", "high angle view, looking down at character, full body, character sheet layout"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_comfy_workflow(seed, pose_desc, view_name):
    """Build a ComfyUI pass-through workflow JSON for 1 view."""
    wf = {
        # 1: Load Checkpoint
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL}
        },
        # 2: LoRA Loader
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": LORA_NAME,
                "strength_model": LORA_WEIGHT,
                "strength_clip": LORA_WEIGHT,
            }
        },
        # 3: Positive prompt
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": f"{INSTANCE_PROMPT}, {pose_desc}", "clip": ["2", 1]}
        },
        # 4: Negative prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["2", 1]}
        },
        # 5: Empty latent (1536x1024 — Author-Empfehlung für CharTurn)
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1536, "height": 1024, "batch_size": 1}
        },
        # 6: KSampler
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
        # 7: VAE Decode
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]}
        },
        # 8: Save Image
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": f"katharina_v2_{view_name}"}
        }
    }
    return wf


def submit_workflow(workflow):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code == 200:
        data = r.json()
        return data.get("prompt_id")
    raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")


def wait_for_prompt(prompt_id, timeout=600):
    """Wait for prompt completion. Returns history entry with outputs.

    Edge case: if ComfyUI marks the job 'cached' (all nodes had identical inputs
    to a previous run), it executes in <100ms but produces no new outputs.
    In that case we return None so the caller can detect & re-submit.
    """
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
                    # Cached / no outputs
                    print(f"  [cache] Prompt completed but no outputs (cached or empty)")
                    return None
        time.sleep(3)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout}s")


def find_output_image(history_entry, prefix):
    """Find the output image filename in the history entry."""
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                fname = img.get("filename", "")
                if prefix in fname or "katharina_v2" in fname:
                    return img
    # Fallback: any image
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            return node_out["images"][0]
    return None


def download_output(image_info, save_to):
    """Download a generated image from ComfyUI."""
    fname = image_info["filename"]
    subfolder = image_info.get("subfolder", "")
    img_type = image_info.get("type", "output")
    params = urllib.parse.urlencode({"filename": fname, "subfolder": subfolder, "type": img_type})
    url = f"{HOST}/ComfyBackendDirect/view?{params}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    only_one = "--one" in sys.argv

    print(f"=== katharina_characterset_v2 (Pony CharTurn LoRA) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"LoRA: {LORA_NAME}")
    print(f"LoRA weight: {LORA_WEIGHT}")
    print(f"Resolution: 1536x1024 (Author-Empfehlung)")
    print(f"")

    if not do_submit:
        print("Run with --submit to generate all 6 views.")
        print("Run with --submit --one to generate just view 1 (faster smoke test).")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    views_to_run = VIEWS[:1] if only_one else VIEWS

    for i, (view_name, pose_desc) in enumerate(views_to_run):
        seed = 100 + i * 7
        print(f"\n[{i+1}/{len(views_to_run)}] {view_name} (seed {seed})")
        print(f"  Pose: {pose_desc[:100]}")

        wf = build_comfy_workflow(seed, pose_desc, view_name)
        # Cache-Bypass: minimal andere steps/cfg pro View (ComfyUI-Quirk #4)
        wf["6"]["inputs"]["steps"] = 28 + i  # 28, 29, 30, 31, 32, 33
        wf["6"]["inputs"]["cfg"] = round(7.5 + (i * 0.05), 2)  # 7.5, 7.55, 7.6, ...
        wf["6"]["inputs"]["denoise"] = round(1.0 - (i * 0.001), 4)  # 0.999, 0.998, ...
        print(f"  Steps: {wf['6']['inputs']['steps']}, Cfg: {wf['6']['inputs']['cfg']}, Denoise: {wf['6']['inputs']['denoise']}")

        try:
            prompt_id = submit_workflow(wf)
            print(f"  Prompt ID: {prompt_id}")

            history = wait_for_prompt(prompt_id, timeout=600)
            if history is None:
                print(f"  ✗ Cached run with no outputs — Cache-Bypass hat nicht gegriffen, retry mit seed+1000")
                wf["6"]["inputs"]["seed"] = seed + 1000
                prompt_id = submit_workflow(wf)
                history = wait_for_prompt(prompt_id, timeout=600)
                if history is None:
                    print(f"  ✗ Auch Retry gecacht — skip")
                    continue
            img_info = find_output_image(history, view_name)

            if not img_info:
                print(f"  ✗ No image in output")
                print(f"  History keys: {list(history.get('outputs', {}).keys())}")
                continue

            save = f"{OUT_DIR}/{view_name}.png"
            size = download_output(img_info, save)
            print(f"  ✓ {save} ({size//1024} KB)")

        except Exception as e:
            print(f"  ✗ {e}")

        time.sleep(2)

    print(f"\n=== FERTIG ===")
    print(f"Output: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        p = os.path.join(OUT_DIR, f)
        print(f"  {f}: {os.path.getsize(p)//1024} KB")
