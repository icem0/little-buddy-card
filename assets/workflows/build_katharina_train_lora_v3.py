#!/usr/bin/env python3
"""
katharina_train_lora_v3 — ComfyUI TrainLoraNode MIT Cache-Umgehung

Cache-Bug-Diagnose:
  - TrainLoraNode-Workflows werden von ComfyUI komplett gecacht
    (execution_cached: nodes: []) selbst bei random seed / steps / unique ConsoleDebug+
  - Ursache: ComfyUI hasht die Node-TYPEN-Struktur, nicht nur Inputs
  - LoadImageTextDataSetFromFolder + MakeTrainingDataset + TrainLoraNode
    = IMMER gleicher Hash

WORKAROUND (dieses Script):
  - KEIN LoadImageTextDataSetFromFolder
  - Stattdessen: pro Bild einzeln LoadImage + CLIPTextEncode
  - Das ändert die Node-Typen → anderer Hash → kein Cache
  - MakeTrainingDataset kriegt 2 separate Image-Inputs + 2 Text-Inputs

ABER: MakeTrainingDataset nimmt nur EIN image + EIN text.
Workaround dafür: Wir trainieren mit NUR 1 Bild (Master) in diesem Pass,
dann ein 2. Pass mit dem 2. Bild. Oder: wir concatenieren.

Einfachste Lösung, die den Cache bricht:
  - Node 1: CheckpointLoaderSimple
  - Node 2: LoadImage (Bild 1)
  - Node 3: CLIPTextEncode (Caption 1)
  - Node 4: LoadImage (Bild 2)
  - Node 5: CLIPTextEncode (Caption 2)
  - Node 6: MakeTrainingDataset mit [2,0] + [4,0] (2 Bilder) — aber API nimmt nur 1
  
→ MakeTrainingDataset nimmt LISTE von Bildern. Wir können mehrere LoadImage
  in eine Liste packen via "image": [["2",0], ["4",0]]

Getestet:结构上 anders als v2 → anderer Hash.
"""

import os, sys, time, random
import requests

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"
LORA_OUTPUT_DIR = "/root/little-buddy-card/assets/loras"
LORA_NAME = "katharina_char_lora_v1"

RANK = 8
LEARNING_RATE = 0.0005
STEPS = 300
BATCH_SIZE = 1
GRAD_ACCUM = 1
OPTIMIZER = "AdamW"
LOSS_FUNCTION = "MSE"


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def load_images_and_captions(folder):
    """Lädt alle PNG + TXT-Paare aus dem Ordner."""
    images = []
    captions = []
    for f in sorted(os.listdir(folder)):
        if f.endswith(".png"):
            img_path = os.path.join(folder, f)
            txt_path = img_path.replace(".png", ".txt")
            if os.path.exists(txt_path):
                images.append(img_path)
                with open(txt_path) as tf:
                    captions.append(tf.read().strip())
    return images, captions


def build_multi_image_workflow(images, captions, seed, steps, lora_prefix):
    """Workflow mit separaten LoadImage/CLIPTextEncode pro Bild.

    Cache-Bypass: Node-Struktur ist ANDERS als v2
    (kein LoadImageTextDataSetFromFolder mehr).
    """
    wf = {}
    wf["1"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": BASE_MODEL}
    }

    # Pro Bild: LoadImage + CLIPTextEncode
    img_nodes = []
    pos_nodes = []
    neg_nodes = []
    node_id = 2
    for i, (img_path, cap) in enumerate(zip(images, captions)):
        # Bild via SwarmUI-Upload (base64) oder ComfyUI LoadImage (Pfad)
        # Wir nutzen "LoadImage" mit filename (Pfad relativ zu ComfyUI input)
        # ComfyUI erwartet Pfad unter ComfyUI/input/ — wir kopieren dorthin
        wf[str(node_id)] = {
            "class_type": "LoadImage",
            "inputs": {"image": os.path.basename(img_path)}
        }
        img_nodes.append([str(node_id), 0])

        wf[str(node_id + 1)] = {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": cap, "clip": ["1", 1]}
        }
        pos_nodes.append([str(node_id + 1), 0])

        node_id += 2

    # Negativ (einmal)
    wf[str(node_id)] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "bad quality, blurry, deformed", "clip": ["1", 1]}
    }
    neg_node = [str(node_id), 0]
    node_id += 1

    # MakeTrainingDataset mit ALLEN Bildern + Positiv-Conditionings
    # API: images = Liste von [node, 0], texts = Liste von [node, 0]
    wf[str(node_id)] = {
        "class_type": "MakeTrainingDataset",
        "inputs": {
            "images": img_nodes,   # Liste von Image-Inputs
            "positive": pos_nodes,  # Liste von Conditioning-Inputs
            "vae": ["1", 2],
            "clip": ["1", 1],
        }
    }
    dataset_node = str(node_id)
    node_id += 1

    # TrainLoraNode
    wf[str(node_id)] = {
        "class_type": "TrainLoraNode",
        "inputs": {
            "model": ["1", 0],
            "latents": [dataset_node, 0],
            "positive": [dataset_node, 1],
            "negative": neg_node,
            "batch_size": BATCH_SIZE,
            "grad_accumulation_steps": GRAD_ACCUM,
            "steps": steps,
            "learning_rate": LEARNING_RATE,
            "rank": RANK,
            "optimizer": OPTIMIZER,
            "loss_function": LOSS_FUNCTION,
            "seed": seed,
            "training_dtype": "bf16",
            "lora_dtype": "bf16",
            "quantized_backward": "None",
            "algorithm": "none",
            "gradient_checkpointing": True,
            "checkpoint_depth": 1,
            "offloading": "none",
            "existing_lora": "none",
            "bucket_mode": "None",
            "bypass_mode": False,
        }
    }
    train_node = str(node_id)
    node_id += 1

    # LoraSave
    wf[str(node_id)] = {
        "class_type": "LoraSave",
        "inputs": {
            "filename_prefix": f"loras/{lora_prefix}",
            "rank": RANK,
            "lora_type": "standard",
            "bias_diff": True,
        }
    }

    return wf


def upload_images_to_comfyui(images, sid):
    """Kopiert Bilder in ComfyUI's input-Verzeichnis (für LoadImage)."""
    # ComfyUI input-Pfad: wir müssen via API-Upload
    for img_path in images:
        fname = os.path.basename(img_path)
        # Upload via SwarmUI-Input-Endpoint oder ComfyUI-Upload
        # ComfyUI: POST /ComfyBackendDirect/upload/image
        with open(img_path, "rb") as f:
            files = {"image": (fname, f, "image/png")}
            r = requests.post(f"{HOST}/ComfyBackendDirect/upload/image",
                           files=files, timeout=30)
        if r.status_code == 200:
            print(f"  ✓ Upload: {fname}")
        else:
            print(f"  ✗ Upload fehlgeschlagen: {fname} ({r.status_code})")


def submit_workflow(wf):
    payload = {"prompt": wf}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")
    return r.json().get("prompt_id")


def wait_and_check(pid, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{pid}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if pid in data:
                entry = data[pid]
                msgs = entry.get("status", {}).get("messages", [])
                cached = any(m[0] == "execution_cached" for m in msgs)
                completed = entry.get("status", {}).get("completed", False)
                if cached and not completed:
                    print(f"  ⚠ CACHE-HIT erkannt")
                    return "cached"
                if completed:
                    return entry
        time.sleep(5)
    return None


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_train_lora_v3 (Cache-Umgehung: separate LoadImage pro Bild) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Rank: {RANK}, Steps: {STEPS}, LR: {LEARNING_RATE}, Optimizer: {OPTIMIZER}")
    print()

    images, captions = load_images_and_captions(DATASET_DIR)
    print(f"Geladene Bilder: {len(images)}")
    for i, (img, cap) in enumerate(zip(images, captions)):
        print(f"  [{i+1}] {os.path.basename(img)}: {len(cap)} Zeichen Caption")

    if len(images) < 1:
        print("✗ Keine Bilder gefunden!")
        sys.exit(1)

    if not do_submit:
        print("\nRun mit --submit zum Training.")
        sys.exit(0)

    # Bilder hochladen
    print(f"\n=== Bilder zu ComfyUI hochladen ===")
    sid = get_session()
    upload_images_to_comfyui(images, sid)
    time.sleep(2)

    # Seed + Steps variieren für Cache-Bypass
    seed = random.randint(1000, 9999)
    steps = STEPS + random.randint(0, 50)
    lora_prefix = f"{LORA_NAME}_v3_{int(time.time()) % 100000}"

    print(f"\nSeed: {seed}, Steps: {steps}, Prefix: loras/{lora_prefix}")

    wf = build_multi_image_workflow(images, captions, seed, steps, lora_prefix)
    print(f"Workflow: {len(wf)} Nodes (strukturell anders als v2 → kein Cache)")

    pid = submit_workflow(wf)
    print(f"Prompt ID: {pid}")
    print(f"Warte auf Training...")

    result = wait_and_check(pid)
    if result == "cached":
        print(f"⚠ Immer noch Cache-Hit — Cache-Bug ist hartnäckiger als erwartet")
    elif result is None:
        print(f"⚠ Timeout")
    else:
        print(f"✓ Training abgeschlossen")
        outputs = result.get("outputs", {})
        if outputs:
            print(f"Outputs: {list(outputs.keys())}")
        else:
            print(f"Keine Outputs (LoRA auf Disk)")

    # LoRA auf Backend suchen
    print(f"\n=== LoRA-Check ===")
    r = requests.post(f"{HOST}/API/ListModels",
                   json={"session_id": sid, "path": "loras", "depth": 2, "subtype": "LoRA"},
                   timeout=10)
    if r.status_code == 200:
        files = r.json().get("files", [])
        matches = [f for f in files if "katharina" in f.get("name", "").lower()]
        if matches:
            for m in matches:
                print(f"  ✓ {m.get('name')}: {m.get('size')} bytes")
        else:
            print(f"  ✗ Keine katharina-LoRA gefunden")
    else:
        print(f"  ✗ ListModels fehlgeschlagen: {r.status_code}")
