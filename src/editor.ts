/**
 * Little Buddy Card — Visual configuration editor.
 *
 * Follows the Mushroom card pattern: a thin LitElement wrapper that drives
 * Home Assistant's native <ha-form> component with a schema. This is the
 * same approach Mushroom uses for its card editors — no external UI library
 * required, and it inherits HA's look & feel (entity pickers, selectors,
 * sectioned layout) automatically.
 *
 * Because <ha-form> only ships a single flat schema, we render the repeated
 * "mood trigger" rules with a small hand-built Mushroom-flavoured list
 * (label + entity picker + state input + remove button) so the user can map
 * "which mood is triggered by which entity state".
 */
import { LitElement, html, css, nothing, type TemplateResult } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import type { HomeAssistant, LovelaceCardEditor } from 'custom-card-helpers';
import type { LittleBuddyCardConfig, MoodTrigger } from './little-buddy-card';
import './editor';

const MOOD_OPTIONS = [
  { value: 'happy', label: 'Happy / Glücklich' },
  { value: 'sad', label: 'Sad / Traurig' },
  { value: 'hungry', label: 'Hungry / Hungrig' },
  { value: 'thirsty', label: 'Thirsty / Durstig' },
  { value: 'sleepy', label: 'Sleepy / Müde' },
  { value: 'angry', label: 'Angry / Wütend' },
  { value: 'playful', label: 'Playful / Verspielt' },
];

/** Schema for the main <ha-form> block. */
const BASE_SCHEMA = [
  { name: 'name', label: 'Buddy Name', selector: { text: {} } },
  {
    name: 'mood',
    label: 'Mood entity (input_select)',
    selector: { entity: { domain: ['input_select', 'sensor', 'input_text'] } },
  },
  {
    name: 'xp',
    label: 'XP entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'level',
    label: 'Level entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'health',
    label: 'Health entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'hunger',
    label: 'Hunger entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'energy',
    label: 'Energy entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'happiness',
    label: 'Happiness entity (input_number)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'tree_level',
    label: 'Tree level entity (input_select)',
    selector: { entity: { domain: ['input_select', 'sensor', 'input_text'] } },
  },
  {
    name: 'xp_per_click',
    label: 'XP per click entity (input_number, optional)',
    selector: { entity: { domain: ['input_number', 'sensor'] } },
  },
  {
    name: 'gif_url',
    label: 'Pet GIF URL entity (optional)',
    selector: { entity: { domain: ['sensor', 'input_text'] } },
  },
  {
    name: 'tree_gif_url',
    label: 'Tree GIF URL entity (optional)',
    selector: { entity: { domain: ['sensor', 'input_text'] } },
  },
  {
    name: 'asset_ext',
    label: 'Asset extension (png = dummy, gif = final art)',
    selector: {
      select: {
        mode: 'dropdown',
        options: [
          { value: 'png', label: 'png (dev / dummy)' },
          { value: 'gif', label: 'gif (final art)' },
        ],
      },
    },
  },
] as const;

@customElement('little-buddy-card-editor')
export class LittleBuddyCardEditor extends LitElement implements LovelaceCardEditor {
  @property({ attribute: false }) public hass?: HomeAssistant;
  @state() private _config?: LittleBuddyCardConfig;

  public setConfig(config: LittleBuddyCardConfig): void {
    this._config = config;
  }

  private _schema(): unknown[] {
    return [...BASE_SCHEMA];
  }

  private _computeLabel = (schema: { name: string; label?: string }): string => {
    return schema.label ?? schema.name;
  };

  private _valueChanged(ev: CustomEvent): void {
    const target = ev.target as HTMLElement & { name?: string };
    if (!this._config || !target.name) return;
    const newConfig = { ...this._config } as Record<string, unknown>;
    const value = (ev.detail as { value?: unknown }).value;
    newConfig[target.name] = value ?? '';

    // Strip empties so defaults apply cleanly.
    if (newConfig[target.name] === '') {
      delete newConfig[target.name];
    }
    this._dispatchConfig(newConfig as LittleBuddyCardConfig);
  }

  private _moodRuleChanged(index: number, field: keyof MoodTrigger, value: string): void {
    const moods = [...(this._config?.moods ?? [])] as MoodTrigger[];
    if (!moods[index]) moods[index] = { mood: '', entity: '', state: '' };
    moods[index] = { ...moods[index], [field]: value };
    const newConfig = { ...this._config, moods } as LittleBuddyCardConfig;
    this._dispatchConfig(newConfig);
  }

  private _addMoodRule(): void {
    const moods = [...(this._config?.moods ?? []), { mood: '', entity: '', state: '' }] as MoodTrigger[];
    this._dispatchConfig({ ...this._config, moods } as LittleBuddyCardConfig);
  }

  private _removeMoodRule(index: number): void {
    const moods = (this._config?.moods ?? []).filter((_, i) => i !== index);
    const newConfig = { ...this._config, moods } as LittleBuddyCardConfig;
    this._dispatchConfig(newConfig);
  }

  private _dispatchConfig(config: LittleBuddyCardConfig): void {
    const event = new Event('config-changed', {
      bubbles: true,
      composed: true,
    });
    (event as unknown as { detail: unknown }).detail = { config };
    this.dispatchEvent(event);
  }

  private _renderMoodRules(): TemplateResult | typeof nothing {
    const moods = this._config?.moods ?? [];
    return html`
      <div class="mood-section">
        <h3>Mood triggers — welche Stimmung durch welche Entität ausgelöst wird</h3>
        <p class="hint">
          Optional. Wenn gesetzt, gewinnt die erste Regel, deren Entität den
          eingestellten Zustand hat. Ansonsten wird die <i>Mood entity</i> oben
          verwendet.
        </p>
        ${moods.map(
          (rule, i) => html`
            <div class="mood-rule">
              <ha-select
                label="Stimmung"
                .value=${rule?.mood ?? ''}
                @closed=${(e: Event) => e.stopPropagation()}
                @change=${(e: Event) =>
                  this._moodRuleChanged(i, 'mood', (e.target as HTMLInputElement).value)}
              >
                ${MOOD_OPTIONS.map(
                  (o) => html`<ha-list-item value="${o.value}">${o.label}</ha-list-item>`,
                )}
              </ha-select>
              <ha-entity-picker
                label="Entität"
                .hass=${this.hass}
                .value=${rule?.entity ?? ''}
                @value-changed=${(e: CustomEvent) =>
                  this._moodRuleChanged(i, 'entity', e.detail.value ?? '')}
              ></ha-entity-picker>
              <ha-textfield
                label="Zustand (state)"
                .value=${rule?.state ?? ''}
                @change=${(e: Event) =>
                  this._moodRuleChanged(i, 'state', (e.target as HTMLInputElement).value)}
              ></ha-textfield>
              <ha-icon-button
                class="remove"
                @click=${() => this._removeMoodRule(i)}
                .label=${'Regel entfernen'}
              >
                <ha-icon icon="mdi:delete"></ha-icon>
              </ha-icon-button>
            </div>
          `,
        )}
        <mwc-button outlined @click=${this._addMoodRule}>
          <ha-icon icon="mdi:plus"></ha-icon> Mood-Regel hinzufügen
        </mwc-button>
      </div>
    `;
  }

  private _previewUrl(): string {
    const cfg = this._config;
    if (!cfg) return '';
    const ext = cfg.asset_ext === 'gif' ? 'gif' : 'png';
    // Best-effort preview: read live state if hass present, else placeholder.
    const mood = (cfg.mood && this.hass?.states?.[cfg.mood]?.state) || 'happy';
    const lvlRaw = cfg.level ? this.hass?.states?.[cfg.level]?.state : undefined;
    const lvl = Math.min(Math.max(parseInt(lvlRaw || '1', 10) || 1, 1), 5);
    return `/local/little-buddy-card/pets/level_${lvl}/${mood}.${ext}`;
  }

  render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) {
      return nothing;
    }
    return html`
      <div class="card-config">
        <ha-form
          .hass=${this.hass}
          .data=${this._config}
          .schema=${this._schema()}
          .computeLabel=${this._computeLabel}
          @value-changed=${this._valueChanged}
        ></ha-form>
        <div class="preview">
          <span class="preview-label">Vorschau (Pet)</span>
          <img class="preview-img" src="${this._previewUrl()}" alt="preview" @error=${this._onPreviewError} />
        </div>
        ${this._renderMoodRules()}
      </div>
    `;
  }

  private _onPreviewError(ev: Event) {
    const img = ev.target as HTMLImageElement;
    img.style.visibility = 'hidden';
  }

  static styles = css`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: var(--mush-spacing, 16px);
      padding: 4px 0;
      color: var(--primary-text-color, var(--text-color));
    }
    .preview {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 12px;
      background: var(--secondary-background-color, var(--card-background-color));
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color, #e0e0e0);
    }
    .preview-label {
      font-size: 0.8rem;
      opacity: 0.7;
    }
    .preview-img {
      height: 96px;
      width: auto;
      image-rendering: pixelated;
    }
    .mood-section {
      border-top: 1px solid var(--divider-color, #e0e0e0);
      padding-top: 12px;
    }
    .mood-section h3 {
      font-size: 0.95rem;
      margin: 0 0 4px;
      color: var(--primary-text-color, #212121);
    }
    .mood-section .hint {
      font-size: 0.8rem;
      opacity: 0.75;
      margin: 0 0 12px;
    }
    .mood-rule {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr auto;
      gap: 8px;
      align-items: end;
      margin-bottom: 8px;
    }
    .mood-rule ha-select,
    .mood-rule ha-entity-picker,
    .mood-rule ha-textfield {
      width: 100%;
    }
    mwc-button {
      margin-top: 4px;
    }
  `;
}
