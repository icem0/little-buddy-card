# Training — Character Consistency LoRA (Katharina / Little Buddy Card)

Spezifikation: `docs/T6-CHARACTER-CONSISTENCY-STRATEGY.md`

## Was liegt hier

| Datei | Weg | Zweck |
|-------|-----|-------|
| `dataset.toml` | kohya_ss | Bucket-Config, 1024 res, batch 4, 20 repeats |
| `train_lora.sh` | kohya_ss | Production-Run: rank 16, lr 1e-4, 20 epochs, bf16, cosine |
| `train_lora_comfyui.json` | SwarmUI/ComfyUI `TrainLoraNode` | Schnellweg auf 4090, 1000 steps, experimentell |

## Schritt 0 — Dataset

10–20 Master-Bilder nach `assets/dataset/katharina/` legen. Pro Bild eine `.caption`
Datei mit dem **identischen Instance-Prompt** (siehe Spec §3) + optionalem Pose-Suffix.
Alle Bilder im Master-Look generieren (gleiche Sampler/CFG/Steps).

Instance-Prompt (Basis für jede `.caption`):

```
pixel art, katharina character, cute chibi kawaii girl, blonde hair in two long braids, (bright crimson red long dress:1.4) with puffy sleeves and white collar, white socks, black mary jane shoes, big round innocent eyes, sweet innocent, white background, masterpiece, highly detailed
```

Negativ-Prompt (beim Dataset-Generieren UND Inference) → Spec §3 Blockliste.

## Schritt 1 — Trainieren

**Production (kohya_ss):**
```bash
bash assets/training/train_lora.sh
# => assets/loras/katharina_char_lora_0000XX.safetensors
```

**Schnellweg (ComfyUI pass-through, 4090):**
```bash
curl -s -X POST http://192.168.178.53:7801/ComfyBackendDirect/prompt \
  -H 'Content-Type: application/json' \
  -d @assets/training/train_lora_comfyui.json
# prompt_id aus Response; dann History/View wie in Skill beschrieben
```

## Schritt 2 — Inference

Stack: **SDXL base + `nerijs/pixel-art-xl` (style, ~0.8) + `katharina_char_lora` (char, 0.6–0.8)**.
Trigger `pixel art` im Prompt. LoRA-File nach `~/SwarmUI/.../models/loras/` kopieren.

## Hyperparameter (Kurzfassung)

Rank 16 · Alpha 16 · LR 1e-4 · 20 epochs · batch 4 (+accum 2) · cosine+warmup ·
bf16 · dropout 0.05 · seed 42 · nur UNet (kein Text-Encoder-Training).
