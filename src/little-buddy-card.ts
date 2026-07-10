/**
 * Little Buddy Card — Gamified Lovelace Card for Home Assistant
 * A pixel-art pet/tree companion that grows based on XP and level.
 */
import { LitElement, html, css, nothing, type TemplateResult } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import type { HomeAssistant, LovelaceCardEditor, LovelaceCardConfig } from 'custom-card-helpers';

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
    xp_to_next: 'XP to next level',
    click_to_gain: 'Click to gain XP',
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
    xp_to_next: 'XP bis zum nächsten Level',
    click_to_gain: 'Klicke um XP zu erhalten',
  },
};

export interface LittleBuddyCardConfig extends LovelaceCardConfig {
  title?: string;
  name?: string;
  mood?: string;
  xp?: string;
  level?: string;
  health?: string;
  hunger?: string;
  energy?: string;
  happiness?: string;
  tree_level?: string;
  gif_url?: string;
  tree_gif_url?: string;
  xp_per_click?: string;
  moods?: MoodTrigger[];
}

export interface MoodTrigger {
  mood: string;
  entity: string;
  state: string;
}

/**
 * Register the card with Home Assistant's card picker ("+ Add Card").
 * Without this entry the card only works via manual YAML — it never shows
 * up in the visual editor.
 */
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: 'little-buddy-card',
  name: 'Little Buddy Card',
  description: 'A gamified Lovelace card with growable pixel-art pets and trees.',
});

@customElement('little-buddy-card')
export class LittleBuddyCard extends LitElement {
  @state() private _config?: LittleBuddyCardConfig;
  @state() private _hass?: HomeAssistant;

  static get properties() {
    return {
      _config: { state: true },
      _hass: { state: true },
    };
  }

  /**
   * Returns the visual configuration editor element.
   * This is what makes the card editable through the dashboard UI.
   */
  public static async getConfigElement(): Promise<LovelaceCardEditor> {
    return document.createElement('little-buddy-card-editor') as LovelaceCardEditor;
  }

  /**
   * Default config used when the card is dropped on a dashboard from the
   * card picker. Uses sensible entity ids that match the README helpers.
   */
  public static getStubConfig(): Record<string, unknown> {
    return {
      name: 'Little Buddy',
      mood: 'input_select.little_buddy_mood',
      xp: 'input_number.little_buddy_xp',
      level: 'input_number.little_buddy_level',
      health: 'input_number.little_buddy_health',
      hunger: 'input_number.little_buddy_hunger',
      energy: 'input_number.little_buddy_energy',
      happiness: 'input_number.little_buddy_happiness',
      tree_level: 'input_select.little_buddy_tree_level',
      xp_per_click: 'input_number.little_buddy_xp_per_click',
    };
  }

  setConfig(config: LittleBuddyCardConfig) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this._config = config;
  }

  set hass(hass: HomeAssistant) {
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

  /**
   * Resolve the effective mood.
   * 1) If `config.moods` trigger rules are present, evaluate them in order:
   *    when a rule's `entity` matches `state`, that rule's `mood` wins.
   * 2) Otherwise fall back to the `config.mood` entity (the classic path).
   * 3) Final fallback: 'happy'.
   */
  private resolveMood(): string {
    const rules = this._config?.moods;
    if (Array.isArray(rules) && rules.length) {
      for (const rule of rules) {
        if (rule?.entity && rule?.state !== undefined && rule?.mood) {
          if (this.getStateStr(rule.entity) === String(rule.state)) {
            return rule.mood;
          }
        }
      }
    }
    const mood = this.getStateStr(this._config?.mood);
    return mood || 'happy';
  }

  // Get XP per click from config entity or default 10
  private getXpPerClick(): number {
    const xpPerEntity = this._config?.xp_per_click;
    if (xpPerEntity) {
      const val = this.getStateNum(xpPerEntity);
      if (!isNaN(val) && val > 0) return Math.floor(val);
    }
    return 10;
  }

  private getPetImageUrl(): string {
    // If gif_url entity provided, use its state
    const gifEntity = this._config?.gif_url;
    if (gifEntity) {
      const gifState = this.getStateStr(gifEntity);
      if (gifState) return gifState;
    }
    // Otherwise construct from level and mood
    const mood = this.resolveMood();
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

  private async _handlePetClick() {
    if (!this._hass || !this._config?.xp) {
      return;
    }
    const xpEntity = this._config.xp;
    const currentXp = this.getStateNum(xpEntity);
    const xpToAdd = this.getXpPerClick();
    const newXp = currentXp + xpToAdd;
    try {
      await this._hass.callService('input_number', 'set_value', {
        entity_id: xpEntity,
        value: newXp,
      });
    } catch (e) {
      console.error('Failed to set XP:', e);
    }
  }

  render() {
    if (!this._hass || !this._config) {
      return html``;
    }

    const language = getLocale(this._hass);
    const strings = STRINGS[language as keyof typeof STRINGS] || STRINGS.en;

    const mood = this.resolveMood();
    const moodStr = strings[`mood_${mood}` as keyof typeof strings] || mood;

    const xpNum = this.getStateNum(this._config?.xp) || 0;
    const calculatedLevel = Math.floor(xpNum / 1000) + 1;
    const level = Math.min(calculatedLevel, 5);
    const healthNum = this.getStateNum(this._config?.health) || 0;
    const hungerNum = this.getStateNum(this._config?.hunger) || 0;
    const energyNum = this.getStateNum(this._config?.energy) || 0;
    const happinessNum = this.getStateNum(this._config?.happiness) || 0;
    const buddyName = this._config?.name || this._config?.title || 'Little Buddy';

    return html`
      <div class="card" @click=${this._handlePetClick}>
        <div class="header">
          <div class="title">${buddyName}</div>
          <div class="xp">${strings.level}: ${level} · XP: ${xpNum}</div>
        </div>
        <div class="content">
          <div class="pet-wrapper">
            <img class="pet" src="${this.getPetImageUrl()}" alt="Little Buddy" @error=${this._onImgError} />
          </div>
          <img class="tree" src="${this.getTreeImageUrl()}" alt="Buddy Tree" @error=${this._onImgError} />
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
        <div class="xp-bar">
          <div class="xp-bar-bg"></div>
          <div class="xp-bar-fill" style="width: ${(xpNum % 1000) / 10}%"></div>
          <div class="xp-text">${xpNum % 1000} / 1000 ${strings.xp_to_next}</div>
        </div>
        <div class="mood">
          <span class="label">${strings.mood_happy}:</span> <span class="value">${moodStr}</span>
          <span class="hint">${strings.click_to_gain}</span>
        </div>
      </div>
    `;
  }

  private _onImgError(ev: Event) {
    const img = ev.target as HTMLImageElement;
    // Use a transparent 1x1 pixel gif as fallback to avoid broken image icons
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    img.alt = 'Image not found';
  }

  static get styles() {
    return css`
      .card {
        padding: 16px;
        background-color: var(--card-background-color, var(--background-color));
        border-radius: var(--border-radius, 8px);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: box-shadow 0.2s ease;
      }
      .card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
      .pet-wrapper {
        width: 128px;
        height: 128px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }
      .pet {
        height: 128px;
        width: auto;
        image-rendering: pixelated;
        pointer-events: none;
      }
      .tree {
        height: 128px;
        width: auto;
        image-rendering: pixelated;
      }
      .stats {
        display: grid;
        gap: 6px;
        width: 100%;
        font-size: 0.9em;
      }
      .stat {
        display: flex;
        justify-content: space-between;
      }
      .label {
        font-weight: 500;
      }
      .xp-bar {
        width: 100%;
        background: var(--divider-color, var(--grey-light-2));
        border-radius: 4px;
        overflow: hidden;
        height: 8px;
        position: relative;
      }
      .xp-bar-bg {
        width: 100%;
        height: 100%;
        background: var(--divider-color, var(--grey-light-2));
      }
      .xp-bar-fill {
        height: 100%;
        background: var(--paper-item-selected-color, var(--accent-color));
        width: 0%;
        transition: width 0.2s ease;
      }
      .xp-text {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        text-align: center;
        line-height: 8px;
        font-size: 0.75em;
        color: var(--primary-text-color, var(--text-color));
        pointer-events: none;
      }
      .mood {
        margin-top: 8px;
        font-size: 0.9em;
        text-align: center;
        width: 100%;
      }
      .hint {
        font-size: 0.75em;
        opacity: 0.7;
        margin-top: 4px;
      }
    `;
  }
}
