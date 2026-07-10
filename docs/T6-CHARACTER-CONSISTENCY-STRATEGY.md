# T6 — Character Consistency Strategy (LoRA-Training-Spec)

> Autoritative Quelle: Skill `pixel-art-character-consistency` (verified 2026-07-07 / 2026-07-08,
> eigene Tests auf SwarmUI @ 192.168.178.53:7801, 4090). Dieses Dokument destilliert die
> Erkenntnisse in eine konkrete Trainings-Spezifikation. Die im Task referenzierte alte
> Doc `T6-CHARACTER-CONSISTENCY-STRATEGY.md` existierte nicht — hier rekonstruiert.

## 0. TL;DR — Die eine Erkenntnis

**Same seed + same prompt + same model reicht NICHT** für konsistente Charakter-Posen.
SD(SDXL)-Modelle driften pro Prompt subtil → 4 "gleiche" Mädchen sehen aus wie 4 verschiedene.

Die EINZIGE deterministische Lösung: **Custom Character-LoRA** auf 10–20 Variationen.
Dauert 5–15 min auf einer 4090. Wan 2.2 Animate (ComfyUI pass-through) ist die nächste
Stufe, wenn img2img nicht reicht — aber LoRA ist der Konsistenz-Anker.

## 1. Was NICHT funktioniert (8 dokumentierte Fehlversuche)

| Methode | Symptom |
|---------|---------|
| 4× t2i, gleicher Seed | 4 verschiedene Charaktere (Sampling-Drift) |
| img2img creativity 0.25–0.35 | Master-Stil da, aber Zöpfe/Accessoires weg |
| img2img creativity 0.05–0.15 | Alle Frames identisch, keine Animation |
| Token-Weight `(braids:1.5)` + CFG 8–20 (RDXL) | inkonsistent, manchmal Zöpfe, manchmal nicht |
| IP-Adapter weight=1.0 | 1:1 Klon, keine Pose-Variation |
| IP-Adapter weight=0.4 bei großem Prompt-Delta | komplett anderer Charakter |
| Strip-Sheet 1024×256 "Frame 1,2,3,4" | Modell ignoriert Layout → nur 1 zentraler Char |
| Action-Wörter "jumping high"/"leaping" | Street-Fighter-Bias statt cute chibi |

**img2img Sweet-Spots (nur als Fallback, wenn kein LoRA verfügbar):**

| creativity | Effekt | Char-Features | Nutzung |
|-----------|--------|--------------|---------|
| 0.05–0.15 | Master bleibt 1:1 | ✅ bleiben | Mikro-Tweak |
| 0.20–0.30 | + minimale Variation | ⚠️ Haarfarbe weg | ähnliche Posen |
| 0.35–0.50 | + neue Pose | ❌ Zöpfe/Accessoires weg | Style-Variation |
| 0.55–0.70 | starke Änderung | ❌ Char anders | Style-Transfer |
| 0.70–0.85 | **sichtbare Pose-Änderung** | ⚠️ Frisur-Drift möglich | **Animation (User 2026-07-08: 0.5 zu zaghaft → 0.7–0.85)** |

## 2. Style-Anchor — `nerijs/pixel-art-xl`

Für SDXL-Fidelity + Pixel-Art-Discipline (raehoshi-Style):

- **Base:** `stabilityai/stable-diffusion-xl-base-1.0` (6.6 GB)
- **LoRA:** `nerijs/pixel-art-xl` (162 MB, https://huggingface.co/nerijs/pixel-art-xl)
- **Trigger:** `pixel art` im Prompt
- **Beste Wahl** für SDXL-Aesthetic + Pixel-Art-Discipline
- Alternativ/Production: `RDXL_Pixel_Art_-_Pony_2.safetensors` (Pony/SDXL, lokal auf 192.168.178.53:7801)
  — 1024×1024 nativ, Trigger `pixel art,`, verifizierte Animations-Configs siehe
  `references/rdxl-pony-pipeline-2026-07-08.md`.

> Wichtig: Der Character-LoRA (unten) wird AUF EINEM dieer Style-Anchor-Bases trainiert,
> nicht auf dem Style-LoRA selbst. Inference = Base + Style-LoRA + Character-LoRA.

## 3. Dataset-Spezifikation

- **Größe:** 10–20 Bilder des Charakters in leicht verschiedenen Posen / Blickwinkeln /
  leichter Kleidungsvariation.
- **Konsistenz-Regel:** ALLE Bilder im Master-Look generieren (gleiche Sampler, CFG, Steps,
  Prompt-Struktur). Inkonsistentes Dataset → inkonsistente LoRA.
- **Auflösung:** 1024×1024 (SDXL native) für Training; für reine Sprites ggf. auf
  512–768 downscalen, aber SDXL-Training will ≥1024 für Qualität.
- **Captioning:**
  - **Nicht** jedes Bild einzeln beschreiben (das lehrt den Charakter nicht).
  - **Empfohlen:** *Instance-Prompt* + leichtes *Regularization*.
  - Instance-Prompt (Caption aller Trainingsbilder, identisch):
    `pixel art, katharina character, cute chibi kawaii girl, blonde hair in two long braids,
    (bright crimson red long dress:1.4) with puffy sleeves and white collar, white socks,
    black mary jane shoes, big round innocent eyes, sweet innocent, white background,
    masterpiece, highly detailed`
  - Pro-Bild-Zusatz (optional, für Pose-Variation): `looking at viewer, standing pose` /
    `three quarter view` / `side profile` etc. — aber der Charakter-Teil bleibt IDENTISCH.
  - **Kein** TAG-Blind-Captioning (WD14) — das zerstört die Charakter-Pinning.
    Instance-Prompt-Approach ist hier robuster.

### Negativ-Blockliste (RDXL_Pixel_Art_-_Pony_2, verifiziert)
Wird beim Dataset-Generieren UND beim Inference als negative prompt genutzt, um
Accessoire-/Frisur-/Kleiderfarben-Drift zu blocken:

```
blurry, deformed, noise, borders, text, signature, watermark, nsfw, mature, realistic,
photo, 3d, multiple girls, fighting, weapon, dynamic pose, schürze, apron, handtasche, bag,
purse, cross, crucifix, religious, kruzifix, kreuz, nurse, krankenschwester, doctor, uniform,
profession, costume, dress over dress, accessory, accessories, jewelry, hat, hair bow,
hairband, glasses, wings, halo, tail, bun, ponytail, short hair, no braids, hair down,
loose hair, black hair, brown hair, red hair, blue hair, pink hair, white dress, blue dress,
green dress, yellow dress, black dress, brown dress, gray dress, multicolored dress, pattern,
scenery, landscape, dark background, colored background, gradient background, deformed face,
missing eye, extra eye, deformed hands, extra fingers, ugly, disfigured, malformed, poorly drawn
```

## 4. Empfohlene Hyperparameter (LoRA-Training)

| Parameter | Empfehlung | Quelle / Begründung |
|-----------|-----------|---------------------|
| **Rank (Dim)** | **16** | Sweet-Spot Char-LoRA (nicht zu groß/klein), Skill §Realitäts-Checks |
| Alpha | 16 (= rank, also α/rank = 1.0) | Standard für SDXL-LoRA |
| Learning Rate | **1e-4 (0.0001)** | kohya-Standard für SDXL LoRA; TrainLoraNode-Beispiel nutzt 5e-4 (aggressiv, nur für的实验节点) |
| Optimizer | AdamW8bit | TrainLoraNode-Default; kohya: `AdamW8bit` |
| LR-Scheduler | cosine | mit warmup |
| Warmup | 10% der steps | — |
| Epochs | **10–20** | bei 10–20 Bildern → 200–400 total steps bei batch 4 |
| Steps (Gesamt) | ~1000 (TrainLoraNode-Default) | 4090: 5–15 min |
| Batch Size | 4 (kohya) / 1 (ComfyUI-Node) | ComfyUI-Node unterstützt nur 1 |
| grad_accumulation | 1 (ComfyUI) / 2–4 (kohya) | — |
| Loss | MSE (ComfyUI) / `l2` (kohya) | — |
| Precision | bf16 (train + lora) | 4090 unterstützt bf16 |
| Seed | 42 | reproduzierbar |
| Network Dropout | 0.05–0.1 | Overfitting vermeiden |
| CLIP-Text-Encoder | **nicht** separat trainiert (nur UNet) | Skill: "Text-Encoder wird NICHT separat trainiert" |

### Inference-Tuning (wenn LoRA fertig)
- LoRA weight **0.6–0.8** = sweet spot
- >0.9 = Charakter exakt, aber Verhalten steif
- <0.5 = LoRA-Effekt zu schwach

## 5. Konkrete Trainings-Configs

Zwei Wege (beide im Repo unter `assets/training/`):

1. **`kohya_ss` SDXL LoRA** (`dataset.toml` + `train_lora.sh`) — Production-Grade,
   volle Kontrolle, Gradient-Accumulation, cosine scheduler. EMPFOHLEN.
2. **SwarmUI / ComfyUI `TrainLoraNode`** (`train_lora_comfyui.json`) — pass-through
   auf der 4090, experimentell, läuft in 5–15 min. Schnellweg ohne kohya-Setup.

→ Siehe `assets/training/README.md` für Aufruf.

## 6. Realitäts-Checks (nicht vergessen)

- `TrainLoraNode` ist NICHT production-grade (experimentelles ComfyUI-Feature).
- LoRA-Qualität hängt massiv vom Dataset ab.
- Trigger-Wort im Prompt bleibt nötig für Konsistenz (auch bei Char-LoRA).
- Rank 16 sweet spot — nicht 32+ für Char-LoRAs.
