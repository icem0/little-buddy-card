# Little-Buddy-Card — Workflow Version Log

## Master v14 (2026-07-13) — FINALES KATHARINA-MASTER

**Beschreibung:** Sauberes, abgenommenes Master-Asset für alle weiteren Phasen (WanAnimate, LoRA-Training).

**Finale Spezifikationen (konsolidiert aus 14 Iterationen):**
- Base: `RDXL_Pixel_Art_-_Pony_2.safetensors` (Pony-SDXL)
- Resolution: 800×800
- Steps: 30, Cfg: 7.0, Sampler: euler_ancestral, Seed: 42
- **Pony-Standardformat:** score_9, score_8_up, score_7_up, score_6_up, source_anime
- **Quality:** masterpiece, best quality, amazing quality
- **Charakter:** pixel art, cute childlike small girl, (blonde_braids:1.3)
- **Outfit:** (bright crimson red dress:1.4), (long_dress:1.2), white peter pan collar, short puffy sleeves
- **Accessoires:** white knee-high socks, black mary jane shoes
- **Anatomie:** (chibi proportions:1.1), large round head, tiny limbs
- **Pose:** standing straight, both feet planted, both arms at sides
- **Schatten:** (neutral gray soft shadow under feet:1.2)
- **Hintergrund:** pure white background, no scenery, isolated character

**Was hat es gebraucht (Lessons Learned):**
- 14 Iterationen (v1-v14) für ein einziges abgenommenes Master
- Token-Weighting statt Begriffs-Listen
- Pony-Score-Tags (PFLICHT für Pony-Base, Anatomie-Bug ohne)
- Gras im Negativ (Hauptbias)
- Grünen Schatten explizit blocken
- "knee-length" raus (triggert Knie-Zeigen bei Chibi)
- "blonde_braids" zusammengesetzt statt "blonde hair in two long braids"
- 800×800 (512² produzierte Multi-Char-Bug)

**Pfade:**
- `assets/characters/katharina/master/katharina_master.png` (offiziell, 381 KB)
- `assets/katharina_master.png` (Standard-Pfad)
- `assets/temp/katharina_master.png` (WanAnimate-Input)

**NÄCHSTE PHASE:** WanAnimate — Master drehen, 49-Frame-Video mit verschiedenen Blickwinkeln
