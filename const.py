"""Constants for the SunPower Maxeon integration."""

DOMAIN = "sunpower_maxeon"

OAUTH2_AUTHORIZE = "https://api.sunpower.maxeon.com/v1/authorize"
OAUTH2_TOKEN = "https://api.sunpower.maxeon.com/v1/token"

# Dummy API responses
DUMMY_API = {
    "systems": [
        {
            "system_sn": "SOD123456789001",
            "active_at": 1718612017,
            "installed_pv_power": 7.2,
            "inverter_model": "RESERVE-INV-1-P5-L1-INT",
            "inverter_rated_power": 5,
            "battery_model": "RESERVE-BAT-1-DC-10.1-INT",
            "battery_capacity": 10.08,
            "battery_usable_capacity": 9.752,
            "meter_type": "CT",
            "feedin_threshold": 90,
            "inv_version": "01000.165",
            "ems_version": "V0.11.04",
            "bms_version": "V1.53",
            "status": "normal"
        }
    ],
    "system_details": {
        "SOD123456789001": {
            "system_sn": "SOD123456789001",
            "active_at": 1718612017,
            "installed_pv_power": 7.2,
            "inverter_model": "RESERVE-INV-1-P5-L1-INT",
            "inverter_rated_power": 5,
            "battery_model": "RESERVE-BAT-1-DC-10.1-INT",
            "battery_capacity": 10.08,
            "battery_usable_capacity": 9.752,
            "meter_type": "CT",
            "feedin_threshold": 90,
            "inv_version": "01000.165",
            "ems_version": "V0.11.04",
            "bms_version": "V1.53",
            "status": "normal"
        }
    },
    # You can keep expanding:
    # "alerts": {...},
    # "power_flow": {...},
    # "production": {...},
}
