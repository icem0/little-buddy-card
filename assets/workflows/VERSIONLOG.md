# Workflow Version Control Standard — Katharina Hop Animation

## Regeln (gültig ab 2026-07-10)

1. **Jeder Workflow hat eine eindeutige Versionsnummer** `v{N}` — aufsteigend, nie überschreiben.
2. **Drei Artefakte pro Version** (im Ordner `assets/workflows/`):
   - `katharina_hop_v{N}_api.json` — API-Format (für `/ComfyBackendDirect/prompt`)
   - `katharina_hop_v{N}_ui.json` — UI-Format (für ComfyUI Workflows-Tab)
   - `build_katharina_hop_v{N}.py` — Builder-Script (from-scratch, reproduzierbar)
   - **WICHTIG:** Bei JEDER Änderung MUSS der Builder laufen (auch ohne `--submit`) → speichert lokal + ComfyUI-Tab automatisch. Kein lokales Script ohne ComfyUI-Tab-Eintrag!
3. **`latest` Symlink** zeigt immer auf die höchste getestete Version.
4. **`VERSIONLOG.md`** (diese Datei) dokumentiert pro Version:
   - Was geändert wurde
   - Welche Qualität (User-Feedback)
   - Seed + Auflösung
   - Output-Datei
5. **Keine "clean" / "v9" / "test" Namenswildnis** mehr — nur `v{N}`.
6. **txt2img-Workflows:** gleiche Regeln, Name `katharina_txt2img_v{N}` (Character-Set für LoRA-Training).

## Versionen

### v1–v10 (2026-07-07 bis 2026-07-08, Historie)
- Ursprüngliche Wan2.2 Animate Entwicklung, 6 Iterationen bis Erfolg (v6).
- v8: erster stabiler Workflow mit `SaveVideo` (MP4), 832×480, seed 42.
- Quelle: `swarmui-api` Skill, Sektion "L1–L9 WanAnimate-Lessons".

### v11–v12 (2026-07-08)
- `katharina_idle_hop_v11.gif`, `v12.gif` in `assets/animations/`.
- Keine API/UI-JSON erhalten — nur GIF-Output.

### v13 "clean" (2026-07-10, 09:00) — VERWORFEN
- Erster Versuch "übersichtlicher" Workflow.
- **Fehler:** `SaveImage` statt Video → 49 einzelne PNGs, kein Video.
- **Qualität:** Brei (59k unique colors statt 164 im Master → VAEDecode Noise).
- **Status:** ❌ Verworfen, nicht versioniert. Dateien: `katharina_hop_clean_*.json`.

### v14 (2026-07-10, 10:30) — AKTIV
- **Builder:** `build_katharina_hop_v9.py` → umbenannt zu `build_katharina_hop_v14.py`
- **Änderungen vs v8:**
  - Output: `SaveAnimatedWEBP` (animierte WebP-Datei) + `SwarmSaveAnimatedWebpWS` (SwarmUI-Delivery)
    → kein `CreateVideo`/`SaveVideo` Crash mehr
  - Auflösung: **512×512** (runter von 832×480 für schnellere Dev)
  - `widgets_values` Fix: KSampler `control_after_generate` explicit ("fixed") nach seed
    → kein Slot-Shift mehr (steps bleibt int)
  - Saubere Gruppierung: 5 farbige Gruppen, `_meta.title` auf jedem Node
  - Semantiche Node-IDs: 10s=Loaders, 20s=Encoders, 30s=Generator, 40s=Sampler, 50s=Output
- **Seed:** 777
- **Output:** `katharina_hop_00119_.webp` (53 Frames, 9.8MB, 512×512)
- **Status:** ✅ Funktioniert, wartet auf User-Abnahme
- **Bekannt:** 512×512 ist niedriger als v8's 832×480 — kann hochgedreht werden wenn Animation passt.

## Nächste Version (v15+)
- Wenn User "passt": Auflösung auf 832×480 (oder höher) hochdrehen.
- Wenn User "Verbessern": Prompt anpassen, mehr Frames (77), andere Sampler-Settings.
- Jede Änderung = neue Version + Eintrag hier.

## Quick Reference

| Version | Datum | Status | Output | Seed | Res | Notes |
|---------|-------|--------|--------|------|-----|-------|
| v8 | 07-08 | ✅ Referenz | MP4 | 42 | 832×480 | Alter stabiler Workflow |
| v13 "clean" | 07-10 | ❌ Verworfen | PNG×49 | 42 | 832×480 | Brei, SaveImage-Fehler |
| **v14** | **07-10** | **✅ Getestet** | **WebP** | **777** | **512×512** | **SaveAnimatedWEBP, ComfyUI-Tab vorhanden** |
| v15 | 07-10 | ✅ Getestet | WebP | 777 | 512×512 | Stärkerer Sprung-Prompt + neues Master |
| **txt2img_v1** | **07-10** | **✅ ComfyUI-Tab** | **PNG×8** | **1000+** | **800×800** | **RDXL Pixel Art + littlebuddy LoRA, Character-Set für LoRA-Training** |
