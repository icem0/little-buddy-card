#!/usr/bin/env python3
"""
katharina_train_lora_v1 — Character-LoRA-Training via ComfyUI TrainLoraNode

Dataset: 9 Bilder (Master + 8 img2img-Winkel) in
         assets/training/katharina_char_v1/images/
         + 9 .txt Captions (konsolidierte Specs)

LoRA-Settings:
  - Rank 16, Alpha 16
  - AdamW8bit, lr 1e-4
  - 1500 steps
  - Dauer: ~15 min auf RTX 4090
  - Output: katharina_char_lora_v1.safetensors

Pipeline:
  LoadCheckpoint → MakeTrainingDataset → TrainLoraNode → LoraSave
  (alles via ComfyUI pass-through, kein externer kohya_ss-Setup nötig)
"""

import os, sys, json, time, urllib.parse, requests

HOST = "http://192.168.178.53:7801"

BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images"
LORA_OUTPUT_DIR = "/root/little-buddy-card/assets/loras"
LORA_NAME = "katharina_char_lora_v1"

# Trainings-Hyperparameter
RANK = 16
ALPHA = 16
LEARNING_RATE = 0.0001  # 1e-4 (kohya SDXL default)
STEPS = 1500
BATCH_SIZE = 1
GRAD_ACCUM = 1
OPTIMIZER = "AdamW8bit"


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def get_lora_save_path():
    """LoraSave filename_prefix — SwarmUI legt Output unter SwarmUI/Output/{prefix}_*.safetensors."""
    return LORA_NAME


def build_train_workflow():
    """ComfyUI pass-through Workflow für LoRA-Training.

    Nodes:
      1: CheckpointLoaderSimple (Base)
      2: LoadImages (Dataset aus Verzeichnis)
      3: MakeTrainingDataset (encode images + captions → latents + conditioning)
      4: TrainLoraNode (model + latents + positive, 1500 steps)
      5: LoraSave (filename_prefix)
    """
    # Build a UNIQUE workflow per call to force cache-bypass
    # Cache-bypass: vary the steps parameter (Quirk #15)
    # ONLY vary parameters that DON'T affect training outcome
    import datetime
    unique_offset = int(datetime.datetime.now().timestamp()) % 100
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    LORA_NAME_UNIQUE = f"{LORA_NAME}_{timestamp}"
    wf = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL}
        },
        "2": {
            "class_type": "LoadImageTextDataSetFromFolder",
            "inputs": {"folder": DATASET_DIR}
        },
        "3": {
            "class_type": "MakeTrainingDataset",
            "inputs": {
                "images": ["2", 0],
                "vae": ["1", 2],
                "clip": ["1", 1],
            }
        },
        "4": {
            "class_type": "TrainLoraNode",
            "inputs": {
                "model": ["1", 0],
                "latents": ["3", 0],
                "positive": ["3", 1],
                "batch_size": BATCH_SIZE,
                "grad_accumulation_steps": GRAD_ACCUM,
                "steps": 1500,
                "learning_rate": LEARNING_RATE,
                "rank": RANK,
                "optimizer": OPTIMIZER,
                "loss_function": "MSE",
                "seed": 42,
                "training_dtype": "bf16",
                "lora_dtype": "bf16",
                "quantized_backward": "None",
                "algorithm": "none",
                "gradient_checkpointing": False,
                "checkpoint_depth": 1,
                "offloading": "none",
                "existing_lora": "none",
                "bucket_mode": "None",
                "bypass_mode": False,
            }
        },
        "5": {
            "class_type": "LoraSave",
            "inputs": {
                "filename_prefix": f"loras/{LORA_NAME_UNIQUE}",
                "rank": RANK,
                "lora_type": "standard",
                "bias_diff": True,
            }
        }
    }
    return wf


def submit_workflow(workflow):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code == 200:
        return r.json().get("prompt_id")
    raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")


def wait_for_prompt(prompt_id, timeout=1800):
    """Warte bis Training fertig (kann 15-20 min dauern)."""
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
        elapsed = int(time.time() - start)
        if elapsed % 60 < 5:  # alle ~60s Status loggen
            print(f"  [{elapsed}s] Training läuft...")
        time.sleep(5)
    raise TimeoutError(f"Training did not finish in {timeout}s")


def find_lora_output(history_entry):
    """LoraSave Output finden (safetensors-Datei)."""
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        # LoraSave kann entweder 'files' oder 'gifs' oder andere keys haben
        for key in ["files", "gifs", "images", "videos"]:
            if key in node_out:
                return node_out[key]
        # Fallback: alle values mit filename
        for v in node_out.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "filename" in v[0]:
                return v
    return None


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    dry_run = "--dry" in sys.argv

    print(f"=== katharina_train_lora_v1 (Character-LoRA-Training) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"LoRA-Output: loras/{LORA_NAME}.safetensors")
    print(f"")
    print(f"Hyperparameter:")
    print(f"  Rank:        {RANK}")
    print(f"  Alpha:       {ALPHA}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Steps:       {STEPS}")
    print(f"  Batch size:  {BATCH_SIZE}")
    print(f"  Grad accum:  {GRAD_ACCUM}")
    print(f"  Optimizer:   {OPTIMIZER}")
    print(f"  Erwartete Dauer: ~15 min auf RTX 4090")

    # Dataset-Check
    n_imgs = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".png")])
    n_txts = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".txt")])
    print(f"")
    print(f"Dataset-Check:")
    print(f"  Bilder:  {n_imgs}")
    print(f"  Captions: {n_txts}")

    if n_imgs < 5 or n_txts < 5:
        print(f"  ⚠ Zu wenig Trainings-Material! Brauche min. 5 Bild-Caption-Pairs.")
        sys.exit(1)

    if not do_submit:
        print(f"")
        print(f"Run with --submit to start training.")
        print(f"Run with --submit --dry for dry-run (submit + cancel).")
        sys.exit(0)

    # Workflow bauen
    wf = build_train_workflow()
    print(f"")
    print(f"Workflow gebaut: {len(wf)} Nodes")

    if dry_run:
        print(f"DRY-RUN: submit und sofort abbrechen")
        pid = submit_workflow(wf)
        print(f"  Prompt ID: {pid}")
        # Sofort interrupt senden
        requests.post(f"{HOST}/ComfyBackendDirect/interrupt", json={})
        print(f"  Interrupt gesendet")
        sys.exit(0)

    # ECHTES TRAINING
    print(f"")
    print(f"=== STARTE TRAINING ===")
    pid = submit_workflow(wf)
    print(f"Prompt ID: {pid}")
    print(f"Warte auf Completion (timeout 30 min)...")

    try:
        history = wait_for_prompt(pid, timeout=1800)
        if history is None:
            print(f"⚠ Training returned without outputs (cache hit or empty)")
            sys.exit(1)
        print(f"")
        print(f"=== TRAINING FERTIG ===")
        print(f"Status: {history.get('status', {}).get('status_str', 'unknown')}")
        lora_out = find_lora_output(history)
        if lora_out:
            print(f"LoRA-Output:")
            for item in lora_out:
                print(f"  {item}")
        else:
            print(f"Keine LoRA-Output-Files in History gefunden.")
            print(f"History outputs:")
            for nid, out in history.get("outputs", {}).items():
                print(f"  Node {nid}: {list(out.keys())}")
    except TimeoutError as e:
        print(f"⚠ Training Timeout: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    print(f"")
    print(f"=== POST-CHECK ===")
    print(f"Suche LoRA-Datei in SwarmUI Output...")
    # SwarmUI output path: View/local/raw/YYYY-MM-DD/loras/katharina_char_lora_v1_*.safetensors
    # Wir können via API nach dem File suchen
    r = requests.get(f"{HOST}/API/ListModels", json={
        "session_id": "ignore",
        "path": "loras",
        "depth": 2,
        "subtype": "LoRA"
    }, timeout=10)
    if r.status_code == 200:
        data = r.json()
        files = data.get("files", [])
        matches = [f for f in files if "katharina" in f.get("name", "").lower()]
        for m in matches:
            print(f"  ✓ {m.get('name', 'unknown')}: {m.get('size', 'unknown')} bytes")
