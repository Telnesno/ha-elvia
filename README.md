# Elvia for HomeAssistant

![GitHub release (latest by date)](https://img.shields.io/github/v/release/sindrebroch/ha-elvia?style=flat-square)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/sindrebroch)

HomeAssistant-integration for Elvia

## Requirements

- Metering point id. (Målepunkt-ID, not Målernummer) Log into [Elvia](https://www.elvia.no/minside), click "Forbruk" and find your Målepunkt-ID at the bottom of the page.
- API-key. Sign up for GridTariffAPI at [Elvia developer portal](https://elvia.portal.azure-api.net/), click "Products" and then "Grid Tariff" and subscribe with your subscription name (call whatever). API-key available under "Profile".
- Token. Log into [Elvia](https://www.elvia.no/minside), under "Andre tjenester", click "Se tilganger" and "opprett token for måleverdier i API".

## Installation

<details>
   <summary>HACS (Recommended)</summary>

   1. Ensure that [HACS](https://hacs.xyz/) is installed.
   2. Add this repository as a custom repository
   3. Search for and install the "Elvia" integration.
   4. Restart Home Assistant.
   5. Add the `Elvia` integration to HA from the integration-page
</details>

<details>
   <summary>Manual installation</summary>

   1. Download the `Source code (zip)` file from the
      [latest release](https://github.com/sindrebroch/ha-elvia/releases/latest).
   2. Unpack the release and copy the `custom_components/elvia` directory
      into the `custom_components` directory of your Home Assistant
      installation.
   3. Restart Home Assistant.
   4. Add the `Elvia` integration to HA from the integration-page
</details>


## Sensors
- Energy price
   - Daily tariff (array of hourly values for the day)

- Fixed price hourly
- Fixed price level
- Fixed price monthly

- Average max
   - Current month
   - Previous month

- Max hours [1, 2, 3]
   - Current month
      - StartTime (attribute)
      - EndTime (attribute)
   - Previous month
      - StartTime (attribute)
      - EndTime (attribute)

## Debugging
If something is not working properly, logs might help with debugging. To turn on debug-logging add this to your `configuration.yaml`
```
logger:
  default: info
  logs:
    custom_components.elvia: debug
```

## API limitations
Limited to 200 calls/hour/user. The integration normally polls once every hour.

## Inspiration
https://github.com/uphillbattle/NettleieElvia
