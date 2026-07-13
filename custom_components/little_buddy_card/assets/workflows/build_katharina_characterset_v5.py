#!/usr/bin/env python3
"""
katharina_characterset_v5 — Rotes Kleid + Süss + Chibi-Beine

Fix für v4-Probleme (User-Feedback 2026-07-13):
  1. Kleid ist meist weiß (58-64% weiß, 11-16% rot) → radical color pin
  2. Sie wirkt sexy, nicht süß → mehr chibi-Anker, anti-realism stärker
  3. Beine zu lang → chibi body ratio lock (kurze Beine, großer Kopf)

Setup-Änderungen ggü. v4:
  - Kleid-Pin: (red dress:1.5) → (solid bright crimson red dress:1.8)
  - "monochrome red, no white parts, no white accents, no white sections, fully red"
  - Chibi-Body-Lock: "stubby legs, short legs, large round head, baby proportions"
  - Süss-Anker: "kawaii, cute, adorable, childlike, innocent, sweet, wholesome"
  - Anti-sexy: "no makeup, no lipstick, no jewelry, no adult features, no mature"
  - Steps: 28 (KONSISTENT — fixed for all views since seed is already fixed)
  - CharTurn-Weight: 0.2 → 0.15 (noch weniger Style-Eingriff)
"""

import os
import sys
import json
import time
import urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
PIXEL_LORA = "concept\\Pixel_Art_XL_-_v1-1.safetensors"
PIXEL_LORA_WEIGHT = 0.85
CHARTURN_LORA = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
CHARTURN_LORA_WEIGHT = 0.15  # war 0.2 in v4
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v5"
TEMP_OUT = "/root/little-buddy-card/assets/temp"

# Massive Kleid-Pinning + Chibi-Body-Lock + Süss-Anker
INSTANCE_PROMPT = (
    "pixel art, katharina character, "
    "kawaii cute adorable innocent sweet wholesome childlike small girl, "
    "blonde hair in two long braids, "
    "(solid bright crimson red simple knee-length dress:1.8), monochrome red, "
    "no white parts, no white accents, no white sections, no white trim, no white collar, "
    "fully red dress, completely red outfit, "
    "small white peter pan collar, "
    "short puffy sleeves, "
    "white knee-high socks covering full legs, white socks on legs, fully covered legs, "
    "black mary jane shoes, "
    "no leggings, no tights, no stockings, no pants, no trousers, no jeans, no bare legs, no naked legs, "
    "chibi body proportions, baby proportions, stubby legs, short legs, tiny legs, "
    "large round head, small body, oversized head, "
    "big round innocent eyes, small button nose, plump cheeks, sweet innocent smile, "
    "no makeup, no lipstick, no jewelry, no adult features, no mature, no sensual, no seductive, "
    "white background, no scenery, no background elements, no background objects, no background symbols, "
    "empty white background, isolated character only, "
    "masterpiece, best quality, highly detailed, sharp focus, 8bit pixel art style"
)

# Massive Negativ-Liste
NEGATIVE = (
    # === Kleid-Farbe (Problem #1: weiß statt rot) ===
    "white dress, ivory dress, cream dress, off-white dress, light dress, "
    "dress with white parts, dress with white accents, white trim, white collar on dress, "
    "two-tone dress, multicolored dress, gradient dress, "
    "pink dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, orange dress, grey dress, beige dress, "
    "polka dot dress, striped dress, plaid dress, floral print dress, checkered dress, "
    # === Sexy-Bias (Problem #2) ===
    "sexy, sensual, seductive, alluring, flirtatious, suggestive, erotic, mature, adult, "
    "developed body, curvy, voluptuous, large breasts, cleavage, "
    "18, 20, 25, old, beautiful woman, attractive, hot, pinup, "
    "makeup, lipstick, eyeliner, mascara, high heels, jewelry, necklace, earrings, "
    "long legs, slender legs, tall body, long body, model proportions, "
    "bare legs, naked legs, exposed legs, leg visible, thigh visible, "
    "back turned, from behind, rear view, bent over, looking over shoulder, "
    "nsfw, nude, naked, exposed, undressed, topless, lingerie, underwear, "
    # === Beine-Länge (Problem #3) ===
    "long legs, tall character, adult proportions, realistic proportions, "
    "slim legs, thin legs, slender, model height, "
    # === Outfit-Konflikte ===
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "shorts, capri pants, yoga pants, sweatpants, "
    # === Falsche Haarvarianten ===
    "no braids, loose hair, hair down, hair open, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, multicolored hair, "
    # === Hintergrund-Probleme ===
    "background pattern, background object, background symbol, background asset, "
    "background prop, scenery element, scenery, landscape, decoration, decorative, "
    "faint pattern, suggested pattern, watermark-like pattern, "
    "any object in background, any element in background, any prop, "
    # === Multi-Charakter + Größen-Drift ===
    "two characters, multiple characters, second character, additional character, "
    "other character, background character, scaled character, resized character, "
    "size difference, size variation, different size, different scale, different height, "
    "doppelganger, twin, duplicate, copy, mirror image, "
    # === Style-Drift ===
    "realistic, photo, 3d render, photorealistic, painterly, gradient, complex, blurry, lowres, "
    "soft shading, anti-aliased, semi-realistic, anime style, manga style, "
    "smooth skin, detailed face, hyper detailed, "
    # === Folklore/Tracht ===
    "folklore, folk, traditional, bavarian, dirndl, tracht, costume, "
    "wreath, flower crown, embroidered, "
    # === Quality ===
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "bad quality, worst quality, jpeg artifacts, "
    "multiple girls, fighting, action pose, dynamic, "
    # === Accessoires ===
    "apron, schürze, handtasche, bag, purse, religious, cross, crucifix, kruzifix, "
    "wings, halo, tail, animal ears, cat ears, bunny ears, fantasy, "
    "hat, headband, bow tie, hair bow, hair accessory, headband, cap, hood, "
    "scarf, gloves, belt, backpack, satchel, watch, glasses, sunglasses, "
    "bracelet, ring"
)

# 6 View-Slots
VIEWS = [
    ("01_front", "front view, looking at viewer, standing straight, both arms at sides, turnaround sheet, multiple views, character reference"),
    ("02_3quarter_left", "three quarter view from the left, slight turn, gentle smile, head slightly tilted, character design sheet, model sheet reference"),
    ("03_side_right", "side view facing right, profile, standing still, calm expression, model sheet reference, turnaround"),
    ("04_back_3quarter", "three quarter view from behind, mostly back, slight head turn to the right, turnaround, multiple views"),
    ("05_low_angle", "slight low angle view, looking up at the character, gentle pose, character reference, turnaround sheet"),
    ("06_top_down", "high angle view, looking down at character, full body, character sheet layout, multiple views"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_comfy_workflow(seed, pose_desc, view_name, view_index):
    """Build ComfyUI pass-through workflow. Seed+Steps konstant für Größen-Konsistenz."""
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": BASE_MODEL}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "model": ["1", 0], "clip": ["1", 1],
            "lora_name": PIXEL_LORA, "strength_model": PIXEL_LORA_WEIGHT, "strength_clip": PIXEL_LORA_WEIGHT}},
        "3": {"class_type": "LoraLoader", "inputs": {
            "model": ["2", 0], "clip": ["2", 1],
            "lora_name": CHARTURN_LORA, "strength_model": CHARTURN_LORA_WEIGHT, "strength_clip": CHARTURN_LORA_WEIGHT}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{INSTANCE_PROMPT}, {pose_desc}", "clip": ["3", 1]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["3", 1]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["3", 0], "seed": seed, "steps": 28, "cfg": 7.5,
            "sampler_name": "euler_ancestral", "scheduler": "normal",
            "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0], "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": f"katharina_v5_{view_name}"}}
    }
    return wf


def submit_workflow(workflow):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code == 200:
        return r.json().get("prompt_id")
    raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")


def wait_for_prompt(prompt_id, timeout=600):
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
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout}s")


def find_output_image(history_entry, prefix):
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                fname = img.get("filename", "")
                if prefix in fname or "katharina_v5" in fname:
                    return img
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            return node_out["images"][0]
    return None


def download_output(image_info, save_to):
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
    fixed_seed = 100

    print(f"=== katharina_characterset_v5 (Rotes Kleid + Chibi) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Pixel-LoRA: {PIXEL_LORA} (weight {PIXEL_LORA_WEIGHT})")
    print(f"CharTurn-LoRA: {CHARTURN_LORA} (weight {CHARTURN_LORA_WEIGHT}, war 0.2 in v4)")
    print(f"Seed: {fixed_seed} (konstant), Steps: 28 (konstant)")
    print(f"Kleid-Pin: (solid bright crimson red dress:1.8), monochrome red, no white parts")
    print(f"Chibi-Lock: stubby legs, short legs, large round head, baby proportions")
    print(f"Süss-Anker: kawaii cute adorable innocent sweet wholesome childlike")
    print(f"Anti-Sexy: no makeup, no lipstick, no jewelry, no adult features")
    print()

    if not do_submit:
        print("Run with --submit to generate all 6 views.")
        print("Run with --submit --one to generate just view 1.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    views_to_run = VIEWS[:1] if only_one else VIEWS

    for i, (view_name, pose_desc) in enumerate(views_to_run):
        # Bei fixed seed/steps müssen wir für Cache-Bypass anders variieren
        # Wir variieren cfg und sampler_name (subtle aber hash-ändernd)
        wf = build_comfy_workflow(fixed_seed, pose_desc, view_name, i)
        # Cache-Bypass: cfg + denoise + seed-mix pro View (steps bleibt konstant)
        wf["7"]["inputs"]["cfg"] = round(7.5 + (i * 0.15), 2)  # 7.5, 7.65, 7.8, 7.95, 8.1, 8.25
        wf["7"]["inputs"]["denoise"] = round(1.0 - (i * 0.01), 4)  # 1.0, 0.99, 0.98, 0.97, 0.96, 0.95
        print(f"\n[{i+1}/{len(views_to_run)}] {view_name} (seed {fixed_seed})")
        print(f"  Cfg: {wf['7']['inputs']['cfg']}, Denoise: {wf['7']['inputs']['denoise']}")

        try:
            prompt_id = submit_workflow(wf)
            history = wait_for_prompt(prompt_id, timeout=600)
            if history is None:
                print(f"  ✗ Cache-Hit, retry mit seed+500")
                wf["7"]["inputs"]["seed"] = fixed_seed + 500
                prompt_id = submit_workflow(wf)
                history = wait_for_prompt(prompt_id, timeout=600)
                if history is None:
                    print(f"  ✗ Auch Retry gecacht — skip")
                    continue
            img_info = find_output_image(history, view_name)
            if not img_info:
                print(f"  ✗ No image in output")
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
