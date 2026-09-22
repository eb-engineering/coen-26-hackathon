"""
Gera uma biblioteca de mapas de eficiência de máquina elétrica (EM) para o
modelo longitudinal do Truck BEV.

Estes mapas NÃO são digitalizados das imagens de referência fornecidas (isso
exigiria extração pixel a pixel das linhas de contorno) — são superfícies
paramétricas suaves cujo formato/eficiência de pico/ponto ótimo são
*inspirados* nos três exemplos (um mapa "ilha" de ~90,5%, um mapa amplo de
~94%+ e um mapa bem "chato" de ~97-98%), além de algumas variantes extras
para que as equipes do hackathon tenham vários mapas para combinar com
diferentes relações de transmissão final, como solicitado.

Each map is saved as JSON:
{
  "id": "...",
  "speed_rpm": [...]  breakpoints,
  "torque_nm": [...]  breakpoints (0..max_torque_nm),
  "efficiency": [ [row per speed] , ... ]  shape (len(speed_rpm), len(torque_nm)),
  "max_torque_nm": flat-torque region limit,
  "corner_speed_rpm": speed where constant-power region begins,
  "max_speed_rpm": absolute max mechanical speed,
  "max_power_kw": approx corner power (informational only)
}

Torque-speed envelope = constant torque up to corner_speed_rpm, then
constant power (torque tapering as 1/speed) up to max_speed_rpm.
"""
import json
import math
import os

import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "em_maps")
os.makedirs(OUT_DIR, exist_ok=True)


def envelope_torque(speed_rpm, max_torque_nm, corner_speed_rpm, max_speed_rpm):
    """Max available torque at a given speed given a base-speed (corner) motor envelope."""
    if speed_rpm <= corner_speed_rpm:
        return max_torque_nm
    if speed_rpm >= max_speed_rpm:
        return 0.0
    corner_power = max_torque_nm * corner_speed_rpm
    return corner_power / speed_rpm


def build_map(map_id, max_torque_nm, corner_speed_rpm, max_speed_rpm,
              peak_eff, peak_speed_frac, peak_torque_frac, spread_speed, spread_torque,
              floor_eff, high_speed_penalty, mass_kg, cost_index):
    """
    Build a smooth efficiency surface over the (speed, torque) grid, shaped like a
    typical electric-machine map: a high-efficiency "island" centered around
    (peak_speed_frac * max_speed, peak_torque_frac * max_torque), efficiency
    dropping off at very low torque (electrical/iron losses dominate), at very
    low speed, and mildly at very high speed (iron/switching losses).
    """
    n_speed, n_torque = 46, 46
    speed_grid = np.linspace(50, max_speed_rpm, n_speed)  # avoid exactly 0 rpm
    torque_grid = np.linspace(0.5, max_torque_nm, n_torque)

    eff = np.zeros((n_speed, n_torque))
    peak_speed = peak_speed_frac * max_speed_rpm
    peak_torque = peak_torque_frac * max_torque_nm

    for i, n in enumerate(speed_grid):
        for j, tq in enumerate(torque_grid):
            # Gaussian "sweet spot" bump
            ds = (n - peak_speed) / (spread_speed * max_speed_rpm)
            dtq = (tq - peak_torque) / (spread_torque * max_torque_nm)
            bump = math.exp(-(ds ** 2 + dtq ** 2))

            # Carga relativa ao envelope disponível nessa rotação.
            tq_cap = max(envelope_torque(n, max_torque_nm, corner_speed_rpm, max_speed_rpm), 1e-6)
            load_frac = min(tq / tq_cap, 1.0)
            partial_load_penalty = 8.0 * (1 - load_frac) ** 1.6

            # high speed iron-loss penalty
            speed_frac = n / max_speed_rpm
            hs_penalty = high_speed_penalty * 18.0 * max(0.0, speed_frac - 0.60) ** 1.5

            e = floor_eff + (peak_eff - floor_eff) * bump - partial_load_penalty - hs_penalty
            e = max(min(e, peak_eff), 40.0)  # clip to sane efficiency range [40, peak]

            # zero-out (mask) points outside the torque-speed envelope
            if tq > tq_cap * 1.02:
                e = np.nan
            eff[i, j] = e

    data = {
        "id": map_id,
        "speed_rpm": speed_grid.tolist(),
        "torque_nm": torque_grid.tolist(),
        "efficiency_pct": eff.tolist(),
        "max_torque_nm": max_torque_nm,
        "corner_speed_rpm": corner_speed_rpm,
        "max_speed_rpm": max_speed_rpm,
        "max_power_kw": round(max_torque_nm * corner_speed_rpm * 2 * math.pi / 60 / 1000, 1),
        "mass_kg": mass_kg,
        "cost_index": cost_index,
    }
    path = os.path.join(OUT_DIR, f"{map_id}.json")
    with open(path, "w") as f:
        json.dump(data, f)
    print(f"wrote {path}  peak_power={data['max_power_kw']}kW  peak_eff~{peak_eff}%")
    return data


MAPS = [
    dict(map_id="motor_01", max_torque_nm=550, corner_speed_rpm=2600, max_speed_rpm=9000,
         peak_eff=95.0, peak_speed_frac=0.25, peak_torque_frac=0.55,
         spread_speed=0.13, spread_torque=0.22, floor_eff=72.0, high_speed_penalty=1.0,
         mass_kg=220, cost_index=42),

    dict(map_id="motor_02", max_torque_nm=750, corner_speed_rpm=1800, max_speed_rpm=6000,
         peak_eff=94.0, peak_speed_frac=0.38, peak_torque_frac=0.38,
         spread_speed=0.22, spread_torque=0.32, floor_eff=80.0, high_speed_penalty=0.8,
         mass_kg=240, cost_index=45),

    dict(map_id="motor_03", max_torque_nm=650, corner_speed_rpm=2800, max_speed_rpm=10000,
         peak_eff=97.5, peak_speed_frac=0.48, peak_torque_frac=0.28,
         spread_speed=0.16, spread_torque=0.22, floor_eff=82.0, high_speed_penalty=0.5,
         mass_kg=320, cost_index=65),

    dict(map_id="motor_04", max_torque_nm=900, corner_speed_rpm=2200, max_speed_rpm=8000,
         peak_eff=93.5, peak_speed_frac=0.35, peak_torque_frac=0.55,
         spread_speed=0.20, spread_torque=0.25, floor_eff=78.0, high_speed_penalty=0.7,
         mass_kg=360, cost_index=58),

    dict(map_id="motor_05", max_torque_nm=400, corner_speed_rpm=4500, max_speed_rpm=12000,
         peak_eff=95.5, peak_speed_frac=0.62, peak_torque_frac=0.25,
         spread_speed=0.18, spread_torque=0.22, floor_eff=78.0, high_speed_penalty=0.4,
         mass_kg=230, cost_index=50),

    dict(map_id="motor_06", max_torque_nm=500, corner_speed_rpm=2400, max_speed_rpm=7500,
         peak_eff=89.0, peak_speed_frac=0.32, peak_torque_frac=0.40,
         spread_speed=0.18, spread_torque=0.25, floor_eff=68.0, high_speed_penalty=1.2,
         mass_kg=180, cost_index=30),

    dict(map_id="motor_07", max_torque_nm=900, corner_speed_rpm=1400, max_speed_rpm=5500,
         peak_eff=94.0, peak_speed_frac=0.24, peak_torque_frac=0.68,
         spread_speed=0.16, spread_torque=0.20, floor_eff=76.0, high_speed_penalty=1.1,
         mass_kg=330, cost_index=50),

    dict(map_id="motor_08", max_torque_nm=350, corner_speed_rpm=5200, max_speed_rpm=13000,
         peak_eff=96.0, peak_speed_frac=0.64, peak_torque_frac=0.22,
         spread_speed=0.17, spread_torque=0.18, floor_eff=77.0, high_speed_penalty=0.35,
         mass_kg=210, cost_index=55),

    dict(map_id="motor_09", max_torque_nm=500, corner_speed_rpm=3000, max_speed_rpm=9000,
         peak_eff=92.5, peak_speed_frac=0.40, peak_torque_frac=0.42,
         spread_speed=0.22, spread_torque=0.25, floor_eff=75.0, high_speed_penalty=0.7,
         mass_kg=150, cost_index=38),

    dict(map_id="motor_10", max_torque_nm=700, corner_speed_rpm=2600, max_speed_rpm=9500,
         peak_eff=97.0, peak_speed_frac=0.34, peak_torque_frac=0.52,
         spread_speed=0.12, spread_torque=0.16, floor_eff=79.0, high_speed_penalty=0.55,
         mass_kg=285, cost_index=58),

    dict(map_id="motor_11", max_torque_nm=1000, corner_speed_rpm=1600, max_speed_rpm=6500,
         peak_eff=91.5, peak_speed_frac=0.28, peak_torque_frac=0.62,
         spread_speed=0.20, spread_torque=0.24, floor_eff=73.0, high_speed_penalty=0.9,
         mass_kg=400, cost_index=44),

    dict(map_id="motor_12", max_torque_nm=650, corner_speed_rpm=2500, max_speed_rpm=8500,
         peak_eff=94.5, peak_speed_frac=0.42, peak_torque_frac=0.40,
         spread_speed=0.24, spread_torque=0.27, floor_eff=78.0, high_speed_penalty=0.65,
         mass_kg=260, cost_index=52),
]

if __name__ == "__main__":
    index = []
    for spec in MAPS:
        d = build_map(**spec)
        index.append({k: d[k] for k in ("id", "max_torque_nm",
                                          "corner_speed_rpm", "max_speed_rpm", "max_power_kw",
                                          "mass_kg", "cost_index")})
    with open(os.path.join(OUT_DIR, "_index.json"), "w") as f:
        json.dump(index, f, indent=2)
    print(f"\n{len(MAPS)} efficiency maps generated in {OUT_DIR}")
