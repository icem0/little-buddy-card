# Little Buddy Card 🌱🐾

A gamified Lovelace card for Home Assistant with growable pixel-art pets and trees.

## Features

- 5-stage pet evolution (Egg → Hatchling → Child → Adult → Elder)
- Companion tree that grows with your XP (Seed → Elder)
- 7 mood states (happy, sad, hungry, thirsty, sleepy, angry, playful)
- XP / level / stat tracking
- Mushroom-style visual editor (`ha-form`)
- Pure Lovelace — no Python backend required
- Update notifications: appears in **Home Assistant → Settings → System → Updates**

## Requirements

- Home Assistant **≥ 2024.1**
- HACS

## Installation

1. HACS → ⋮ → **Custom repositories** → Add `https://github.com/icem0/little-buddy-card`, Category **Plugin**
2. HACS → **Frontend** → search "Little Buddy Card" → **Download**
3. **Hard-refresh** (Ctrl+Shift+R)
4. Dashboard → Edit → **+ Add Card** → "Little Buddy Card"

## Updates

Home Assistant will notify you automatically. Open **Settings → System → Updates** and click **Update**.
