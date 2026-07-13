#!/usr/bin/env python3
"""
img2img Character-Consistency Workflow v1 — Katharina
Uses LoadImage + VAEEncode + LoRA + KSampler(denoise) for controlled variation.

Strategy (per User 2026-07-10):
- LoadImage (reference) → VAEEncode → latent
- LoraLoader (littlebuddy_pixel) on base model
- KSampler with denoise=0.35-0.5 (low = stays near reference)
- Only pose/view changes, style+clothing locked

Usage:
    python3 build_img2img_consistency_v1.py            # save + show plan
    python3 build_img2img_consistency_v1.py --submit    # generate set
"""

import requests
import json
import sys
import os
import time
import urllib.parse
import base64

HOST = "http://192.168.178.53:7801"
WF_DIR = "/root/little-buddy-card/assets/workflows"
OUT_DIR = "/root/little-buddy-card/assets/training/candidate_set_v2"
REF_IMAGE = "/root/little-buddy-card/assets/training/candidate_set/katharina_fixed_00.png"
BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
CHAR_LORA = "littlebuddy_pixel_00001_.safetensors"
VERSION = "v2"
WF_NAME = f"katharina_img2img_consistency_{VERSION}"

# Pose/view variations (subtle, no action words)
VARIATIONS = [
    "full side profile view, facing left, standing",
    "full side profile view, facing right, standing",
    "back view, looking behind, hands on hips",
    "top-down three-quarter view, looking up",
    "low angle view from below, standing tall",
    "extreme three-quarter turn, almost front-facing",
    "seated cross-legged on floor, hands on knees",
    "crouching low, hands on ground",
]

INSTANCE_PROMPT = (
    "pixel art, katharina character, cute chibi kawaii girl, "
    "blonde hair in two long braids, simple red polka-dotted dress, "
    "white socks, black mary jane shoes, "
    "big round innocent eyes, sweet innocent, white background, masterpiece"
)

NEGATIVE = (
    "muted, blurry, deformed, holding object, book, picture, frame, paper, "
    "pinafore, school uniform, collar, puffy sleeves, multiple girls, adult, "
    "wings, halo, tail, animal ears, fantasy, white dress, blue dress, "
    "bun, ponytail, short hair, black/brown/blue/pink hair"
)

DENOISE = 0.6  # low = stays near reference (style+clothing locked)


def upload_ref():
    """Upload reference image to ComfyUI input dir."""
    with open(REF_IMAGE, "rb") as f:
        r = requests.post(f"{HOST}/ComfyBackendDirect/upload/image",
                         files={"image": ("katharina_ref.png", f, "image/png")}, timeout=30)
    return r.json().get("name", "katharina_ref.png")


def build_workflow(var_suffix, seed, ref_name, denoise=DENOISE):
    prompt = f"{INSTANCE_PROMPT}, {var_suffix}"
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": BASE_MODEL}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "model": ["1", 0], "clip": ["1", 1], "lora_name": CHAR_LORA,
            "strength_model": 0.8, "strength_clip": 0.8}},
        "3": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
        "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["3", 0], "vae": ["1", 2]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 1]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["2", 1]}},
        "7": {"class_type": "KSampler", "inputs": {
            "model": ["2", 0], "positive": ["5", 0], "negative": ["6", 0],
            "latent_image": ["4", 0], "seed": seed, "steps": 28, "cfg": 7.5,
            "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "katharina_consistent"}},
    }


def build_ui_format(var_suffix, seed, ref_name, denoise=DENOISE):
    try:
        obj = requests.get(f"{HOST}/ComfyBackendDirect/object_info", timeout=10).json()
    except:
        obj = {}
    prompt = f"{INSTANCE_PROMPT}, {var_suffix}"
    NODES = [
        (1, "CheckpointLoaderSimple", "Load Base (RDXL Pixel Art)", {"ckpt_name": BASE_MODEL}, [0, 0]),
        (2, "LoraLoader", f"Load LoRA ({CHAR_LORA})", {
            "model": [1, 0], "clip": [1, 1], "lora_name": CHAR_LORA,
            "strength_model": 0.8, "strength_clip": 0.8}, [0, 200]),
        (3, "LoadImage", "Load Reference Image", {"image": ref_name}, [0, 400]),
        (4, "VAEEncode", "Encode Reference → Latent", {"pixels": [3, 0], "vae": [1, 2]}, [350, 400]),
        (5, "CLIPTextEncode", "Positive Prompt", {"text": prompt, "clip": [2, 1]}, [350, 0]),
        (6, "CLIPTextEncode", "Negative Prompt", {"text": NEGATIVE, "clip": [2, 1]}, [350, 200]),
        (7, "KSampler", f"Sample (denoise={denoise})", {
            "model": [2, 0], "positive": [5, 0], "negative": [6, 0], "latent_image": [4, 0],
            "seed": seed, "steps": 28, "cfg": 7.5, "sampler_name": "euler_ancestral",
            "scheduler": "normal", "denoise": denoise}, [700, 200]),
        (8, "VAEDecode", "Decode → Image", {"samples": [7, 0], "vae": [1, 2]}, [1050, 200]),
        (9, "SaveImage", "Save (katharina_consistent)", {"images": [8, 0], "filename_prefix": "katharina_consistent"}, [1050, 400]),
    ]
    ui_nodes, links, link_id = [], [], 0
    for nid, ct, title, inputs, pos in NODES:
        schema = obj.get(ct, {})
        req = schema.get("input", {}).get("required", {})
        order = schema.get("input_order", {})
        ordered = order.get("required", []) + order.get("optional", [])
        node = {"id": nid, "type": ct, "pos": list(pos), "size": {"0": 300, "1": 130},
                "flags": {}, "order": nid, "mode": 0, "inputs": [], "outputs": [],
                "properties": {"Node name for S&R": ct}, "widgets_values": [], "title": title}
        for oi, (ot, on) in enumerate(zip(schema.get("output", []), schema.get("output_name", []))):
            node["outputs"].append({"name": on, "type": ot, "links": [], "slot_index": oi})
        for w in ordered:
            if w in inputs and isinstance(inputs[w], list) and len(inputs[w]) == 2 and isinstance(inputs[w][0], (str, int)):
                continue
            if ct == "KSampler" and w == "seed":
                node["widgets_values"].append(inputs.get("seed", 0))
                node["widgets_values"].append("fixed")
                continue
            if w not in inputs:
                continue
            node["widgets_values"].append(inputs[w])
        for iname, val in inputs.items():
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], (str, int)):
                link_id += 1
                src = val[0] if isinstance(val[0], int) else int(val[0])
                tn = req.get(iname, ["WILDCARD"])[0] if isinstance(req.get(iname, ["WILDCARD"]), list) else "WILDCARD"
                node["inputs"].append({"name": iname, "type": tn, "link": link_id})
                links.append([link_id, src, val[1], nid, len(node["inputs"]) - 1, tn])
        ui_nodes.append(node)
    return {"id": WF_NAME, "revision": 0, "last_node_id": 9, "last_link_id": link_id,
            "nodes": ui_nodes, "links": links,
            "groups": [{"id": 1, "title": f"Katharina img2img Consistency {VERSION}",
                        "bounding": [0, 0, 1400, 700], "color": "#166534", "font_size": 24, "flags": {"collapsed": False}}],
            "definitions": {"subgraphs": []}, "config": {},
            "extra": {"ds": {"scale": 0.8, "offset": [0, 0]}}, "version": 0.4}


def save_to_comfyui(ui_wf, name=WF_NAME):
    fp = urllib.parse.quote(f"workflows/{name}.json", safe="")
    r = requests.post(f"{HOST}/ComfyBackendDirect/userdata/{fp}",
                     data=json.dumps(ui_wf).encode(), headers={"Content-Type": "application/octet-stream"}, timeout=10)
    return r.status_code, r.text


def submit(wf):
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json={"prompt": wf}, timeout=30)
    return r.json().get("prompt_id") if r.status_code == 200 else None


def poll(pid, timeout=180):
    for _ in range(timeout // 5):
        time.sleep(5)
        r = requests.get(f"{HOST}/ComfyBackendDirect/history/{pid}", timeout=10)
        if r.status_code == 200 and pid in r.json():
            return r.json()[pid].get("outputs", {})
    return None


if __name__ == "__main__":
    do_submit = "--submit" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"=== Saving {WF_NAME} ===")
    ref_name = upload_ref()
    print(f"  Ref uploaded: {ref_name}")
    ui_wf = build_ui_format(VARIATIONS[0], 42, ref_name)
    api_wf = build_workflow(VARIATIONS[0], 42, ref_name)
    with open(os.path.join(WF_DIR, f"{WF_NAME}_api.json"), "w") as f:
        json.dump(api_wf, f, indent=2)
    with open(os.path.join(WF_DIR, f"{WF_NAME}_ui.json"), "w") as f:
        json.dump(ui_wf, f, indent=2)
    code, body = save_to_comfyui(ui_wf)
    print(f"  Local + ComfyUI tab ({code}): {body[:80]}")

    if not do_submit:
        print(f"\nPlan: {len(VARIATIONS)} variations × 800×800, denoise={DENOISE}")
        for i, v in enumerate(VARIATIONS):
            print(f"  [{i}] {v}")
        print("\nRun with --submit to generate.")
        sys.exit(0)

    for i, var in enumerate(VARIATIONS):
        seed = 2000 + i * 7
        print(f"[{i+1}/{len(VARIATIONS)}] {var[:50]}... (seed {seed})")
        wf = build_workflow(var, seed, ref_name)
        pid = submit(wf)
        if not pid:
            print("  ✗ Submit failed")
            continue
        out = poll(pid)
        if out:
            for nid, nout in out.items():
                if "images" in nout:
                    for img in nout["images"]:
                        print(f"  ✓ {img['filename']}")
        else:
            print("  ✗ Timeout")
        time.sleep(1)
    print(f"\n✅ Done: {OUT_DIR}")
