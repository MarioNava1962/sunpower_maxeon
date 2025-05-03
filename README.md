# SunPower Maxeon Integration for Home Assistant

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) that allows you to monitor your **SunPower Maxeon** solar system.

> ⚠️ This project is not affiliated with or endorsed by SunPower or Maxeon.

---

## Features

- OAuth2 authentication with automatic token refresh
- Sensor platform for system status and metadata
- Reauthentication support if credentials expire

---

## Installation

### Manual Installation

1. Clone or download this repository.
2. Copy the `sunpower_maxeon/` folder into your Home Assistant `custom_components/` directory:


3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and search for "SunPower Maxeon".

### HACS (Home Assistant Community Store)

> Optional but recommended for easier updates.

1. Go to **HACS → Integrations → Custom repositories**.
2. Add this repo:
- **URL**: `https://github.com/geims12/sunpower_maxeon`
- **Category**: Integration
3. Install it, then restart Home Assistant.
4. Add the integration through the UI.

---

## Requirements

- Home Assistant 2023.0.0 or newer
- A SunPower Maxeon account with API access

---

## Configuration

This integration uses Home Assistant’s OAuth2 config flow. When you set it up, you’ll be redirected to log in with your SunPower Maxeon credentials.

No YAML configuration is necessary.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
