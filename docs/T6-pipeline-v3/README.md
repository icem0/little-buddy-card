# Wan 2.2 Animate Pipeline — Katharina Hüpf-Animation

**Erfolgreich getestet:** 2026-07-08 mit `prompt_id 9d29ffbf-a143-425e-8b13-35346e2262a8`

## Input Files
- **Katharina-Master:** `assets/temp/katharina_master.png` (1024x1024, RDXL_Pixel_Art_-_Pony_2 mit creativity 0.5)
- **Hüpf-Video:** `assets/temp/hop_video.mp4` (455KB, 8fps, gebaut aus 4 Frames)
  - Frame 1: am Boden
  - Frame 2: leichter Anhub
  - Frame 3: höchster Punkt (mid-air)
  - Frame 4: Landung

## Output
- **Video:** `assets/animations/katharina_idle_hop.mp4` (63KB, 832x480, 16fps, 49 frames, 3.3s)
- **Preview:** `assets/animations/katharina_idle_hop_preview.png`

## Workflow-Datei
- **Workflow-JSON (API-Format):** `wan_animate_workflow.json`

## Wie in ComfyUI laden
1. Öffne SwarmUI WebUI: `http://192.168.178.53:7801/`
2. Klicke "Open Workflow" → lade `wan_animate_workflow.json`
3. Lade dein eigenes Reference-Image als `katharina_master.png` in ComfyUI input
4. Lade dein eigenes Pose-Video als `hop_video.mp4` in ComfyUI input
5. Klicke "Queue Prompt" → 5-10 Minuten warten
6. Output landet in `ComfyUI/output/`

## Verwendete Modelle
| Node | Model |
|------|-------|
| UNETLoader | `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors` |
| CLIPLoader | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (im Clip-Ordner) |
| VAELoader | `Wan/wan_2.1_vae.safetensors` |
| CLIPVisionLoader | `clip_vision_h.safetensors` |

## Pipeline-Architektur
```
LoadImage (Katharina) ──┐
                        ├─→ CLIPVisionEncode → WanAnimateToVideo
LoadVideo (Hüpf) ─────┤                                       │
                        │      (mit ModelSamplingSD3 + shift=8)
CLIPTextEncode (+) ─────┤                                       │
CLIPTextEncode (-) ─────┘                                       │
                                                                ▼
                                                            VAEDecode
                                                                │
                                                                ▼
                                                          CreateVideo (16fps)
                                                                │
                                                                ▼
                                                            SaveVideo (mp4)
```

## Wichtige Learnings
1. **WanAnimate braucht nicht:** IP-Adapter, ControlNet, LoRA-Training — eingebaute `reference_image` + `pose_video` Inputs reichen
2. **Image-Stack-Reihenfolge im WanAnimate-Output:**
   - `output[0]` = positive (CONDITIONING)
   - `output[1]` = negative (CONDITIONING)
   - `output[2]` = **latent** ← den brauchen wir für VAEDecode
3. **GetVideoComponents.frame_count** muss mit `WanAnimateToVideo.length` übereinstimmen (hier: 49)
4. **Modell-Subtypes in SwarmUI:**
   - UMT5/T5 ist im **Clip-Ordner** (nicht T5-XXL wie gedacht)
   - Wan-VAEs im `Wan/` Subfolder
5. **Workflow-Fixes die nötig waren:**
   - `LoadVideo.video` → `LoadVideo.file`
   - `CLIPVisionEncode` braucht `crop="center"`
   - WanAnimateToVideo Output[2] = latent (nicht video)

## Nächste Schritte
- T6-2: Andere Animationen (Wave, Spin, Dance) — gleicher Workflow, anderes Pose-Video
- T6-3: Pixel-Art-Post-Processing (rembg Background-Removal, GIF-Export)
- T6-4: 7 Moods × 5 Levels = 35 Animations pipeline
