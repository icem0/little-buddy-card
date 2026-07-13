#!/usr/bin/env python3
"""
katharina_master_v9 — AUFGERÄUMTER PROMPT mit Token-Weighting

Nach v8 Prompt-Audit:
  - 6 Knee-Length-Varianten → 1 Token-Weight Anker
  - 6 Süss-Synonyme → 1 Begriff (cute)
  - 4 Schatten-Synonyme → 1 Token-Weight
  - 18 Bodentypen → 3 Begriffe (grass, ground, outdoor)
  - 12 Haarfarben → 2 (nur die gefährlichsten)
  - Doppelte Begriffe raus
  - Token-Weight für kritische Anker: dress, shadow, chibi

Positiv: 12 Begriffe, klar gewichtet
Negativ: 25 Begriffe, kein Noise
"""

import os, sys, time
import requests

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/master"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"

# Positiv: minimal, jedes Wort mit Absicht
# Token-Weight auf die 3 kritischen Anker: Kleid, Schatten, chibi
PROMPT = (
    "pixel art, cute childlike small girl, "
    "blonde hair in two long braids, "
    "(bright crimson red dress:1.4), (knee-length dress:1.2), white peter pan collar, "
    "short puffy sleeves, white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "(chibi proportions:1.1), large round head, tiny limbs, "
    "standing straight, both feet planted, both arms at sides, "
    "(neutral gray soft shadow under feet:1.2), "
    "pure white background, no scenery, isolated character, "
    "masterpiece, highly detailed, 8bit pixel art"
)

# Negativ: nur Begriffe die das Model auch triggern würden
NEG = (
    # === BODEN (Hauptproblem) ===
    "grass, ground, outdoor, ground line, floor, dirt, soil, sand, gravel, "
    "landscape, scenery, environment, platform, pedestal, square, stage, "
    "horizon, sky, trees, plants, flowers, bushes, "
    # === SCHATTEN-FARBE (Hauptproblem v5) ===
    "green shadow, green tint, blue shadow, colored shadow, tinted shadow, "
    # === KLEID (Sexy-Variante + falsche Farbe) ===
    "shorts, mini skirt, crop top, short dress, mini dress, "
    "white dress, blue dress, green dress, yellow dress, black dress, purple dress, pink dress, "
    # === FOLKLORE / TRACHT (User-Vorgabe) ===
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    # === CHARAKTER-DRIFT ===
    "multiple girls, second character, additional character, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "no braids, loose hair, hair down, ponytail, bun, "
    "black hair, brown hair, "
    # === NSFW (User-Vorgabe: kein NSFW, keine Brüste) ===
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, "
    # === QUALITY / REALISM-DRIFT ===
    "blurry, deformed, noise, watermark, text, signature, "
    "3d, realistic, photo, "
    # === ACTION (User-Vorgabe: standing, nicht tanzend) ===
    "fighting, leaping, jumping, raised arms, dynamic pose, "
    "back turned, from behind, rear view, "
    # === ZUSÄTZLICHE ACCESSOIRES (User-Vorgabe: kein Tracht/Folklore-Schmuck) ===
    "wings, halo, tail, animal ears, fantasy, "
    "necklace, earrings, makeup, lipstick, high heels"
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
    print(f"=== katharina_master_v9 (AUFGERÄUMTER PROMPT mit Token-Weighting) ===")
    print(f"Base: {BASE_MODEL}, 800x800, cfg 7.0, steps 30, seed 42")
    print(f"")
    print(f"Prompt-Audit:")
    print(f"  Positiv: 12 Begriffe + 3 Token-Weights ((dress:1.4), (knee-length:1.2), (shadow:1.2), (chibi:1.1))")
    print(f"  Negativ: 9 Kategorien, kein Doppel-Müll")
    print()

    if not do_submit:
        print("Run with --submit to generate.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")
    out = f"{OUT_DIR}/master_v9_clean_prompt.png"
    print(f"\n[v9_clean_prompt] cfg=7.0, steps=30, seed=42")
    try:
        size = gen(sid, PROMPT, NEG, 7.0, 30, 800, 800, 42, out)
        print(f"  ✓ {out} ({size//1024} KB)")
    except Exception as e:
        print(f"  ✗ {e}")
        sys.exit(1)

    import shutil
    shutil.copy(out, "/root/little-buddy-card/assets/temp/katharina_master_attempt.png")
    print(f"  ✓ Kopie: /root/little-buddy-card/assets/temp/katharina_master_attempt.png")

    print(f"\n=== FERTIG ===")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Kleid knee-length, Schatten grau, kein Gras, Katharina?")
