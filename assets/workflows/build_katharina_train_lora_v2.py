#!/usr/bin/env python3
"""
katharina_train_lora_v2 — Korrigierter TrainLoraNode-Workflow

Fixes aus ComfyUI-Source-Code (nodes_train.py):
  - optimizer: "AdamW" (NICHT "AdamW8bit" — das ist kohya-only, INVALID in ComfyUI)
  - rank: 8 (default, kleiner = weniger Memorisier-Kapazität bei 2 Bildern)
  - learning_rate: 0.0005 (ComfyUI default)
  - gradient_checkpointing: True (für VRAM)
  - MakeTrainingDataset Output: [0]=latents, [1]=positive
  - TrainLoraNode: model=["1",0], latents=["3",0], positive=["3",1]

Cache-Bypass: random seed + steps-Variation pro Run
"""

import os, sys, time, random
import requests

HOST = "http://192.168.178.53:7801"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
DATASET_DIR = "/root/little-buddy-card/assets/training/katharina_char_v1/images_v2"
LORA_OUTPUT_DIR = "/root/little-buddy-card/assets/loras"
LORA_NAME = "katharina_char_lora_v1"

RANK = 8
LEARNING_RATE = 0.0005
STEPS = 300  # bei 2 Bildern: weniger = weniger reine Memorisierung
BATCH_SIZE = 1
GRAD_ACCUM = 1
OPTIMIZER = "AdamW"
LOSS_FUNCTION = "MSE"


def get_session():
    r = requests.post(f"{HOST}/API/GetNewSession", json={}, timeout=10)
    return r.json()["session_id"]


def restart_backends():
    """ComfyUI-Cache vollständig leeren.

    KRITISCH: TrainLoraNode-Workflows werden von ComfyUI's
    Cache-Layer gecacht (gleiche Node-Typen = gleicher Hash),
    selbst wenn wir seed/steps/unique-text ändern.

    RestartBackends löscht den Cache komplett → erster Run
    nach Restart ist garantiert un-gecacht.
    """
    sid = get_session()
    r = requests.post(f"{HOST}/API/RestartBackends",
                    json={"session_id": sid}, timeout=30)
    if r.status_code == 200:
        print(f"  ✓ Backends restartet (Cache geleert)")
        return True
    else:
        print(f"  ✗ Restart fehlgeschlagen: {r.status_code}")
        return False


def wait_for_backend(timeout=120):
    """Warte bis ComfyUI wieder bereit ist (längere Timeout, retry bei HTML-Fehler)."""
    import time
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{HOST}/ComfyBackendDirect/system_stats", timeout=3)
            if r.status_code == 200 and '"devices"' in r.text:
                return True
        except:
            pass
        time.sleep(5)
    return False


def build_workflow(seed, steps, lora_prefix, unique_text):
    return {
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
        },
        "5": {
            "class_type": "LoraSave",
            "inputs": {
                "filename_prefix": f"loras/{lora_prefix}",
                "rank": RANK,
                "lora_type": "standard",
                "bias_diff": True,
            }
        },
        # === CACHE-BYPASS: Dummy-Node mit unique Text ===
        # ComfyUI hasht den ganzen Workflow. Ein ConsoleDebug+ mit
        # Zufalls-Text bricht den Hash bei jedem Run.
        "6": {
            "class_type": "ConsoleDebug+",
            "inputs": {"text": unique_text}
        },
    }


def submit_workflow(workflow):
    payload = {"prompt": workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=300)
    if r.status_code != 200:
        raise Exception(f"Submit failed: {r.status_code} {r.text[:300]}")
    return r.json().get("prompt_id")


def check_history(prompt_id):
    r = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get(prompt_id)


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    print(f"=== katharina_train_lora_v2 (KORRIGIERT) ===")
    print(f"Base: {BASE_MODEL}")
    print(f"Dataset: {DATASET_DIR}")
    print(f"LoRA: {LORA_NAME}.safetensors")
    print(f"")
    print(f"Fixes vs v1:")
    print(f"  optimizer: AdamW (war AdamW8bit=INVALID)")
    print(f"  rank: {RANK} (war 16)")
    print(f"  learning_rate: {LEARNING_RATE} (war 1e-4)")
    print(f"  gradient_checkpointing: True (war False)")
    print(f"  MakeTrainingDataset: latents[0], positive[1] (war falsch)")
    print(f"  steps: {STEPS} (bei 2 Bildern: weniger Overfit)")
    print()

    n_imgs = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".png")])
    n_txts = len([f for f in os.listdir(DATASET_DIR) if f.endswith(".txt")])
    print(f"Dataset: {n_imgs} Bilder, {n_txts} Captions")
    if n_imgs < 2 or n_txts < 2:
        print(f"  ⚠ Dataset zu klein!")
        sys.exit(1)

    if not do_submit:
        print("Run with --submit to train.")
        sys.exit(0)

    # Cache-Bypass: random seed + steps-Variation + unique ConsoleDebug+ text
    import datetime
    seed = random.randint(1000, 9999)
    steps = STEPS + random.randint(0, 50)
    lora_prefix = f"{LORA_NAME}_{int(time.time())%100000}"
    unique_text = f"cache_bypass_{datetime.datetime.now().isoformat()}_{random.randint(0, 99999)}"

    print(f"Seed: {seed} (random)")
    print(f"Steps: {steps} (variiert)")
    print(f"Output-Prefix: loras/{lora_prefix}")
    print(f"Unique Text: {unique_text[:50]}")
    print()

    wf = build_workflow(seed, steps, lora_prefix, unique_text)
    print(f"Workflow: {len(wf)} Nodes")

    # === CACHE-BYPASS: Backends restarten (löscht kompletten Cache) ===
    print(f"\nRestartBackends (Cache leeren)...")
    if not restart_backends():
        print(f"  ✗ Restart fehlgeschlagen, trotzdem versuchen")
    if not wait_for_backend():
        print(f"  ⚠ Backend nicht rechtzeitig bereit")

    pid = submit_workflow(wf)
    print(f"Prompt ID: {pid}")
    print(f"Warte auf Training (poll jede 30s)...")

    # Poll
    last_log = 0
    for _ in range(120):  # max 60 min
        time.sleep(30)
        hist = check_history(pid)
        if hist is None:
            continue
        messages = hist.get("status", {}).get("messages", [])
        cached = any(m[0] == "execution_cached" for m in messages)
        completed = hist.get("status", {}).get("completed", False)
        if cached and not completed:
            print(f"  ✗ CACHE-HIT — retry mit neuem seed+text")
            seed = random.randint(1000, 9999)
            steps = STEPS + random.randint(0, 50)
            lora_prefix = f"{LORA_NAME}_{int(time.time())%100000}"
            unique_text = f"cache_bypass_retry_{datetime.datetime.now().isoformat()}_{random.randint(0,99999)}"
            wf = build_workflow(seed, steps, lora_prefix, unique_text)
            pid = submit_workflow(wf)
            print(f"  Neuer Prompt ID: {pid}, seed {seed}")
            continue
        if completed:
            print(f"  ✓ Training fertig")
            outputs = hist.get("outputs", {})
            if outputs:
                for nid, out in outputs.items():
                    for key in ["files", "gifs", "images", "videos"]:
                        if key in out:
                            print(f"  Node {nid} {key}: {out[key]}")
            else:
                print(f"  Keine Outputs in History (LoRA evtl. auf Disk)")
            break
        elapsed = int(time.time() - time.time())  # noop
        print(f"  ... läuft (poll)")

    print()
    print(f"=== CHECK: LoRA-Datei auf Backend ===")
    # Liste LoRAs via SwarmUI
    sid = get_session()
    r = requests.post(f"{HOST}/API/ListModels", json={
        "session_id": sid,
        "path": "loras",
        "depth": 2,
        "subtype": "LoRA"
    }, timeout=10)
    if r.status_code == 200:
        data = r.json()
        files = data.get("files", [])
        matches = [f for f in files if "katharina" in f.get("name", "").lower()]
        for m in matches:
            print(f"  ✓ {m.get('name')}: {m.get('size')} bytes")
    else:
        print(f"  ⚠ ListModels failed: {r.status_code}")
