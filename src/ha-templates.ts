/**
 * Minimal HA template subscription — mirrors the behaviour of Mushroom's
 * `subscribeRenderTemplate` from `src/ha/data/ws-templates.ts`, but without
 * pulling in Mushroom's full HA-frontend fork.
 *
 * Uses Home Assistant's WebSocket API (`connection.subscribeMessage`) which is
 * the exact transport `subscribeRenderTemplate` wraps. This lets the card
 * render live-updating Jinja templates in config fields (e.g. `name`).
 */
import type { Connection } from 'home-assistant-js-websocket';
import type { HomeAssistant } from 'custom-card-helpers';

export type UnsubscribeFunc = () => Promise<void>;

export interface RenderTemplateResult {
  result: string;
  listeners: {
    all: boolean;
    domains: string[];
    entities: string[];
    time: boolean;
  };
}

type RenderTemplateCallback = (result: RenderTemplateResult) => void;

export function subscribeRenderTemplate(
  conn: Connection,
  callback: RenderTemplateCallback,
  params: {
    template: string;
    entity_ids?: string | string[];
    variables?: Record<string, unknown>;
    timeout?: number;
    strict?: boolean;
  },
): Promise<UnsubscribeFunc> {
  // HA's render_template websocket subscription returns the result on every
  // relevant state change. `result` is the rendered string.
  return conn.subscribeMessage<RenderTemplateResult>(
    (msg) => callback(msg),
    {
      type: 'render_template',
      template: params.template,
      entity_ids: params.entity_ids,
      variables: params.variables,
      timeout: params.timeout,
      strict: params.strict,
    },
  );
}

/** True if the string contains Jinja template markers. */
export function isTemplate(value: string | undefined): boolean {
  if (!value) return false;
  return value.includes('{{') || value.includes('{%') || value.includes('{%-');
}

/** Convenience: resolve a value that may be a template or a static string. */
export function resolveValue(
  hass: HomeAssistant | undefined,
  raw: string | undefined,
  templateResults: Map<string, string>,
  key: string,
): string {
  if (!raw) return '';
  if (!isTemplate(raw)) return raw;
  return templateResults.get(key) ?? raw;
}
