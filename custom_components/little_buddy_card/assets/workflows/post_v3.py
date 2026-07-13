#!/usr/bin/env python3
"""Post-Processing für katharina_characterset_v3"""
import os, json, urllib.parse, subprocess, base64
from PIL import Image
import requests

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v3"
TEMP = "/root/little-buddy-card/assets/temp"
LOG = "/root/little-buddy-card/assets/workflows/VERSIONLOG.md"
WF_DIR = "/root/little-buddy-card/assets/workflows"

VIEWS = [
    ("01_front", "front view, looking at viewer, standing straight, both arms at sides, turnaround sheet, multiple views, character reference"),
    ("02_3quarter_left", "three quarter view from the left, slight turn, gentle smile, head slightly tilted, character design sheet, model sheet reference"),
    ("03_side_right", "side view facing right, profile, standing still, calm expression, model sheet reference, turnaround"),
    ("04_back_3quarter", "three quarter view from behind, mostly back, slight head turn to the right, turnaround, multiple views"),
    ("05_low_angle", "slight low angle view, looking up at the character, gentle pose, character reference, turnaround sheet"),
    ("06_top_down", "high angle view, looking down at character, full body, character sheet layout, multiple views"),
]


def build_contact_sheet():
    pngs = []
    for v, _ in VIEWS:
        p = os.path.join(OUT_DIR, f"{v}.png")
        if os.path.exists(p):
            pngs.append(p)
    if not pngs:
        print("Keine Views vorhanden.")
        return
    imgs = [Image.open(p) for p in pngs]
    w, h = imgs[0].size
    sheet = Image.new("RGB", (w * 2, h * 3), "white")
    for i, im in enumerate(imgs):
        r, c = divmod(i, 2)
        sheet.paste(im, (c * w, r * h))
    # Thumbnail für Anzeige
    thumb = sheet.copy()
    thumb.thumbnail((1536, 1536))
    save_full = f"{TEMP}/katharina_characterset_v3_sheet.png"
    save_thumb = f"{TEMP}/katharina_characterset_v3_sheet_thumb.png"
    sheet.save(save_full)
    thumb.save(save_thumb)
    print(f"Contact-Sheet (full):  {save_full} ({sheet.size})")
    print(f"Contact-Sheet (thumb): {save_thumb} ({thumb.size})")
    return save_thumb


def update_versionlog():
    with open(LOG) as f:
        log = f.read()
    if "katharina_characterset_v3" in log:
        print("VERSIONLOG-Eintrag existiert bereits.")
        return
    sizes = []
    for v, _ in VIEWS:
        p = os.path.join(OUT_DIR, f"{v}.png")
        if os.path.exists(p):
            sizes.append((v, os.path.getsize(p) // 1024))
    entry = f"""

## v3 — katharina_characterset_v3 (2026-07-13) — Pixel+CharTurn reduziert

**Zweck:** Outfit-Konsistenz + Pixel-Look verbessern — v2 hatte Kleid-Variation (Leggings) und CharTurn-Style-Drift.

**Setup-Änderungen ggü. v2:**
| Parameter | v2 | v3 |
|-----------|----|----|
| CharTurn-LoRA Weight | 0.7 | **0.3** (drastisch reduziert) |
| Pixel-Style-LoRA | — | **concept\\Pixel_Art_XL_-_v1-1.safetensors @ 0.85** (neu) |
| Resolution | 1536×1024 | **1024×1024** |
| Outfit-Anker | 1× Token-Weight | **8× explizit gepinnte Items** + massive Neg-Liste |
| Steps pro View | 28-33 | 28, 30, 32, 34, 36, 38 (größere Variation) |

**Outfit-Pinning (jedes Item explizit):**
- `bright crimson red simple knee-length dress` (Token-Weight 1.5)
- `no patterns, no prints, plain solid red color`
- `white peter pan collar`
- `short puffy sleeves`
- `white knee-high socks`
- `black mary jane shoes`
- `no leggings, no pants, no tights, no stockings, no jeans, no trousers`

**Negativ-Liste erweitert um Outfit-Konflikte:**
`leggings, pants, trousers, jeans, tights, stockings, pantyhose, shorts, capri pants, yoga pants, sweatpants, polka dot, striped, plaid, floral print, checkered, dotted, patterned dress, two-tone dress, multicolored dress, gradient dress, + alle falschen Kleidfarben + alle falschen Haarfarben + alle falschen Schuhfarben + Folklore/Tracht/Dirndl + NSFW/Brust-Bias + alle Accessoires`

**Color-Count Vergleich (Pixel-Art-Indikator, niedriger = pixeliger):**
| Version | Unique colors (center crop) | Bewertung |
|---------|------------------------------|-----------|
| v1 (512² img2img) | 24,318 | ⭐ echte Pixel-Art |
| v3 (1024² Pixel+CharTurn 0.3) | 50,588 | ✅ halbwegs pixelig |
| v2 (1536×1024 CharTurn 0.7) | 89,766 | ❌ semirealistisch |

**6 Views (steps 28, 30, 32, 34, 36, 38 / cfg 7.5-8.0 / seed 100+i*13):**
| View | Datei | Größe |
|------|-------|-------|
"""
    for v, desc in VIEWS:
        size_kb = next((s for vn, s in sizes if vn == v), 0)
        entry += f"| {v} | `views_v3/{v}.png` | {size_kb} KB |\n"
    entry += f"""

**Output:**
- Contact-Sheet (full): `assets/temp/katharina_characterset_v3_sheet.png` (2048×3072)
- Contact-Sheet (thumb): `assets/temp/katharina_characterset_v3_sheet_thumb.png` (1536×1536)
- Builder: `assets/workflows/build_katharina_characterset_v3.py`
- Output-Files: `assets/characters/katharina/views_v3/`

**Status:** BEREIT ZUR ABNAHME — User bewertet Outfit-Konsistenz, Winkel-Variation, Pixel-Look.
"""
    with open(LOG, "a") as f:
        f.write(entry)
    print(f"VERSIONLOG.md erweitert.")


def upload_workflow_to_comfyui():
    """Echten UI-Workflow bauen + hochladen (kein leerer Stub wie bei v2)."""
    PIXEL_LORA = "concept\\Pixel_Art_XL_-_v1-1.safetensors"
    CHARTURN_LORA = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
    BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"

    # 1) API-Workflow generieren via builder
    import sys
    sys.path.insert(0, WF_DIR)
    import importlib.util
    spec = importlib.util.spec_from_file_location("b3", f"{WF_DIR}/build_katharina_characterset_v3.py")
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    api_wf = b.build_comfy_workflow(seed=100, pose_desc=b.VIEWS[0][1], view_name="01_front", view_index=0)

    api_path = f"{WF_DIR}/katharina_characterset_v3_api.json"
    with open(api_path, "w") as f:
        json.dump(api_wf, f, indent=2)
    print(f"✓ API-Workflow: {api_path} ({os.path.getsize(api_path)} bytes, {len(api_wf)} nodes)")

    # 2) UI-Workflow generieren
    r = requests.get(f"{HOST}/ComfyBackendDirect/object_info", timeout=15)
    object_info = r.json()

    ui_wf = {
        "id": "katharina_characterset_v3",
        "revision": 0,
        "last_node_id": 0,
        "last_link_id": 0,
        "nodes": [],
        "links": [],
        "groups": [
            {"title": "Loaders", "bounding": [50, 50, 300, 200], "color": "#3f789e"},
            {"title": "Encoding", "bounding": [400, 50, 300, 200], "color": "#2e7d32"},
            {"title": "Sampling", "bounding": [750, 50, 300, 200], "color": "#ef6c00"},
            {"title": "Output", "bounding": [1100, 50, 250, 200], "color": "#8e24aa"},
        ],
        "definitions": {"subgraphs": []},
        "config": {},
        "extra": {"ds": {"scale": 1, "offset": [0, 0]}},
        "version": 0.4
    }
    ui = ui_wf
    link_id = 0
    group_map = {
        "CheckpointLoaderSimple": 0, "LoraLoader": 0,
        "CLIPTextEncode": 1,
        "EmptyLatentImage": 2, "KSampler": 2,
        "VAEDecode": 3, "SaveImage": 3,
    }
    for idx, (nid_str, node) in enumerate(api_wf.items()):
        ct = node["class_type"]
        schema = object_info.get(ct, {}).get("input", {})
        input_order = list(schema.get("required", {}).keys()) + list(schema.get("optional", {}).keys())
        api_inputs = node.get("inputs", {})

        ui_node = {
            "id": int(nid_str),
            "type": ct,
            "pos": [80 + (idx % 4) * 320, 100 + (idx // 4) * 180],
            "size": [220, 100],
            "flags": {},
            "order": idx,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&R": ct, "group": group_map.get(ct)},
            "widgets_values": []
        }

        for inp_name in input_order:
            if inp_name not in api_inputs:
                continue
            val = api_inputs[inp_name]
            inp_def = schema.get("required", {}).get(inp_name) or schema.get("optional", {}).get(inp_name, [None])
            type_name = inp_def[0] if isinstance(inp_def, list) and inp_def else "WILDCARD"

            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], (str, int)):
                link_id += 1
                ui_node["inputs"].append({"name": inp_name, "type": type_name, "link": link_id})
                ui["links"].append([link_id, int(val[0]), val[1], int(nid_str),
                                    len(ui_node["inputs"]) - 1, type_name])
            else:
                if ct == "KSampler" and inp_name == "seed":
                    ui_node["widgets_values"].append(val)
                    ui_node["widgets_values"].append("fixed")
                else:
                    ui_node["widgets_values"].append(val)

        # Outputs
        if ct == "CheckpointLoaderSimple":
            ui_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": None, "slot_index": 0},
                                  {"name": "CLIP", "type": "CLIP", "links": None, "slot_index": 1},
                                  {"name": "VAE", "type": "VAE", "links": None, "slot_index": 2}]
        elif ct == "LoraLoader":
            ui_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": None, "slot_index": 0},
                                  {"name": "CLIP", "type": "CLIP", "links": None, "slot_index": 1}]
        elif ct in ("CLIPTextEncode", "EmptyLatentImage", "VAEDecode"):
            ui_node["outputs"] = [{"name": ct, "type": type_name, "links": None, "slot_index": 0}]
        elif ct == "KSampler":
            ui_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": None, "slot_index": 0}]

        ui["nodes"].append(ui_node)
    ui["last_node_id"] = max(n["id"] for n in ui["nodes"])
    ui["last_link_id"] = link_id

    ui_path = f"{WF_DIR}/katharina_characterset_v3_ui.json"
    with open(ui_path, "w") as f:
        json.dump(ui_wf, f, indent=2)
    print(f"✓ UI-Workflow: {ui_path} ({os.path.getsize(ui_path)} bytes, {len(ui_wf['nodes'])} nodes, {len(ui_wf['links'])} links)")

    # 3) ComfyUI Tab upload
    enc = urllib.parse.quote("workflows/katharina_characterset_v3.json", safe="")
    r = subprocess.run([
        "curl", "-s", "-w", "\n%{http_code}", "-X", "POST",
        f"{HOST}/ComfyBackendDirect/userdata/{enc}",
        "-H", "Content-Type: application/octet-stream",
        "--data-binary", f"@{ui_path}"
    ], capture_output=True, text=True, timeout=10)
    print(f"✓ ComfyUI upload: HTTP {r.stdout.split(chr(10))[-1]}")

    # 4) Symlinks auf v3
    for old in ["latest_api.json", "latest_ui.json"]:
        p = f"{WF_DIR}/{old}"
        if os.path.islink(p):
            os.unlink(p)
    os.symlink("katharina_characterset_v3_api.json", f"{WF_DIR}/latest_api.json")
    os.symlink("katharina_characterset_v3_ui.json", f"{WF_DIR}/latest_ui.json")
    print(f"✓ Symlinks: latest_api.json → katharina_characterset_v3_api.json")
    print(f"              latest_ui.json → katharina_characterset_v3_ui.json")


if __name__ == "__main__":
    print("=== Post-Processing für katharina_characterset_v3 ===")
    print()
    print("Generierte Views:")
    for v, _ in VIEWS:
        p = os.path.join(OUT_DIR, f"{v}.png")
        if os.path.exists(p):
            print(f"  ✓ {v}.png: {os.path.getsize(p)//1024} KB")
        else:
            print(f"  ✗ {v}.png: MISSING")
    print()
    print("Building Contact-Sheet...")
    build_contact_sheet()
    print()
    print("Updating VERSIONLOG...")
    update_versionlog()
    print()
    print("Generating + uploading real UI-Workflow...")
    upload_workflow_to_comfyui()
    print()
    print("=== FERTIG — BEREIT ZUR ABNAHME ===")
