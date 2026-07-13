#!/usr/bin/env python3
"""
katharina_dataset_v2 — Sauberes LoRA-Dataset (15 Bilder)

Nach User-Feedback v1 war Müll (creativity=0.5 zu hoch, generische Variationen).
v2 nutzt:
  - creativity=0.30 (Master bleibt dominant, Mikro-Pose kommt durch)
  - 15 Bilder (mehr Datenpunkte = besseres LoRA)
  - 5 echte Winkel + 10 Mikro-Variationen
  - Pro Bild individuelle Caption mit Mikro-Pose-Description
    → LoRA lernt: Pose-Variation kommt vom Prompt, Charakter bleibt gleich

Captions-Strategie:
  Basis-Caption (gleich für alle): Charakter-Specs
  + Suffix (pro Bild unterschiedlich): Pose-Description

Dataset-Pfad: /root/little-buddy-card/assets/training/katharina_char_v1/images/
"""

import os, sys, time, base64
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
MASTER_PATH = "/root/little-buddy-card/assets/characters/katharina/master/katharina_master.png"
DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"

# Basis-Caption (Charakter-Specs, gleich für alle)
BASE_CAPTION = (
    "pixel art, cute childlike small girl, "
    "(blonde_braids:1.3), "
    "(bright crimson red dress:1.4), (long_dress:1.2), white peter pan collar, "
    "short puffy sleeves, white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "(chibi proportions:1.1), large round head, tiny limbs, "
    "masterpiece, best quality, amazing quality, "
    "score_9, score_8_up, score_7_up, score_6_up, source_anime"
).strip()

# Konsistenter Negativ (kein 3-Beine-Bug, kein Gras, etc.)
NEG = (
    "score_1, score_2, score_3, source_pony, source_furry, source_hentai, "
    "grass, ground, outdoor, ground line, floor, dirt, soil, sand, gravel, "
    "landscape, scenery, environment, platform, pedestal, square, stage, "
    "horizon, sky, trees, plants, flowers, bushes, "
    "green shadow, green tint, blue shadow, colored shadow, tinted shadow, "
    "shorts, mini skirt, crop top, short dress, mini dress, "
    "white dress, blue dress, green dress, yellow dress, black dress, purple dress, pink dress, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "multiple girls, second character, additional character, "
    "leggings, pants, trousers, jeans, tights, stockings, pantyhose, "
    "no braids, loose hair, hair down, ponytail, bun, "
    "black hair, brown hair, "
    "three legs, extra leg, extra limb, deformed legs, fused legs, bad anatomy, "
    "nsfw, nude, naked, exposed, cleavage, lingerie, underwear, "
    "mature, adult, developed body, curvy, large breasts, "
    "blurry, deformed, noise, watermark, text, signature, "
    "3d, realistic, photo, "
    "fighting, leaping, jumping, raised arms, dynamic pose, "
    "back turned, from behind, rear view, "
    "wings, halo, tail, animal ears, fantasy, "
    "necklace, earrings, makeup, lipstick, high heels"
)

# 15 Variationen: 5 echte Winkel + 10 Mikro-Posen
# Jede Variation hat einen einzigartigen Pose-Suffix für die Caption
VARIATIONS = [
    # === 5 echte Winkel (mit ECHTER Drehung, höherer creativity) ===
    ("02_front",       "front view, looking at viewer, facing forward, gentle smile", 0.30, 100),
    ("03_3quarter_r",  "3/4 view from the right, head turned right, facing camera diagonally", 0.35, 110),
    ("04_3quarter_l",  "3/4 view from the left, head turned left, facing camera diagonally", 0.35, 120),
    ("05_side_r",      "side view facing right, profile from the right side, calm expression", 0.40, 130),
    ("06_back_3q",     "3/4 view from behind, mostly back view, slight head turn to the right, looking over shoulder", 0.40, 140),
    # === 10 Mikro-Posen (nur Mikro-Variation, Master bleibt dominant) ===
    ("07_tilt_r",      "slight head tilt to the right, curious look, gentle smile", 0.25, 200),
    ("08_tilt_l",      "slight head tilt to the left, curious look, gentle smile", 0.25, 210),
    ("09_look_up",     "looking up slightly, hopeful expression, eyes looking up", 0.25, 220),
    ("10_look_down",   "looking down slightly, thoughtful expression, eyes looking down", 0.25, 230),
    ("11_weight_l",    "standing with weight on left leg, slight hip tilt to the right", 0.25, 240),
    ("12_weight_r",    "standing with weight on right leg, slight hip tilt to the left", 0.25, 250),
    ("13_hand_slight", "one hand slightly raised in a small wave gesture, friendly pose", 0.25, 260),
    ("14_arms_back",   "both arms behind back, shy pose, gentle smile", 0.25, 270),
    ("15_eye_blink",   "one eye closed in a wink, playful expression, head slightly tilted", 0.30, 280),
    ("16_smile_big",   "big happy smile, cheerful expression, both eyes bright", 0.25, 290),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen_img2img(sid, master_b64, prompt, neg, seed, creativity, out_path):
    """img2img via SwarmUI mit Master als Init."""
    payload = {
        "session_id": sid, "images": 1, "model": BASE_MODEL,
        "prompt": prompt, "negativeprompt": neg,
        "width": 800, "height": 800, "steps": 28, "cfgscale": 7.0,
        "sampler": "euler_ancestral", "seed": seed,
        "initimage": master_b64, "init_image_creativity": creativity,
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
    with open(out_path, "wb") as f:
        f.write(r2.content)
    return len(r2.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_dataset_v2 (SAUBER, 15 Bilder) ===")
    print(f"Master: {MASTER_PATH}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"")
    print(f"Methode:")
    print(f"  1× Master + 5× echte Winkel (creativity 0.30-0.40) + 10× Mikro-Posen (creativity 0.25)")
    print(f"  Pro Bild individuelle Caption mit Pose-Suffix")
    print(f"")
    print(f"Base-Caption (alle 16):")
    print(f"  {BASE_CAPTION[:200]}...")
    print()

    if not do_submit:
        print("Run with --submit to generate.")
        sys.exit(0)

    os.makedirs(DATASET_DIR, exist_ok=True)

    # Master als base64
    with open(MASTER_PATH, "rb") as f:
        master_b64 = base64.b64encode(f.read()).decode()
    print(f"Master base64: {len(master_b64)} chars")

    sid = get_session()
    print(f"Session: {sid[:16]}...")
    print()

    # 15 Variationen generieren
    for i, (idx_name, pose_suffix, creativity, seed) in enumerate(VARIATIONS):
        out_png = f"{DATASET_DIR}/{idx_name}.png"
        out_txt = f"{DATASET_DIR}/{idx_name}.txt"
        full_prompt = BASE_CAPTION + ", " + pose_suffix
        print(f"[{i+1}/{len(VARIATIONS)}] {idx_name} (seed {seed}, creativity {creativity})")
        print(f"  Pose: {pose_suffix[:80]}")

        try:
            size = gen_img2img(sid, master_b64, full_prompt, NEG, seed, creativity, out_png)
            print(f"  ✓ {out_png} ({size//1024} KB)")

            # Caption mit Pose-Suffix schreiben (für LoRA-Training: lernt Pose-Variation)
            with open(out_txt, "w") as f:
                f.write(full_prompt + "\n")
            print(f"  ✓ {out_txt}")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print()
    print(f"=== FERTIG — Dataset bereit für LoRA-Training ===")
    n_pngs = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".png")])
    n_txts = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".txt")])
    print(f"  Bilder:  {n_pngs}")
    print(f"  Captions: {n_txts}")
    print()
    print("User-Bewertung: Dataset in assets/training/katharina_char_v1/images/")
