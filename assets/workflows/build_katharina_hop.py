#!/usr/bin/env python3
"""
Wan2.2 Animate Workflow Builder — Katharina Hop Animation
Generates clean, human-readable ComfyUI workflows in both API and UI format.

Design principles:
1. Semantic node IDs (not random numbers) — grouped by function
2. _meta.title on every node — human-readable labels in ComfyUI
3. Logical left-to-right positioning: Loaders → Encoders → Generator → Sampler → Output
4. SaveImage instead of SaveVideo — SwarmUI compatible (no CreateVideo/SaveVideo crash)
5. Built from scratch each time — no copy-paste JSON patching (lesson L9)
"""

import json
import urllib.parse
import requests
import sys
import os

HOST = "http://192.168.178.53:7801"

# ═══════════════════════════════════════════════════════════════════════════
# WORKFLOW DEFINITION — single source of truth
# ═══════════════════════════════════════════════════════════════════════════

# Each node: (id, class_type, title, inputs_dict, group, position)
# Groups: "loaders" (left), "encoders" (mid-left), "generator" (center),
#          "sampler" (mid-right), "output" (right)

NODES = [
    # ── LOADERS ──────────────────────────────────────────────────────────────
    (10, "UNETLoader", "Load Wan2.2 Animate Model", {
        "unet_name": "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
        "weight_dtype": "default",
    }, "loaders", (0, 0)),

    (11, "CLIPLoader", "Load umt5 Text Encoder (Wan)", {
        "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "type": "wan",
    }, "loaders", (0, 150)),

    (12, "VAELoader", "Load Wan VAE", {
        "vae_name": "wan_2.1_vae.safetensors",
    }, "loaders", (0, 300)),

    (13, "CLIPVisionLoader", "Load CLIP Vision", {
        "clip_name": "clip_vision_h.safetensors",
    }, "loaders", (0, 450)),

    (14, "LoadImage", "Load Reference Image (Katharina)", {
        "image": "katharina_master.png",
    }, "loaders", (0, 600)),

    # ── ENCODERS ─────────────────────────────────────────────────────────────
    (20, "CLIPVisionEncode", "Encode Reference Image → CLIP Vision", {
        "clip_vision": [13, 0],
        "image": [14, 0],
        "crop": "center",
    }, "encoders", (350, 0)),

    (21, "CLIPTextEncode", "Encode Positive Prompt", {
        "text": "cute chibi kawaii girl with blonde braids in red dress, hopping happily, pixel art style, consistent character design, smooth animation",
        "clip": [11, 0],
    }, "encoders", (350, 200)),

    (22, "CLIPTextEncode", "Encode Negative Prompt", {
        "text": "blurry, deformed, dark, static, no motion, low quality, ugly, watermark, text, jpeg artifacts, frame jitter",
        "clip": [11, 0],
    }, "encoders", (350, 400)),

    # ── GENERATOR ────────────────────────────────────────────────────────────
    (30, "ModelSamplingSD3", "Apply SD3 Sampling Shift", {
        "model": [10, 0],
        "shift": 8,
    }, "generator", (700, 0)),

    (31, "WanAnimateToVideo", "Wan2.2 Animate → Latent Video", {
        "positive": [21, 0],
        "negative": [22, 0],
        "vae": [12, 0],
        "width": 832,
        "height": 480,
        "length": 49,
        "batch_size": 1,
        "continue_motion_max_frames": 5,
        "video_frame_offset": 0,
        "clip_vision_output": [20, 0],
        "reference_image": [14, 0],
    }, "generator", (700, 250)),

    # ── SAMPLER ─────────────────────────────────────────────────────────────
    (40, "KSampler", "Sample Latent (20 steps, uni_pc)", {
        "model": [30, 0],
        "seed": 42,
        "steps": 20,
        "cfg": 5.5,
        "sampler_name": "uni_pc",
        "scheduler": "simple",
        "positive": [31, 0],   # WanAnimateToVideo enriched conditioning
        "negative": [31, 1],   # WanAnimateToVideo enriched conditioning
        "latent_image": [31, 2],  # WanAnimateToVideo raw latent (output[2])
        "denoise": 1.0,
    }, "sampler", (1050, 250)),

    # ── OUTPUT ───────────────────────────────────────────────────────────────
    (50, "VAEDecode", "Decode Latent → Image Frames", {
        "samples": [40, 0],
        "vae": [12, 0],
    }, "output", (1400, 250)),

    (51, "SaveImage", "Save Frames (SwarmUI Compatible)", {
        "images": [50, 0],
        "filename_prefix": "katharina_hop",
    }, "output", (1400, 450)),
]

# ═══════════════════════════════════════════════════════════════════════════
# BUILDER
# ═══════════════════════════════════════════════════════════════════════════

# Group metadata for UI format
GROUPS = {
    "loaders":  {"title": "1. Loaders — Model + CLIP + VAE + Reference Image", "color": "#3f6212"},
    "encoders": {"title": "2. Encoders — CLIP Vision + Text Prompts",          "color": "#1e40af"},
    "generator": {"title": "3. Generator — WanAnimate + ModelSampling",        "color": "#7c2d12"},
    "sampler":   {"title": "4. Sampler — KSampler (uni_pc, 20 steps)",         "color": "#581c87"},
    "output":   {"title": "5. Output — VAE Decode → SaveImage (SwarmUI)",      "color": "#166534"},
}


def build_api_format(nodes, seed=42):
    """Build ComfyUI API format (for /prompt submission).
    
    IMPORTANT: Connection references must use STRING node IDs: ["40", 0] not [40, 0].
    ComfyUI's validate_inputs does prompt[o_id]['class_type'] where o_id comes
    from the connection array — if it's an int, it KeyError's on the string-keyed dict.
    """
    wf = {}
    for nid, class_type, title, inputs, _, _ in nodes:
        # Deep-copy inputs and convert connection refs to string IDs
        node_inputs = {}
        for k, v in inputs.items():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], (str, int)):
                # Connection: [source_node, output_slot] → string ID
                node_inputs[k] = [str(v[0]), v[1]]
            else:
                node_inputs[k] = v
        
        if class_type == "KSampler" and seed is not None:
            node_inputs["seed"] = seed
            
        wf[str(nid)] = {
            "class_type": class_type,
            "inputs": node_inputs,
            "_meta": {"title": title},
        }
    return wf


def build_ui_format(nodes, groups_meta, seed=42):
    """Build ComfyUI UI format (for Workflows tab — visible with positions/groups)."""
    # Fetch object_info for output slot types
    try:
        obj_info = requests.get(f"{HOST}/ComfyBackendDirect/object_info", timeout=10).json()
    except:
        obj_info = {}

    ui_nodes = []
    links = []
    link_id = 0

    for idx, (nid, class_type, title, inputs, group, pos) in enumerate(nodes):
        # Build node
        ui_node = {
            "id": nid,
            "type": class_type,
            "pos": list(pos),
            "size": {"0": 280, "1": 120},
            "flags": {},
            "order": idx,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&R": class_type},
            "widgets_values": [],
            "title": title,
        }

        # Get schema for this node type
        schema = obj_info.get(class_type, {})
        req = schema.get("input", {}).get("required", {})
        opt = schema.get("input", {}).get("optional", {})
        all_inputs = {**req, **opt}

        # Determine output types from schema
        output_types = schema.get("output", [])
        output_names = schema.get("output_name", [])
        for oi, (otype, oname) in enumerate(zip(output_types, output_names)):
            ui_node["outputs"].append({
                "name": oname,
                "type": otype,
                "links": [],
                "slot_index": oi,
            })

        # Process inputs
        for input_name, val in inputs.items():
            if input_name not in all_inputs:
                # Skip if not in schema (e.g. 'device' removed)
                ui_node["widgets_values"].append(val)
                continue

            input_def = all_inputs[input_name]
            is_connection = isinstance(val, list) and len(val) == 2 and isinstance(val[0], (str, int))

            if is_connection:
                # Connection: [source_node_id, source_slot]
                link_id += 1
                source_node_id = val[0] if isinstance(val[0], int) else int(val[0])
                source_slot = val[1]

                type_name = input_def[0] if isinstance(input_def, list) and input_def else "WILDCARD"

                ui_node["inputs"].append({
                    "name": input_name,
                    "type": type_name,
                    "link": link_id,
                })

                links.append([
                    link_id,
                    source_node_id,
                    source_slot,
                    nid,
                    len(ui_node["inputs"]) - 1,
                    type_name,
                ])

                # Also update source node's output links list
                for sn in ui_nodes:
                    if sn["id"] == source_node_id and source_slot < len(sn["outputs"]):
                        sn["outputs"][source_slot]["links"].append(link_id)
                        break
            else:
                # Widget value
                ui_node["widgets_values"].append(val)

        ui_nodes.append(ui_node)

    # Build groups
    ui_groups = []
    for gid, (gkey, gmeta) in enumerate(groups_meta.items()):
        # Find bounding box of nodes in this group
        group_nodes = [(n["pos"][0], n["pos"][1], n["size"]["0"], n["size"]["1"])
                       for n in ui_nodes
                       for _, _, _, _, ng, _ in [next(x for x in nodes if x[0] == n["id"])]
                       if ng == gkey]
        if group_nodes:
            min_x = min(gn[0] for gn in group_nodes) - 20
            min_y = min(gn[1] for gn in group_nodes) - 40
            max_x = max(gn[0] + gn[2] for gn in group_nodes) + 20
            max_y = max(gn[1] + gn[3] for gn in group_nodes) + 20
        else:
            min_x, min_y, max_x, max_y = 0, 0, 300, 200

        ui_groups.append({
            "id": gid + 1,
            "title": gmeta["title"],
            "bounding": [min_x, min_y, max_x - min_x, max_y - min_y],
            "color": gmeta["color"],
            "font_size": 24,
            "flags": {"collapsed": False},
        })

    max_node_id = max(n[0] for n in nodes)
    ui_wf = {
        "id": "katharina_hop_clean",
        "revision": 0,
        "last_node_id": max_node_id,
        "last_link_id": link_id,
        "nodes": ui_nodes,
        "links": links,
        "groups": ui_groups,
        "definitions": {"subgraphs": []},
        "config": {},
        "extra": {"ds": {"scale": 0.8, "offset": [0, 0]}},
        "version": 0.4,
    }
    return ui_wf


def save_to_comfyui(ui_workflow, name="katharina_hop_clean"):
    """Save UI-format workflow to ComfyUI userdata/workflows/ (visible in Workflows tab)."""
    file_path = urllib.parse.quote(f"workflows/{name}.json", safe="")
    data = json.dumps(ui_workflow, indent=2).encode("utf-8")

    r = requests.post(
        f"{HOST}/ComfyBackendDirect/userdata/{file_path}",
        data=data,
        headers={"Content-Type": "application/octet-stream"},
        timeout=10,
    )
    return r.status_code, r.text


def submit_workflow(api_workflow, seed=42):
    """Submit API-format workflow to ComfyUI /prompt endpoint."""
    # Override seed
    for nid, node in api_workflow.items():
        if node["class_type"] == "KSampler":
            node["inputs"]["seed"] = seed

    payload = {"prompt": api_workflow}
    r = requests.post(f"{HOST}/ComfyBackendDirect/prompt", json=payload, timeout=30)
    return r.status_code, r.json()


def poll_completion(prompt_id, timeout=600, interval=5):
    """Poll until workflow completes or timeout."""
    import time
    for i in range(timeout // interval):
        time.sleep(interval)
        try:
            h = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=10)
            hist = h.json()
            if prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                status = hist[prompt_id].get("status", {})
                return True, outputs, status, i * interval
            q = requests.get(f"{HOST}/ComfyBackendDirect/queue", timeout=10)
            queue = q.json()
            running = len(queue.get("queue_running", []))
            pending = len(queue.get("queue_pending", []))
            if i % 6 == 0:
                print(f"  [{i*interval}s] running={running} pending={pending}")
            if not running and not pending and i > 2:
                # Check history one more time
                h2 = requests.get(f"{HOST}/ComfyBackendDirect/history/{prompt_id}", timeout=10)
                if prompt_id in h2.json():
                    outputs = h2.json()[prompt_id].get("outputs", {})
                    status = h2.json()[prompt_id].get("status", {})
                    return True, outputs, status, i * interval
                return False, {}, {"error": "queue empty, no output"}, i * interval
        except Exception as e:
            print(f"  [{i*interval}s] poll error: {e}")
    return False, {}, {"error": "timeout"}, timeout


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    do_submit = "--submit" in sys.argv
    do_save = "--save" not in sys.argv or "--save" in sys.argv  # default: save

    # Build both formats
    api_wf = build_api_format(NODES, seed=seed)
    ui_wf = build_ui_format(NODES, GROUPS, seed=seed)

    # Save locally
    out_dir = "/root/little-buddy-card/assets/workflows"
    os.makedirs(out_dir, exist_ok=True)

    api_path = os.path.join(out_dir, "katharina_hop_clean_api.json")
    ui_path = os.path.join(out_dir, "katharina_hop_clean_ui.json")
    with open(api_path, "w") as f:
        json.dump(api_wf, f, indent=2)
    with open(ui_path, "w") as f:
        json.dump(ui_wf, f, indent=2)
    print(f"✅ API format: {api_path}")
    print(f"✅ UI format:  {ui_path}")
    print(f"   Nodes: {len(NODES)} | Groups: {len(GROUPS)} | Output: SaveImage (SwarmUI compatible)")

    # Save to ComfyUI Workflows tab
    if do_save:
        print("\n--- Saving to ComfyUI Workflows tab ---")
        code, body = save_to_comfyui(ui_wf, "katharina_hop_clean")
        print(f"   Status: {code} | Response: {body[:200]}")

    # Submit for generation
    if do_submit:
        print(f"\n--- Submitting workflow (seed={seed}) ---")
        code, resp = submit_workflow(api_wf, seed=seed)
        print(f"   Status: {code} | Response: {json.dumps(resp)}")

        if "prompt_id" in resp:
            prompt_id = resp["prompt_id"]
            print(f"   Prompt ID: {prompt_id}")
            print("   Polling (expected ~3-4 min)...")
            success, outputs, status, elapsed = poll_completion(prompt_id)
            if success:
                print(f"\n✅ COMPLETED in {elapsed}s")
                print(f"   Status: {json.dumps(status)}")
                for nid, nout in outputs.items():
                    print(f"   Node {nid}: {json.dumps(nout)}")
            else:
                print(f"\n❌ FAILED: {json.dumps(status)}")
        else:
            print(f"   ❌ Submission failed")
