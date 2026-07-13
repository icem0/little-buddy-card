#!/usr/bin/env python3
"""
katharina_characterset_v1 — Character-Set Generator (Contact-Sheet)

Generiert ein Multi-View-Image von Katharina (verschiedene Winkel) in EINEM Bild
(Contact-Sheet), aus dem wir die Einzelbilder für LoRA-Training extrahieren.

Pipeline:
  1. Katharina in 6 Posen/Winkeln (je 1 Bild) via img2img vom Master
     - 1x Front, 1x 3/4-View, 1x Side-Left, 1x Side-Right, 1x Back, 1x Slight-Tilt
  2. Contact-Sheet via ImageGrid-Node (6 Bilder in einer Reihe)
  3. User gibt Master-Look frei
  4. Crop → 6 Einzelbilder für LoRA-Training

v1 — 2026-07-13, Little Buddy Card
  - Base: RDXL_Pixel_Art_-_Pony_2 (SDXL pixel art)
  - Kein zusätzliches LoRA (das littlebuddy_pixel ist nicht Katharina)
  - Master: katharina_master.png (rote Kleid, blonde Zöpfe, klein)
  - Style-Anker: Token-Weight auf Kleid + neg-Liste für Haar-/Kleid-Farben
  - Multi-View via img2img mit creativity 0.4-0.55 + view-spezifische Prompts
"""

import os
import sys
import json
import time
import shutil
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
SID = "4cb8a9a0a2d35bb13f9edc19f4dd7df1649c18e2"  # Refresh before submit

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
MASTER_PATH = "/root/little-buddy-card/assets/katharina_master.png"
OUT_BASE = "/root/little-buddy-card/assets/characters/katharina/views"
TEMP_OUT = "/root/little-buddy-card/assets/temp"

# Katharina's definitive Feature-Spec (single source of truth for all generations)
# KEIN Folklore, KEIN Tracht, KEIN NSFW, KEIN Brust-Bias
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

# Anti-Folklore/Tracht/NSFW/Brust-Bias (kritisch — User-Vorgabe)
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

# 6 View-Slots für Character-Set
# Sanfte Winkel-Variation, keine Action-Wörter (verhindert Street-Fighter-Bias)
VIEWS = [
    ("01_front", "front view, looking at viewer, standing straight, both arms at sides"),
    ("02_3quarter", "three quarter view from the right, slight turn, gentle smile, head slightly tilted"),
    ("03_side_left", "side view facing left, profile, standing still, calm expression"),
    ("04_side_right", "side view facing right, profile, standing still, calm expression"),
    ("05_back_3quarter", "three quarter view from behind, mostly back, slight head turn to the right"),
    ("06_low_angle", "slight low angle view, looking up at the character, gentle pose"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def upload_to_comfyui(local_path, name=None):
    """Upload an image to ComfyUI input dir."""
    name = name or os.path.basename(local_path)
    with open(local_path, "rb") as f:
        files = {"image": (name, f, "image/png")}
        r = requests.post(f"{HOST}/ComfyBackendDirect/upload/image", files=files, timeout=30)
    if r.status_code == 200:
        return r.json().get("name", name)
    raise Exception(f"Upload failed: {r.status_code} {r.text[:200]}")


def generate_view(sid, view_name, pose_desc, master_filename, seed, creativity=0.5):
    """Generate 1 view of Katharina via img2img from master."""
    prompt = f"{INSTANCE_PROMPT}, {pose_desc}"
    payload = {
        "session_id": sid,
        "images": 1,
        "model": BASE_MODEL,
        "prompt": prompt,
        "negativeprompt": NEGATIVE,
        "width": 512,
        "height": 512,
        "steps": 28,
        "cfgscale": 7.5,
        "sampler": "euler_ancestral",
        "seed": seed,
        "initimage": _img_to_b64_inline(master_filename),  # base64 OR filename — SwarmUI handles both? NO: needs b64
        "init_image_creativity": creativity,
    }
    # Actually use the filename approach via initimage_files: not supported, must use b64
    import base64
    with open(master_filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload["initimage"] = b64

    r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
    if r.status_code == 200:
        data = r.json()
        if "images" in data and data["images"]:
            return data["images"][0]
    raise Exception(f"Gen failed [{view_name}]: {r.status_code} {r.text[:300]}")


def _img_to_b64_inline(path):
    """Placeholder — kept for compatibility."""
    return None


def download_output(sid, img_path, save_to):
    """Download generated image to local."""
    url = f"{HOST}/{img_path}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


def build_contact_sheet(view_paths, save_to, cols=3):
    """Compose N images into a grid contact sheet using PIL."""
    imgs = [Image.open(p) for p in view_paths]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "white")
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        sheet.paste(im, (c * w, r * h))
    sheet.save(save_to)
    return sheet


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    only_master = "--master-only" in sys.argv

    # === Step 1: Print plan ===
    print(f"=== katharina_characterset_v1 ===")
    print(f"Base model: {BASE_MODEL}")
    print(f"Master: {MASTER_PATH}")
    print(f"Output: {OUT_BASE}/")
    print(f"")
    print(f"6 Views (img2img creativity=0.5, seed=100+idx):")
    for v, desc in VIEWS:
        print(f"  {v}: {desc[:80]}")
    print(f"")
    print(f"Instance prompt ({len(INSTANCE_PROMPT.split())} words):")
    print(f"  {INSTANCE_PROMPT[:200]}...")
    print(f"")
    print(f"Negative prompt ({len(NEGATIVE.split(','))} exclusions)")
    print(f"")
    print(f"Output Contact-Sheet: {TEMP_OUT}/katharina_characterset_v1_sheet.png")
    print(f"")

    if not do_submit:
        print(f"Run with --submit to generate all 6 views + contact sheet.")
        print(f"Run with --master-only to only verify master upload + first view.")
        sys.exit(0)

    # === Step 2: Submit ===
    sid = SID  # Or refresh
    print(f"Session: {sid[:16]}...")

    # Use the SwarmUI txt2img with initimage (img2img via SwarmUI API)
    # ALTERNATIVE: ComfyUI pass-through with CheckpointLoader + LoraLoader
    # For v1 we go with SwarmUI txt2img path (simpler)

    import base64
    with open(MASTER_PATH, "rb") as f:
        master_b64 = base64.b64encode(f.read()).decode()

    if only_master:
        # Test single view
        view_name, pose_desc = VIEWS[0]
        seed = 100
        payload = {
            "session_id": sid,
            "images": 1,
            "model": BASE_MODEL,
            "prompt": f"{INSTANCE_PROMPT}, {pose_desc}",
            "negativeprompt": NEGATIVE,
            "width": 512, "height": 512,
            "steps": 28, "cfgscale": 7.5,
            "sampler": "euler_ancestral",
            "seed": seed,
            "initimage": master_b64,
            "init_image_creativity": 0.5,
        }
        r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
        if r.status_code == 200:
            data = r.json()
            if "images" in data and data["images"]:
                save = f"{OUT_BASE}/{view_name}.png"
                size = download_output(sid, data["images"][0], save)
                print(f"Downloaded: {save} ({size//1024} KB)")
        sys.exit(0)

    # Full set
    generated = []
    for i, (view_name, pose_desc) in enumerate(VIEWS):
        seed = 100 + i * 7
        print(f"[{i+1}/{len(VIEWS)}] {view_name} (seed {seed}, creativity 0.5)...")
        payload = {
            "session_id": sid,
            "images": 1,
            "model": BASE_MODEL,
            "prompt": f"{INSTANCE_PROMPT}, {pose_desc}",
            "negativeprompt": NEGATIVE,
            "width": 512, "height": 512,
            "steps": 28, "cfgscale": 7.5,
            "sampler": "euler_ancestral",
            "seed": seed,
            "initimage": master_b64,
            "init_image_creativity": 0.5,
        }
        try:
            r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
            if r.status_code != 200:
                print(f"  ✗ HTTP {r.status_code}: {r.text[:200]}")
                continue
            data = r.json()
            if "images" not in data or not data["images"]:
                print(f"  ✗ No images in response: {data}")
                continue
            save = f"{OUT_BASE}/{view_name}.png"
            size = download_output(sid, data["images"][0], save)
            print(f"  ✓ {view_name}.png ({size//1024} KB)")
            generated.append(save)
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    if len(generated) == 6:
        # Build contact sheet
        sheet_path = f"{TEMP_OUT}/katharina_characterset_v1_sheet.png"
        sheet = build_contact_sheet(generated, sheet_path, cols=3)
        print(f"\n✓ Contact-Sheet: {sheet_path} ({sheet.size})")
        print(f"\n=== BEREIT ZUR ABNAHME ===")
        print(f"  6 Views: {OUT_BASE}/")
        print(f"  Sheet:   {sheet_path}")
    else:
        print(f"\n⚠ Nur {len(generated)}/6 Views generiert.")
