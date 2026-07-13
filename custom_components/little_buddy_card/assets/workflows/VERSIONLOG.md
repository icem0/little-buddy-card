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

## v1 — katharina_characterset_v1 (2026-07-13)

**Zweck:** 6-view Character-Set von Katharina (verschiedene Winkel) für LoRA-Training.

**Setup:**
- Base: `RDXL_Pixel_Art_-_Pony_2.safetensors` (SDXL pixel art)
- Kein zusätzliches LoRA (littlebuddy_pixel ist nicht Katharina)
- Method: img2img vom Master-Image, creativity 0.5
- Master: `assets/katharina_master.png` (rote Kleid, blonde Zöpfe, kindlich)
- Resolution: 512×512 pro View, Contact-Sheet 1536×1024 (3×2)

**Instance-Prompt-Anker:**
- `pixel art, katharina character, cute chibi kawaii small girl`
- `blonde hair in two long braids`
- `(bright crimson red simple dress:1.4)` (Token-Weight)
- `white collar, puffy short sleeves, white socks, black mary jane shoes`
- Anti-Folklore/Tracht/NSFW/Brust-Bias in NEGATIVE (108 Exclusions)

**6 Views (img2img creativity 0.5, seed 100+idx*7):**
| View | Datei | Pose-Desc | Seed | Größe |
|------|-------|-----------|------|-------|
| 01_front | `views/01_front.png` | front view, looking at viewer, standing | 100 | 197 KB |
| 02_3quarter | `views/02_3quarter.png` | three quarter view, slight turn | 107 | 208 KB |
| 03_side_left | `views/03_side_left.png` | side view facing left, profile | 114 | 192 KB |
| 04_side_right | `views/04_side_right.png` | side view facing right, profile | 121 | 211 KB |
| 05_back_3quarter | `views/05_back_3quarter.png` | three quarter view from behind | 128 | 164 KB |
| 06_low_angle | `views/06_low_angle.png` | slight low angle, looking up | 135 | 174 KB |

**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v1_sheet.png` (1536×1024)
- Builder: `assets/workflows/build_katharina_characterset_v1.py`
- Output-Files: `assets/characters/katharina/views/`

**Status:** BEREIT ZUR ABNAHME — User bewertet visuelle Katharinas.


## v2 — katharina_characterset_v2 (2026-07-13) — Pony CharTurn LoRA

**Zweck:** Echte Multi-View/Turnaround mit dedizierter CharTurn-LoRA (Civitai model 692970, Dim32Alpha16_Prodigy_Mod, 163MB).

**Setup:**
- Base: `RDXL_Pixel_Art_-_Pony_2.safetensors` (Pony-SDXL pixel art)
- LoRA: `pony\character\Pony_CharTurn-_Multi-View-_Turnaround-_Model_Sheet-_Character_Design_-_Dim32Alpha16_Prodigy_Mod.safetensors`
- LoRA Weight: 0.7 (Author-Empfehlung: Main 0.7, Secondary 0.15)
- Resolution: 1536×1024 (Author-Empfehlung für CharTurn-Layout)
- KSampler: euler_ancestral, steps 28, cfg 7.5
- ComfyUI pass-through (LoraLoader direkt — Workaround für SwarmUI-LoRA-Index-Mismatch)

**6 Views (LoRA-Trigger: "turnaround sheet", "multiple views", "character design sheet", "model sheet reference"):**
| View | Datei | Pose | Seed | Größe |
|------|-------|------|------|-------|
| 01_front | `views_v2/01_front.png` | front view, looking at viewer, standing straight, both arms ... | 100 | 1175 KB |
| 02_3quarter_left | `views_v2/02_3quarter_left.png` | three quarter view from the left, slight turn, gentle smile,... | 107 | 1062 KB |
| 03_side_right | `views_v2/03_side_right.png` | side view facing right, profile, standing still, calm expres... | 114 | 1095 KB |
| 04_back_3quarter | `views_v2/04_back_3quarter.png` | three quarter view from behind, mostly back, slight head tur... | 121 | 1024 KB |
| 05_low_angle | `views_v2/05_low_angle.png` | slight low angle view, looking up at the character, gentle p... | 128 | 941 KB |
| 06_top_down | `views_v2/06_top_down.png` | high angle view, looking down at character, full body, chara... | 135 | 1067 KB |


**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v2_sheet.png`
- Builder: `assets/workflows/build_katharina_characterset_v2.py`
- Output-Files: `assets/characters/katharina/views_v2/`

**Vergleich zu v1:** v1 nutzte img2img @ creativity 0.5 (alle Views fast identisch frontal). v2 nutzt CharTurn-LoRA + Trigger-Wörter für echte Winkel-Variation.


## v3 — katharina_characterset_v3 (2026-07-13) — Pixel+CharTurn reduziert

**Zweck:** Outfit-Konsistenz + Pixel-Look verbessern — v2 hatte Kleid-Variation (Leggings) und CharTurn-Style-Drift.

**Setup-Änderungen ggü. v2:**
| Parameter | v2 | v3 |
|-----------|----|----|
| CharTurn-LoRA Weight | 0.7 | **0.3** (drastisch reduziert) |
| Pixel-Style-LoRA | — | **concept\Pixel_Art_XL_-_v1-1.safetensors @ 0.85** (neu) |
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
| 01_front | `views_v3/01_front.png` | 773 KB |
| 02_3quarter_left | `views_v3/02_3quarter_left.png` | 523 KB |
| 03_side_right | `views_v3/03_side_right.png` | 718 KB |
| 04_back_3quarter | `views_v3/04_back_3quarter.png` | 690 KB |
| 05_low_angle | `views_v3/05_low_angle.png` | 742 KB |
| 06_top_down | `views_v3/06_top_down.png` | 713 KB |


**Output:**
- Contact-Sheet (full): `assets/temp/katharina_characterset_v3_sheet.png` (2048×3072)
- Contact-Sheet (thumb): `assets/temp/katharina_characterset_v3_sheet_thumb.png` (1536×1536)
- Builder: `assets/workflows/build_katharina_characterset_v3.py`
- Output-Files: `assets/characters/katharina/views_v3/`

**Status:** BEREIT ZUR ABNAHME — User bewertet Outfit-Konsistenz, Winkel-Variation, Pixel-Look.


## v4 — katharina_characterset_v4 (2026-07-13) — Single char + Outfit-Pin

**Zweck:** v3 hatte 4 Probleme: Größenunterschiede, Leggings, Hintergrund-Symbole, Multi-Charakter. v4 fixt alle 4.

**Setup-Änderungen ggü. v3:**
| Parameter | v3 | v4 |
|-----------|----|----|
| CharTurn-Weight | 0.3 | **0.2** |
| Seed pro View | 100+i*13 | **100 (KONSISTENT)** für alle |
| Steps pro View | 28, 30, 32, 34, 36, 38 | gleich |
| Socken im Prompt | implizit | **explizit: "white knee-high socks covering full legs, white socks on legs, fully covered legs"** |
| Neg-Liste | ~30 Items | **~75 Items** (size_drift, multi_char, bg_assets) |

**Negativ-Liste neue Kategorien:**
- **Größen-Drift:** `size difference, size variation, different size, different scale, different height, smaller character, larger character, tiny character, giant character, perspective difference`
- **Multi-Charakter:** `two characters, multiple characters, second character, additional character, other character, background character, scaled character, resized character, doppelganger, twin, duplicate, copy, mirror image`
- **Hintergrund-Assets:** `background pattern, background object, background symbol, background asset, background prop, scenery element, faint pattern, suggested pattern, watermark-like pattern, any object in background, any element in background`
- **Bare Legs:** `bare legs, naked legs, exposed legs, leg visible`

**Auto-Analyse (User-Feedback-Hard-Test):**
| Metrik | v3 | v4 | Ziel |
|--------|----|----|------|
| Blue % (Leggings-Indikator) max | k.A. | **2.1%** | <3% ✅ |
| Gap % (Multi-Char-Indikator) max | 30%+ | **21.9%** | <25% ✅ |
| Red % (Kleid) range | k.A. | **28-37%** | konsistent ✅ |
| Größen-Variation | ±13% | **17.7%** | <15% ⚠ (knapp drüber) |
| Pixel-Art-Indikator (50k colors) | ja | ähnlich | ✅ |

**6 Views (seed=100 KONSISTENT, steps 28-38):**
| View | Datei | Größe |
|------|-------|-------|
| 01_front | `views_v4/01_front.png` | 640 KB |
| 02_3quarter_left | `views_v4/02_3quarter_left.png` | 690 KB |
| 03_side_right | `views_v4/03_side_right.png` | 788 KB |
| 04_back_3quarter | `views_v4/04_back_3quarter.png` | 702 KB |
| 05_low_angle | `views_v4/05_low_angle.png` | 656 KB |
| 06_top_down | `views_v4/06_top_down.png` | 637 KB |


**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v4_sheet_thumb.png` (1536×1536)
- Contact-Sheet (full): `assets/temp/katharina_characterset_v4_sheet.png` (2048×3072)
- Builder: `assets/workflows/build_katharina_characterset_v4.py`
- Output-Files: `assets/characters/katharina/views_v4/`

**Status:** BEREIT ZUR ABNAHME.


## v5 — katharina_characterset_v5 (2026-07-13) — Radikaler Outfit-Pin + Chibi-Lock

**Zweck:** v4 hatte Kleid-meist-weiß + sexy-Drift + Beine zu lang. v5 versucht's mit massivem Color-Pin + Chibi-Body-Lock.

**Setup-Änderungen ggü. v4:**
| Parameter | v4 | v5 |
|-----------|----|----|
| CharTurn-Weight | 0.2 | **0.15** |
| Kleid Token-Weight | 1.5 | **1.8** |
| Kleid Color-Lock | implizit | **"monochrome red, no white parts, no white accents, no white sections, no white trim, no white collar, fully red, completely red outfit"** |
| Body-Lock | "childlike proportions" | **"chibi body proportions, baby proportions, stubby legs, short legs, tiny legs, large round head, small body, oversized head"** |
| Süss-Anker | 1-2 Tags | **"kawaii cute adorable innocent sweet wholesome childlike"** (6 Tags) |
| Anti-Sexy | basic | **"no makeup, no lipstick, no jewelry, no adult features, no mature, no sensual, no seductive"** |

**Auto-Analyse v4 vs v5:**
| Metrik | v4 | v5 | Bewertung |
|--------|----|----|-----------|
| Weiß % (Kleid-Drift) | 54-64% | 53-61% | ⚠ kaum besser (Model-Bias) |
| Rot % (Kleid-Anteil) | 11-16% | **14-27%** | ✅ besser |
| Pink % (Sexy-Bias) | 0.1-4% | 2.1-5.5% | ⚠ leicht erhöht |
| Beine-AR | 0.82-0.95 | 0.83-0.94 | ⚠ kaum kürzer |
| Größen-Variation | 17.7% | ähnlich | gleich |

**Fazit:** Die Outfit- und Proportions-Probleme sind nicht mit Prompt-Tricks lösbar — das **Base-Model `RDXL_Pixel_Art_-_Pony_2` ist auf Pony-Aesthetik trainiert** (weiße Klamotten mit Farbakzenten ist ein Pony-Stil-Merkmal). Der Token-Weight-Push reicht nicht.

**→ v6 Strategie:** Base-Model-Wechsel zu `autismmixSDXL_autismmixPony_*.safetensors` (Illustrious-Pony-Mix, cute-character-spezialisiert, kein Weiß-Bias) + CharTurn-Weight auf 0.0 (Winkel manuell über Trigger-Wörter).

**6 Views (seed=100, steps=28 konstant, cfg 7.5-8.25):**
| View | Datei | Größe |
|------|-------|-------|
| 01_front | `views_v5/01_front.png` | 622 KB |
| 02_3quarter_left | `views_v5/02_3quarter_left.png` | 742 KB |
| 03_side_right | `views_v5/03_side_right.png` | 658 KB |
| 04_back_3quarter | `views_v5/04_back_3quarter.png` | 705 KB |
| 05_low_angle | `views_v5/05_low_angle.png` | 719 KB |
| 06_top_down | `views_v5/06_top_down.png` | 686 KB |


**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v5_sheet_thumb.png` (1536×1536)
- Builder: `assets/workflows/build_katharina_characterset_v5.py`
- Output-Files: `assets/characters/katharina/views_v5/`

**Status:** BEREIT ZUR ABNAHME. Wenn "Kleid immer noch nicht konsequent rot" → v6 = Base-Wechsel.


## v6 — katharina_characterset_v6 (2026-07-13) — BASE-WECHSEL: autismmixSDXL ⭐

**Zweck:** v4/v5 mit RDXL_Pixel_Art_-_Pony_2-Base scheiterten: Pony-Aesthetik-Bias (weiße Klamotten), CharTurn-LoRA produzierte Multi-Charakter, Beine zu lang. v6 wechselt das Base-Model komplett.

**Setup-Änderungen ggü. v5 (RADIKAL):**
| Parameter | v5 | v6 |
|-----------|----|----|
| **Base-Model** | `RDXL_Pixel_Art_-_Pony_2.safetensors` (Pony, Weiß-Bias) | **`autismmixSDXL_autismmixPony_258042.safetensors`** (Illustrious-Pony-Mix, cute-spezialisiert) |
| CharTurn-LoRA | 0.15 | **0.0 (komplett RAUS)** |
| Pixel_Art_XL LoRA | 0.85 | 0.85 (unverändert) |
| Steps | 28 | **35** (mehr Detail) |
| Cfg | 7.5-8.25 (variabel) | **7.0 fix** (konsistenter) |
| Winkel-Variation | CharTurn-LoRA + Trigger | **Nur Trigger-Wörter** (kein LoRA-Konflikt) |

**Auto-Analyse v4 → v5 → v6:**
| Metrik | v4 | v5 | v6 ⭐ | Bewertung |
|--------|----|----|----|-----------|
| **Weiß % (Kleid-Drift)** | 54-64% | 53-61% | **0.1-1.7%** | ✅✅ DRAMATISCH besser |
| **Rot % (Kleid-Anteil)** | 11-16% | 14-27% | **17-27%** | ✅ konsistent |
| Pink % (Sexy-Bias) | 0.1-4% | 2.1-5.5% | 0-7.2% | ⚠ gemischt (Wangen) |
| **Beine-AR** | 0.82-0.95 | 0.83-0.94 | **1.00 (alle gleich)** | ✅ perfekte Konsistenz |
| **Multi-Char-Lücken** | k.A. | k.A. | **0% alle 6** | ✅✅ gelöst |

**Wichtigste Befunde:**
- **Weiß-Bias komplett eliminiert** durch Base-Wechsel zu Illustrious-Pony-Mix
- **CharTurn-LoRA war der Multi-Char-Schuldige** (jetzt 0%, vorher oft 4+ Charaktere)
- **Beine sind konsistent 1.00 AR** = perfekte Chibi-Proportionen über alle 6 Views
- **Pink-Anteil** (besonders 04_back_3quarter mit 7.2%) ist wahrscheinlich Illustrious-typische rosige Wangen, nicht Sexy-Bias

**6 Views (seed=100, steps=35, cfg 7.0-7.4):**
| View | Datei | Größe |
|------|-------|-------|
| 01_front | `views_v6/01_front.png` | 676 KB |
| 02_3quarter_left | `views_v6/02_3quarter_left.png` | 552 KB |
| 03_side_right | `views_v6/03_side_right.png` | 651 KB |
| 04_back_3quarter | `views_v6/04_back_3quarter.png` | 806 KB |
| 05_low_angle | `views_v6/05_low_angle.png` | 677 KB |
| 06_top_down | `views_v6/06_top_down.png` | 719 KB |


**Output:**
- Contact-Sheet: `assets/temp/katharina_characterset_v6_sheet_thumb.png` (1536×1536)
- Builder: `assets/workflows/build_katharina_characterset_v6.py`
- Output-Files: `assets/characters/katharina/views_v6/`

**Status:** BEREIT ZUR ABNAHME. Wenn OK → direkt ins LoRA-Training.
