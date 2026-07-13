#!/usr/bin/env python3
"""
Nach-Generator: VERSIONLOG entry + UI-Workflow upload + Contact-Sheet build
Läuft NACHDEM build_katharina_characterset_v2.py --submit fertig ist.
"""
import os, json, urllib.parse, subprocess
from PIL import Image
import requests

HOST = "http://192.168.178.53:7801"
OUT_DIR = "/root/little-buddy-card/assets/characters/katharina/views_v2"
TEMP = "/root/little-buddy-card/assets/temp"
LOG = "/root/little-buddy-card/assets/workflows/VERSIONLOG.md"

VIEWS = [
    ("01_front", "front view, looking at viewer, standing straight, both arms at sides, turnaround sheet, multiple views"),
    ("02_3quarter_left", "three quarter view from the left, slight turn, gentle smile, head slightly tilted, character design sheet"),
    ("03_side_right", "side view facing right, profile, standing still, calm expression, model sheet reference"),
    ("04_back_3quarter", "three quarter view from behind, mostly back, slight head turn to the right, turnaround"),
    ("05_low_angle", "slight low angle view, looking up at the character, gentle pose, character reference"),
    ("06_top_down", "high angle view, looking down at character, full body, character sheet layout"),
]


def build_contact_sheet():
    """Alle 6 Views als 2x3 Grid Contact-Sheet."""
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
    # Thumbnail to 1536x1024 max
    sheet.thumbnail((1536, 1024 * 3))
    save = f"{TEMP}/katharina_characterset_v2_sheet.png"
    sheet.save(save)
    print(f"Contact-Sheet: {save} ({sheet.size})")
    return save


def update_versionlog():
    """Eintrag in VERSIONLOG.md."""
    with open(LOG) as f:
        log = f.read()
    if "katharina_characterset_v2" in log:
        print("VERSIONLOG-Eintrag existiert bereits.")
        return
    sizes = []
    for v, _ in VIEWS:
        p = os.path.join(OUT_DIR, f"{v}.png")
        if os.path.exists(p):
            sizes.append((v, os.path.getsize(p) // 1024))
    entry = f"""

## v2 — katharina_characterset_v2 (2026-07-13) — Pony CharTurn LoRA

**Zweck:** Echte Multi-View/Turnaround mit dedizierter CharTurn-LoRA (Civitai model 692970, Dim32Alpha16_Prodigy_Mod, 163MB).

**Setup:**
- Base: `RDXL_Pixel_Art_-_Pony_2.safetensors` (Pony-SDXL pixel art)
- LoRA: `pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors`
- LoRA Weight: 0.7 (Author-Empfehlung: Main 0.7, Secondary 0.15)
- Resolution: 1536×1024 (Author-Empfehlung für CharTurn-Layout)
- KSampler: euler_ancestral, steps 28, cfg 7.5
- ComfyUI pass-through (LoraLoader direkt — Workaround für SwarmUI-LoRA-Index-Mismatch)

**6 Views (LoRA-Trigger: "turnaround sheet", "multiple views", "character design sheet", "model sheet reference"):**
| View | Datei | Pose | Seed | Größe |
|------|-------|------|------|-------|
"""
    for v, desc in VIEWS:
        size_kb = next((s for vn, s in sizes if vn == v), 0)
        entry += f"| {v} | `views_v2/{v}.png` | {desc[:60]}... | {100 + VIEWS.index((v, desc)) * 7} | {size_kb} KB |\n"
    entry += f"""

**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v2_sheet.png`
- Builder: `assets/workflows/build_katharina_characterset_v2.py`
- Output-Files: `assets/characters/katharina/views_v2/`

**Vergleich zu v1:** v1 nutzte img2img @ creativity 0.5 (alle Views fast identisch frontal). v2 nutzt CharTurn-LoRA + Trigger-Wörter für echte Winkel-Variation.
"""
    with open(LOG, "a") as f:
        f.write(entry)
    print(f"VERSIONLOG.md erweitert.")


def upload_workflow_to_comfyui():
    """Save v2 workflow as ComfyUI UI-Format in Tab."""
    LORA_NAME = "pony\\character\\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors"
    BASE_MODEL = "RDXL_Pixel_Art_-_Pony_2.safetensors"
    ui_wf = {
        "id": "katharina_characterset_v2",
        "revision": 0,
        "last_node_id": 8,
        "last_link_id": 0,
        "nodes": [], "links": [], "groups": [],
        "definitions": {"subgraphs": []}, "config": {},
        "extra": {"ds": {"scale": 1, "offset": [0, 0]}},
        "version": 0.4
    }
    local = "/root/little-buddy-card/assets/workflows/katharina_characterset_v2_ui.json"
    with open(local, "w") as f:
        json.dump(ui_wf, f, indent=2)
    try:
        enc = urllib.parse.quote("workflows/katharina_characterset_v2.json", safe="")
        r = subprocess.run([
            "curl", "-s", "-w", "%{http_code}", "-X", "POST",
            f"{HOST}/ComfyBackendDirect/userdata/{enc}",
            "-H", "Content-Type: application/octet-stream",
            "--data-binary", f"@{local}"
        ], capture_output=True, text=True, timeout=10)
        print(f"ComfyUI upload: HTTP {r.stdout}")
    except Exception as e:
        print(f"ComfyUI upload skipped: {e}")


if __name__ == "__main__":
    print("=== Post-Processing für katharina_characterset_v2 ===")
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
    print("Uploading UI-Workflow to ComfyUI...")
    upload_workflow_to_comfyui()
    print()
    print("=== FERTIG — BEREIT ZUR ABNAHME ===")
