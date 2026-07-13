#!/usr/bin/env python3
"""
katharina_variations_loop_v1 — 8 Variationen vom Master-Prompt

Stop-the-line Pattern: User bewertet, KEINE Auto-Auswahl.
Zweck: Beste 2-3 Bilder finden für Character-LoRA-Training.

Setup:
  - Base: autismmixSDXL_autismmixPony_258042.safetensors (Illustrious-Mix, cute)
  - Pixel-LoRA: concept\\Pixel_Art_XL_-_v1-1.safetensors (0.85)
  - KEIN CharTurn-LoRA
  - 8 Variationen, seeds 100-107
  - Resolution 1024×1024, steps 35, cfg 7.0

Katharina-Specs (konsolidiert aus User-Feedback v1-v6):
  - Rotes knielanges Kleid (KEIN Weiß, KEIN Pattern)
  - Weiße Zöpfe (blonde) mit Zöpfen
  - Weißer Peter-Pan-Kragen
  - Puffärmel
  - Weiße Kniestrümpfe (Beine komplett bedeckt)
  - Schwarze Mary-Janes
  - Chibi-Proportionen (kurze Beine, großer Kopf)
  - Kindlich, süß, KEIN sexy, KEIN Folklore
"""

import os
import sys
import json
import time
import urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"

BASE_MODEL = "autismmixSDXL_autismmixPony_258042.safetensors"
PIXEL_LORA = "concept\\Pixel_Art_XL_-_v1-1.safetensors"
PIXEL_LORA_WEIGHT = 0.85
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/variations_v1"

# Master-Prompt — konsolidiert, EINHEITLICH für alle 8 Variationen
# WICHTIG: KEINE "turnaround"/"multiple views" Trigger (lösten Multi-Char aus)
INSTANCE_PROMPT = (
    "pixel art, katharina character, "
    "kawaii cute adorable innocent sweet wholesome childlike small girl, "
    "blonde hair in two long braids, "
    "(solid bright crimson red simple knee-length dress:1.5), monochrome red, "
    "no white parts, no white accents, no white sections, "
    "fully red dress, completely red outfit, "
    "small white peter pan collar, "
    "short puffy sleeves, "
    "white knee-high socks covering full legs, "
    "black mary jane shoes, "
    "no leggings, no tights, no stockings, no pants, no jeans, no bare legs, no naked legs, "
    "chibi body proportions, baby proportions, stubby legs, short legs, tiny legs, "
    "large round head, small body, oversized head, "
    "big round innocent eyes, small button nose, plump cheeks, sweet innocent smile, "
    "no makeup, no lipstick, no jewelry, no adult features, no mature, no sensual, no seductive, "
    "white background, no scenery, no background elements, no background objects, "
    "empty white background, isolated character only, "
    "masterpiece, best quality, highly detailed, sharp focus, 8bit pixel art style"
)

NEGATIVE = (
    "two characters, multiple characters, second character, additional character, "
    "other character, background character, scaled character, resized character, "
    "size difference, size variation, different size, different scale, different height, "
    "white dress, ivory dress, cream dress, off-white dress, light dress, "
    "dress with white parts, dress with white accents, white trim, "
    "two-tone dress, multicolored dress, gradient dress, "
    "pink dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, orange dress, grey dress, beige dress, "
    "polka dot dress, striped dress, plaid dress, floral print dress, checkered dress, "
    "sexy, sensual, seductive, alluring, flirtatious, suggestive, erotic, mature, adult, "
    "developed body, curvy, voluptuous, large breasts, cleavage, "
    "18, 20, 25, old, beautiful woman, attractive, hot, pinup, "
    "makeup, lipstick, eyeliner, mascara, high heels, jewelry, necklace, earrings, "
    "long legs, slender legs, tall body, long body, model proportions, "
    "bare legs, naked legs, exposed legs, leg visible, thigh visible, "
    "back turned, from behind, rear view, bent over, looking over shoulder, "
    "nsfw, nude, naked, exposed, undressed, topless, lingerie, underwear, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "shorts, capri pants, yoga pants, sweatpants, "
    "no braids, loose hair, hair down, hair open, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, "
    "background pattern, background object, background symbol, background asset, "
    "background prop, scenery element, scenery, landscape, decoration, decorative, "
    "faint pattern, suggested pattern, watermark-like pattern, "
    "realistic, photo, 3d render, photorealistic, painterly, gradient, complex, blurry, lowres, "
    "soft shading, anti-aliased, semi-realistic, anime style, manga style, "
    "smooth skin, detailed face, hyper detailed, "
    "folklore, folk, traditional, bavarian, dirndl, tracht, costume, "
    "wreath, flower crown, embroidered, "
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "bad quality, worst quality, jpeg artifacts, "
    "multiple girls, fighting, action pose, dynamic, "
    "apron, schürze, handtasche, bag, purse, religious, cross, crucifix, kruzifix, "
    "wings, halo, tail, animal ears, cat ears, bunny ears, fantasy, "
    "hat, headband, bow tie, hair bow, hair accessory, headband, cap, hood, "
    "scarf, gloves, belt, backpack, satchel, watch, glasses, sunglasses, "
    "bracelet, ring"
)


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_comfy_workflow(seed):
    """8 Variationen — gleicher Prompt, verschiedene seeds."""
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": BASE_MODEL}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "model": ["1", 0], "clip": ["1", 1],
            "lora_name": PIXEL_LORA, "strength_model": PIXEL_LORA_WEIGHT, "strength_clip": PIXEL_LORA_WEIGHT}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": INSTANCE_PROMPT, "clip": ["2", 1]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["2", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["2", 0], "seed": seed, "steps": 35, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "normal",
            "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["5", 0], "denoise": 1.0}},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": f"katharina_var_v1"}}
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


def find_output_image(history_entry, seed):
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        if "images" in node_out:
            for img in node_out["images"]:
                fname = img.get("filename", "")
                if "katharina_var_v1" in fname:
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
    n_variations = 8
    seeds = list(range(100, 100 + n_variations))  # 100, 101, ..., 107

    print(f"=== katharina_variations_loop_v1 (8 Seeds, gleicher Prompt) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Pixel-LoRA: {PIXEL_LORA} (weight {PIXEL_LORA_WEIGHT})")
    print(f"KEIN CharTurn-LoRA")
    print(f"Seeds: {seeds}")
    print(f"Resolution: 1024×1024, Steps: 35, Cfg: 7.0 (alle gleich)")
    print(f"Output: {OUT_DIR}/")
    print()
    print("Katharina-Specs (Master):")
    print("  - Rotes knielanges Kleid (monochrome, kein Weiß, kein Pattern)")
    print("  - Blonde Zöpfe, weißer Peter-Pan-Kragen, Puffärmel")
    print("  - Weiße Kniestrümpfe, schwarze Mary-Janes")
    print("  - Chibi-Proportionen, süß, kindlich")
    print("  - Kein Folklore/Tracht, kein NSFW, kein Sexy")
    print()

    if not do_submit:
        print("Run with --submit to generate 8 variations.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    for i, seed in enumerate(seeds):
        print(f"\n[{i+1}/{n_variations}] seed {seed}")
        wf = build_comfy_workflow(seed)

        try:
            prompt_id = submit_workflow(wf)
            history = wait_for_prompt(prompt_id, timeout=600)
            if history is None:
                print(f"  ✗ Cache-Hit, retry mit seed+10000")
                wf["6"]["inputs"]["seed"] = seed + 10000
                prompt_id = submit_workflow(wf)
                history = wait_for_prompt(prompt_id, timeout=600)
                if history is None:
                    print(f"  ✗ Auch Retry gecacht — skip")
                    continue
            img_info = find_output_image(history, seed)
            if not img_info:
                print(f"  ✗ No image in output")
                continue
            save = f"{OUT_DIR}/var_{i+1:02d}_seed{seed}.png"
            size = download_output(img_info, save)
            print(f"  ✓ {save} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print(f"\n=== FERTIG — 8 Variationen bereit zur Abnahme ===")
    print(f"Output: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        p = os.path.join(OUT_DIR, f)
        print(f"  {f}: {os.path.getsize(p)//1024} KB")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Welche 2-3 Variationen sehen am meisten nach Katharina aus?")
    print("  Sag die Nummern (var_01, var_02, ...) — die werden Trainings-Set fürs LoRA.")
