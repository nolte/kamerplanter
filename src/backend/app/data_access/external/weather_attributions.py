"""REQ-046 §5 — provider attribution strings (NOTICE-relevant).

Central module constant consumed later by the UI weather section, the API
``available`` response and the NOTICE file. Keeping the attributions here keeps
the per-adapter modules free of duplicated licence text.
"""

#: Maps a weather adapter ``source_name`` to its required attribution string.
WEATHER_ATTRIBUTIONS: dict[str, str] = {
    "open-meteo": "Weather data by Open-Meteo.com (CC BY 4.0)",
    "dwd": "Datenbasis: Deutscher Wetterdienst (DWD GeoNutzV)",
    "openweathermap": "Weather data by OpenWeatherMap (OpenWeatherMap terms of use)",
    # REQ-041 — NASA POWER (CC-BY-4.0 / US public domain; citation requested).
    "nasa-power": "Klima- und Strahlungsdaten: NASA POWER (power.larc.nasa.gov)",
}
