"""
Ponto de entrada via linha de comando para a simulação longitudinal do Truck BEV.

Uso (esta é a forma principal de avaliar uma nova configuração):

    python run_from_config.py --config configs/minha_config.json --output outputs/resultado_001.json

Esquema do JSON de configuração (só estes 4 campos são ajustáveis pela equipe,
conforme as regras do desafio):
{
  "final_drive_ratio": 8.0,
  "initial_soc_pct": 90.0,
  "em_map_id": "motor_04",
  "battery_id": "battery_04"
}

O resultado completo (métricas de resumo + traço completo no tempo) é escrito
em --output como JSON. Um resumo de uma linha também é impresso no stdout,
permitindo obter os números principais sem abrir o arquivo.
"""
import argparse
import json
import sys

try:
    from simulate_core import run_simulation
    from vehicle_params import PARAM_RANGES
except ImportError:
    from src.simulate_core import run_simulation
    from src.vehicle_params import PARAM_RANGES


def validate_config(cfg):
    errors = []
    fdr = cfg.get("final_drive_ratio")
    soc = cfg.get("initial_soc_pct")
    map_id = cfg.get("em_map_id")
    battery_id = cfg.get("battery_id")

    r = PARAM_RANGES["final_drive_ratio"]
    if fdr is None or not (r["min"] <= fdr <= r["max"]):
        errors.append(f"final_drive_ratio deve estar entre {r['min']} e {r['max']} (recebido {fdr})")

    r = PARAM_RANGES["initial_soc_pct"]
    if soc is None or not (r["min"] <= soc <= r["max"]):
        errors.append(f"initial_soc_pct deve estar entre {r['min']} e {r['max']} (recebido {soc})")

    choices = PARAM_RANGES["em_map_id"]["choices"]
    if map_id not in choices:
        errors.append(f"em_map_id deve ser um de {choices} (recebido {map_id!r})")

    choices = PARAM_RANGES["battery_id"]["choices"]
    if battery_id not in choices:
        errors.append(f"battery_id deve ser um de {choices} (recebido {battery_id!r})")

    return errors


def main():
    ap = argparse.ArgumentParser(description="Roda a simulação longitudinal do Truck BEV a partir de um arquivo de configuração.")
    ap.add_argument("--config", required=True, help="Caminho do JSON de entrada")
    ap.add_argument("--output", required=True, help="Caminho para escrever o JSON de resultado")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    errors = validate_config(cfg)
    if errors:
        print("REJEITADO: a configuração viola as faixas permitidas:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)

    result = run_simulation(
        final_drive_ratio=cfg["final_drive_ratio"],
        initial_soc_pct=cfg["initial_soc_pct"],
        em_map_id=cfg["em_map_id"],
        battery_id=cfg["battery_id"],
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    s = result["summary"]
    print(json.dumps({
        "kwh_per_100km": s["kwh_per_100km"],
        "autonomia_estimada_km": s["autonomia_estimada_km"],
        "final_soc_pct": s["final_soc_pct"],
        "min_soc_pct": s["min_soc_pct"],
        "battery_mass_kg": s["battery_mass_kg"],
        "powertrain_cost_index": s["powertrain_cost_index"],
        "max_torque_demanded_nm": s["max_torque_demanded_nm"],
        "max_torque_delivered_nm": s["max_torque_delivered_nm"],
        "max_torque_available_nm": s["max_torque_available_nm"],
        "max_power_demanded_kw": s["max_power_demanded_kw"],
        "max_power_delivered_kw": s["max_power_delivered_kw"],
        "max_power_available_kw": s["max_power_available_kw"],
        "trace_error_rms_mps": s["trace_error_rms_mps"],
        "max_speed_error_mps": s["max_speed_error_mps"],
        "pct_time_torque_saturated": s["pct_time_torque_clipped"],
        "any_torque_clipped": s["any_torque_clipped"],
        "any_soc_violation": s["any_soc_violation"],
        "output_file": args.output,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
