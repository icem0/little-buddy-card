#!/usr/bin/env python3
"""
katharina_char_turn_v1 -- CharTurn-LoRA direkt für Winkel-Generierung (Phase 4)

KEIN eigenes Training (ComfyUI 0.27.0 cached TrainLoraNode hartnäckig).
Wir nutzen Pony_CharTurn als CHARAKTER-DREH-LoRA:
  - Base: RDXL_Pixel_Art_-_Pony_2
  - CharTurn-LoRA (weight 0.7) via ComfyUI pass-through
  - Master-Prompt + view-spezifische Trigger
  - Output: 6-8 Winkel-Bilder

CharTurn-Trigger-Wörter (aus Author-Doku):
  "turnaround sheet, character design sheet, multiple views, model sheet reference"

WICHTIG: ComfyUI 0.27.0 cached TrainLoraNode, aber NICHT
normale Generation (KSampler/SaveImage). CharTurn als LoRA-Strong
im Generate-Workflow funktioniert.

Cache-Bypass: seed + cfg + steps variieren pro Bild (Quirk #15).
"""

import os, sys, time, random
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
CHARTERN_LORA = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
CHARTERN_WEIGHT = 0.7

DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_charturn_v1"

PROMPT_BASE = (
    "score_9, score_8_up, score_7_up, score_6_up, source_anime, "
    "masterpiece, best quality, amazing quality, "
    "pixel art, cute childlike small girl, "
    "(blonde_braids:1.3), "
    "(bright crimson red dress:1.4), (long_dress:1.2), white peter pan collar, "
    "short puffy sleeves, white knee-high socks, black mary jane shoes, "
    "big round innocent eyes, plump cheeks, sweet innocent smile, "
    "(chibi proportions:1.1), large round head, tiny limbs, "
    "(neutral gray soft shadow under feet:1.2), "
    "pure white background, no scenery, isolated character, "
    "turnaround sheet, character design sheet, multiple views, model sheet reference"
)

NEG = (
    "score_1, score_2, score_3, source_pony, source_furry, source_hentai, "
    "grass, ground, outdoor, ground line, floor, dirt, soil, sand, gravel, "
    "landscape, scenery, environment, platform, pedestal, square, stage, "
    "horizon, sky, trees, plants, flowers, bushes, "
    "green shadow, green tint, blue shadow, colored shadow, tinted shadow, "
    "shorts, mini skirt, crop top, short dress, mini dress, "
    "white dress, blue dress, green dress, yellow dress, black dress, purple dress, pink dress, "
    "folklore, folk, bavarian, dirndl, tracht, costume, wreath, flower crown, "
    "multiple girls, second character, additional character, additional figure, "
    "scaled character, resized character, size difference, "
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

# 6 Winkel für Character-Set
VIEWS = [
    ("v1_front",      "single character, front view, facing forward, looking at viewer"),
    ("v2_3q_right",  "single character, 3/4 view from the right, head turned right"),
    ("v3_3q_left",   "single character, 3/4 view from the left, head turned left"),
    ("v4_side_right", "single character, side view from the right, profile"),
    ("v5_side_left",  "single character, side view from the left, profile"),
    ("v6_back",       "single character, back view, facing away, braids visible from behind"),
]


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def build_workflow(seed, cfg, steps, prompt, neg, filename_prefix):
    """
    CharTurn als LoRA-Strength im Generate-Workflow.
    KSampler (nicht TrainLoraNode) → kein Cache-Bug.
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL}
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": CHARTERN_LORA,
                "strength_model": CHARTERN_WEIGHT,
                "strength_clip": CHARTERN_WEIGHT,
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 1]}
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": neg, "clip": ["2", 1]}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1}
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "denoise": 1.0,
            }
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]}
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": filename_prefix}
        }
    }


def submit_and_wait(workflow, timeout=300):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")
    prompt_id = r.json().get("prompt_id")

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
    raise TimeoutError(f"Prompt {prompt_id} timeout")


def find_output(history):
    outputs = history.get("outputs", {})
    for nid, out in outputs.items():
        if "images" in out:
            for img in out["images"]:
                return img
    return None


def download(img_info, save_to):
    fname = img_info["filename"]
    subfolder = img_info.get("subfolder", "")
    img_type = img_info.get("type", "output")
    params = urllib.parse.urlencode({"filename": fname, "subfolder": subfolder, "type": img_type})
    url = f"{HOST}/ComfyBackendDirect/view?{params}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_char_turn_v1 (CharTurn-LoRA direkt, Phase 4) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"CharTurn-LoRA: {CHARTERN_LORA} (weight {CHARTERN_WEIGHT})")
    print(f"6 Winkel: front, 3/4 right, 3/4 left, side right, side left, back")
    print(f"1024x1024, KSampler (kein TrainLoraNode → kein Cache-Bug)")
    print()

    if not do_submit:
        print("Run with --submit to generate.")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_dir_comfy = "/root/ComfyUI/output"

    for i, (idx_name, view_suffix) in enumerate(VIEWS):
        seed = random.randint(1000, 9999)
        cfg = random.choice([7.0, 7.5, 8.0])
        steps = random.randint(25, 35)
        prefix = f"katharina_charturn_v1_{idx_name}"

        full_prompt = PROMPT_BASE + ", " + view_suffix
        print(f"\n[{i+1}/{len(VIEWS)}] {idx_name}")
        print(f"  View: {view_suffix[:70]}")
        print(f"  seed={seed}, cfg={cfg}, steps={steps}")

        try:
            wf = build_workflow(seed, cfg, steps, full_prompt, NEG, prefix)
            history = submit_and_wait(wf)
            if history is None:
                print(f"  ✗ Cached or empty")
                continue
            img_info = find_output(history)
            if not img_info:
                print(f"  ✗ No image")
                continue
            out_path = os.path.join(OUT_DIR, f"{idx_name}.png")
            size = download(img_info, out_path)
            print(f"  ✓ {out_path} ({size//1024} KB)")
        except Exception as e:
            print(f"  ✗ {e}")
        time.sleep(2)

    print()
    print(f"=== FERTIG ===")
    n = len([f for f in os.listdir(OUT_DIR) if f.endswith(".png")])
    print(f"  {n} Winkel-Bilder: {OUT_DIR}")
