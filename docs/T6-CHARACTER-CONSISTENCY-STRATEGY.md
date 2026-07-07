# T6 — Pixel-Art Character-Consistency Strategy

> Forschungs-Synthese für konsistente Little-Buddy-Generierung. Stand: 2026-07-07.

## 🧠 Das Kern-Problem

AI-Modelle generieren pro Prompt ein komplett neues Bild. **Ohne Fixes**:
- Bild 1: blond, Bild 2: brünett, Bild 3: mit Brille, Bild 4: andere Augenfarbe
- Konsistenz nur über **drei kombinierte Techniken** erreichbar

## ✅ DIE DREI-SCHICHT-STRATEGIE (Apatero / Cobalt-Explorer / edgardojs SRS)

```
┌──────────────────────────────────────────────────────────────┐
│ Schicht 1: Character LoRA (Identity Anchor)                  │
│ → Einmal trainieren, immer wieder verwenden                  │
│ → 15-20 curated Reference-Images                             │
│ → Trigger-Word im Prompt, LoRA-Weight 1.0-1.2                │
├──────────────────────────────────────────────────────────────┤
│ Schicht 2: Strukturiertes Prompting (Pose/State)             │
│ → Mood-Wort, Level-Wort, Pose-Wort, Style-Wort trennen      │
│ → Fixed seed + batch generation für Varianten                │
├──────────────────────────────────────────────────────────────┤
│ Schicht 3: Post-Processing (Pixel-Art Look)                  │
│ → SDXL 1024² → Nearest-Neighbor downscale → 32×32            │
│ → Background-Removal (rembg) → transparent PNG               │
│ → Optional: sprite-sheet compositing                         │
└──────────────────────────────────────────────────────────────┘
```

## 🎨 EMPFOHLENE PIXEL-ART LoRAs (SDXL-basiert, 2025-2026)

| LoRA | Quelle | Trigger | Weight | Use Case |
|------|--------|---------|--------|----------|
| **`nerijs/pixel-art-xl`** | [HuggingFace](https://huggingface.co/nerijs/pixel-art-xl) | *(kein Trigger, einfach pixel art)* | 0.8-1.0 | **⭐ Standard-Empfehlung**, breit kompatibel |
| **PIXART Pixel Art Style** | [Civitai](https://civitai.com/models/2233307/pixel-art-style-lora) | `PIXART` | 0.7-1.0 | Modern, 81MB, gut dokumentiert |
| **ntc-ai/SDXL-LoRA-slider.pixel-art** | HuggingFace | `pixel art` | 0.6-0.9 | Stärkerer Stil-Effekt |

## 🎯 CHARACTER-LORA TRAINING (Custom Little Buddy)

### Datensatz-Setup
- **15-20 Reference-Images** generieren via SwarmUI (raehoshi-illust-xl-3-sft) mit:
  - Variation: 7 Moods × 3 Posen (front, 3/4, side) = 21 Bilder
  - Style: chibi, cute, simple, kawaii
  - Background: solid white (für einfaches BG-Removal später)
  - Format: 1024×1024 PNG

### Training-Parameter (kohya_ss / ai-toolkit Empfehlung 2026)
```
Base model:     SDXL 1.0 (oder raehoshi-illust-xl-3-sft)
Network rank:   16-32 (höher = mehr Kapazität aber Risiko Overfitting)
Network alpha:  16 (gleicher Wert wie rank)
Learning rate:  0.0001 (1e-4)
Optimizer:      AdamW8bit
Epochs:         8-15 (für kleine Datensätze)
Batch size:     1 (mit gradient accumulation 4-8)
Resolution:     1024
Trigger word:   "littlebuddy" (eigener Token, nicht im Vokabular)
```

### Trigger-Word-Trick
Der Trigger-Word muss:
1. **Einzigartig** sein (nicht im Trainingsdatensatz des Base-Models)
2. **In JEDER Caption** als erstes Wort stehen
3. **Im Inference-Prompt** den LoRA aktivieren

Beispiel-Caption:
```
"littlebuddy, cute chibi blob creature, [mood:happy], front view, simple white background"
```

## 🔄 WORKFLOW FÜR LITTLE BUDDY CARD

### Phase 1: Reference-Set erstellen
```bash
# 21 Bilder generieren (7 moods × 3 angles)
python3 generate_references.py --model raehoshi --count 21
# Output: refs/littlebuddy_{mood}_{angle}.png
```

### Phase 2: LoRA trainieren
```bash
# kohya_ss Lokal oder via SwarmUI/ComfyUI training node
python3 train_lora.py \
  --base_model raehoshi-illust-xl-3-sft \
  --dataset refs/ \
  --trigger_word littlebuddy \
  --output lora/littlebuddy_v1.safetensors
```

### Phase 3: Sprite-Generierung
```bash
# Für jedes Level × Mood einen Sprite
for level in 1 2 3 4 5; do
  for mood in happy sad hungry thirsty sleepy angry playful; do
    python3 generate_sprite.py \
      --lora lora/littlebuddy_v1.safetensors \
      --prompt "littlebuddy, ${mood} expression, chibi level ${level}" \
      --output assets/pets/level_${level}/${mood}.png
  done
done
```

### Phase 4: Post-Processing
```python
# Für jedes Sprite: 1024 → 32x32 + Alpha
from PIL import Image
from rembg import remove

img = Image.open("sprite_1024.png")
img_small = img.resize((32, 32), Image.NEAREST)  # nearest-neighbor für pixel look
img_rgba = remove(img_small)  # transparent background
img_rgba.save("sprite_32x32.png")
```

## 💡 PRO-TIPPS AUS DER COMMUNITY

### 1. **Seed-Lock für gleiche Pose**
Beim Generieren verschiedener Moods: **gleichen seed** verwenden + nur Mood-Wort ändern → gleiche Pose, anderer Ausdruck.

### 2. **ControlNet + Reference-Image**
ComfyUI Workflow: Ein "Master-Sprite" generieren, dann via IP-Adapter / ControlNet alle anderen ableiten → Look bleibt identisch.

### 3. **Multi-Concept LoRA vermeiden**
EIN LoRA = EINE Figur. Nicht "littlebuddy + tree + background" in einem LoRA. Separate LoRAs:
- `littlebuddy_v1.safetensors` (Charakter)
- `pixel_style_v1.safetensors` (Style-Anker, optional)
- `tree_growth_v1.safetensors` (separater Charakter für den Baum)

### 4. **Civitai-Backup**
Trainierte LoRAs auf Civitai hochladen (kostenlos, mit Trigger-Name) → Backup + Community-Nutzung + Versionierung.

## 📊 KOSTEN / ZEIT-SCHÄTZUNG

| Phase | Dauer | Compute |
|-------|-------|---------|
| Reference-Set (21 Bilder) | ~10 min | SwarmUI GPU |
| LoRA-Training (15-20 imgs, 10 epochs) | ~30-60 min | 12-16GB VRAM (RTX 3080+) |
| Sprite-Generation (35+5 = 40 Bilder) | ~20-30 min | SwarmUI GPU |
| Post-Processing (40 Bilder) | ~2-5 min | Lokal CPU |

**Total: ~1-2 Stunden für komplettes Asset-Set.**

## 📁 VERZEICHNIS-STRUKTUR (in repo)

```
little-buddy-card/
├── assets/
│   ├── lora/
│   │   └── littlebuddy_v1.safetensors  # NICHT in git (zu groß)
│   ├── pets/
│   │   ├── level_1/{happy,sad,hungry,thirsty,sleepy,angry,playful}.png
│   │   ├── level_2/...
│   │   └── level_5/...
│   ├── trees/
│   │   └── {seed,sprout,sapling,young_tree,full_grown}.png
│   └── refs/
│       └── littlebuddy_training_set/
└── scripts/
    ├── generate_references.py
    ├── train_lora.py  (Doku, nicht ausgeführt)
    ├── generate_sprite.py
    └── postprocess_pixel.py
```

## 🎯 EMPFEHLUNG FÜR LITTLE BUDDY

1. **Sofort:** `nerijs/pixel-art-xl` runterladen + in SwarmUI LoRA-Ordner legen → sofortige Pixel-Art-Qualität ohne Custom-Training
2. **Phase 2 (T6 Implementation):** Custom `littlebuddy` LoRA trainieren mit 15-20 ref-images für **Identitäts-Konsistenz** über alle 35 Pet-Sprites
3. **Phase 3:** Tree-Charakter separater LoRA (oder LoRA-frei mit starkem Prompt)
4. **Phase 4:** Sprite-Sheet-Builder für Animation (idle, walk, eat — 4-frame-cycles)

## 🔗 WICHTIGE QUELLEN

- [Cobalt Explorer: Character Sheets for Stable Diffusion](https://cobaltexplorer.com/2023/06/character-sheets-for-stable-diffusion/)
- [Apatero: Generate Clean Spritesheets in ComfyUI](https://apatero.com/blog/generate-clean-spritesheets-comfyui-guide-2025)
- [edgardojs: Sprite Character LoRA Training SRS (GitHub)](https://github.com/edgardojs/comfyui_automate/blob/main/sprite_character_lora_srs.md)
- [nerijs/pixel-art-xl (HuggingFace)](https://huggingface.co/nerijs/pixel-art-xl)
- [PIXART Pixel Art Style LoRA (Civitai)](https://civitai.com/models/2233307/pixel-art-style-lora)
- [Astropulse (Cody): AI Pixel Art Tools](https://astropulse.co/)
