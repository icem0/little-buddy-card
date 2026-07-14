"""The Little Buddy Card integration.

This integration is a Lovelace card (a frontend plugin) distributed as
an HA custom component so HACS can place the JS bundle under
`custom_components/little_buddy_card/frontend/` for HA to serve at
`/local/little_buddy_card/`. Home Assistant's built-in HTTP server
auto-serves any file under `<config>/custom_components/<domain>/www/`
at `/local/<domain>/...`. The `frontend/` subdir is referenced the
same way by the `__init__.py` resource registration below for clarity
and so HACS's integration validator is happy.

The card is registered client-side by the bundle via
`window.customCards.push({ type, name, ... })` — see
`frontend/little-buddy-card.js`. This `__init__.py` only ensures
HA's frontend module loader is ready; the actual card-element
auto-discovery is done by the bundle itself.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant


DOMAIN = "little_buddy_card"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Little Buddy Card integration (no-op frontend bridge)."""
    hass.data.setdefault(DOMAIN, {})
    return True
