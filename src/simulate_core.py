"""
Simulação longitudinal principal do Truck BEV.

Método: modelo quase-estático "backward-then-clip" rodado a cada passo de
1 segundo do ciclo de condução:

  1. Calcula a força/torque de tração necessário na roda para seguir o ciclo
     de referência a partir da velocidade ATUAL do caminhão (não da
     velocidade ideal de referência) — isso permite que o caminhão fique
     para trás do ciclo se o motor/relação estiverem subdimensionados (um
     "trace miss" de verdade, como ferramentas reais de simulação veicular
     reportam).
  2. Converte torque de roda <-> torque de motor pela relação de transmissão
     final e pela eficiência do driveline (fixa em 96%).
  3. Limita o torque do motor ao envelope torque-velocidade do mapa de
     eficiência escolhido (região de torque constante e depois potência
     constante).
  4. Recalcula a força/aceleração REAL alcançável com o torque limitado, e
     integra isso para obter a velocidade real do caminhão no próximo passo.
  5. Consulta a eficiência do motor no ponto de operação (já limitado) e
     calcula a potência elétrica solicitada do motor/inversor.
  6. Aplica a perda ôhmica da bateria (P = I² × R, com tensão nominal fixa),
     que depende do pacote de bateria escolhido — isso é o que faz a
     resistência interna afetar as perdas reais da simulação.
  7. Integra o SOC e, ao final, estima a autonomia do veículo.

A massa total é veículo-base + motor/inversor + bateria. Motor e bateria
também têm custos relativos, usados na restrição de orçamento do desafio.

Tudo que a lista de avaliação do hackathon pede fica registrado:
  - traço de v_ref vs v_sim
  - energia consumida (kWh) e regenerada (kWh), já contabilizando a perda
    ôhmica da bateria
  - traço de SOC, SOC mínimo/final
  - torque/potência máximos exigidos vs. disponíveis
  - autonomia estimada (km)
  - "trace_error_rms_mps": 0 se o caminhão seguiu o ciclo perfeitamente
"""
import json
import math
import os

import numpy as np
from scipy.interpolate import RegularGridInterpolator

try:
    from vehicle_params import VehicleParams, DEFAULT_VEHICLE
    from battery_options import get_battery, BATTERY_SYSTEM_VOLTAGE_V
except ImportError:
    from src.vehicle_params import VehicleParams, DEFAULT_VEHICLE
    from src.battery_options import get_battery, BATTERY_SYSTEM_VOLTAGE_V

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EM_MAP_DIR = os.path.join(DATA_DIR, "em_maps")


def load_cycle(path=None):
    path = path or os.path.join(DATA_DIR, "mixed_cycle.json")
    with open(path) as f:
        d = json.load(f)
    return np.array(d["time_s"]), np.array(d["speed_mps"]), d.get("source", "")


def load_em_map(em_map_id):
    path = os.path.join(EM_MAP_DIR, f"{em_map_id}.json")
    if not os.path.exists(path):
        raise ValueError(f"em_map_id desconhecido '{em_map_id}'. Os mapas disponíveis estão listados em "
                          f"{os.path.join(EM_MAP_DIR, '_index.json')}")
    with open(path) as f:
        m = json.load(f)
    speed = np.array(m["speed_rpm"])
    torque = np.array(m["torque_nm"])
    eff = np.array(m["efficiency_pct"], dtype=float)  # pode conter NaN fora do envelope
    interp = RegularGridInterpolator((speed, torque), eff, bounds_error=False, fill_value=None)
    return m, interp


def envelope_torque_nm(speed_rpm, max_torque_nm, corner_speed_rpm, max_speed_rpm):
    speed_rpm = max(speed_rpm, 1e-6)
    if speed_rpm <= corner_speed_rpm:
        return max_torque_nm
    if speed_rpm >= max_speed_rpm:
        return 0.0
    corner_power = max_torque_nm * corner_speed_rpm
    return corner_power / speed_rpm


def run_simulation(final_drive_ratio, initial_soc_pct, em_map_id, battery_id,
                    vehicle: VehicleParams = DEFAULT_VEHICLE, cycle_path=None):
    """
    Roda a simulação completa do ciclo misto para uma configuração.
    Retorna um dicionário (serializável em JSON) com métricas de resumo e o
    traço completo no tempo.
    """
    t, v_ref, cycle_source = load_cycle(cycle_path)
    n = len(t)
    dt = float(vehicle.dt_s)

    map_meta_raw, eff_interp = load_em_map(em_map_id)
    # cópia segura para JSON dos metadados do mapa (células NaN -> null)
    map_meta = {k: v for k, v in map_meta_raw.items() if k != "efficiency_pct"}
    map_meta["efficiency_pct"] = [
        [None if (isinstance(x, float) and math.isnan(x)) else x for x in row]
        for row in map_meta_raw["efficiency_pct"]
    ]
    max_torque_nm = map_meta["max_torque_nm"]
    corner_speed_rpm = map_meta["corner_speed_rpm"]
    max_speed_rpm = map_meta["max_speed_rpm"]

    battery = get_battery(battery_id)
    batt_capacity_kwh = battery["capacidade_kwh"]
    batt_capacity_j = batt_capacity_kwh * 3.6e6
    batt_resistance_ohm = battery["resistencia_interna_mohm"] / 1000.0
    batt_voltage_v = BATTERY_SYSTEM_VOLTAGE_V

    motor_mass_kg = map_meta["mass_kg"]
    motor_cost = map_meta["cost_index"]
    powertrain_cost = motor_cost + battery["custo_relativo"]
    m = vehicle.mass_no_battery_kg + motor_mass_kg + battery["massa_kg"]
    g = vehicle.gravity_m_s2
    rho = vehicle.air_density_kg_m3
    Cd = vehicle.drag_coefficient
    A = vehicle.frontal_area_m2
    Crr = vehicle.rolling_resistance_coeff
    r_wheel = vehicle.wheel_radius_m
    eta_dl = vehicle.driveline_efficiency

    v_sim = np.zeros(n)
    v_sim[0] = v_ref[0]
    motor_torque_nm = np.zeros(n)
    motor_torque_requested_nm = np.zeros(n)
    motor_torque_available_nm = np.zeros(n)
    motor_speed_rpm = np.zeros(n)
    motor_eff_pct = np.full(n, np.nan)
    elec_power_kw = np.zeros(n)      # potência elétrica no motor/inversor (antes da perda ôhmica da bateria)
    battery_power_kw = np.zeros(n)   # potência real trocada com a bateria (já com a perda ôhmica)
    soc_pct = np.zeros(n)
    soc_pct[0] = initial_soc_pct
    torque_clipped_flag = np.zeros(n, dtype=bool)
    soc_violation_flag = np.zeros(n, dtype=bool)

    total_energy_consumed_kwh = 0.0
    total_energy_regen_kwh = 0.0
    total_battery_ir_loss_kwh = 0.0
    max_torque_requested = 0.0
    max_torque_delivered = 0.0
    max_power_requested_kw = 0.0
    max_power_delivered_kw = 0.0
    max_motor_speed_rpm = 0.0

    for i in range(n - 1):
        v_now = v_sim[i]
        v_target = v_ref[i + 1]
        a_req = (v_target - v_now) / dt

        f_road_load = 0.5 * rho * Cd * A * v_now ** 2 + Crr * m * g * (1 if v_now > 0.05 else 0)
        f_traction_req = m * a_req + f_road_load
        wheel_torque_req = f_traction_req * r_wheel

        wheel_speed_rad_s = max(v_now, 0.0) / r_wheel
        motor_speed_rad_s = wheel_speed_rad_s * final_drive_ratio
        n_motor_rpm = motor_speed_rad_s * 60.0 / (2 * math.pi)

        motor_torque_req = wheel_torque_req / final_drive_ratio
        if motor_torque_req >= 0:
            motor_torque_req = motor_torque_req / eta_dl   # tração: perdas do driveline somam ao motor
        else:
            motor_torque_req = motor_torque_req * eta_dl   # regen: perdas do driveline reduzem o torque visto no motor

        tq_cap = envelope_torque_nm(n_motor_rpm, max_torque_nm, corner_speed_rpm, max_speed_rpm)
        tq_actual = float(np.clip(motor_torque_req, -tq_cap, tq_cap))
        clipped = abs(tq_actual - motor_torque_req) > 1e-6
        torque_clipped_flag[i] = clipped

        # Recalcula o que o caminhão CONSEGUE fazer de verdade com o torque limitado
        wheel_torque_actual = tq_actual * final_drive_ratio * (eta_dl if tq_actual >= 0 else 1 / eta_dl)
        f_traction_actual = wheel_torque_actual / r_wheel
        a_actual = (f_traction_actual - f_road_load) / m
        v_next = max(v_now + a_actual * dt, 0.0)
        v_sim[i + 1] = v_next

        mech_power_w = tq_actual * motor_speed_rad_s
        requested_mech_power_w = motor_torque_req * motor_speed_rad_s
        eff_lookup_tq = max(min(abs(tq_actual), max_torque_nm), 0.5)
        eff_pct = float(eff_interp([[max(n_motor_rpm, 50), eff_lookup_tq]])[0])
        eff_pct = 40.0 if math.isnan(eff_pct) else max(min(eff_pct, 99.0), 40.0)
        eff_frac = eff_pct / 100.0

        if mech_power_w >= 0:
            elec_power_w = mech_power_w / eff_frac
        else:
            elec_power_w = mech_power_w * eff_frac
            max_regen_w = vehicle.max_regen_power_kw * 1000
            elec_power_w = max(elec_power_w, -max_regen_w)  # limite de potência de regen

        # Eficiência de conversão dependente do SOC, interpolada a cada passo.
        battery_eff_frac = float(np.interp(
            soc_pct[i], battery["soc_breakpoints_pct"], battery["soc_efficiency_pct"]
        )) / 100.0

        # Perda ôhmica da bateria (P = I² × R) — depende do pacote escolhido.
        current_a = elec_power_w / batt_voltage_v
        ir_loss_w = current_a ** 2 * batt_resistance_ohm
        if elec_power_w >= 0:
            battery_power_w = elec_power_w / battery_eff_frac + ir_loss_w
        else:
            battery_power_w = elec_power_w * battery_eff_frac + ir_loss_w

        d_soc = -(battery_power_w * dt) / batt_capacity_j * 100.0
        new_soc = soc_pct[i] + d_soc
        if new_soc < vehicle.battery_min_soc_pct or new_soc > vehicle.battery_max_soc_pct:
            soc_violation_flag[i] = True
        soc_pct[i + 1] = float(np.clip(new_soc, 0.0, 100.0))

        motor_torque_nm[i] = tq_actual
        motor_torque_requested_nm[i] = motor_torque_req
        motor_torque_available_nm[i] = tq_cap
        motor_speed_rpm[i] = n_motor_rpm
        motor_eff_pct[i] = eff_pct
        elec_power_kw[i] = elec_power_w / 1000.0
        battery_power_kw[i] = battery_power_w / 1000.0

        if battery_power_w >= 0:
            total_energy_consumed_kwh += battery_power_w * dt / 3.6e6
        else:
            total_energy_regen_kwh += -battery_power_w * dt / 3.6e6
        total_battery_ir_loss_kwh += ir_loss_w * dt / 3.6e6

        max_torque_requested = max(max_torque_requested, abs(motor_torque_req))
        max_torque_delivered = max(max_torque_delivered, abs(tq_actual))
        max_power_requested_kw = max(max_power_requested_kw, abs(requested_mech_power_w) / 1000.0)
        max_power_delivered_kw = max(max_power_delivered_kw, abs(mech_power_w) / 1000.0)
        max_motor_speed_rpm = max(max_motor_speed_rpm, n_motor_rpm)

    trace_error_rms_mps = float(np.sqrt(np.mean((v_ref - v_sim) ** 2)))
    speed_error_mps = v_ref - v_sim
    max_speed_error_mps = float(np.max(np.abs(speed_error_mps)))
    distance_km = float(np.trapezoid(v_ref, t) / 1000.0)
    net_energy_kwh = total_energy_consumed_kwh - total_energy_regen_kwh
    kwh_per_100km = net_energy_kwh / distance_km * 100.0 if distance_km > 0 else float("nan")

    # Autonomia estimada: energia utilizável da bateria (até a reserva mínima de SOC)
    # dividida pelo consumo médio observado no ciclo misto.
    usable_capacity_kwh = batt_capacity_kwh * (100.0 - vehicle.battery_min_soc_pct) / 100.0
    if kwh_per_100km and kwh_per_100km > 0:
        autonomia_km = usable_capacity_kwh / (kwh_per_100km / 100.0)
    else:
        autonomia_km = float("nan")

    results = {
        "inputs": {
            "final_drive_ratio": final_drive_ratio,
            "initial_soc_pct": initial_soc_pct,
            "em_map_id": em_map_id,
            "battery_id": battery_id,
        },
        "map_metadata": map_meta,
        "battery_metadata": battery,
        "cycle_source": cycle_source,
        "summary": {
            "massa_total_kg": round(m, 1),
            "battery_mass_kg": battery["massa_kg"],
            "powertrain_cost_index": round(powertrain_cost, 1),
            "distance_km": round(distance_km, 3),
            "energy_consumed_kwh": round(total_energy_consumed_kwh, 4),
            "energy_regenerated_kwh": round(total_energy_regen_kwh, 4),
            "battery_ir_loss_kwh": round(total_battery_ir_loss_kwh, 4),
            "net_energy_kwh": round(net_energy_kwh, 4),
            "kwh_per_100km": round(kwh_per_100km, 3),
            "autonomia_estimada_km": round(autonomia_km, 1) if not math.isnan(autonomia_km) else None,
            "final_soc_pct": round(float(soc_pct[-1]), 3),
            "min_soc_pct": round(float(soc_pct.min()), 3),
            "max_torque_demanded_nm": round(max_torque_requested, 2),
            "max_torque_delivered_nm": round(max_torque_delivered, 2),
            "max_torque_available_nm": max_torque_nm,
            "max_power_demanded_kw": round(max_power_requested_kw, 2),
            "max_power_delivered_kw": round(max_power_delivered_kw, 2),
            "max_power_available_kw": map_meta["max_power_kw"],
            "max_motor_speed_rpm": round(max_motor_speed_rpm, 1),
            "map_max_speed_rpm": max_speed_rpm,
            "trace_error_rms_mps": round(trace_error_rms_mps, 5),
            "max_speed_error_mps": round(max_speed_error_mps, 5),
            "any_torque_clipped": bool(torque_clipped_flag.any()),
            "pct_time_torque_clipped": round(float(torque_clipped_flag.mean() * 100), 2),
            "any_soc_violation": bool(soc_violation_flag.any()),
        },
        "trace": {
            "time_s": t.tolist(),
            "speed_ref_mps": v_ref.tolist(),
            "speed_sim_mps": v_sim.tolist(),
            "speed_error_mps": speed_error_mps.tolist(),
            "motor_torque_nm": motor_torque_nm.tolist(),
            "motor_torque_requested_nm": motor_torque_requested_nm.tolist(),
            "motor_torque_available_nm": motor_torque_available_nm.tolist(),
            "torque_saturated": torque_clipped_flag.tolist(),
            "motor_speed_rpm": motor_speed_rpm.tolist(),
            "motor_efficiency_pct": [None if math.isnan(x) else x for x in motor_eff_pct.tolist()],
            "elec_power_kw": elec_power_kw.tolist(),
            "battery_power_kw": battery_power_kw.tolist(),
            "soc_pct": soc_pct.tolist(),
        },
    }
    return results


if __name__ == "__main__":
    res = run_simulation(final_drive_ratio=8.0, initial_soc_pct=90.0,
                          em_map_id="motor_02", battery_id="battery_05")
    print(json.dumps(res["summary"], indent=2, ensure_ascii=False))
