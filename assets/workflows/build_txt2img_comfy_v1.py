#!/usr/bin/env python3
"""
txt2img via ComfyUI Direct — Katharina Character Set (v1)
Uses LoraLoader node (bypasses SwarmUI API LoRA validation).

Same strategy as build_txt2img_set.py but ComfyUI-native:
- CheckpointLoaderSimple (RDXL_Pixel_Art base)
- LoraLoader (littlebuddy_pixel)
- CLIPTextEncode + KSampler + VAEDecode + SaveImage
- 800x800

Usage:
    python3 build_txt2img_comfy_v1.py            # save workflow only
    python3 build_txt2img_comfy_v1.py --submit   # generate
    python3 build_txt2img_comfy_v1.py --submit --seed 42  # single test
"""

import requests
import json
import sys
import os
import time
import urllib.parse

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/training/candidate_set"
WF_DIR = "/root/little-buddy-card/assets/workflows"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
CHAR_LORA = "littlebuddy_pixel_00001_.safetensors"
VERSION = "v1"
WF_NAME = f"katharina_txt2img_{VERSION}"

POSES = [
    "standing on the ground, both feet planted, idle pose, arms at sides",
    "standing, weight shifted to one foot, slight head tilt, calm pose",
    "sitting on a small stool, hands in lap, relaxed",
    "standing, one hand raised waving, gentle smile",
    "standing, both arms slightly out for balance, soft stance",
    "turned slightly to the side, three-quarter view, casual",
    "standing, looking up with curious expression, hands behind back",
    "standing, gentle hop mid-air, both feet barely off ground",
]

INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii girl, "
    "blonde hair in two long braids, simple red polka-dotted dress, "
    "white socks, black mary jane shoes, "
    "big round innocent eyes, sweet innocent, white background, masterpiece, highly detailed"
)

NEGATIVE = (
    "muted, blurry, deformed, fighting, action pose, multiple girls, adult, "
    "schürze, pinafore, apron, uniform, school uniform, collar, puffy sleeves, "
    "holding object, book, picture, frame, paper, sign, prop, "
    "handbag, bag, purse, cross, crucifix, religious, kruzifix, "
    "nurse, costume, wings, halo, tail, animal ears, fantasy, "
    "white dress, blue dress, green dress, bun, ponytail, short hair, "
    "black hair, brown hair, blue hair, pink hair, folk pattern, ornaments, "
    "decorative, busy background, complex details"
)


def build_workflow(pose_suffix, seed, lora_weight=0.8):
    """Build ComfyUI API-format workflow with LoraLoader."""
    prompt = f"{INSTANCE_PROMPT}, {pose_suffix}"
    wf = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": BASE_MODEL},
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": CHAR_LORA,
                "strength_model": lora_weight,
                "strength_clip": lora_weight,
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 1]},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": NEGATIVE, "clip": ["2", 1]},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 800, "height": 800, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": 28,
                "cfg": 7.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": "katharina_set"},
        },
    }
    return wf


def build_ui_format(pose_suffix, seed, lora_weight=0.8):
    """Build ComfyUI UI-format workflow (visible in Workflows tab)."""
    try:
        obj_info = requests.get(f"{HOST}/ComfyBackendDirect/object_info", timeout=10).json()
    except:
        obj_info = {}

    prompt = f"{INSTANCE_PROMPT}, {pose_suffix}"

    # Node definitions: (id, class_type, title, inputs, pos)
    NODES = [
        (1, "CheckpointLoaderSimple", "Load Base Model (RDXL Pixel Art)", {"ckpt_name": BASE_MODEL}, [0, 0]),
        (2, "LoraLoader", f"Load Character LoRA ({CHAR_LORA})", {
            "model": [1, 0], "clip": [1, 1], "lora_name": CHAR_LORA,
            "strength_model": lora_weight, "strength_clip": lora_weight,
        }, [0, 200]),
        (3, "CLIPTextEncode", "Encode Positive Prompt", {"text": prompt, "clip": [2, 1]}, [350, 0]),
        (4, "CLIPTextEncode", "Encode Negative Prompt", {"text": NEGATIVE, "clip": [2, 1]}, [350, 200]),
        (5, "EmptyLatentImage", "Empty Latent (800x800)", {"width": 800, "height": 800, "batch_size": 1}, [350, 400]),
        (6, "KSampler", "Sample (28 steps, euler_ancestral)", {
            "model": [2, 0], "positive": [3, 0], "negative": [4, 0], "latent_image": [5, 0],
            "seed": seed, "steps": 28, "cfg": 7.5, "sampler_name": "euler_ancestral",
            "scheduler": "normal", "denoise": 1.0,
        }, [700, 200]),
        (7, "VAEDecode", "Decode Latent → Image", {"samples": [6, 0], "vae": [1, 2]}, [1050, 200]),
        (8, "SaveImage", "Save Image (katharina_set)", {"images": [7, 0], "filename_prefix": "katharina_set"}, [1050, 400]),
    ]

    ui_nodes = []
    links = []
    link_id = 0

    for nid, class_type, title, inputs, pos in NODES:
        schema = obj_info.get(class_type, {})
        req = schema.get("input", {}).get("required", {})
        input_order = schema.get("input_order", {})
        ordered = input_order.get("required", []) + input_order.get("optional", [])

        ui_node = {
            "id": nid, "type": class_type, "pos": list(pos),
            "size": {"0": 300, "1": 130}, "flags": {}, "order": nid, "mode": 0,
            "inputs": [], "outputs": [], "properties": {"Node name for S&R": class_type},
            "widgets_values": [], "title": title,
        }

        # outputs
        for oi, (otype, oname) in enumerate(zip(
            schema.get("output", []), schema.get("output_name", []))):
            ui_node["outputs"].append({"name": oname, "type": otype, "links": [], "slot_index": oi})

        # widgets_values in input_order (KSampler needs control_after_generate)
        for wname in ordered:
            if wname in inputs and isinstance(inputs[wname], list) and len(inputs[wname]) == 2 and isinstance(inputs[wname][0], (str, int)):
                continue  # connection
            if class_type == "KSampler" and wname == "seed":
                ui_node["widgets_values"].append(inputs.get("seed", 0))
                ui_node["widgets_values"].append("fixed")
                continue
            if wname not in inputs:
                continue
            ui_node["widgets_values"].append(inputs[wname])

        # connections
        for iname, val in inputs.items():
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], (str, int)):
                link_id += 1
                src = val[0] if isinstance(val[0], int) else int(val[0])
                slot = val[1]
                type_name = req.get(iname, ["WILDCARD"])[0] if isinstance(req.get(iname, ["WILDCARD"]), list) else "WILDCARD"
                ui_node["inputs"].append({"name": iname, "type": type_name, "link": link_id})
                links.append([link_id, src, slot, nid, len(ui_node["inputs"]) - 1, type_name])

        ui_nodes.append(ui_node)

    # groups
    groups = [{
        "id": 1, "title": f"Katharina txt2img {VERSION} — RDXL Pixel Art + littlebuddy LoRA",
        "bounding": [0, 0, 1400, 700], "color": "#581c87", "font_size": 24, "flags": {"collapsed": False},
    }]

    return {
        "id": WF_NAME, "revision": 0, "last_node_id": 8, "last_link_id": link_id,
        "nodes": ui_nodes, "links": links, "groups": groups,
        "definitions": {"subgraphs": []}, "config": {},
        "extra": {"ds": {"scale": 0.8, "offset": [0, 0]}}, "version": 0.4,
    }


def save_to_comfyui(ui_wf, name=WF_NAME):
    """Save UI-format workflow to ComfyUI Workflows tab."""
    file_path = urllib.parse.quote(f"workflows/{name}.json", safe="")
    data = json.dumps(ui_wf, indent=2).encode("utf-8")
    r = requests.post(
        f"{HOST}/ComfyBackendDirect/userdata/{file_path}",
        data=data, headers={"Content-Type": "application/octet-stream"}, timeout=10)
    return r.status_code, r.text


def submit(wf):
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt",
                      json={"prompt": wf}, timeout=30)
    if r.status_code == 200:
        return r.json().get("prompt_id")
    raise Exception(f"Submit failed: {r.status_code} {r.text[:200]}")


def poll(prompt_id, timeout=180):
    for i in range(timeout // 5):
        time.sleep(5)
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=10)
        if r.status_code == 200:
            hist = r.json()
            if prompt_id in hist:
                return hist[prompt_id].get("outputs", {})
    return None


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    single_seed = None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--seed" and i + 1 < len(sys.argv[1:]):
            single_seed = int(sys.argv[1:][i + 1])

    os.makedirs(OUT_DIR, exist_ok=True)

    # ALWAYS save workflow (UI + API + ComfyUI tab) — versioned, never overwritten
    print(f"=== Saving {WF_NAME} (always, versioned) ===")
    ui_wf = build_ui_format(POSES[0], 42)
    api_wf = build_workflow(POSES[0], 42)

    # Local files
    with open(os.path.join(WF_DIR, f"{WF_NAME}_api.json"), "w") as f:
        json.dump(api_wf, f, indent=2)
    with open(os.path.join(WF_DIR, f"{WF_NAME}_ui.json"), "w") as f:
        json.dump(ui_wf, f, indent=2)
    print(f"  Local: {WF_NAME}_api.json + {WF_NAME}_ui.json")

    # ComfyUI Workflows tab
    code, body = save_to_comfyui(ui_wf)
    print(f"  ComfyUI tab: {code} {body[:80]}")

    if not do_submit:
        print(f"\nPlan: {len(POSES)} poses × 800×800, ComfyUI-direct + LoRA")
        print(f"Base: {BASE_MODEL}")
        print(f"LoRA: {CHAR_LORA}")
        for i, p in enumerate(POSES):
            print(f"  [{i}] {p[:60]}...")
        print("\nRun with --submit to generate.")
        sys.exit(0)

    if single_seed is not None:
        wf = build_workflow(POSES[0], single_seed)
        pid = submit(wf)
        print(f"Submitted: {pid}")
        out = poll(pid)
        if out:
            for nid, nout in out.items():
                if "images" in nout:
                    for img in nout["images"]:
                        print(f"  Image: {img['filename']}")
        else:
            print("  ✗ Timeout")
    else:
        for i, pose in enumerate(POSES):
            seed = 1000 + i * 7
            print(f"[{i+1}/{len(POSES)}] Pose {i} (seed {seed})...")
            wf = build_workflow(pose, seed)
            try:
                pid = submit(wf)
                out = poll(pid)
                if out:
                    for nid, nout in out.items():
                        if "images" in nout:
                            for img in nout["images"]:
                                print(f"  ✓ {img['filename']}")
                else:
                    print(f"  ✗ Timeout")
            except Exception as e:
                print(f"  ✗ {e}")
            time.sleep(1)
        print(f"\n✅ Set complete")
