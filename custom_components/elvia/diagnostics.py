"""Diagnostics support for Elvia."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.elvia.const import DOMAIN
from custom_components.elvia.coordinator import ElviaDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""

    diagnostics: dict[str, Any] = {}

    coordinator: ElviaDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    # Coordinator.data is a flattened dict (see coordinator._async_update_data).
    # Try to obtain the raw meteringpoint/GridTariffCollection from coordinator attributes
    # or from the flattened dict (key "meteringpoint").
    raw = getattr(coordinator, "meteringpoint", None)
    if raw is None and isinstance(coordinator.data, dict):
        raw = coordinator.data.get("meteringpoint")

    if raw is None:
        return diagnostics

    # Be defensive: ensure the raw object contains the expected attributes
    grid = getattr(raw, "gridTariff", None)
    mp_and_levels = getattr(raw, "meteringPointsAndPriceLevels", None)

    if grid is None:
        # Nothing useful to return for diagnostics
        return diagnostics

    diagnostics["tariffPrice"] = json.dumps(grid.tariffPrice, default=str)
    diagnostics["tariffType"] = json.dumps(grid.tariffType, default=str)
    if mp_and_levels is not None:
        diagnostics["meteringPointsAndPriceLevels"] = json.dumps(
            mp_and_levels, default=str
        )

    return diagnostics