#!/usr/bin/env python3
"""
katharina_characterset_v6 — Base-Wechsel: autismmixSDXL + Pixel_Art_XL LoRA

Fix für v5-Probleme (User-Feedback 2026-07-13):
  - Kleid ist meist weiß → RDXL_Pixel_Art_-_Pony_2 hat Pony-Bias auf Weiß + Akzent
  - 4 Charaktere pro Bild / nur ein Kopf → CharTurn-LoRA bricht durch bei "turnaround"/"multiple views" Trigger
  - Beine zu lang → Pony-Bias auf realistische Proportionen
  - Sexy-Drift → Pony-Trainingsset hat reife Charaktere

Lösung: Base-Wechsel zu autismmixSDXL (Illustrious-Pony-Mix, cute-spezialisiert)
  - CharTurn-LoRA raus (weight 0.0) → keine Multi-Char mehr
  - Pixel_Art_XL LoRA bleibt (0.85) → Pixel-Look
  - Winkel nur via Trigger-Wörter (manuell)
  - Steps 35, Cfg 7.0 fix
  - Seed 100 konstant

Katharina-Specs unverändert (rotes Kleid, blonde Zöpfe, weißer Kragen, Socken, Mary-Janes, kindlich)
"""

import os
import sys
import json
import time
import urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"

# BASE-WECHSEL: Pony-Pixel-Art raus, Illustrious-Pony-Mix rein
BASE_MODEL = "autismmixSDXL_autismmixPony_258042.safetensors"
PIXEL_LORA = "concept\\Pixel_Art_XL_-_v1-1.safetensors"
PIXEL_LORA_WEIGHT = 0.85
# CharTurn RAUS
CHARTURN_LORA = None
CHARTURN_LORA_WEIGHT = 0.0
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v6"
TEMP_OUT = "/root/little-buddy-card/assets/temp"

# Katharina-Spec unverändert, aber Winkel rein über Trigger-Wörter (kein LoRA)
INSTANCE_PROMPT = (
    "pixel art, katharina character, "
    "kawaii cute adorable innocent sweet wholesome childlike small girl, "
    "blonde hair in two long braids, "
    "(solid bright crimson red simple knee-length dress:1.5), monochrome red, "
    "no white parts, no white accents, no white sections, no white trim, "
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

NEGATIVE = (
    # === Multi-Charakter (kritisch — CharTurn ist raus, aber wir negieren für alle Fälle) ===
    "two characters, multiple characters, second character, additional character, "
    "other character, background character, scaled character, resized character, "
    "size difference, size variation, different size, different scale, different height, "
    "smaller character, larger character, tiny character, giant character, "
    "doppelganger, twin, duplicate, copy, mirror image, "
    "crowd, group of people, multiple views in one image, turnaround sheet showing multiple figures, "
    # === Kleid-Farbe (Problem: Weiß statt Rot) ===
    "white dress, ivory dress, cream dress, off-white dress, light dress, "
    "dress with white parts, dress with white accents, white trim, white collar on dress, "
    "two-tone dress, multicolored dress, gradient dress, "
    "pink dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, orange dress, grey dress, beige dress, "
    "polka dot dress, striped dress, plaid dress, floral print dress, checkered dress, "
    # === Sexy-Bias ===
    "sexy, sensual, seductive, alluring, flirtatious, suggestive, erotic, mature, adult, "
    "developed body, curvy, voluptuous, large breasts, cleavage, "
    "18, 20, 25, old, beautiful woman, attractive, hot, pinup, "
    "makeup, lipstick, eyeliner, mascara, high heels, jewelry, necklace, earrings, "
    "long legs, slender legs, tall body, long body, model proportions, "
    "bare legs, naked legs, exposed legs, leg visible, thigh visible, "
    "back turned, from behind, rear view, bent over, looking over shoulder, "
    "nsfw, nude, naked, exposed, undressed, topless, lingerie, underwear, "
    # === Beine-Länge ===
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

# 6 View-Slots — NUR über Trigger-Wörter, kein CharTurn-LoRA
VIEWS = [
    ("01_front", "single character, full body, front view, looking at viewer, standing straight, both arms at sides"),
    ("02_3quarter_left", "single character, full body, three quarter view from the left, slight turn, gentle smile, head slightly tilted"),
    ("03_side_right", "single character, full body, side view facing right, profile, standing still, calm expression"),
    ("04_back_3quarter", "single character, full body, three quarter view from behind, mostly back, slight head turn to the right"),
    ("05_low_angle", "single character, full body, slight low angle view, looking up at the character, gentle pose"),
    ("06_top_down", "single character, full body, high angle view, looking down at character, full body visible"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_comfy_workflow(seed, pose_desc, view_name, view_index):
    """Build ComfyUI workflow mit autismmix-Base + Pixel_Art_XL LoRA, OHNE CharTurn."""
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": BASE_MODEL}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "model": ["1", 0], "clip": ["1", 1],
            "lora_name": PIXEL_LORA, "strength_model": PIXEL_LORA_WEIGHT, "strength_clip": PIXEL_LORA_WEIGHT}},
        # CharTurn RAUS — direkt von LoraLoader zu CLIPTextEncode
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{INSTANCE_PROMPT}, {pose_desc}", "clip": ["2", 1]}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["2", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["2", 0], "seed": seed, "steps": 35, "cfg": 7.0,
            "sampler_name": "euler_ancestral", "scheduler": "normal",
            "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["5", 0], "denoise": 1.0}},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": f"katharina_v6_{view_name}"}}
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
                if prefix in fname or "katharina_v6" in fname:
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

    print(f"=== katharina_characterset_v6 (BASE-WECHSEL: autismmixSDXL) ===")
    print(f"Base: {BASE_MODEL} (Illustrious-Pony-Mix, cute-spezialisiert)")
    print(f"Pixel-LoRA: {PIXEL_LORA} (weight {PIXEL_LORA_WEIGHT})")
    print(f"CharTurn-LoRA: RAUS (weight 0.0)")
    print(f"Seed: {fixed_seed} (konstant), Steps: 35 (fix), Cfg: 7.0 (fix)")
    print(f"Winkel: nur via Trigger-Wörter, kein LoRA")
    print(f"Katharina-Specs: unverändert")
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
        # Cache-Bypass: steps/cfg/denoise minimal pro View (steps bleibt 35 fix als base)
        wf = build_comfy_workflow(fixed_seed, pose_desc, view_name, i)
        # Bei fixem steps+cfg müssen wir cfg minimal variieren (Δ0.1 reicht für Cache-Break)
        wf["6"]["inputs"]["cfg"] = round(7.0 + (i * 0.08), 2)  # 7.0, 7.08, 7.16, 7.24, 7.32, 7.4
        wf["6"]["inputs"]["denoise"] = round(1.0 - (i * 0.008), 4)  # 1.0, 0.992, 0.984, 0.976, 0.968, 0.96
        print(f"\n[{i+1}/{len(views_to_run)}] {view_name} (seed {fixed_seed})")
        print(f"  Cfg: {wf['6']['inputs']['cfg']}, Denoise: {wf['6']['inputs']['denoise']}")

        try:
            prompt_id = submit_workflow(wf)
            history = wait_for_prompt(prompt_id, timeout=600)
            if history is None:
                print(f"  ✗ Cache-Hit, retry mit seed+1000")
                wf["6"]["inputs"]["seed"] = fixed_seed + 1000
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
