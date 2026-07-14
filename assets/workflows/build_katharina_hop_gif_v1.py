#!/usr/bin/env python3
"""
katharina_hop_gif_v1 -- Katharina hüpft vor Freude (Wan2.2 I2V)

KEIN CharTurn (User will Bewegung, nicht Drehung).
Wan2.2 Image-to-Video: Master als Startframe + "hüpft vor Freude" Prompt
→ animiertes GIF/WEBP.

Pipeline:
  WanVideoModelLoader (Animate-14B)
  LoadWanVideoT5TextEncoder
  WanVideoVAELoader
  LoadImage (Master)
  WanVideoEncode (Startframe → latent)
  Wan22ImageToVideoLatent (timestep/length)
  CLIPTextEncode (WanVideo-Text)
  WanVideoSampler
  WanVideoDecode
  SaveAnimatedWEBP

Cache-Bypass: seed variieren (KSampler/Sampler haben keinen 0.27.0-Cache-Bug)
"""

import os, sys, time, random
import requests
from PIL import Image

HOST = "http://192.168.178.53:7801"
MASTER = "/root/little-buddy-card/assets/characters/katharina/master/katharina_master.png"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/hop_gif_v1"

WAN_MODEL = "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors"
T5_MODEL = "t5xxl_fp16.safetensors"  # fp16 (kein fp8 scaled)
VAE_MODEL = "Wan\\wan_2.1_vae.safetensors"

PROMPT = (
    "pixel art animation of a small cute childlike girl, "
    "blonde braids, bright crimson red dress, white peter pan collar, "
    "white knee-high socks, black mary jane shoes, "
    "jumping up and down with joy, happy bounce, little hop, "
    "arms raised slightly, gleeful expression, sweet smile, "
    "chibi proportions, pure white background, "
    "cute bouncing animation, 8bit pixel art style"
)

NEG = (
    "blurry, low quality, deformed, extra limbs, three legs, "
    "nsfw, nude, multiple characters, background, scenery, "
    "grass, ground, platform, realistic, 3d, photo, "
    "fighting, violence, sad, crying"
)


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def upload_image(img_path):
    """Master zu ComfyUI hochladen für LoadImage."""
    fname = os.path.basename(img_path)
    with open(img_path, "rb") as f:
        files = {"image": (fname, f, "image/png")}
        r = requests.post(f"{HOST}/ComfyBackendDirect/upload/image", files=files, timeout=30)
    if r.status_code == 200:
        return fname
    raise Exception(f"Upload fehlgeschlagen: {r.status_code}")


def build_workflow(seed, steps, cfg, length, master_fname, prefix):
    return {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": WAN_MODEL,
                "base_precision": "fp16",
                "quantization": "disabled",
                "load_device": "main_device",
            }
        },
        "2": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {
                "model_name": T5_MODEL,
                "precision": "fp16",
            }
        },
        "3": {
            "class_type": "WanVideoVAELoader",
            "inputs": {"model_name": VAE_MODEL, "precision": "fp16"}
        },
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": master_fname}
        },
        "5": {
            "class_type": "WanVideoEncode",
            "inputs": {
                "vae": ["3", 0],
                "image": ["4", 0],
                "enable_vae_tiling": False,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 144,
            }
        },
        "6": {
            "class_type": "Wan22ImageToVideoLatent",
            "inputs": {
                "vae": ["3", 0],
                "width": 512,
                "height": 512,
                "length": length,
                "batch_size": 1,
            }
        },
        "7": {
            "class_type": "WanVideoTextEncode",
            "inputs": {
                "positive_prompt": PROMPT,
                "negative_prompt": NEG,
            }
        },
        "9": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": ["1", 0],
                "image_embeds": ["5", 0],  # Startframe-Encode
                "positive": ["7", 0],
                "negative": ["7", 1],
                "latent": ["6", 0],  # I2V-Latent
                "steps": steps,
                "cfg": cfg,
                "shift": 5.0,
                "seed": seed,
                "force_offload": True,
                "scheduler": "unipc",
                "riflex_freq_index": 0,
            }
        },
        "10": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["3", 0],
                "samples": ["9", 0],
                "enable_vae_tiling": True,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 144,
            }
        },
        "11": {
            "class_type": "SaveAnimatedWEBP",
            "inputs": {
                "images": ["10", 0],
                "filename_prefix": prefix,
                "fps": 12,
                "lossless": False,
                "quality": 90,
                "method": "default",
            }
        },
    }


def submit_and_wait(workflow, timeout=900):
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json={"prompt": workflow}, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")
    pid = r.json().get("prompt_id")
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{pid}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if pid in data:
                entry = data[pid]
                if entry.get("status", {}).get("completed"):
                    return entry
                # Error?
                for m in entry.get("status", {}).get("messages", []):
                    if m[0] == "execution_error":
                        raise Exception(f"Execution error: {m[1]}")
        time.sleep(5)
    raise TimeoutError(f"Timeout {pid}")


def find_webp(history):
    for nid, out in history.get("outputs", {}).items():
        if "images" in out:
            for img in out["images"]:
                if img.get("filename", "").endswith(".webp"):
                    return img
    return None


def download(img_info, save_to):
    import urllib.parse
    params = urllib.parse.urlencode({
        "filename": img_info["filename"],
        "subfolder": img_info.get("subfolder", ""),
        "type": img_info.get("type", "output"),
    })
    r = requests.get(f"{HOST}/ComfyBackendDirect/view?{params}", timeout=60)
    r.raise_for_status()
    with open(save_to, "wb") as f:
        f.write(r.content)
    return len(r.content)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_hop_gif_v1 (Wan2.2 I2V: hüpft vor Freude) ===")
    print(f"Wan: {WAN_MODEL}")
    print(f"T5: {T5_MODEL}")
    print(f"VAE: {VAE_MODEL}")
    print(f"Master: {MASTER}")
    print(f"512x512, 16 frames, 12 fps")
    print()

    if not do_submit:
        print("Run with --submit")
        sys.exit(0)

    os.makedirs(OUT_DIR, exist_ok=True)
    print("Master hochladen...")
    master_fname = upload_image(MASTER)
    print(f"  ✓ {master_fname}")

    seed = random.randint(1000, 9999)
    steps = 20
    cfg = 6.0
    length = 16  # 16 Frames
    prefix = f"katharina_hop_v1_{int(time.time())%100000}"

    print(f"\nSeed: {seed}, Steps: {steps}, CFG: {cfg}, Frames: {length}")
    print(f"Submit...")

    try:
        wf = build_workflow(seed, steps, cfg, length, master_fname, prefix)
        history = submit_and_wait(wf)
        img_info = find_webp(history)
        if not img_info:
            print("  ✗ Kein WEBP-Output")
            sys.exit(1)
        out_path = os.path.join(OUT_DIR, "katharina_hop_v1.webp")
        size = download(img_info, out_path)
        print(f"  ✓ {out_path} ({size//1024} KB)")
        print(f"\n=== FERTIG ===")
        print(f"  Katharina hüpft vor Freude: {out_path}")
    except Exception as e:
        print(f"  ✗ {e}")
        sys.exit(1)
