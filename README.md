# Little Buddy Card 🌱🐾

A **gamified Lovelace card** for [Home Assistant](https://www.home-assistant.io/) with growable pixel-art pets and trees. Track XP, levels, mood, learning progress, and more — directly on your dashboard.

## ✨ Features

- **Growable companions** — Pixel pets that evolve through 5 levels (Egg → Hatchling → Young → Adult → Elder)
- **Dynamic tree growth** — A companion tree that grows from seed to mighty oak based on your activity/XP
- **Mood system** — 7 emotions (happy, sad, hungry, thirsty, sleepy, angry, playful) with animated GIF states
- **Gamification loop** — XP, level progression (1–50), stat tracking (Health, Hunger, Energy, Happiness)
- **Multi-language** — English 🇬🇧 and German 🇩🇪 support out of the box
- **Interactive** — Click on your pet to gain XP (configurable amount)
- **No Python backend needed** — Pure Lovelace card + native HA entities (`input_select`, `input_number`, `template` sensors, automations)

## 📋 Requirements

- Home Assistant ≥ 2024.1
- [HACS](https://hacs.xyz/) (Home Assistant Community Store)

## 📦 Installation

### Via HACS (Recommended)

1. Open **HACS** → **Frontend** → **Explore & Download Repositories**
2. Search for **Little Buddy Card**
3. Click **Download**

### Manual Installation

```bash
# Clone into your HA config's www directory
cd /config/www/community/
git clone https://github.com/icem0/little-buddy-card.git little-buddy-card
```

Then add to `configuration.yaml`:

```yaml
lovelace:
  modules:
    - /community_little-buddy-card/little-buddy-card.js
```

## 🛠️ Setup

### Step 1: Create HA Entities

Add these helpers in **Settings → Devices & Services → Helpers**:

| Helper | Type | Options/Range |
|--------|------|-------------|
| `input_select.little_buddy_mood` | Select | happy, sad, hungry, thirsty, sleepy, angry, playful |
| `input_number.little_buddy_xp` | Number (int) | 0–50000 |
| `input_number.little_buddy_level` | Number (int) | 1–50 |
| `input_number.little_buddy_health` | Number (int) | 0–100 |
| `input_number.little_buddy_hunger` | Number (int) | 0–100 |
| `input_number.little_buddy_energy` | Number (int) | 0–100 |
| `input_number.little_buddy_happiness` | Number (int) | 0–100 |
| `input_select.little_buddy_tree_level` | Select | seed, sprout, sapling, young_tree, full_grown |
| `input_bool.little_buddy_is_awake` | Boolean | — |

Optional entities (if you want to use them):

| Helper | Type | Options/Range |
|--------|------|-------------|
| `input_number.little_buddy_xp_per_click` | Number (int) | 1–100 (default: 10) |
| `input_text.little_buddy_gif_url` | Text | URL to a GIF (overrides pet image) |
| `input_text.little_buddy_tree_gif_url` | Text | URL to a GIF (overrides tree image) |

### Step 2: Add Template Sensors (Optional but recommended)

If you want to use the card without manually updating the level, you can add these template sensors to automatically compute level from XP:

```yaml
template:
  - sensor:
      - name: "Little Buddy GIF URL"
        state: >
          {% set mood = states('input_select.little_buddy_mood') %}
          {% set level = states('input_number.little_buddy_level') | int(1) %}
          '/local/little-buddy-card/pets/level_{{ min(level, 5) }}/{{ mood }}.gif'
      - name: "Little Buddy Tree GIF"
        state: >
          {% set tree = states('input_select.little_buddy_tree_level') %}
          '/local/little-buddy-card/trees/{{ tree }}.gif'
```

### Step 3: Add to Lovelace Dashboard

**Option A — Visual editor (recommended):**
1. Open your dashboard in **Edit** mode → **+ Add Card**.
2. Search for **Little Buddy Card** (registered automatically via `window.customCards`).
3. Click it → the configuration panel opens. Pick your entities from the dropdowns, set a name, and optionally add **mood triggers** (which mood is activated by which entity state).
4. Done — no YAML needed.

**Option B — YAML:**

```yaml
type: custom:little-buddy-card
title: "Little Buddy"
entities:
  mood: input_select.little_buddy_mood
  xp: input_number.little_buddy_xp
  level: input_number.little_buddy_level
  health: input_number.little_buddy_health
  hunger: input_number.little_buddy_hunger
  energy: input_number.little_buddy_energy
  happiness: input_number.little_buddy_happiness
  tree_level: input_select.little_buddy_tree_level
  gif_url: sensor.little_buddy_gif_url
  tree_gif_url: sensor.little_buddy_tree_gif
  xp_per_click: input_number.little_buddy_xp_per_click
```

### Mood triggers (optional)

Instead of (or in addition to) the `mood` entity, you can let **other entities**
drive the pet's mood. In the visual editor, open **"Mood triggers"** and add
rules. The first rule whose entity state matches wins; otherwise the `mood`
entity is used. Example YAML equivalent:

```yaml
type: custom:little-buddy-card
name: "Buddy"
xp: input_number.little_buddy_xp
mood: input_select.little_buddy_mood
moods:
  - mood: sleepy      # if bedroom_light == "off"
    entity: light.bedroom
    state: "off"
  - mood: hungry      # if fridge_door just opened
    entity: binary_sensor.fridge_door
    state: "on"
  - mood: angry       # if alarm is triggered
    entity: alarm_control_panel.home
    state: "triggered"
```

This lets you map *any* Home Assistant entity/state to one of the 7 moods
(happy, sad, hungry, thirsty, sleepy, angry, playful) — without touching
automations.

### Actions (tap / hold / double-tap)

The pet card responds to interactions. By default, **tapping the pet grants
XP** (amount from `xp_per_click`, default 10). You can override this with a
custom `tap_action`, and add `hold_action` / `double_tap_action` (full HA
action schema — same as any Lovelace card):

```yaml
type: custom:little-buddy-card
name: "{{ states('sensor.buddy_name') }}"   # live template!
xp: input_number.little_buddy_xp
mood: input_select.little_buddy_mood
tap_action:
  action: toggle
  entity: light.bedroom
hold_action:
  action: perform-action
  service: input_number.set_value
  data:
    entity_id: input_number.little_buddy_happiness
    value: 100
double_tap_action:
  action: more-info
  entity: input_number.little_buddy_xp
```

> **Live templates:** `name` (and `title`) accept Jinja templates — they
> update in real time via HA's websocket template subscription.

### Asset extension (dev vs. final art)

The card loads sprites from `/local/little-buddy-card/...`. While the animated
GIF art pipeline is in progress, set `asset_ext: png` (default) to use the
static placeholder PNGs shipped in `assets/`. Flip to `asset_ext: gif` once
the real pixel-art sprites land — no code change needed, just drop the GIFs at
the same paths.

## 🍄 Mushroom-style integration

The card follows the Mushroom card conventions so it feels at home next to
other Mushroom cards:

- Registers via `registerCustomCard()` (picker shows a **preview** + **docs link**)
- Theme-aware: uses HA CSS variables (`--card-background-color`, `--accent-color`, `--mush-spacing`, …)
- Visual editor built on HA's native `<ha-form>` with entity pickers
- Live template rendering via `subscribeRenderTemplate`

## 🎮 Gamification Mechanics

### XP System

- **XP Sources:** Learning app events, automation triggers, manual service calls, or clicking on the pet
- **Level Thresholds:** Level N requires `N * 1000` total XP
- **Tree Growth:** Every 5 levels → next tree stage (seed → sprout → sapling → young_tree → full_grown)

### Mood Decay

Automations decay mood stats over time:

- Hunger increases by +2 every 30 min (max 100)
- Energy decreases by -3 every hour while awake
- Happiness drops when hunger > 70 or energy < 20

### Actions (Service Calls)

```yaml
# Feed your buddy
- service: input_number.set_value
  data: { entity_id: input_number.little_buddy_hunger, value: "{{ states('input_number.little_buddy_hunger') | int - 30 }}" }

# Play with buddy (gain XP + boost happiness)
- service: python_script.gain_xp
  data: { amount: 50 }

# Or simply click on the pet in the card to gain XP (amount configurable via input_number.little_buddy_xp_per_click)
```

## 🌍 Localization

| Language | Status |
|----------|--------|
| 🇬🇧 English | ✅ Built-in |
| 🇩🇪 Deutsch | ✅ Built-in |

Auto-detected from HA locale. Override via `language: de` in card config.

## 🖼️ Pixel Art Assets

All GIFs are created with [ComfyUI](https://github.com/comfyanonymous/ComfyUI) + stable diffusion models fine-tuned for 32×32 pixel art style. Each pet has frames for all 7 mood states × 5 levels = **35 unique animations**, plus 5 tree stages.

## 🛠️ Development

```bash
npm install
npm run build   # Compile TypeScript → dist/little-buddy-card.js
npm run watch   # Auto-rebuild on changes
```

## 📄 License

MIT — See [LICENSE](LICENSE)