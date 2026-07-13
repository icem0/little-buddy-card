#!/usr/bin/env python3
"""
katharina_dataset_v1 — Dataset für Character-LoRA-Training

9 Bilder total:
  - 1× Master v14 (offizielles, 800x800)
  - 8× img2img-Variationen (Mikro-Winkel: leichte Drehung, verschiedene seeds)

Mikro-Winkel-Auswahl (subtil, keine Action):
  - slight 3/4 turn to the right
  - slight 3/4 turn to the left
  - slight tilt head right
  - slight tilt head left
  - looking up slightly
  - looking down slightly
  - standing with weight on left leg
  - standing with weight on right leg

img2img @ creativity 0.30 (niedrig → Master bleibt dominant, nur Mikro-Variation)
"""

import os, sys, time, base64
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
MASTER_PATH = "/root/little-buddy-card/assets/characters/katharina/master/katharina_master.png"
DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"

# Caption für ALLE Bilder (einheitlich, das ist der Char-Trigger)
CAPTION = (
    "pixel art, cute childlike small girl, "
    "(blonde_braids:1.3), "
    "(bright crimson red dress:1.4), (long_dress:1.2), white peter pan collar, "
    "short puffy sleeves, white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "(chibi proportions:1.1), large round head, tiny limbs, "
    "standing straight, both feet planted, both arms at sides, "
    "(neutral gray soft shadow under feet:1.2), "
    "pure white background, no scenery, isolated character, "
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

# 9 ECHTE Winkel-Variationen (Katharina wird GEDREHT)
# img2img @ creativity 0.45-0.55 (höher als Mikro-Pose, damit Drehung erkennbar wird)
VARIATIONS = [
    ("01_master",  None, "master_v14"),  # Master selbst, kein img2img
    ("02_front",       "front view, looking at viewer, facing forward, gentle smile", 100),
    ("03_3quarter_r",  "3/4 view from the right, head turned right, facing camera diagonally", 110),
    ("04_3quarter_l",  "3/4 view from the left, head turned left, facing camera diagonally", 120),
    ("05_side_r",      "side view facing right, profile from the right side, calm expression", 130),
    ("06_side_l",      "side view facing left, profile from the left side, calm expression", 140),
    ("07_back_3q",     "3/4 view from behind, mostly back view, slight head turn to the right, looking over shoulder", 150),
    ("08_back",        "back view, facing away from viewer, back of head, braids visible from behind", 160),
    ("09_low_angle",   "low angle view, looking up at the character, camera below, character taller in frame", 170),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def gen_img2img(sid, master_b64, pose_desc, seed, creativity, out_path):
    """img2img via SwarmUI mit Master als Init + Mikro-Pose-Description."""
    full_prompt = CAPTION + ", " + pose_desc
    payload = {
        "session_id": sid, "images": 1, "model": BASE_MODEL,
        "prompt": full_prompt, "negativeprompt": NEG,
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
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r2.content)
    return len(r2.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_dataset_v1 (9 Bilder für LoRA-Training) ===")
    print(f"Master: {MASTER_PATH}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Method: 1× Master + 8× img2img Mikro-Winkel @ creativity 0.30")
    print(f"Base: {BASE_MODEL}, 800x800, steps 28, cfg 7.0")
    print()
    print("Caption (einheitlich für alle 9 Bilder):")
    print(f"  {CAPTION[:200]}...")
    print()

    if not do_submit:
        print("Run with --submit to generate dataset.")
        sys.exit(0)

    os.makedirs(DATASET_DIR, exist_ok=True)

    # 1) Master kopieren
    master_dst = f"{DATASET_DIR}/01_master.png"
    if not os.path.exists(master_dst) or os.path.getsize(master_dst) < 10000:
        import shutil
        shutil.copy(MASTER_PATH, master_dst)
        print(f"  ✓ Master kopiert: {master_dst}")
    else:
        print(f"  ✓ Master existiert: {master_dst}")

    # 2) Master als base64 für img2img
    with open(MASTER_PATH, "rb") as f:
        master_b64 = base64.b64encode(f.read()).decode()

    # 3) 8 Variationen generieren
    sid = get_session()
    print(f"Session: {sid[:16]}...")

    for i, (idx_name, pose_desc, seed) in enumerate(VARIATIONS):
        if pose_desc is None:
            # Master selbst, schon kopiert
            continue

        out_path = f"{DATASET_DIR}/{idx_name}.png"
        creativity = 0.50  # Mittel: Master bleibt erkennbar, aber Drehung kommt durch
        print(f"\n[{i+1}/9] {idx_name} (seed {seed}, creativity {creativity})")
        print(f"  Pose: {pose_desc[:80]}")

        try:
            size = gen_img2img(sid, master_b64, pose_desc, seed, creativity, out_path)
            print(f"  ✓ {out_path} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)
    print()
    print("=== Caption-Dateien schreiben ===")
    for f_name in sorted(os.listdir(DATASET_DIR)):
        if f_name.endswith(".png"):
            txt_path = os.path.join(DATASET_DIR, f_name.replace(".png", ".txt"))
            with open(txt_path, "w") as f:
                f.write(CAPTION)
            print(f"  ✓ {txt_path}")

    print()
    print(f"=== FERTIG — Dataset bereit für LoRA-Training ===")
    print(f"  {len([f for f in os.listdir(DATASET_DIR) if f.endswith('.png')])} Bilder")
    print(f"  {len([f for f in os.listdir(DATASET_DIR) if f.endswith('.txt')])} Captions")
    print()
    print("NÄCHSTER SCHRITT: LoRA-Training via ComfyUI TrainLoraNode")
    print("  Rank 16, AdamW8bit, lr 1e-4, 1500 steps, ~15 min")
