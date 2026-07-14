"""The Little Buddy Card integration.

This integration is a Lovelace card (frontend plugin) distributed as
an HA custom component. The bundle lives under
`custom_components/little_buddy_card/frontend/`.

On setup, we:
  1. Register `frontend/` as a static path at `/local/little_buddy_card/`
     so Home Assistant's web server can serve the bundle.
  2. Call `add_extra_js_url(..., es5=False)` so Lovelace picks up the
     bundle as a JavaScript module resource automatically — the user does
     NOT need to add it manually under "Settings → Dashboards → Resources".

This is the canonical "Lovelace card as a HACS-Integration" pattern
(see hacs.xyz/docs/publish/integration). Without these two steps, the
bundle would be installed on disk but never loaded by the browser,
and `window.customCards.push(...)` would never run.

NOTE: Older HA docs referenced `add_extra_module_url`. In current HA core
(2024.x+) the public API is `add_extra_js_url(hass, url, es5=False)`
(where es5=False means "load as an ES module"). We use that.
"""
from __future__ import annotations

import os

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant


DOMAIN = "little_buddy_card"
MODULE_URL = "/local/little_buddy_card/little-buddy-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Little Buddy Card integration and register the frontend."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

    # 1. Serve frontend/ at /local/little_buddy_card/
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/local/little_buddy_card", frontend_dir, cache_headers=False)]
    )

    # 2. Register the bundle as a Lovelace JavaScript module (es5=False => module)
    add_extra_js_url(hass, MODULE_URL, es5=False)

    hass.data.setdefault(DOMAIN, {})
    return True
