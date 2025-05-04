"""Constants for the SunPower Maxeon integration."""

DOMAIN = "sunpower_maxeon"

OAUTH2_AUTHORIZE = "https://api.sunpower.maxeon.com/v1/authorize"
OAUTH2_TOKEN = "https://api.sunpower.maxeon.com/v1/token"

SYSTEMS = {
    "systems": [
        {
            "system_sn": "default",
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
            "status": "dummy_data"
        }
    ]
}

SYSTEM_DETAILS = {
    "default": {
        "system_sn": "default",
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
        "status": "dummy_data"
    }
}

ENERGY_METER = {
  "system_sn": "default",
  "timestamp": 1680334973,
  "e_pv_generation": 7000,
  "e_storage_charge": 4000,
  "e_storage_discharge": 6000,
  "e_grid_import": 1000,
  "e_grid_export": 3000,
  "e_consumption": 7000,
  "status": "dummy_data",
  "p_max_charge": 5000,
  "p_max_discharge": 5000
}

POWER_METER = {
  "system_sn": "default",
  "timestamp": 1680334973,
  "p_pv": 1992,
  "p_grid": -1126,
  "p_storage": 0,
  "soc": 75,
  "p_consumption": 866,
  "status": "dummy_data"
}

CHARGING_SCHEDULE = {
    "enable": True,
    "start_time_1": "14:00",
    "end_time_1": "16:00",
    "start_time_2": "14:00",
    "end_time_2": "16:00",
    "max_soc": 95
}