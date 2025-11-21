import pytest
from types import SimpleNamespace

from custom_components.elvia.coordinator import ElviaDataUpdateCoordinator
from custom_components.elvia.sensor import ElviaBaseSensor, DAILY_TARIFF


class FakeApi:
    def __init__(self):
        self._metering_point_id = "MPID123"

    async def meteringpoint(self):
        return SimpleNamespace()

    async def maxhours(self):
        return {}


@pytest.mark.asyncio
async def test_coordinator_flattening(hass):
    api = FakeApi()
    fake_tariffType = SimpleNamespace(title="t", companyName="c", tariffKey="k")
    coord = ElviaDataUpdateCoordinator(hass=hass, api=api, tariffType=fake_tariffType)

    # Monkeypatch map methods to avoid complex model construction — set expected attributes directly
    async def dummy_map_meteringpoint_values(data):
        coord.energy_price = 12.34
        coord.fixed_price_hourly = 1.23
        coord.fixed_price_level_info = "info"
        coord.fixed_price_level = 99
        coord.tariff_prices = [{"startTime": "x"}]

    async def dummy_map_maxhour_values(data):
        coord.mapped_maxhours = {
            "current_month": {
                "1": {"value": 10, "startTime": "s1", "endTime": "e1"},
                "2": {"value": 11, "startTime": "s1b", "endTime": "e1b"},
                "3": {"value": 12, "startTime": "s1c", "endTime": "e1c"},
                "average": 5,
                "uom": "kWh",
            },
            "previous_month": {
                "1": {"value": 8, "startTime": "s2", "endTime": "e2"},
                "average": 4,
                "uom": "kWh",
            },
        }

    coord.map_meteringpoint_values = dummy_map_meteringpoint_values
    coord.map_maxhour_values = dummy_map_maxhour_values

    data = await coord._async_update_data()

    assert isinstance(data, dict)
    assert data["daily_tariff"] == 12.34
    assert data["fixed_price_hourly"] == 1.23
    assert data["fixed_price_monthly"] == 99
    assert data["average_max_current"] == 5
    assert data["max_hours_current_1"] == 10
    assert data["max_hours_current_1_start"] == "s1"
    assert data["max_hours_current_1_end"] == "e1"
    # MPID-prefixed variants
    assert data[f"{api._metering_point_id}_daily_tariff"] == 12.34


@pytest.mark.asyncio
async def test_sensor_native_value(hass):
    api = FakeApi()
    fake_tariffType = SimpleNamespace(title="t", companyName="c", tariffKey="k")
    coord = ElviaDataUpdateCoordinator(hass=hass, api=api, tariffType=fake_tariffType)

    coord.data = {"daily_tariff": 7.89, f"{api._metering_point_id}_daily_tariff": 7.89}

    sensor = ElviaBaseSensor(
        coordinator=coord,
        description=DAILY_TARIFF,
        key_prefix="elvia",
        metering_point_id=api._metering_point_id,
    )

    assert sensor.native_value == 7.89
