/**
 * Little Buddy Card — Gamified Lovelace Card for Home Assistant
 * A pixel-art pet/tree companion that grows based on XP and level.
 */
import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

/**
 * Detect active language from HA locale or fallback to browser default.
 */
function getLocale(hass) {
  if (hass?.locale?.language) return hass.locale.language;
  const nav = navigator.language || navigator.languages?.[0] || 'en';
  return nav.startsWith('de') ? 'de' : 'en';
}

/**
 * Embedded translations for the card UI.
 */
const STRINGS = {
  en: {
    mood_happy: 'Happy',
    mood_sad: 'Sad',
    mood_hungry: 'Hungry',
    mood_thirsty: 'Thirsty',
    mood_sleepy: 'Sleepy',
    mood_angry: 'Angry',
    mood_playful: 'Playful',
    level: 'Level',
    xp: 'XP',
    health: 'Health',
    hunger: 'Hunger',
    energy: 'Energy',
    happiness: 'Happiness',
    tree_level: 'Tree',
  },
  de: {
    mood_happy: 'Glücklich',
    mood_sad: 'Traurig',
    mood_hungry: 'Hungrig',
    mood_thirsty: 'Durstig',
    mood_sleepy: 'Müde',
    mood_angry: 'Wütend',
    mood_playful: 'Verspielt',
    level: 'Level',
    xp: 'XP',
    health: 'Gesundheit',
    hunger: 'Hunger',
    energy: 'Energie',
    happiness: 'Glücklichkeit',
    tree_level: 'Baum',
  },
};

@customElement('little-buddy-card')
export class LittleBuddyCard extends LitElement {
  @state() private _config?: any;
  @state() private _hass?: any;

  static get properties() {
    return {
      _config: {},
      _hass: {},
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
  }

  render() {
    if (!this._hass || !this._config) {
      return html``;
    }

    const language = getLocale(this._hass);
    const strings = STRINGS[language as keyof typeof STRINGS] || STRINGS.en;

    return html`
      <div class="card">
        <h2>${strings.level}</h2>
        <p>Little Buddy Card</p>
      </div>
    `;
  }

  static get styles() {
    return css`
      .card {
        padding: 16px;
        background-color: var(--card-background-color, var(--background-color));
        border-radius: var(--border-radius, 8px);
      }
    `;
  }
}
