# Wan 2.2 Animate Setup für Little Buddy Card

## Status
- ComfyUI: NOT ONLINE YET (Backend loading failed)
- WanAnimateToVideo: vorinstalliert
- Bestehende Modelle: WAN I2V high/low noise, wan_2.1_vae

## Fehlende Modelle (~22 GB)
| # | Datei | Größe | Download URL | Zielpfad |
|---|-------|-------|--------------|----------|
| 1 | Wan2.2_Animate_14B_FP8.safetensors | 16.5 GB | https://huggingface.co/okabeee/Wan2.2_Animate_14B_FP8/resolve/main/Wan2.2_Animate_14B_FP8.safetensors | diffusion_models/Wan/ |
| 2 | clip_vision_h.safetensors | 1.2 GB | https://huggingface.co/AtelierDarren/Wan2.2_Animate/resolve/main/clip_vision_h.safetensors | clip_vision/ |
| 3 | umt5-xxl-enc-fp8_e4m3fn.safetensors | 6.4 GB | https://huggingface.co/AtelierDarren/Wan2.2_Animate/resolve/main/umt5-xxl-enc-fp8_e4m3fn.safetensors | text_encoders/ |
| 4 | lightx2v_I2V_14B_480p_cfg_step_distill_rank32_bf16.safetensors | 356 MB | https://huggingface.co/AtelierDarren/Wan2.2_Animate/resolve/main/lightx2v_I2V_14B_480p_cfg_step_distill_rank32_bf16.safetensors | loras/ |
| 5 | WanAnimate_relight_lora_fp16.safetensors | 1.4 GB | https://huggingface.co/AtelierDarren/Wan2.2_Animate/resolve/main/WanAnimate_relight_lora_fp16.safetensors | loras/ |

## Workflow Steps
1. ComfyUI online bringen (SwarmUI Settings → Restart ComfyUI Backend)
2. Modelle via SwarmUI downloaden (siehe oben)
3. WanAnimate-Workflow-JSON in ComfyUI laden
4. Katharina-Master als reference_image
5. Hüpf-Video als pose_video
6. Output: animation in /output/

## Alternative: ComfyUI Manager (wenn online)
- Settings → Install Custom Nodes → "ComfyUI-WanVideoWrapper" (Kijai)
- "ComfyUI-Manager" für einfachere Verwaltung
