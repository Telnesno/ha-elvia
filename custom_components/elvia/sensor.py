
"""Elvia sensors for Home Assistant.

Copilot fix for 2024.1 changes to Home Assistant, see https://developers.home-assistant.io/blog/2023/12/11/entity-description-changes/

This version avoids:
- Mutating SensorEntityDescription (immutable/frozen since HA 2024.1),
- Accessing a non-existent attribute on the coordinator (e.g. `coordinator.metering_point_id`).

References:
- HA 2024.1 entity description changes and resulting crashes when mutating .key. See issue logs quoting
  FrozenInstanceError in 'custom_components/elvia/sensor.py'.  #21, #20
- https://github.com/sindrebroch/ha-elvia/issues/21
- https://github.com/sindrebroch/ha-elvia/issues/20
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

# --------------------------------------------------------------------------------------
# Entity descriptions
# --------------------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class ElviaSensorEntityDescription(SensorEntityDescription):
    """Extended description holding a value extractor."""
    value_fn: Callable[[dict[str, Any], str], Any] | None = None
    # Optional attributes extractor
    attrs_fn: Callable[[dict[str, Any], str], dict[str, Any]] | None = None


# Helpers to read from coordinator.data in a safe way.
def _first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in data:
            return data.get(k)
    return None


def _attrs_window(data: dict[str, Any], base_key: str) -> dict[str, Any]:
    # Common attributes used by "max-hours" sensors
    return {
        "StartTime": data.get(f"{base_key}_start"),
        "EndTime": data.get(f"{base_key}_end"),
    }


DAILY_TARIFF = ElviaSensorEntityDescription(
    key="daily_tariff",
    name="Elvia Daily Tariff",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(d, ["daily_tariff", f"{mpid}_daily_tariff"]),
)

FIXED_PRICE_HOURLY = ElviaSensorEntityDescription(
    key="fixed_price_hourly",
    name="Elvia Fixed Price Hourly",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(
        d, ["fixed_price_hourly", f"{mpid}_fixed_price_hourly"]
    ),
)

FIXED_PRICE_LEVEL = ElviaSensorEntityDescription(
    key="fixed_price_level",
    name="Elvia Fixed Price Level",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(
        d, ["fixed_price_level", f"{mpid}_fixed_price_level"]
    ),
)

FIXED_PRICE_MONTHLY = ElviaSensorEntityDescription(
    key="fixed_price_monthly",
    name="Elvia Fixed Price Monthly",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(
        d, ["fixed_price_monthly", f"{mpid}_fixed_price_monthly"]
    ),
)

AVG_MAX_CURRENT = ElviaSensorEntityDescription(
    key="max_hour_avg_current",
    name="Elvia Max Hour Average (Current Month)",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(
        d, ["average_max_current", f"{mpid}_average_max_current", "max_hour_avg_current"]
    ),
)

AVG_MAX_PREVIOUS = ElviaSensorEntityDescription(
    key="max_hour_avg_previous",
    name="Elvia Max Hour Average (Previous Month)",
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda d, mpid: _first_present(
        d, ["average_max_previous", f"{mpid}_average_max_previous", "max_hour_avg_previous"]
    ),
)

# Max-hours 1/2/3 for current & previous months.
def _mk_maxhours_desc(n: int, is_current: bool) -> ElviaSensorEntityDescription:
    suffix = "current" if is_current else "previous"
    base_key = f"max_hours_{suffix}_{n}"
    return ElviaSensorEntityDescription(
        key=f"{base_key}",
        name=f"Elvia Max Hours {n} ({'Current' if is_current else 'Previous'} Month)",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d, mpid, bk=base_key: _first_present(
            d, [bk, f"{mpid}_{bk}"]
        ),
        attrs_fn=lambda d, mpid, bk=base_key: _attrs_window(d, bk),
    )


MAXHOURS_CURR_1 = _mk_maxhours_desc(1, True)
MAXHOURS_CURR_2 = _mk_maxhours_desc(2, True)
MAXHOURS_CURR_3 = _mk_maxhours_desc(3, True)
MAXHOURS_PREV_1 = _mk_maxhours_desc(1, False)
MAXHOURS_PREV_2 = _mk_maxhours_desc(2, False)
MAXHOURS_PREV_3 = _mk_maxhours_desc(3, False)


# --------------------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elvia sensors from a config entry."""
    # Coordinator may be stored directly, or inside a dict.
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    coordinator: CoordinatorEntity | None = None

    if stored is None:
        # Nothing to set up (defensive).
        return

    # Try common patterns
    if hasattr(stored, "data") and hasattr(stored, "async_request_refresh"):
        # Looks like it's the coordinator instance itself.
        coordinator = stored  # type: ignore[assignment]
    elif isinstance(stored, dict) and "coordinator" in stored:
        coordinator = stored["coordinator"]

    if coordinator is None:
        # As a last resort, accept whatever was stored.
        coordinator = stored  # type: ignore[assignment]

    # Read the metering point ID from the config entry (do NOT access coordinator.metering_point_id).
    metering_point_id: str | None = entry.data.get("metering_point_id")
    # If your flow stored it under another key, try common alternates:
    if not metering_point_id:
        metering_point_id = entry.data.get("mpid") or entry.data.get("meteringPointId")

    # Build entity list
    descriptions: list[ElviaSensorEntityDescription] = [
        DAILY_TARIFF,
        FIXED_PRICE_HOURLY,
        FIXED_PRICE_LEVEL,
        FIXED_PRICE_MONTHLY,
        AVG_MAX_CURRENT,
        AVG_MAX_PREVIOUS,
        MAXHOURS_CURR_1,
        MAXHOURS_CURR_2,
        MAXHOURS_CURR_3,
        MAXHOURS_PREV_1,
        MAXHOURS_PREV_2,
        MAXHOURS_PREV_3,
    ]

    entities: list[ElviaBaseSensor] = [
        ElviaBaseSensor(
            coordinator=coordinator,
            description=desc,
            key_prefix="elvia",
            metering_point_id=metering_point_id or "",
        )
        for desc in descriptions
    ]

    async_add_entities(entities)


# --------------------------------------------------------------------------------------
# Entities
# --------------------------------------------------------------------------------------

class ElviaBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Elvia sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CoordinatorEntity,
        description: ElviaSensorEntityDescription,
        key_prefix: str,
        metering_point_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description  # do NOT mutate description.key
        # Build a stable unique_id from domain + prefix + description.key
        self._attr_unique_id = f"{DOMAIN}_{key_prefix}_{description.key}"
        # Store MPID locally; do not rely on coordinator attributes
        self._metering_point_id = metering_point_id

        # Nice display name if description.name exists
        if description.name:
            self._attr_name = description.name

    @property
    def native_value(self) -> Any:
        """Return the sensor value based on coordinator data."""
        data: dict[str, Any] = getattr(self.coordinator, "data", {}) or {}
        if not data or not isinstance(self.entity_description, ElviaSensorEntityDescription):
            return None

        value_fn = self.entity_description.value_fn
        if value_fn is None:
            return None

        try:
            return value_fn(data, self._metering_point_id)
        except Exception:
            # Be defensive to avoid crashing sensor setup
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return optional attributes (e.g., start/end window for max-hours sensors)."""
        data: dict[str, Any] = getattr(self.coordinator, "data", {}) or {}
        desc = self.entity_description
        if not isinstance(desc, ElviaSensorEntityDescription) or desc.attrs_fn is None:
            return None

        try:
            attrs = desc.attrs_fn(data, self._metering_point_id) or {}
            # Drop empty attrs
            return {k: v for k, v in attrs.items() if v is not None}
        except Exception:
            return None
