"""Diagnostics support for Elvia."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.elvia.const import DOMAIN
from custom_components.elvia.coordinator import ElviaDataUpdateCoordinator
from custom_components.elvia.models import GridTariffCollection


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

    diagnostics["tariffPrice"] = json.dumps(raw.gridTariff.tariffPrice, default=str)
    diagnostics["tariffType"] = json.dumps(raw.gridTariff.tariffType, default=str)
    diagnostics["meteringPointsAndPriceLevels"] = json.dumps(
        raw.meteringPointsAndPriceLevels, default=str
    )

    return diagnostics