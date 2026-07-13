#!/usr/bin/env python3
"""
katharina_master_v5 — v3-Settings (RDXL_Pixel_Art) mit gras im Negativ

Einfachster Fix: alle Outdoor-Bodentypen in NEG.
"""

import os, sys, time
import requests

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/master"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"

# Gleiche Specs wie v3
PROMPT = (
    "pixel art, katharina character, cute chibi kawaii small girl, "
    "blonde hair in two long braids, "
    "simple bright crimson red dress, white peter pan collar, short puffy sleeves, "
    "white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "small child body, childlike proportions, large round head, tiny limbs, "
    "standing straight, both feet planted on ground, both arms relaxed at sides, "
    "soft round shadow under feet, "
    "white background, no scenery, isolated character, "
    "masterpiece, highly detailed, sharp focus, 8bit pixel art style"
)

# NEG mit ALLEM was zu Outdoor-Boden führen könnte
NEG = (
    # === BODEN / OUTDOOR (Hauptproblem v3) ===
    "grass, lawn, meadow, field, ground, dirt, soil, mud, sand, "
    "gravel, stone floor, cobblestone, tile floor, wood floor, "
    "outdoor, outdoors, outside, nature, forest, garden, park, "
    "outdoor scene, outdoor background, landscape, scenery, environment, "
    "platform, pedestal, square, stage, podium, ground line, floor line, "
    "horizon, sky, sun, clouds, trees, bushes, flowers, plants, "
    # === Charakter-Konflikte (Standard) ===
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


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen(sid, prompt, neg, cfg, steps, w, h, seed, out_path):
    payload = {
        "session_id": sid, "images": 1, "model": BASE_MODEL,
        "prompt": prompt, "negativeprompt": neg,
        "width": w, "height": h, "steps": steps, "cfgscale": cfg,
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
    print(f"=== katharina_master_v5 (RDXL_Pixel_Art + GRAS im Neg) ===")
    print(f"Base: {BASE_MODEL}, 800x800, cfg 7.0, steps 30, seed 42")
    print(f"Neg erweitert um: grass, lawn, meadow, field, ground, dirt, soil, sand, "
          f"gravel, outdoor, garden, park, horizon, sky, sun, clouds, trees, plants...")
    print()

    if not do_submit:
        print("Run with --submit to generate.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")
    out = f"{OUT_DIR}/master_v5_grass_neg.png"
    print(f"\n[v5_grass_neg] cfg=7.0, steps=30, seed=42")
    try:
        size = gen(sid, PROMPT, NEG, 7.0, 30, 800, 800, 42, out)
        print(f"  ✓ {out} ({size//1024} KB)")
    except Exception as e:
        print(f"  ✗ {e}")
        sys.exit(1)

    print(f"\n=== FERTIG ===")
    print(f"Output: {out}")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Kein Gras mehr? Weißer Hintergrund? Rotes Kleid? Katharina?")
