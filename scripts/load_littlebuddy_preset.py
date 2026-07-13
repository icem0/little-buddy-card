#!/usr/bin/env python3
"""
load_littlebuddy_preset.py — Wendet das Little-Buddy-Sprite-Preset auf SwarmUI an.

Task t_99cd9b1a: LoRA laden + Prompt-Templates + Pixel-Art-Parameter setzen.
Generiert KEINE Bilder (nur Konfiguration / "Load"-Schritt).

Usage:
    python3 load_littlebuddy_preset.py --check     # nur SwarmUI-Reachability + LoRA-Status
    python3 load_littlebuddy_preset.py --apply     # Model+LoRA+Params via API setzen
    python3 load_littlebuddy_preset.py --print     # Preset als Text ausgeben (Plan)

Die Templates (Prompt/Pose) werden als Rueckgabe ausgegeben, damit sie in die
SwarmUI-Prompt-Felder kopiert werden koennen (WebUI hat keinen direkten Set-Prompt-API-Call
ausser ueber GenerateText2Image, welches hier NICHT ausgeloest wird).
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


def check_reachability(host):
    if requests is None:
        print("[ERR] requests nicht installiert")
        return False
    try:
        r = requests.post(f"{host}/API/GetNewSession", json={}, timeout=8)
        if r.status_code == 200 and "session_id" in r.json():
            print(f"[OK] SwarmUI erreichbar @ {host}")
            return r.json()["session_id"]
        print(f"[WARN] SwarmUI antwortet nicht korrekt: {r.status_code} {r.text[:120]}")
        return False
    except Exception as e:
        print(f"[ERR] SwarmUI NICHT erreichbar @ {host}: {e}")
        return False


def check_lora(host, session, lora_name):
    r = requests.post(f"{host}/API/ListModels",
                      json={"session_id": session, "path": "", "depth": 10,
                            "subtype": "LoRA", "allowRemote": False}, timeout=15)
    data = r.json()
    found = []
    # ListModels liefert verschachtelte Struktur; wir sammeln alle .safetensors
    def walk(node):
        if isinstance(node, dict):
            name = node.get("name", "")
            if name.endswith(".safetensors"):
                found.append(name)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(data)
    if lora_name in found:
        print(f"[OK] LoRA im SwarmUI-Index: {lora_name}")
        return True
    print(f"[WARN] LoRA '{lora_name}' NICHT im SwarmUI-Index ({len(found)} LoRAs gescannt).")
    print("       -> Physisch in ComfyUI models/loras/ legen ODER ComfyUI-Direct (build_*.py) nutzen.")
    return False


def apply_config(host, preset):
    if requests is None:
        print("[ERR] requests fehlt")
        return False
    sess = check_reachability(host)
    if not sess:
        return False
    sw = preset["swarmui"]
    # Model waehlen
    r = requests.post(f"{host}/API/SelectModel",
                      json={"session_id": sess, "model": sw["base_model"]}, timeout=30)
    print(f"SelectModel {sw['base_model']}: {r.status_code}")
    # LoRA-Status
    check_lora(host, sess, sw["loras"][0])
    print("Config angewandt (Model+LoRA geprueft). Prompt-Templates siehe --print.")
    return True


def print_preset(preset):
    g = preset["generation"]
    print("=== Little Buddy Sprite Preset ===")
    print(f"Base Model : {preset['swarmui']['base_model']}")
    print(f"LoRA       : {preset['swarmui']['loras'][0]} (weight {preset['swarmui']['lora_weights'][0]})")
    print(f"Sampler    : {g['sampler']}  Steps {g['steps']}  CFG {g['cfgscale']}")
    print(f"Res        : gen {g['generate_resolution']} -> sprite {g['sprite_target_resolution']} "
          f"(no_smoothing={g['no_smoothing']}, {g['post_process']})")
    print(f"Trigger    : {preset['trigger']}")
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
        sess = check_reachability(host)
        if sess:
            check_lora(host, sess, preset["swarmui"]["loras"][0])
    elif mode == "--apply":
        apply_config(host, preset)
    else:
        print_preset(preset)
