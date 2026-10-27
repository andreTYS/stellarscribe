# Datos de `/api`

JSON estáticos que consumen la app Flutter (`/web/`) y los juegos (`/juegos/`).
Se regeneran con `python3 herramientas/corregir_datos.py api <solar_cycles_historical.json>`
(el archivo histórico está en el Drive del proyecto).

| Archivo | Contenido | Origen |
|---|---|---|
| `current_space_weather.json` | Estado del clima espacial | NOAA SWPC (sept. 2025). `current_kp`, `max_kp_24h` y `geomagnetic_activity_level` se calculan a partir del Kp |
| `basic_sunspot_data.json` | Manchas solares por día, sept. 2023 – ago. 2025 | SILSO, valor mensual. Antes este campo tenía por error el año decimal (p. ej. `2023.73`) |
| `solar_cycles_historical.json` | Manchas solares por mes desde 1749 | SILSO (Drive: `solar_cycles_historical.json`) |
| `basic_flare_data.json`, `basic_cme_data.json` | Erupciones y CMEs | Sintéticos con patrones históricos: NASA DONKI no devolvió datos (en el Drive, `cme_data.json` está vacío) |
| `noaa_comprehensive.json` | Kp, rayos X, ciclo solar y pronóstico | NOAA SWPC. `solar_wind`, `magnetometer`, `aurora_forecast` y `forecast_discussion` venían vacíos y se rellenan con valores típicos del periodo. Los `-1` del ciclo solar se completan con SILSO (media de 13 meses) y con la relación empírica entre manchas solares y F10.7 |
| `nasa_power_solar_data.json` | Últimos 14 días (radiación, UV, temperatura) | NASA POWER. Es una versión corta porque la app imprime el archivo entero |
| `nasa_power_solar_data_completo.json` | El año completo | NASA POWER. Los días con `-999` (sin dato) se rellenan con valores similares; cada uno lleva `estimated_fields` |
| `advanced_educational_content.json` | Niveles, mini-juegos y datos curiosos | Contenido propio. Se añaden `concepts`, `mini_game_params` y `fun_facts`, que lee la app |
| `sdo_observations.json` | Longitudes de onda del SDO | NASA SDO |
