#!/usr/bin/env python3
"""
katharina_characterset_v4 — Single character guaranteed + keine Leggings

Fix für v3-Probleme (User-Feedback 2026-07-13):
  1. Größenunterschiede zwischen Charakteren → gleicher seed + size_variation neg
  2. Leggings in einem Bild → massive Neg + Söckchen/Strümpfe explizit im Prompt
  3. Hintergrund-Symbole → background pattern/asset/symbol neg
  4. Mehrere Charaktere pro Bild → CharTurn-Weight 0.3 → 0.2 + multi-character neg

Setup-Änderungen ggü. v3:
  - CharTurn-Weight: 0.3 → 0.2
  - Söckchen/Strümpfe im POSITIVE prompt
  - Negativ-Liste erweitert um Größen-Drift, Multi-Char, Background-Assets
  - Seed-Determinismus: gleicher seed 100 für ALLE Views (statt 100+i*13)
  - Steps-Variation pro View (sonst Cache-Hit)
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
CHARTURN_LORA_WEIGHT = 0.2  # war 0.3 in v3, 0.7 in v2
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v4"
TEMP_OUT = "/root/little-buddy-card/assets/temp"

# Positive prompt: Söckchen + Strümpfe EXPLIZIT, jedes Kleidungsstück gepinnt
INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii small girl, "
    "blonde hair in two long braids, "
    "(bright crimson red simple knee-length dress:1.5), no patterns, no prints, plain solid red color, "
    "white peter pan collar, short puffy sleeves, "
    "white knee-high socks covering full legs, white socks on legs, fully covered legs, "
    "black mary jane shoes, "
    "no leggings, no tights, no stockings, no pants, no trousers, no jeans, no bare legs, no naked legs, "
    "big round innocent eyes, small button nose, plump cheeks, sweet innocent smile, "
    "childlike proportions, large round head, small body, tiny limbs, "
    "white background, no scenery, no background elements, no background objects, no background symbols, "
    "empty white background, isolated character only, "
    "masterpiece, best quality, highly detailed, sharp focus, 8bit pixel art style"
)

# Massive Negativ-Liste — alle 4 Probleme abdecken
NEGATIVE = (
    # === Outfit-Konflikte (Problem #2: Leggings) ===
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "shorts, capri pants, yoga pants, sweatpants, "
    "bare legs, naked legs, exposed legs, leg visible, "
    # === Pattern/Print auf Kleid ===
    "polka dot, striped, plaid, floral print, checkered, dotted, patterned dress, "
    "two-tone dress, multicolored dress, gradient dress, "
    # === Falsche Kleidfarben ===
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, orange dress, grey dress, "
    # === Falsche Schuhfarben ===
    "white shoes, red shoes, blue shoes, pink shoes, "
    # === Falsche Haarvarianten ===
    "no braids, loose hair, hair down, hair open, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, multicolored hair, "
    # === Hintergrund-Probleme (Problem #3: Hintergrund-Symbole) ===
    "background pattern, background object, background symbol, background asset, "
    "background prop, scenery element, scenery, landscape, decoration, decorative, "
    "faint pattern, suggested pattern, watermark-like pattern, "
    "star pattern, circle pattern, dot pattern, geometric pattern, "
    "any object in background, any element in background, any prop, "
    # === Multi-Charakter + Größen-Drift (Probleme #1 + #4) ===
    "two characters, multiple characters, second character, additional character, "
    "other character, background character, scaled character, resized character, "
    "size difference, size variation, different size, different scale, different height, "
    "smaller character, larger character, tiny character, giant character, "
    "perspective difference, distance difference, far away, closer, "
    "doppelganger, twin, duplicate, copy, mirror image, "
    # === Style-Drift ===
    "realistic, photo, 3d render, photorealistic, painterly, gradient, complex, blurry, lowres, "
    "soft shading, anti-aliased, semi-realistic, anime style, manga style, "
    "smooth skin, detailed face, hyper detailed, "
    # === Folklore/Tracht ===
    "folklore, folk, traditional, bavarian, dirndl, tracht, costume, "
    "wreath, flower crown, embroidered, "
    # === NSFW ===
    "nsfw, nude, naked, exposed, undressed, topless, cleavage, lingerie, underwear, "
    "suggestive, sensual, erotic, seductive, mature, adult, "
    "developed body, curvy, voluptuous, large breasts, "
    "18, 20, 25, old, beautiful woman, attractive, hot, "
    "back turned, from behind, rear view, bent over, looking over shoulder, "
    # === Quality ===
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "bad quality, worst quality, jpeg artifacts, "
    "multiple girls, fighting, action pose, dynamic, "
    # === Accessoires ===
    "apron, schürze, handtasche, bag, purse, religious, cross, crucifix, kruzifix, "
    "wings, halo, tail, animal ears, cat ears, bunny ears, fantasy, "
    "hat, headband, bow tie, hair bow, hair accessory, headband, cap, hood, "
    "scarf, gloves, belt, backpack, satchel, watch, glasses, sunglasses, "
    "jewelry, necklace, earrings, bracelet, ring, makeup, lipstick, eyeliner"
)

# 6 View-Slots — CharTurn-Trigger + view-spezifische Posen
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
    """Build ComfyUI pass-through workflow. Seed NICHT variieren — Katharina-Größe konsistent."""
    wf = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL}
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": PIXEL_LORA,
                "strength_model": PIXEL_LORA_WEIGHT,
                "strength_clip": PIXEL_LORA_WEIGHT,
            }
        },
        "3": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["2", 0],
                "clip": ["2", 1],
                "lora_name": CHARTURN_LORA,
                "strength_model": CHARTURN_LORA_WEIGHT,
                "strength_clip": CHARTURN_LORA_WEIGHT,
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": f"{INSTANCE_PROMPT}, {pose_desc}", "clip": ["3", 1]}
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["3", 1]}
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["3", 0],
                "seed": seed,
                "steps": 28,
                "cfg": 7.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "denoise": 1.0,
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["7", 0], "vae": ["1", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": f"katharina_v4_{view_name}"}
        }
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
                    print(f"  [cache] Prompt completed but no outputs (cached or empty)")
                    return None
        time.sleep(3)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout}s")


def find_output_image(history_entry, prefix):
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                fname = img.get("filename", "")
                if prefix in fname or "katharina_v4" in fname:
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
    fixed_seed = 100  # Konsistenz: gleicher Seed für alle Views

    print(f"=== katharina_characterset_v4 (Single char + Outfit-Pin) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Pixel-LoRA: {PIXEL_LORA} (weight {PIXEL_LORA_WEIGHT})")
    print(f"CharTurn-LoRA: {CHARTURN_LORA} (weight {CHARTURN_LORA_WEIGHT}, war 0.3 in v3)")
    print(f"Resolution: 1024x1024")
    print(f"Seed: {fixed_seed} (KONSISTENT für alle Views — Katharina bleibt gleich groß)")
    print(f"Outfit-Anker: knee-high socks covering full legs, no bare legs")
    print(f"Negativ: size_difference, two characters, background pattern/asset/symbol")
    print()

    if not do_submit:
        print("Run with --submit to generate all 6 views.")
        print("Run with --submit --one to generate just view 1 (smoke test).")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    views_to_run = VIEWS[:1] if only_one else VIEWS

    for i, (view_name, pose_desc) in enumerate(views_to_run):
        # Seed bleibt konstant (Katharina-Größe soll gleich bleiben)
        # Cache-Bypass via steps/cfg/denoise variation
        print(f"\n[{i+1}/{len(views_to_run)}] {view_name} (seed {fixed_seed})")
        print(f"  Pose: {pose_desc[:100]}")

        wf = build_comfy_workflow(fixed_seed, pose_desc, view_name, i)
        wf["7"]["inputs"]["steps"] = 28 + i * 2
        wf["7"]["inputs"]["cfg"] = round(7.5 + i * 0.1, 2)
        wf["7"]["inputs"]["denoise"] = round(1.0 - i * 0.005, 4)
        print(f"  Steps: {wf['7']['inputs']['steps']}, Cfg: {wf['7']['inputs']['cfg']}, Denoise: {wf['7']['inputs']['denoise']}")

        try:
            prompt_id = submit_workflow(wf)
            print(f"  Prompt ID: {prompt_id}")

            history = wait_for_prompt(prompt_id, timeout=600)
            if history is None:
                print(f"  ✗ Cache-Hit, retry mit seed+100")
                wf["7"]["inputs"]["seed"] = fixed_seed + 100
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
