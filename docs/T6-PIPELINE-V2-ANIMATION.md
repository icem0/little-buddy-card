# T6 v2 — Pixel-Art + Animation Pipeline (State-Specific Idle Loops)

> Erweitert T6 v1 um Animation. Stand: 2026-07-07. Ziel: GIF-Idle-Animationen pro Mood.

## 🧠 DIE 3 IDLE-PHILOSOPHIEN

**Jeder Mood = EIGENER Idle-Loop.** Ein trauriges Wesen atmet anders als ein glückliches.

| Mood | Idle-Charakter | Frame-Animation |
|------|----------------|-----------------|
| **happy** | Sanftes Hüpfen, Augen funkeln | 2-3 frames: up/down/up |
| **sad** | Kopf hängt, leichter Tremor | 3-4 frames: droop/droop+slight-bounce |
| **hungry** | Magen reibt sich, leckt Lippen | 3 frames: arm-rub-belly/lick |
| **thirsty** | Schaut suchend, Zunge raus | 3 frames: look-around/tongue-out |
| **sleepy** | Gähnen, Augen zu/auf | 4 frames: yawn-half-yawn-eyes-closed |
| **angry** | Zittert vor Wut, Dampf steigt | 3 frames: shake/shake/steam-puff |
| **playful** | Springt rum, wedelt | 4 frames: hop-left/hop-right/wiggle |

## 📊 FRAME-ANZAHL-INDUSTRIE-STANDARD

| Animation | Frames | FPS | Anwendungsfall |
|-----------|--------|-----|----------------|
| **Idle** | **2-4** | 4-8 | Atmen, Wippen, Glitzern |
| Walk | 4-8 | 8-12 | 4 für 16×16, 6-8 für 32×32+ |
| Run | 6-8 | 12-15 | Schnellere Bewegung |
| Jump | 3-5 | 8 | Anticipation + Air + Land |
| Attack | 3-6 | 10-15 | Wind-up + Strike + Recovery |
| Hit/Recoil | 2-3 | 12 | Flash + Rückstoß |
| Death | 4-6 | 8 | One-shot, kein Loop |

**Für Little Buddy Card:**
- **Idle pro Mood:** 2-4 Frames × 7 Moods × 5 Levels = **70-140 Frames total**
- **Plus 1 Tree pro Stage:** 1-2 Frames (Wackeln im Wind) × 5 = 5-10 Frames

## 🎬 ANIMATIONS-GENERIERUNG: DREI METHODEN

### Methode A: **Frame-by-Frame via ComfyUI + LoRA (Empfohlen)**
- 1 "Key Frame" pro Mood generieren (via raehoshi + pixel-art-xl LoRA)
- ComfyUI Node "Image Variation" mit **fixem seed + small variations**
- Post-Process: zusammenkleben → GIF

**Pros:** Maximale Kontrolle, deterministisch
**Cons:** Hand-Arbeit für jeden Mood

### Methode B: **WAN 2.2 Img2Vid (Cinematic, aber schwer für Pixel-Art)**
- Per Civitai-Artikel: WAN 2.2 ist SDXL-kompatibel und liefert coole Animationen
- Du hast schon **WAN** im SwarmUI-Model-Folder! 🎯
- Aber: WAN 2.2 erzeugt cinematische Bewegung, NICHT pixel-perfekt

**Pros:** Funktioniert out-of-the-box via SwarmUI
**Cons:** Frame-Konsistenz bei 32×32 problematisch, oft "wabbernde" Pixel

### Methode C: **AnimateDiff mit SD 1.5 (VERWORFEN)**
- Laut Civitai-Artikel: **funktioniert NICHT mit SDXL** — andere Latent Space, andere CLIP-Encoder
- Nur für SD 1.5 brauchbar → wir nutzen SDXL → **NEIN**

## 🎯 EMPFOHLENE METHODE: A + B HYBRID

**Phase 1: Key-Frame-Generierung** (Methode A, looping pro Mood)
```
Pro Mood: 4 Key-Frames generieren via raehoshi + pixel-art-xl + littlebuddy LoRA
  → Mood-spezifische Prompts: "subtle bounce, eyes sparkling" (happy)
  → Fixed seed pro Mood, kleine Variationen
```

**Phase 2: WAN 2.2 für dynamische "Eingangs-Animationen"** (Methode B)
- Beim Mood-Wechsel: kurze 1-Sekunden-Transition
- "Sad → Happy": WAN generiert "head lifting up, smile forming"
- Nutzt WAN 2.2 TI2V-5B (laut Civitai-Artikel das richtige Model)

**Phase 3: GIF-Assembly** (Python Skript)
- Frames in PIL zusammenbauen
- PIL: `Image.save("happy.gif", save_all=True, append_images=[...], duration=200, loop=0)`

## 💾 ENDGÜLTIGE FRAME-STRUKTUR

```
assets/
├── pets/
│   ├── level_1/
│   │   ├── happy/{01,02,03,04}.png  + happy.gif
│   │   ├── sad/{01,02,03,04}.png    + sad.gif
│   │   ├── hungry/{01,02,03}.png    + hungry.gif
│   │   ├── thirsty/{01,02,03}.png   + thirsty.gif
│   │   ├── sleepy/{01,02,03,04}.png + sleepy.gif
│   │   ├── angry/{01,02,03}.png     + angry.gif
│   │   └── playful/{01,02,03,04}.png+ playful.gif
│   ├── level_2/... (gleiche Struktur)
│   ├── level_3/...
│   ├── level_4/...
│   └── level_5/...
├── trees/
│   ├── seed.png
│   ├── sprout/{01,02}.png           + sprout.gif
│   ├── sapling/{01,02,03}.png       + sapling.gif
│   ├── young_tree/{01,02,03}.png    + young_tree.gif
│   └── full_grown/{01,02,03}.png    + full_grown.gif
└── transitions/  (WAN 2.2 outputs)
    ├── sad_to_happy.mp4
    ├── angry_to_playful.mp4
    └── ...
```

**Total: 35 GIFs + ~140 PNGs + ein paar Transitions**

## 🛠️ TECH-STACK FÜR T6 IMPLEMENTATION

### SwarmUI Setup
- Model: `raehoshi-illust-xl-3-sft` ✅ schon da
- LoRA: `nerijs/pixel-art-xl` herunterladen (via SwarmUI WebUI)
- Optional: `WAN 2.2 TI2V-5B FP16` für Transitions (laut Civitai-Anleitung)

### Local Tools
- **kohya_ss** für LoRA-Training
- **Pillow (PIL)** für GIF-Assembly + Pixel-Resize
- **rembg** für Background-Removal
- **FFmpeg** optional für MP4-Konvertierung

### Prompts pro Mood (für Key-Frame-Generierung)

```python
MOOD_PROMPTS = {
    "happy": {
        "positive": "littlebuddy, chibi creature, gentle bounce, eyes sparkling, smiling, soft glow, pixel art, white background, simple, flat colors",
        "negative": "nsfw, sad, dark, complex, blurry, 3d, realistic",
        "frames": 3,  # 3 slight bounces
    },
    "sad": {
        "positive": "littlebuddy, chibi creature, head down, droopy eyes, tear drop, slight tremble, pixel art, white background, simple, flat colors",
        "negative": "nsfw, happy, smile, complex, blurry, 3d, realistic",
        "frames": 3,
    },
    "hungry": {
        "positive": "littlebuddy, chibi creature, tummy rub, licking lips, looking at empty bowl, pixel art, white background, simple, flat colors",
        "negative": "nsfw, full, fed, complex, blurry, 3d, realistic",
        "frames": 3,
    },
    "thirsty": {
        "positive": "littlebuddy, chibi creature, tongue out, looking around, slight wobble, pixel art, white background, simple, flat colors",
        "negative": "nsfw, water, full, complex, blurry, 3d, realistic",
        "frames": 3,
    },
    "sleepy": {
        "positive": "littlebuddy, chibi creature, yawning, eyes half-closed, drowsy, Z-Z-Z, pixel art, white background, simple, flat colors",
        "negative": "nsfw, alert, awake, complex, blurry, 3d, realistic",
        "frames": 4,
    },
    "angry": {
        "positive": "littlebuddy, chibi creature, shaking, steam puff, sharp eyes, cross mark, pixel art, white background, simple, flat colors",
        "negative": "nsfw, calm, peaceful, complex, blurry, 3d, realistic",
        "frames": 3,
    },
    "playful": {
        "positive": "littlebuddy, chibi creature, hopping, wagging tail, sparkling eyes, action pose, pixel art, white background, simple, flat colors",
        "negative": "nsfw, tired, sad, complex, blurry, 3d, realistic",
        "frames": 4,
    },
}
```

## 🐾 LITTLE BUDDY CARD: GIF-RENDERING IM FRONTEND

Im LitElement:
```typescript
// Card-Config: GIF-URL basiert auf Mood + Level
const gifUrl = `${baseUrl}/assets/pets/level_${level}/${mood}.gif`;

// HTML: <img> mit GIF-Quelle
html`<img src="${gifUrl}" alt="Little Buddy ${mood}" />`;

// State-Change-Animation: opacity fade
<style>
  ha-card { transition: opacity 0.3s ease-in-out; }
</style>
```

## 🎬 ANIMATION TIMING (GIF-Frame-Durations)

| Mood | Frame-Dauer (ms) | Loop-Typ | Begründung |
|------|------------------|----------|------------|
| happy | 250 | bounce | 4 fps = entspannt |
| sad | 400 | droop | 2.5 fps = langsam, lethargisch |
| hungry | 200 | rub | 5 fps = nervös |
| thirsty | 300 | lick | 3.3 fps = suchend |
| sleepy | 600 | yawn | 1.6 fps = träge |
| angry | 150 | shake | 6.6 fps = zittrig |
| playful | 180 | hop | 5.5 fps = energiegeladen |

**Frame-Duration pro GIF konfigurierbar im Mood-Prompt oder im GIF-Metadata (PIL setzt das beim save_all).**

## 🔑 KEY-POINT: STATE-MACHINE FÜR MOOD-WECHSEL

Frontend muss bei Mood-Wechsel das GIF-Asset wechseln:
```typescript
// State subscription
this._hassSubscription = subscribeEntities((entities) => {
  const mood = entities['input_select.little_buddy_mood'];
  if (mood.state !== this._currentMood) {
    this._currentMood = mood.state;
    this.requestUpdate();  // re-renders with new GIF src
  }
});
```

Optional: WAN 2.2 Transition-Video zwischen den GIFs abspielen (1-2 Sekunden cinematic cross-fade).

## 📊 ZEIT-SCHÄTZUNG (REVISED)

| Phase | Dauer |
|-------|-------|
| Reference-Set (21 Bilder) | ~10 min |
| littlebuddy LoRA Training | ~30-60 min |
| 35 Mood-Key-Frames (5 levels × 7 moods) | ~30 min |
| Frame-Variations pro Key (2-3) | ~60-90 min |
| Post-Processing (resize + BG-removal) | ~15 min |
| GIF-Assembly (35 GIFs) | ~10 min |
| Tree-Animationen (5 Stages × 1-3 frames) | ~20 min |
| Optional: WAN 2.2 Transitions (7) | ~30 min |

**Total: 3-5 Stunden für komplettes animiertes Asset-Set.**

## 🔗 QUELLEN

- [Civitai: Build an SDXL Img2Vid Workflow with AnimateDiff (WARUM WAN 2.2 die Antwort ist)](https://civitai.com/articles/19005/build-an-sdxl-img2vid-workflow-with-animatediffand-why-wan-22-is-the-answer)
- [Reddit: SDXL NoobAI Sprite to Perfect Loop Animations via WAN 2.2 FLF](https://www.reddit.com/r/StableDiffusion/comments/1n51gg9/sdxl_il_noobai_sprite_to_perfect_loop_animations/)
- [Sprite-AI: Sprite Animation Frames — How Many Do You Actually Need?](https://www.sprite-ai.art/blog/sprite-animation-frames)
- [Pixel-Editor: Sprite Animation Fundamentals](https://www.pixel-editor.com/articles/sprite-animation-fundamentals)
- [Llamagen: AI Pixel Art Generator for Sprites, Sprite Sheets & Game Assets](https://llamagen.ai/ai-pixel-art-generator)
- [Cobalt Explorer: Character Sheets for Stable Diffusion](https://cobaltexplorer.com/2023/06/character-sheets-for-stable-diffusion/)
- [Apatero: Generate Clean Spritesheets in ComfyUI](https://apatero.com/blog/generate-clean-spritesheets-comfyui-guide-2025)
