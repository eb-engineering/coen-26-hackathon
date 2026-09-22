"""
Parâmetros do veículo Truck BEV.

Os coeficientes de coastdown (arrasto, resistência de rolamento, área
frontal, raio de roda) e a eficiência do driveline são FIXOS — não são uma
escolha livre da equipe no desafio.

A massa do veículo é a soma do veículo-base, do motor/inversor escolhido e
do pacote de bateria. Trocar de motor ou bateria muda massa e consumo.
"""
from dataclasses import dataclass

try:
    from battery_options import BATTERY_CHOICES
except ImportError:
    from src.battery_options import BATTERY_CHOICES


@dataclass(frozen=True)
class VehicleParams:
    # --- Coastdown fixo (NÃO ajustável pela equipe) ---
    # Chassi + cabine + carga, sem bateria e sem motor/inversor.
    mass_no_battery_kg: float = 3000.0
    frontal_area_m2: float = 6.2
    drag_coefficient: float = 0.65
    rolling_resistance_coeff: float = 0.0085
    wheel_radius_m: float = 0.40
    air_density_kg_m3: float = 1.225
    gravity_m_s2: float = 9.81

    # --- Driveline (fixo, conforme o desafio) ---
    driveline_efficiency: float = 0.96

    # --- Bateria: limites de operação fixos (a capacidade/massa/resistência vêm da opção escolhida) ---
    battery_min_soc_pct: float = 10.0
    battery_max_soc_pct: float = 100.0
    max_regen_power_kw: float = 150.0   # limite de potência de carga (proteção da bateria/inversor)

    # Restrições de projeto do desafio. O custo é um índice relativo, não moeda.
    max_battery_mass_kg: float = 900.0
    max_powertrain_cost_index: float = 132.0
    max_speed_tracking_error_mps: float = 0.10
    max_power_demanded_to_available_ratio: float = 1.001

    # --- Restrição mínima do desafio ---
    min_autonomia_km: float = 200.0

    # --- Simulação ---
    dt_s: float = 1.0


DEFAULT_VEHICLE = VehicleParams()

# Faixas/escolhas permitidas para os 4 parâmetros ajustáveis pela equipe
PARAM_RANGES = {
    "final_drive_ratio": {"min": 3.0, "max": 14.0, "default": 8.0},
    "initial_soc_pct": {"min": 20.0, "max": 100.0, "default": 90.0},
    "em_map_id": {
        "choices": [
            "motor_01", "motor_02", "motor_03",
            "motor_04", "motor_05", "motor_06",
            "motor_07", "motor_08", "motor_09",
            "motor_10", "motor_11", "motor_12",
        ],
        "default": "motor_04",
    },
    "battery_id": {
        "choices": BATTERY_CHOICES,
        "default": "battery_04",
    },
    "challenge_constraints": {
        "torque_clipping_allowed": False,
        "max_power_demanded_to_available_ratio": DEFAULT_VEHICLE.max_power_demanded_to_available_ratio,
        "min_soc_pct": DEFAULT_VEHICLE.battery_min_soc_pct,
        "max_soc_pct": DEFAULT_VEHICLE.battery_max_soc_pct,
        "min_autonomia_km": DEFAULT_VEHICLE.min_autonomia_km,
        "max_battery_mass_kg": DEFAULT_VEHICLE.max_battery_mass_kg,
        "max_powertrain_cost_index": DEFAULT_VEHICLE.max_powertrain_cost_index,
        "max_speed_tracking_error_mps": DEFAULT_VEHICLE.max_speed_tracking_error_mps,
    },
}
