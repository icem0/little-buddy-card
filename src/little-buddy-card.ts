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