# Little Buddy Card — Home Assistant Backend Setup

This directory contains the complete backend configuration for the Little Buddy Card. It uses **native Home Assistant entities only** (no custom Python integration) — pure YAML configuration.

## 📁 Files Overview

```
homeassistant/
├── config/
│   ├── inputs.yaml                  # 10 input helpers (mood, stats, level, etc.)
│   └── template_sensors.yaml        # 4 template sensors (XP, progress, etc.)
├── automations/
│   └── little_buddy_mood_decay.yaml # 4 automations (decay, alerts, tree, sleep)
└── scripts/
    ├── little_buddy_gain_xp.yaml    # XP service with level-up + tree logic
    └── little_buddy_actions.yaml    # 5 action scripts (feed, play, sleep, water, pet)
```

## 🚀 Installation

### Option A: Use HA UI Helpers (Recommended)
1. Go to **Settings → Devices & Services → Helpers → Create Helper**
2. Create the following input helpers (one by one):

| Entity ID | Type | Notes |
|-----------|------|-------|
| `input_select.little_buddy_mood` | Select | options: happy, sad, hungry, thirsty, sleepy, angry, playful |
| `input_select.little_buddy_tree_stage` | Select | options: seed, sprout, sapling, young_tree, full_grown |
| `input_number.little_buddy_xp_total` | Number | min 0, max 50000, step 1 |
| `input_number.little_buddy_level` | Number | min 1, max 50, step 1 |
| `input_number.little_buddy_health` | Number | min 0, max 100, initial 80 |
| `input_number.little_buddy_hunger` | Number | min 0, max 100, initial 30 |
| `input_number.little_buddy_energy` | Number | min 0, max 100, initial 90 |
| `input_number.little_buddy_happiness` | Number | min 0, max 100, initial 75 |
| `input_boolean.little_buddy_is_awake` | Boolean | initial on |

### Option B: Copy YAML into `configuration.yaml`
Append all four files' contents to your HA `configuration.yaml`:

```yaml
# Top of configuration.yaml:
input_select: !include_dir_list includes/inputs/  # or paste from inputs.yaml
input_number: !include ...                        # or paste from inputs.yaml
input_boolean: !include ...

template: !include_dir_list ... # or paste from template_sensors.yaml

automation: !include_dir_list automations/
script: !include_dir_list scripts/
```

Or simply paste all the content blocks one after another.

## 🎮 How to Interact

### Service Calls (Developer Tools → Services)

```yaml
# Gain XP (e.g. from a learning app event)
- service: script.little_buddy_gain_xp
  data:
    amount: 100

# Feed your buddy
- service: script.little_buddy_feed

# Play together (boost happiness + XP)
- service: script.little_buddy_play

# Put to sleep (30 min cooldown)
- service: script.little_buddy_sleep

# Quick affection (no cost)
- service: script.little_buddy_pet
```

### Automation Hooks (Connect Your Apps)

To grant XP automatically from external triggers (e.g. learning apps, productivity completion):

```yaml
- alias: "Award XP for completed learning session"
  trigger:
    - platform: state
      entity_id: sensor.anki_cards_reviewed_today
      to: "50"
  action:
    - service: script.little_buddy_gain_xp
      data:
        amount: 50
```

## 📊 XP Curve

| Level | Total XP needed | Tree Stage |
|-------|----------------|------------|
| 1 | 0 | seed |
| 5 | 5,000 | sprout |
| 10 | 10,000 | sapling |
| 15 | 15,000 | young_tree |
| 25 | 25,000 | full_grown |
| 50 | 50,000 | full_grown (max) |

Formula: Level N requires `N × 1000` total XP.

## 🌍 Localization

Template sensor `sensor.little_buddy_mood_display` uses HA's `config.language` to render mood names in English or German. To use German, set `language: de` in your `configuration.yaml`:

```yaml
homeassistant:
  language: de
```

## 🔄 Mood Auto-Resolution

The `little_buddy_mood_decay` automation runs every 30 minutes and:

1. **Hunger ↑** by +3 (max 100)
2. **Energy ↓** by -5 (min 0)
3. **Auto-mood** based on stat thresholds:
   - hunger > 70 → "hungry"
   - energy < 25 → "sleepy"
   - happiness < 30 → "sad"
   - else: "happy"

## 🌙 Sleep Cycle

`little_buddy_sleep_cycle` automation:
- **23:00** → turns `awake` OFF, sets mood to "sleepy"
- **07:00** → restores energy to 100, sets mood to "happy"

## 🔌 Optional: Wire to Real Events

You can hook your Little Buddy into real Home Assistant events:

```yaml
# Award XP when Anki cards reviewed
- trigger:
    - platform: event
      event_type: ankier牌_session_complete
  action:
    - service: script.little_buddy_gain_xp
      data:
        amount: 30

# Auto-feed when kitchen activity detected
- trigger:
    - platform: state
      entity_id: binary_sensor.kitchen_motion
      to: "on"
      for: "00:10:00"
  action:
    - service: script.little_buddy_feed
```

## 📝 Notes

- All scripts are idempotent and safe to call multiple times
- Stat values are clamped to [0, 100] everywhere
- The level system caps at 50 (50,000 XP)
- No external services or APIs required
- The "Angry" mood is reserved for manual triggers (no auto-set yet)
