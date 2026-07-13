#!/usr/bin/env python3
"""
katharina_master_v3 — 4 saubere Versuche parallel mit verschiedenen Settings

Ziel: minimaler Varianz, sauberer weißer Hintergrund, runder Schatten.
Vier Varianten mit unterschiedlichen (prompt, cfg, steps) Kombis.
User wählt die beste.

Settings-Matrix:
  v1: cfg 7.5, steps 28, kein Schatten im Prompt (Baseline)
  v2: cfg 6.5, steps 35, "soft round shadow under feet" im Prompt
  v3: cfg 8.0, steps 40, "soft round shadow under feet" + stärkere Kleid-Pin
  v4: cfg 7.0, steps 30, alle Schatten-Wörter im Negativ + "soft round shadow under feet" im Positiv
"""

import os, sys, time, json, base64
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/master"

# 4 Prompt-Varianten — ALLE mit sauberen Katharina-Specs, nur Schatten-Wording variiert
PROMPTS = {
    "v1_baseline": (
        "pixel art, katharina character, cute chibi kawaii small girl, "
        "blonde hair in two long braids, "
        "simple bright crimson red dress, white peter pan collar, short puffy sleeves, "
        "white knee-high socks, black mary jane shoes, "
        "big round innocent eyes, plump cheeks, sweet innocent smile, "
        "small child body, childlike proportions, large round head, tiny limbs, "
        "standing straight, both feet planted on ground, both arms relaxed at sides, "
        "white background, no scenery, isolated character, "
        "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
    ),
    "v2_soft_shadow": (
        "pixel art, katharina character, cute chibi kawaii small girl, "
        "blonde hair in two long braids, "
        "simple bright crimson red dress, white peter pan collar, short puffy sleeves, "
        "white knee-high socks, black mary jane shoes, "
        "big round innocent eyes, plump cheeks, sweet innocent smile, "
        "small child body, childlike proportions, large round head, tiny limbs, "
        "standing straight, both feet planted on ground, both arms relaxed at sides, "
        "soft round shadow under feet, soft ground shadow, "
        "white background, no scenery, isolated character, "
        "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
    ),
    "v3_strong_pin": (
        "pixel art, katharina character, cute chibi kawaii small girl, "
        "blonde hair in two long braids, "
        "(simple bright crimson red dress:1.4), white peter pan collar, short puffy sleeves, "
        "white knee-high socks, black mary jane shoes, "
        "big round innocent eyes, plump cheeks, sweet innocent smile, "
        "small child body, childlike proportions, large round head, tiny limbs, "
        "standing straight, both feet planted on ground, both arms relaxed at sides, "
        "soft round shadow under feet, soft ground shadow, "
        "white background, no scenery, isolated character, "
        "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
    ),
    "v4_no_shadow_neg": (
        "pixel art, katharina character, cute chibi kawaii small girl, "
        "blonde hair in two long braids, "
        "simple bright crimson red dress, white peter pan collar, short puffy sleeves, "
        "white knee-high socks, black mary jane shoes, "
        "big round innocent eyes, plump cheeks, sweet innocent smile, "
        "small child body, childlike proportions, large round head, tiny limbs, "
        "standing straight, both feet planted on ground, both arms relaxed at sides, "
        "soft round shadow under feet, soft ground shadow, "
        "white background, no scenery, isolated character, "
        "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
    ),
}

# 4 Negativ-Listen — v4 hat zusätzlich "no shadow" / "no platform" / "no pedestal"
NEG_BASE = (
    "fighting, action pose, dynamic pose, leaping, jumping, raised arms, "
    "multiple girls, second character, additional character, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, two-tone dress, patterned dress, polka dot, striped, "
    "no braids, loose hair, hair down, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, "
    "background scenery, landscape, decoration, pattern, "
    "realistic, photo, 3d, multiple views, turnaround, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, 18, 25, "
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "apron, schürze, bag, purse, handtasche, religious, cross, crucifix, "
    "wings, halo, tail, animal ears, fantasy, "
    "back turned, from behind, rear view, bent over, looking over shoulder"
)

NEG_PLATFORM = NEG_BASE + (
    "platform, pedestal, square, tile, box, stage, podium, "
    "ground line, floor line, "
    "hard shadow, sharp shadow, square shadow, blue shadow, "
    "rectangle, rectangular shadow, "
    "colored background, gradient background, off-white background, gray background"
)

NEGS = {
    "v1_baseline": NEG_BASE,
    "v2_soft_shadow": NEG_BASE,
    "v3_strong_pin": NEG_BASE,
    "v4_no_shadow_neg": NEG_PLATFORM,
}

# 4 Settings-Varianten
SETTINGS = {
    "v1_baseline":  {"cfg": 7.5, "steps": 28},
    "v2_soft_shadow": {"cfg": 6.5, "steps": 35},
    "v3_strong_pin":  {"cfg": 8.0, "steps": 40},
    "v4_no_shadow_neg": {"cfg": 7.0, "steps": 30},
}


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen(sid, prompt, neg, cfg, steps, seed, out_path):
    payload = {
        "session_id": sid, "images": 1, "model": BASE_MODEL,
        "prompt": prompt, "negativeprompt": neg,
        "width": 800, "height": 800, "steps": steps, "cfgscale": cfg,
        "sampler": "euler_ancestral", "seed": seed,
    }
    r = requests.post(f"{HOST}/API/GenerateText2Image", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Gen failed: {r.status_code} {r.text[:200]}")
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
    return len(r2.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_master_v3 (4 Settings-Varianten parallel) ===")
    print(f"Base: {BASE_MODEL}, 800x800, txt2img (kein Init)")
    for name, s in SETTINGS.items():
        print(f"  {name}: cfg={s['cfg']}, steps={s['steps']}")
    print()

    if not do_submit:
        print("Run with --submit to generate 4 variants.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    for name in SETTINGS.keys():
        out = f"{OUT_DIR}/master_{name}.png"
        s = SETTINGS[name]
        print(f"\n[{name}] cfg={s['cfg']}, steps={s['steps']}, seed=42")
        try:
            size = gen(sid, PROMPTS[name], NEGS[name], s["cfg"], s["steps"], 42, out)
            print(f"  ✓ {out} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print(f"\n=== FERTIG — 4 Varianten bereit zur Abnahme ===")
    print(f"Output: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        if f.startswith("master_v") and f.endswith(".png"):
            p = os.path.join(OUT_DIR, f)
            print(f"  {f}: {os.path.getsize(p)//1024} KB")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Welche der 4 Varianten sieht am meisten nach Katharina aus?")
    print("  Sag den Namen (v1_baseline / v2_soft_shadow / v3_strong_pin / v4_no_shadow_neg).")
