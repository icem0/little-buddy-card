#!/usr/bin/env bash
# ============================================================================
# kohya_ss SDXL Character-LoRA Training — Little Buddy Card / Katharina
# Spec: docs/T6-CHARACTER-CONSISTENCY-STRATEGY.md
# Ziel: deterministische Charakter-Konsistenz via Custom LoRA (Rank 16).
# ============================================================================
set -euo pipefail

# --- Pfade anpassen ---------------------------------------------------------
ROOT="/root/little-buddy-card"
DATASET_DIR="$ROOT/assets/dataset/katharina"        # 10-20 Master-Bilder + .caption je Bild
OUTPUT_DIR="$ROOT/assets/loras"
LOG_DIR="$ROOT/assets/training/logs"
KOHYA="$(command -v sdxl_train_network.py || echo /opt/kohya_ss/sdxl_train_network.py)"

# --- Style-Anchor Base (SDXL) ----------------------------------------------
# SDXL 1.0 base + nerijs/pixel-art-xl LoRA als Style-Anchor.
# Das Character-LoRA wird auf dem SDXL-base trainiert; Inference stackt
# base + style-lora + character-lora.
MODEL="/opt/models/sdxl/stable-diffusion-xl-base-1.0.safetensors"
VAE="/opt/models/sdxl/sdxl_vae.safetensors"
CLIP1="/opt/models/sdxl/clip_l.safetensors"
CLIP2="/opt/models/sdxl/clip_g.safetensors"

# --- Hyperparameter (aus Spec §4) ------------------------------------------
RANK=16                    # sweet spot char-LoRA
ALPHA=16                   # alpha == rank => 1.0
LR=1e-4                    # kohya SDXL-default
EPOCHS=20                  # bei ~12 Bildern / 20 repeats => ~240 steps/epoch
BATCH=4
ACCUM=2                    # eff. batch 8
WARMUP=10                  # % der gesamten steps
DROPOUT=0.05               # overfit vermeiden
SEED=42
NAME="katharina_char_lora"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

echo ">>> Training $NAME (rank=$RANK, lr=$LR, epochs=$EPOCHS)"
python3 "$KOHYA" \
  --config_file "$ROOT/assets/training/dataset.toml" \
  --pretrained_model_name_or_path "$MODEL" \
  --vae "$VAE" \
  --clip_l "$CLIP1" --clip_g "$CLIP2" \
  --output_dir "$OUTPUT_DIR" \
  --output_name "$NAME" \
  --save_every_n_epochs 5 \
  --train_batch_size "$BATCH" \
  --gradient_accumulation_steps "$ACCUM" \
  --max_train_epochs "$EPOCHS" \
  --learning_rate "$LR" \
  --lr_scheduler "cosine" \
  --lr_warmup_steps 0 \
  --lr_warmup_ratio "$WARMUP" \
  --network_dim "$RANK" \
  --network_alpha "$ALPHA" \
  --network_dropout "$DROPOUT" \
  --optimizer_type "AdamW8bit" \
  --mixed_precision "bf16" \
  --save_precision "bf16" \
  --cache_latents --cache_latents_to_disk \
  --prior_loss_weight 1.0 \
  --max_token_length 225 \
  --seed "$SEED" \
  --logging_dir "$LOG_DIR" \
  --log_with "tensorboard" \
  2>&1 | tee "$LOG_DIR/${NAME}_$(date +%Y%m%d_%H%M).log"

echo ">>> Fertig. LoRA: $OUTPUT_DIR/${NAME}_0000XX.safetensors"
echo ">>> Inference: base + nerijs/pixel-art-xl (weight ~0.8) + ${NAME} (weight 0.6-0.8)"
