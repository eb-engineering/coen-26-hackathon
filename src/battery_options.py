"""Carregamento das opções de bateria do Hackathon EB.

Os dados públicos de cada pacote ficam em ``data/batteries``. A simulação usa
esses mesmos arquivos, evitando uma segunda definição escondida no código.
"""

import json
from pathlib import Path


BATTERY_SYSTEM_VOLTAGE_V = 400.0
BATTERY_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "batteries"
BATTERY_INDEX_PATH = BATTERY_DATA_DIR / "_index.json"


def _load_batteries():
    if not BATTERY_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Índice de baterias não encontrado: {BATTERY_INDEX_PATH}"
        )

    with BATTERY_INDEX_PATH.open("r", encoding="utf-8-sig") as stream:
        items = json.load(stream)

    if not isinstance(items, list) or not items:
        raise ValueError("data/batteries/_index.json deve conter uma lista não vazia")

    batteries = {}
    for item in items:
        battery_id = item.get("id") if isinstance(item, dict) else None
        if not battery_id:
            raise ValueError("Toda bateria deve possuir um campo 'id'")
        if battery_id in batteries:
            raise ValueError(f"ID de bateria duplicado: {battery_id}")
        batteries[battery_id] = item
    return batteries


BATTERIES = _load_batteries()
BATTERY_CHOICES = list(BATTERIES)


def get_battery(battery_id):
    if battery_id not in BATTERIES:
        raise ValueError(
            f"battery_id desconhecido '{battery_id}'. Opções: {BATTERY_CHOICES}"
        )
    return BATTERIES[battery_id]


if __name__ == "__main__":
    for battery in BATTERIES.values():
        print(battery)
