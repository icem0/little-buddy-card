#!/usr/bin/env python3
"""
katharina_master_v4 — 3 verschiedene Base-Checkpoints parallel

RDXL_Pixel_Art_-_Pony_2 hat Outdoors-Bias (Gras statt weißer Hintergrund).
3 neue Versuche mit anderen Checkpoints:

  v1: childrensStories_v1CustomA (Children's Stories — sollte weißen BG können)
  v2: unholyDesireMixSinister_v80 (Illustrious raehoshi — cute kawaii)
  v3: RetroDiffusionModel (SD 1.5 dediziert Pixel-Art)

Gleiche Specs wie v3, cfg 7.0, steps 30, 800x800, seed 42, kein Init.
"""

import os, sys, time
import requests

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/master"

CHECKPOINTS = {
    "v1_childrens": "childrensStories_v1CustomA_74654.safetensors",
    "v2_unholy": "unholyDesireMixSinister_v80.safetensors",
    "v3_retro": "RetroDiffusionModel.safetensors",
}

# Saubere Specs — funktionierten bei v3 visuell (bis auf den Gras-Bias)
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

NEG = (
    "fighting, action pose, dynamic pose, leaping, jumping, raised arms, "
    "multiple girls, second character, additional character, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "white dress, blue dress, green dress, yellow dress, black dress, brown dress, "
    "purple dress, pink dress, two-tone dress, patterned dress, polka dot, striped, "
    "no braids, loose hair, hair down, ponytail, bun, short hair, "
    "black hair, brown hair, blue hair, pink hair, red hair, white hair, grey hair, "
    "background scenery, landscape, decoration, pattern, grass, grass field, meadow, lawn, "
    "realistic, photo, 3d, multiple views, turnaround, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, 18, 25, "
    "blurry, deformed, noise, borders, frame, watermark, text, signature, "
    "apron, schürze, bag, purse, handtasche, religious, cross, crucifix, "
    "wings, halo, tail, animal ears, fantasy, "
    "back turned, from behind, rear view, bent over, looking over shoulder"
)

# SD 1.5 Modelle (RetroDiffusion) brauchen andere Settings + Resolution
SETTINGS = {
    "v1_childrens": {"width": 800, "height": 800, "cfg": 7.0, "steps": 30},
    "v2_unholy": {"width": 800, "height": 800, "cfg": 7.0, "steps": 30},
    "v3_retro": {"width": 512, "height": 512, "cfg": 6.5, "steps": 28},  # SD 1.5 native
}


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen(sid, model, prompt, neg, cfg, steps, w, h, seed, out_path):
    payload = {
        "session_id": sid, "images": 1, "model": model,
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
    print(f"=== katharina_master_v4 (3 verschiedene Base-Checkpoints) ===")
    print(f"Gleiche Specs, nur Checkpoint variiert:")
    for name, model in CHECKPOINTS.items():
        s = SETTINGS[name]
        print(f"  {name}: {model} ({s['width']}x{s['height']}, cfg={s['cfg']}, steps={s['steps']})")
    print()

    if not do_submit:
        print("Run with --submit to generate 3 variants.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    for name, model in CHECKPOINTS.items():
        out = f"{OUT_DIR}/master_v4_{name}.png"
        s = SETTINGS[name]
        print(f"\n[{name}] {model} ({s['width']}x{s['height']}, cfg={s['cfg']}, steps={s['steps']})")
        try:
            size = gen(sid, model, PROMPT, NEG, s["cfg"], s["steps"], s["width"], s["height"], 42, out)
            print(f"  ✓ {out} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print(f"\n=== FERTIG — 3 Varianten bereit zur Abnahme ===")
    print(f"Output: {OUT_DIR}/")
    for f in sorted(os.listdir(OUT_DIR)):
        if f.startswith("master_v4_") and f.endswith(".png"):
            p = os.path.join(OUT_DIR, f)
            print(f"  {f}: {os.path.getsize(p)//1024} KB")
    print()
    print("USER-BEWERTUNG ERWARTET:")
    print("  Welcher Checkpoint macht es am besten (weißer BG, kein Gras, rotes Kleid, Katharina)?")
    print("  Sag den Namen (v1_childrens / v2_unholy / v3_retro).")
