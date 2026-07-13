#!/usr/bin/env python3
"""
katharina_master_v1 — EIN Master-Bild, ein Versuch, dann User-Bewertung.

Methode: img2img vom vorhandenen 256x256 Master-Asset (katharina_master.png in temp/)
  - Wenn das geklappt hat: 800x800 Upscale via img2img mit niedrigem creativity
  - RDXL_Pixel_Art_-_Pony_2 Base (v1-Stil, war der einzige der teilweise funktioniert hat)
  - KEINE LoRAs (Pixel_Art_XL war zu dominant, CharTurn machte Multi-Char)
  - Saubere Specs aus User-Feedback: standing, kleid rot, zöpfe, süß, kindlich
  - Saubere Negativ-Liste (NSFW, Folklore, Action, etc.)

Output: assets/characters/katharina/master/master_v1.png (800x800)
"""

import os, sys, base64, time, json
import requests

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
OUT = "/root/little-buddy-card/assets/characters/katharina/master/master_v1.png"
TMP = "/root/little-buddy-card/assets/temp/katharina_master_attempt.png"

# Saubere Master-Specs aus User-Feedback
PROMPT = (
    "pixel art, katharina character, cute chibi kawaii small girl, "
    "blonde hair in two long braids, "
    "simple bright crimson red dress, white peter pan collar, short puffy sleeves, "
    "white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "small child body, childlike proportions, large round head, tiny limbs, "
    "standing straight, both feet planted on ground, both arms relaxed at sides, "
    "white background, pure white background, no scenery, no floor, no ground, "
    "isolated character, no shadow on ground, no shadow on floor, "
    "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
)

NEG = (
    "fighting, action pose, dynamic pose, leaping, jumping, raised arms, "
    "multiple girls, second character, additional character, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, two-tone dress, patterned dress, polka dot, striped, "
    "no braids, loose hair, hair down, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, "
    "background scenery, landscape, decoration, pattern, "
    "shadow, ground shadow, floor shadow, drop shadow, blue shadow, "
    "no shadow, no ground shadow, no floor shadow, "
    "gradient background, colored background, off-white background, gray background, "
    "background pattern, background object, background symbol, "
    "realistic, photo, 3d, multiple views, turnaround, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, 18, 25, "
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "apron, schürze, bag, purse, handtasche, religious, cross, crucifix, "
    "wings, halo, tail, animal ears, fantasy, "
    "back turned, from behind, rear view, bent over, looking over shoulder"
)


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen(seed, init_b64, creativity, width, height, out_path):
    """img2img via SwarmUI."""
    sid = get_session()
    payload = {
        "session_id": sid, "images": 1, "model": BASE_MODEL,
        "prompt": PROMPT, "negativeprompt": NEG,
        "width": width, "height": height, "steps": 28, "cfgscale": 7.5,
        "sampler": "euler_ancestral", "seed": seed,
        "initimage": init_b64, "init_image_creativity": creativity,
    }
    r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Gen failed: {r.status_code} {r.text[:300]}")
    data = r.json()
    if "images" not in data or not data["images"]:
        raise Exception(f"No images: {data}")
    img_path = data["images"][0]
    url = f"{HOST}/{img_path}"
    r2 = requests.get(url, timeout=60)
    r2.raise_for_status()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r2.content)
    return len(r2.content), sid


if __name__ == "__main__":
    # Echtes Master laden
    src = "/root/little-buddy-card/assets/temp/katharina_master.png"
    if not os.path.exists(src) or os.path.getsize(src) < 10000:
        print(f"❌ Master nicht gefunden: {src}")
        sys.exit(1)
    print(f"Master: {src} ({os.path.getsize(src)//1024} KB)")
    with open(src, "rb") as f:
        master_b64 = base64.b64encode(f.read()).decode()
    print(f"Base64: {len(master_b64)} chars")

    # Versuch 2: txt2img (KEIN img2img) damit kein Schatten vom Master übernommen wird
    # Master dient nur als Referenz im Kopf, nicht als Init
    print(f"\n=== Versuch 2: 800x800 txt2img (kein Init) ===")
    try:
        sid = get_session()
        payload = {
            "session_id": sid, "images": 1, "model": BASE_MODEL,
            "prompt": PROMPT, "negativeprompt": NEG,
            "width": 800, "height": 800, "steps": 28, "cfgscale": 7.5,
            "sampler": "euler_ancestral", "seed": 42,
            # KEIN initimage — sauberer txt2img
        }
        r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
        if r.status_code != 200:
            raise Exception(f"Gen failed: {r.status_code} {r.text[:300]}")
        data = r.json()
        if "images" not in data or not data["images"]:
            raise Exception(f"No images: {data}")
        img_path = data["images"][0]
        url = f"{HOST}/{img_path}"
        r2 = requests.get(url, timeout=60)
        r2.raise_for_status()
        with open(OUT, "wb") as f:
            f.write(r2.content)
        import shutil
        shutil.copy(OUT, TMP)
        print(f"  ✓ {OUT} ({len(r2.content)//1024} KB)")
    except Exception as e:
        print(f"  ✗ {e}")
        sys.exit(1)

    print(f"\n=== FERTIG — Master v1 bereit zur Abnahme ===")
    print(f"  Hauptpfad:  {OUT}")
    print(f"  Temp-Pfad:  {TMP}")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Sieht das Bild nach Katharina aus?")
    print("  Wenn ja → Schritt 2 (WanAnimate drüber)")
    print("  Wenn nein → was genau fehlt (Farbe, Pose, Outfit, Gesicht)?")
