#!/usr/bin/env python3
"""
katharina_variations_loop_v2 — img2img vom ECHTEN Master

KRITISCH:
  - Verwendet /root/little-buddy-card/assets/temp/katharina_master.png als Init
  - NICHT die kaputte 2-KB-Version in assets/katharina_master.png
  - Base: RDXL_Pixel_Art_-_Pony_2 (zurück zu v3/v4, war am wenigsten schlecht)
  - Init-image zwingt den Charakter
  - Pose EXPLIZIT: "standing straight, both feet planted, both arms at sides"
  - KEIN CharTurn-LoRA
  - 8 Variationen, seeds 100-107, creativity 0.4

Katharina-Specs (konsolidiert, v1-typischer Stil):
  - pixel art, katharina character
  - cute chibi kawaii girl
  - blonde hair in two long braids
  - simple red dress (kein Pattern, kein Weiß)
  - white collar
  - white socks, black mary jane shoes
  - big round innocent eyes
  - sweet innocent
  - white background
"""

import os
import sys
import json
import time
import base64
import urllib.parse
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
# KEIN CharTurn-LoRA, KEIN Pixel_Art_XL LoRA (halten wir minimal)
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/variations_v2"

# ECHTES Master — NICHT die kaputte 2-KB-Version
# assets/temp/katharina_master.png ist 256x256, 72 KB
MASTER_PATH = "/root/little-buddy-card/assets/temp/katharina_master.png"
if not os.path.exists(MASTER_PATH) or os.path.getsize(MASTER_PATH) < 10000:
    print(f"❌ FEHLER: Echtes Master nicht gefunden oder zu klein: {MASTER_PATH}")
    print(f"   Existiert: {os.path.exists(MASTER_PATH)}, Größe: {os.path.getsize(MASTER_PATH) if os.path.exists(MASTER_PATH) else 0} bytes")
    sys.exit(1)

# Master-Prompt — explizite standing Pose
INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii girl, "
    "blonde hair in two long braids, "
    "simple red dress, white collar, puffy short sleeves, "
    "white socks, black mary jane shoes, "
    "big round innocent eyes, small button nose, plump cheeks, sweet innocent smile, "
    "childlike proportions, large round head, small body, tiny limbs, "
    "standing straight, both feet planted, both arms at sides, "
    "white background, no scenery, isolated character, "
    "masterpiece, highly detailed, sharp focus"
)

NEGATIVE = (
    "fighting, action pose, dynamic pose, muscular, aggressive, mature, adult, "
    "leaping, jumping, raised arms, multiple girls, second character, "
    "leggings, pants, trousers, jeans, tights, stockings, "
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, two-tone dress, patterned dress, "
    "no braids, loose hair, hair down, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, "
    "background, scenery, landscape, pattern, decoration, "
    "realistic, photo, 3d, multiple views, "
    "folklore, folk, traditional, bavarian, dirndl, tracht, costume, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "apron, schürze, bag, purse, handtasche, cross, crucifix, religious, "
    "wings, halo, tail, animal ears, cat ears, bunny ears, fantasy, "
    "back turned, from behind, rear view, bent over, looking over shoulder"
)

CREATIVITY = 0.4  # Niedrig: Master-Charakter bleibt dominant, nur Mikro-Variation
SEEDS = list(range(100, 108))  # 8 Variationen


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_comfy_workflow(seed, master_b64):
    """img2img via SwarmUI — Init-Image + Prompt."""
    return {
        "session_id": None,  # wird vom Caller gesetzt
        "images": 1,
        "model": BASE_MODEL,
        "prompt": INSTANCE_PROMPT,
        "negativeprompt": NEGATIVE,
        "width": 512,
        "height": 512,
        "steps": 28,
        "cfgscale": 7.5,
        "sampler": "euler_ancestral",
        "seed": seed,
        "initimage": master_b64,
        "init_image_creativity": CREATIVITY,
    }


def submit_to_swarmui(payload):
    """SwarmUI txt2img/img2img endpoint."""
    r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
    if r.status_code == 200:
        data = r.json()
        if "images" in data and data["images"]:
            return data["images"][0]
    raise Exception(f"Gen failed: {r.status_code} {r.text[:300]}")


def download_output(sid, img_path, save_to):
    url = f"{HOST}/{img_path}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv

    print(f"=== katharina_variations_loop_v2 (img2img vom echten Master) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Master: {MASTER_PATH} ({os.path.getsize(MASTER_PATH)//1024} KB)")
    print(f"Method: SwarmUI img2img mit initimage + creativity {CREATIVITY}")
    print(f"Resolution: 512×512 (Master native), Steps: 28, Cfg: 7.5")
    print(f"KEIN CharTurn-LoRA, KEIN Pixel_Art_XL LoRA (minimal)")
    print(f"Seeds: {SEEDS}")
    print(f"Output: {OUT_DIR}/")
    print()
    print("Katharina-Specs:")
    print("  - standing straight, both feet planted, both arms at sides (EXPLIZIT)")
    print("  - simple red dress, white collar, puffy short sleeves")
    print("  - blonde braids, white socks, black mary janes")
    print("  - cute chibi kawaii girl, childlike proportions")
    print("  - kein Folklore, kein NSFW, kein Sexy")
    print()

    if not do_submit:
        print("Run with --submit to generate 8 variations.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)

    # Master als Base64 lesen
    with open(MASTER_PATH, "rb") as f:
        master_b64 = base64.b64encode(f.read()).decode()
    print(f"Master base64: {len(master_b64)} chars")

    sid = get_session()
    print(f"Session: {sid[:16]}...")

    for i, seed in enumerate(SEEDS):
        print(f"\n[{i+1}/{len(SEEDS)}] seed {seed}")
        payload = build_comfy_workflow(seed, master_b64)
        payload["session_id"] = sid

        try:
            img_path = submit_to_swarmui(payload)
            save = f"{OUT_DIR}/var_{i+1:02d}_seed{seed}.png"
            size = download_output(sid, img_path, save)
            print(f"  ✓ {save} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print(f"\n=== FERTIG ===")
    print(f"Output: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        p = os.path.join(OUT_DIR, f)
        print(f"  {f}: {os.path.getsize(p)//1024} KB")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Welche 2-3 sehen am meisten nach Katharina aus?")
    print("  Sag die Nummern — die werden Trainings-Set fürs Character-LoRA.")
