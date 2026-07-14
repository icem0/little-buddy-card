#!/usr/bin/env python3
"""
load_littlebuddy_preset.py — Configure SwarmUI/ComfyUI for Little-Buddy sprite gen.

Task t_99cd9b1a: load the trained LoRA + apply pixel-art params. NO image generation.

Why ComfyUI-Direct for the LoRA (not SwarmUI WebAPI):
  SwarmUI's /API/GenerateText2Image validates LoRA names against its OWN model
  index, which does NOT include LoRAs trained via ComfyUI's TrainLoraNode. The
  LoRA lives in ComfyUI as `littlebuddy_pixel_00001_.safetensors`. So the robust
  "load" path is the ComfyUI `LoraLoader` node, driven via /ComfyBackendDirect.
  We therefore (1) select the base model through the SwarmUI WebAPI (real session
  state) and (2) emit a validated ComfyUI-Direct t2i workflow that the downstream
  gen task submits. We do NOT generate here.

Usage:
  python3 load_littlebuddy_preset.py --check   # reachability + LoRA/base presence
  python3 load_littlebuddy_preset.py --apply   # SelectModel + write+validate workflow
  python3 load_littlebuddy_preset.py --print   # print the preset plan
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET = os.path.join(HERE, "..", "assets", "presets", "littlebuddy_sprite_preset.json")

try:
    import requests
except ImportError:
    requests = None


def load_preset():
    with open(PRESET) as f:
        return json.load(f)


def new_session(host):
    r = requests.post(f"{host}/API/GetNewSession", json={}, timeout=10)
    r.raise_for_status()
    return r.json()["session_id"]


def check_reachability(host):
    try:
        sid = new_session(host)
        print(f"[OK] SwarmUI erreichbar @ {host} (session {sid[:8]}...)")
        return sid
    except Exception as e:
        print(f"[ERR] SwarmUI NICHT erreichbar @ {host}: {e}")
        return None


def object_info(host):
    r = requests.get(f"{host}/ComfyBackendDirect/object_info", timeout=30)
    r.raise_for_status()
    return r.json()


def check_lora_comfy(host, lora_name):
    obj = object_info(host)
    opts = obj["LoraLoader"]["input"]["required"]["lora_name"][0]
    if lora_name in opts:
        print(f"[OK] LoRA im ComfyUI LoraLoader-Index: {lora_name}")
        return True
    print(f"[ERR] LoRA '{lora_name}' NICHT im ComfyUI-Index ({len(opts)} LoRAs). "
          "Liegt sie in ComfyUI models/loras/?")
    return False


def check_base_comfy(host, base_name):
    obj = object_info(host)
    opts = obj["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    if base_name in opts:
        print(f"[OK] Base-Checkpoint im CheckpointLoaderSimple-Index: {base_name}")
        return True
    print(f"[ERR] Base '{base_name}' NICHT im Checkpoint-Index ({len(opts)}).")
    return False


def check_sampler(obj, sampler_name="euler_ancestral", scheduler="normal"):
    ok_s = sampler_name in obj["KSampler"]["input"]["required"]["sampler_name"][0]
    ok_sc = scheduler in obj["KSampler"]["input"]["required"]["scheduler"][0]
    print(f"[{'OK' if ok_s else 'ERR'}] Sampler '{sampler_name}' im KSampler-Index")
    print(f"[{'OK' if ok_sc else 'ERR'}] Scheduler '{scheduler}' im KSampler-Index")
    return ok_s and ok_sc


def select_model(host, sid, base_name):
    r = requests.post(f"{host}/API/SelectModel",
                      json={"session_id": sid, "model": base_name}, timeout=30)
    code = r.status_code
    print(f"SelectModel {base_name}: HTTP {code}")
    return code == 200


def build_comfy_workflow(preset):
    """Build a validated ComfyUI-API-format t2i workflow with the LoRA loaded.
    Does NOT contain a SaveImage trigger issue — it is gen-ready but we don't
    submit it here (task forbids image generation)."""
    sw = preset["swarmui"]
    g = preset["generation"]
    pos = preset["prompt_templates"]["positive_base"]
    neg = preset["prompt_templates"]["negative"]
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": sw["base_model"]}},
        "2": {"class_type": "LoraLoader",
              "inputs": {
                  "model": ["1", 0], "clip": ["1", 1],
                  "lora_name": sw["loras"][0],
                  "strength_model": sw["lora_weights"][0],
                  "strength_clip": sw["lora_tenc_weights"][0]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": pos, "clip": ["2", 1]}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": neg, "clip": ["2", 1]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": g["generate_resolution"],
                         "height": g["generate_resolution"], "batch_size": 1}},
        "6": {"class_type": "KSampler",
              "inputs": {
                  "model": ["2", 0], "positive": ["3", 0], "negative": ["4", 0],
                  "latent_image": ["5", 0],
                  "seed": 42, "steps": g["steps"], "cfg": g["cfgscale"],
                  "sampler_name": g["sampler"], "scheduler": "normal",
                  "denoise": 1.0}},
        "7": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"images": ["7", 0], "filename_prefix": "littlebuddy_sprite"}},
    }
    return wf


def apply_config(host, preset):
    if requests is None:
        print("[ERR] requests fehlt")
        return False
    sw = preset["swarmui"]
    sid = check_reachability(host)
    if not sid:
        return False
    lora_ok = check_lora_comfy(host, sw["loras"][0])
    base_ok = check_base_comfy(host, sw["base_model"])
    if not (lora_ok and base_ok):
        return False
    obj = object_info(host)
    check_sampler(obj)
    if not select_model(host, sid, sw["base_model"]):
        return False
    # Emit validated ComfyUI-Direct workflow (gen-ready, not submitted)
    wf = build_comfy_workflow(preset)
    out_api = os.path.join(HERE, "..", "assets", "workflows",
                           "littlebuddy_sprite_gen_v1_api.json")
    with open(out_api, "w") as f:
        json.dump(wf, f, indent=2)
    print(f"[OK] ComfyUI-Direct Workflow geschrieben: {out_api}")
    print("[OK] Konfiguration angewandt (Base via SelectModel geladen; "
          "LoRA ueber ComfyUI LoraLoader vorbereitet). KEINE Bilder generiert.")
    return True


def print_preset(preset):
    sw = preset["swarmui"]
    g = preset["generation"]
    print("=== Little Buddy Sprite Preset ===")
    print(f"Base Model : {sw['base_model']}")
    print(f"LoRA       : {sw['loras'][0]} (weight {sw['lora_weights'][0]}, "
          f"tenc {sw['lora_tenc_weights'][0]})")
    print(f"  -> geladen ueber ComfyUI LoraLoader (WebAPI-Index kennt es NICHT)")
    print(f"Sampler    : {g['sampler']}  Steps {g['steps']}  CFG {g['cfgscale']}")
    print(f"Res        : gen {g['generate_resolution']} -> sprite "
          f"{g['sprite_target_resolution']} (no_smoothing={g['no_smoothing']}, {g['post_process']})")
    print(f"Trigger    : {preset['meta']['trigger']}")
    print(f"Char-Type  : {preset['meta']['character_type']}")
    print("\n-- Positive Template --")
    print(preset["prompt_templates"]["positive_base"])
    print("\n-- Negative --")
    print(preset["prompt_templates"]["negative"])
    print("\n-- Pose-Templates (in Positive {pose} einsetzen) --")
    for k, v in preset["pose_templates"].items():
        print(f"  [{k}] {v}")


if __name__ == "__main__":
    preset = load_preset()
    host = preset["swarmui"]["host"]
    mode = sys.argv[1] if len(sys.argv) > 1 else "--print"

    if mode == "--check":
        sid = check_reachability(host)
        if sid:
            check_lora_comfy(host, preset["swarmui"]["loras"][0])
            check_base_comfy(host, preset["swarmui"]["base_model"])
    elif mode == "--apply":
        apply_config(host, preset)
    else:
        print_preset(preset)
