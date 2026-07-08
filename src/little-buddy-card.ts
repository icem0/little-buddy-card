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

  // Helper to get state value
  private getState(entityId: string | undefined): any {
    if (!entityId || !this._hass?.states?.[entityId]) return undefined;
    return this._hass.states[entityId].state;
  }

  // Helper to get state as number
  private getStateNum(entityId: string | undefined): number {
    const val = this.getState(entityId);
    return val !== undefined && val !== null ? parseFloat(val) : 0;
  }

  // Helper to get state as string
  private getStateStr(entityId: string | undefined): string {
    const val = this.getState(entityId);
    return val !== undefined && val !== null ? String(val) : '';
  }

  private getPetImageUrl(): string {
    // If gif_url entity provided, use its state
    const gifEntity = this._config?.gif_url;
    if (gifEntity) {
      const gifState = this.getStateStr(gifEntity);
      if (gifState) return gifState;
    }
    // Otherwise construct from level and mood
    const mood = this.getStateStr(this._config?.mood) || 'happy';
    const levelNum = this.getStateNum(this._config?.level) || 1;
    const levelClamped = Math.min(Math.max(levelNum, 1), 5);
    return `/local/little-buddy-card/pets/level_${levelClamped}/${mood}.gif`;
  }

  private getTreeImageUrl(): string {
    const treeGifEntity = this._config?.tree_gif_url;
    if (treeGifEntity) {
      const treeState = this.getStateStr(treeGifEntity);
      if (treeState) return treeState;
    }
    const treeLevel = this.getStateStr(this._config?.tree_level) || 'seed';
    return `/local/little-buddy-card/trees/${treeLevel}.gif`;
  }

  render() {
    if (!this._hass || !this._config) {
      return html``;
    }

    const language = getLocale(this._hass);
    const strings = STRINGS[language as keyof typeof STRINGS] || STRINGS.en;

    const mood = this.getStateStr(this._config?.mood) || 'happy';
    const moodStr = strings[`mood_${mood}` as keyof typeof strings] || mood;

    const levelNum = this.getStateNum(this._config?.level) || 1;
    const xpNum = this.getStateNum(this._config?.xp) || 0;
    const healthNum = this.getStateNum(this._config?.health) || 0;
    const hungerNum = this.getStateNum(this._config?.hunger) || 0;
    const energyNum = this.getStateNum(this._config?.energy) || 0;
    const happinessNum = this.getStateNum(this._config?.happiness) || 0;

    return html`
      <div class="card">
        <div class="header">
          <div class="title">${strings.level}: ${levelNum}</div>
          <div class="xp">XP: ${xpNum}</div>
        </div>
        <div class="content">
          <img class="pet" src="${this.getPetImageUrl()}" alt="Little Buddy" />
          <img class="tree" src="${this.getTreeImageUrl()}" alt="Buddy Tree" />
        </div>
        <div class="stats">
          <div class="stat">
            <span class="label">${strings.health}:</span> <span class="value">${healthNum}</span>
          </div>
          <div class="stat">
            <span class="label">${strings.hunger}:</span> <span class="value">${hungerNum}</span>
          </div>
          <div class="stat">
            <span class="label">${strings.energy}:</span> <span class="value">${energyNum}</span>
          </div>
          <div class="stat">
            <span class="label">${strings.happiness}:</span> <span class="value">${happinessNum}</span>
          </div>
        </div>
        <div class="mood">
          <span class="label">${strings.mood_happy}:</span> <span class="value">${moodStr}</span>
        </div>
      </div>
    `;
  }

  static get styles() {
    return css`
      .card {
        padding: 16px;
        background-color: var(--card-background-color, var(--background-color));
        border-radius: var(--border-radius, 8px);
        font-family: var(--font-family);
        color: var(--primary-text-color, var(--text-color));
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        width: 100%;
        font-size: 1.1em;
      }
      .content {
        display: flex;
        gap: 24px;
        align-items: flex-end;
      }
      .pet, .tree {
        height: 128px;
        width: auto;
        image-rendering: pixelated;
      }
      .stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        width: 100%;
        text-align: left;
        font-size: 0.9em;
      }
      .stat {
        display: flex;
        justify-content: space-between;
      }
      .mood {
        font-size: 0.9em;
        width: 100%;
        text-align: left;
      }
      .label {
        font-weight: 500;
      }
    `;
  }
}
