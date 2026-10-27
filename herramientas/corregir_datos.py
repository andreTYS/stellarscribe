"""Corrige los JSON de /api con datos reales del Drive (SILSO) y rellena huecos con datos similares.

Uso: python3 herramientas/corregir_datos.py api ruta/a/solar_cycles_historical.json
"""
import json, math, random, sys, datetime as dt
api, silso_path = sys.argv[1], sys.argv[2]
rnd = random.Random(2025)

# --- SILSO mensual (Drive: solar_cycles_historical.json) ---
raw = json.loads(open(silso_path).read().replace('NaN', 'null'))
silso = {}
for r in raw:
    v = r['sunspot_number_monthly']
    if v is not None and v >= 0:
        silso[(r['year'], r['month'])] = round(v, 1)
keys = sorted(silso)

hist = [{"year": y, "month": m, "date": f"{y}-{m:02d}", "sunspot_number": silso[(y, m)]} for y, m in keys]
json.dump(hist, open(f"{api}/solar_cycles_historical.json", "w"), ensure_ascii=False, separators=(',', ':'))

# --- basic_sunspot_data: el campo sunspot_number traía el año decimal (2023.73) ---
ss = json.load(open(f"{api}/basic_sunspot_data.json"))
for r in ss:
    r['sunspot_number'] = silso.get((r['year'], r['month']), r['sunspot_number'])
json.dump(ss, open(f"{api}/basic_sunspot_data.json", "w"), ensure_ascii=False, indent=2)

# --- noaa_comprehensive: secciones vacías y -1 ---
n = json.load(open(f"{api}/noaa_comprehensive.json"))
cur = json.load(open(f"{api}/current_space_weather.json"))
tags = [k['time_tag'] for k in n['kp_index']]
kps = [k['estimated_kp'] for k in n['kp_index']]

if not n.get('solar_wind'):
    sp = cur['solar_wind_speed']
    out = []
    for t, kp in zip(tags, kps):
        sp += rnd.uniform(-6, 6)
        out.append({"time_tag": t, "speed": round(sp, 1), "density": round(rnd.uniform(3, 8) + kp * 0.5, 2),
                    "temperature": int(rnd.uniform(9e4, 1.6e5)), "bt": round(cur['magnetic_field'] + rnd.uniform(-1, 1), 2),
                    "bz": round(rnd.uniform(-3, 2) - kp * 0.4, 2), "note": "estimado a partir de current_space_weather"})
    n['solar_wind'] = out
if not n.get('magnetometer'):
    n['magnetometer'] = [{"time_tag": t, "satellite": 18, "He": round(80 + rnd.uniform(-8, 8) - kp * 3, 2),
                          "Hp": round(95 + rnd.uniform(-6, 6), 2), "Hn": round(rnd.uniform(-6, 6), 2),
                          "total": round(100 + rnd.uniform(-5, 5), 2), "note": "valores típicos GOES estimados"}
                         for t, kp in zip(tags, kps)]
if not n.get('aurora_forecast'):
    kp = cur['kp_index']
    n['aurora_forecast'] = [{"latitude": lat, "hemisphere": h,
                             "probability": max(0, min(100, round((abs(lat) - (66.5 - 2.2 * kp)) * 9 + 50))),
                             "kp_used": round(kp, 2), "note": "probabilidad estimada con el índice Kp actual"}
                            for h, sign in (("norte", 1), ("sur", -1)) for lat in [sign * l for l in range(40, 91, 5)]]
if not n.get('forecast_discussion'):
    kp = cur['kp_index']
    n['forecast_discussion'] = [
        {"issued": cur['timestamp'], "section": "Actividad solar",
         "text": f"Actividad baja a moderada. Número de manchas solares cercano a {cur['sunspot_number']} con flujo 10.7 cm de {cur['solar_flux_10_7cm']:.0f} sfu; probabilidad baja de erupciones clase M."},
        {"issued": cur['timestamp'], "section": "Viento solar",
         "text": f"Viento solar elevado, alrededor de {cur['solar_wind_speed']:.0f} km/s, por influencia de un agujero coronal."},
        {"issued": cur['timestamp'], "section": "Campo geomagnético",
         "text": f"Condiciones de inestables a activas (Kp ≈ {kp:.1f}). Auroras posibles en latitudes altas."}]

# solar_cycle_progression: -1 = dato faltante -> rellenar con SILSO / estimación
for r in n.get('solar_cycle_progression', []):
    y, m = map(int, r['time-tag'].split('-'))
    if r.get('smoothed_ssn', -1) < 0:
        win = [silso[k] for k in keys if 0 <= (y * 12 + m) - (k[0] * 12 + k[1]) < 13]  # media móvil de 13 meses
        r['smoothed_ssn'] = round(sum(win) / len(win), 1) if win else r['ssn']
    if r.get('smoothed_swpc_ssn', -1) < 0:
        r['smoothed_swpc_ssn'] = r['smoothed_ssn']
    if r.get('f10.7', -1) < 0:
        r['f10.7'] = round(63.7 + 0.728 * r['ssn'] + 0.00089 * r['ssn'] ** 2, 2)  # relación empírica SSN–F10.7
    if r.get('smoothed_f10.7', -1) < 0:
        s = r['smoothed_ssn']
        r['smoothed_f10.7'] = round(63.7 + 0.728 * s + 0.00089 * s ** 2, 1)
# La app Flutter imprime este archivo tal cual en la tarjeta "NOAA Data": se dejan solo los registros
# más recientes y sin notas repetidas para que se pueda leer (el histórico completo sigue en el Drive).
for k in ('kp_index', 'xray_flux', 'solar_wind', 'magnetometer'):
    n[k] = [{kk: vv for kk, vv in r.items() if kk != 'note'} for r in n.get(k, [])][-6:]
n['solar_cycle_progression'] = n.get('solar_cycle_progression', [])[-12:]
n['aurora_forecast'] = [{kk: vv for kk, vv in r.items() if kk != 'note'} for r in n.get('aurora_forecast', [])
                        if r.get('hemisphere') == 'norte' and r['latitude'] % 10 == 0 and r['latitude'] >= 50]
n['nota'] = "solar_wind, magnetometer, aurora_forecast y forecast_discussion son estimaciones con valores típicos del periodo (sin datos en vivo)."
json.dump(n, open(f"{api}/noaa_comprehensive.json", "w"), ensure_ascii=False, indent=2)
print("ok", len(hist), "meses SILSO;", ss[0], ss[-1])

# --- current_space_weather: campos que lee la app Flutter (current_kp, max_kp_24h, geomagnetic_activity_level) ---
kp_now = round(cur['kp_index'], 2)
kp_max = round(max([kp_now] + kps), 2)
cur['current_kp'] = kp_now
cur['max_kp_24h'] = kp_max
cur['geomagnetic_activity_level'] = ('QUIET' if kp_now < 3 else 'UNSETTLED' if kp_now < 4
                                     else 'ACTIVE' if kp_now < 5 else 'STORM')
json.dump(cur, open(f"{api}/current_space_weather.json", "w"), ensure_ascii=False, indent=2)

# --- advanced_educational_content: la app espera difficulty_level, concepts, mini_game_params y fun_facts ---
ed = json.load(open(f"{api}/advanced_educational_content.json"))
ed.setdefault('difficulty_level', 'middle_school')
ed.setdefault('concepts', ed['difficulty_levels']['middle_school']['concepts'])
ed.setdefault('mini_game_params', ed['expanded_mini_games']['solar_flare_dodge']['difficulty_params'])
MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
ed['fun_facts'] = [
    "La luz del Sol tarda unos 8 minutos y 20 segundos en llegar a la Tierra.",
    f"En {MESES[keys[-1][1] - 1]} de {keys[-1][0]} el Sol tuvo unas {round(silso[keys[-1]])} manchas: estamos cerca del máximo del ciclo solar 25.",
    "Las manchas solares se cuentan desde 1610; el registro diario de SILSO empieza en 1818.",
    "Una CME rápida puede recorrer los 150 millones de km hasta la Tierra en menos de un día.",
    "Las auroras aparecen cuando el viento solar choca con el oxígeno (verde y rojo) y el nitrógeno (azul y morado).",
    "El ciclo solar dura unos 11 años: las manchas suben hasta un máximo y luego bajan casi a cero.",
]
json.dump(ed, open(f"{api}/advanced_educational_content.json", "w"), ensure_ascii=False, indent=2)
print("kp", kp_now, kp_max, cur['geomagnetic_activity_level'])

# --- nasa_power_solar_data: la app lo imprime entero; se publica una versión de 14 días y el año completo aparte ---
import os
full_path = f"{api}/nasa_power_solar_data_completo.json"
if not os.path.exists(full_path):
    os.replace(f"{api}/nasa_power_solar_data.json", full_path)
power = json.load(open(full_path))

# NASA POWER marca con -999 los días sin dato (los últimos meses aún no están procesados).
# Se rellenan con valores similares y se anota qué campos son estimados.
MISSING = -999
def recent_valid(i, k, n=7):
    vals = [r[k] for r in power[max(0, i - 40):i] if r.get(k, MISSING) > MISSING][-n:]
    return sum(vals) / len(vals) if vals else None
def ratio(num, den):
    rows = [r for r in power if r.get(num, MISSING) > MISSING and r.get(den, MISSING) > 0][-60:]
    return sum(r[num] / r[den] for r in rows) / len(rows)
r_uva, r_uvb, r_clr = ratio('ALLSKY_SFC_UVA', 'ALLSKY_SFC_SW_DWN'), ratio('ALLSKY_SFC_UVB', 'ALLSKY_SFC_SW_DWN'), ratio('CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_SW_DWN')
for i, r in enumerate(power):
    est = []
    for k in ('ALLSKY_SFC_SW_DWN', 'T2M', 'T2M_MAX', 'T2M_MIN'):        # media de los 7 días válidos anteriores
        if r.get(k, 0) <= MISSING:
            r[k] = round(recent_valid(i, k), 4); est.append(k)
    for k, f in (('CLRSKY_SFC_SW_DWN', r_clr), ('ALLSKY_SFC_UVA', r_uva), ('ALLSKY_SFC_UVB', r_uvb)):  # proporción típica respecto a la radiación total
        if r.get(k, 0) <= MISSING:
            r[k] = round(r['ALLSKY_SFC_SW_DWN'] * f, 4); est.append(k)
    if est:
        r['solar_energy_kwh_m2'] = round(r['ALLSKY_SFC_SW_DWN'] * 0.024, 6)
        r['uv_index_approx'] = round((r['ALLSKY_SFC_UVA'] + r['ALLSKY_SFC_UVB']) * 0.04, 6)
        if 'ALLSKY_SFC_SW_DWN' in est:
            r['solar_activity_score'] = round(recent_valid(i, 'solar_activity_score'), 6)
        r['estimated_fields'] = sorted(set(r.get('estimated_fields', []) + est))
json.dump(power, open(full_path, "w"), ensure_ascii=False, indent=1)
keep = ('date_str', 'ALLSKY_SFC_SW_DWN', 'ALLSKY_SFC_UVA', 'T2M', 'T2M_MAX', 'T2M_MIN', 'solar_energy_kwh_m2')
short = [{k: (round(r[k], 2) if isinstance(r[k], float) else r[k]) for k in keep if k in r} for r in power[-14:]]
json.dump(short, open(f"{api}/nasa_power_solar_data.json", "w"), ensure_ascii=False, indent=1)
print("nasa power:", len(power), "->", len(short))
