# Referência de restrições e componentes

Este arquivo apresenta os dados utilizados pelo simulador. As fontes carregadas
em tempo de execução são `em_maps/_index.json`, os mapas individuais em
`em_maps/` e `batteries/_index.json`.

## Limites para validação

Os limites são fixos. O simulador calcula os valores de desempenho novamente em
cada execução, durante todo o ciclo de condução, mas não decide se a solução é
válida. Essa comparação deve ser implementada pela equipe.

| Critério | Limite ou condição | Dados disponíveis para validação |
|---|---|---|
| Torque | nenhuma saturação de torque | demanda do ciclo comparada ao envelope torque × rotação do motor selecionado |
| Potência | demanda ≤ potência máxima do motor, com tolerância numérica de 0,1% | demanda mecânica calculada no ciclo e `max_power_kw` do motor |
| Velocidade | erro máximo absoluto ≤ 0,10 m/s | diferença entre `speed_ref_mps` e `speed_sim_mps` |
| SOC | entre 10% e 100% | SOC integrado segundo a segundo com eficiência da bateria dependente do SOC |
| Massa da bateria | ≤ 900 kg | `massa_kg` da bateria selecionada |
| Custo do powertrain | ≤ 132 | `cost_index` do motor + `custo_relativo` da bateria |
| Autonomia | ≥ 200 km | capacidade utilizável e consumo calculado em kWh/100 km |

Massa total usada na dinâmica:

```text
massa_total_kg = 3000 + massa_motor_kg + massa_bateria_kg
```

O volume da bateria é um dado informativo e não possui limite nesta versão.

## Motores

| ID | Torque máx. (Nm) | Rotação de canto (rpm) | Rotação máx. (rpm) | Potência máx. (kW) | Massa (kg) | Custo |
|---|---:|---:|---:|---:|---:|---:|
| `motor_01` | 550 | 2600 | 9000 | 149,7 | 220 | 42 |
| `motor_02` | 750 | 1800 | 6000 | 141,4 | 240 | 45 |
| `motor_03` | 650 | 2800 | 10000 | 190,6 | 320 | 65 |
| `motor_04` | 900 | 2200 | 8000 | 207,3 | 360 | 58 |
| `motor_05` | 400 | 4500 | 12000 | 188,5 | 230 | 50 |
| `motor_06` | 500 | 2400 | 7500 | 125,7 | 180 | 30 |
| `motor_07` | 900 | 1400 | 5500 | 131,9 | 330 | 50 |
| `motor_08` | 350 | 5200 | 13000 | 190,6 | 210 | 55 |
| `motor_09` | 500 | 3000 | 9000 | 157,1 | 150 | 38 |
| `motor_10` | 700 | 2600 | 9500 | 190,6 | 285 | 58 |
| `motor_11` | 1000 | 1600 | 6500 | 167,6 | 400 | 44 |
| `motor_12` | 650 | 2500 | 8500 | 170,2 | 260 | 52 |

Os mapas completos de eficiência estão nos arquivos individuais de cada motor
em `em_maps/`.

## Baterias

| ID | Capacidade (kWh) | Massa (kg) | Volume (L) | Custo | Resistência (mΩ) | Eficiência estimada a 100 kW (%) | SOC de pico (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `battery_01` | 60 | 390 | 360 | 38 | 130 | 91,88 | 85 |
| `battery_02` | 75 | 460 | 420 | 46 | 95 | 94,06 | 72 |
| `battery_03` | 90 | 560 | 510 | 56 | 160 | 90,00 | 58 |
| `battery_04` | 105 | 640 | 590 | 65 | 80 | 95,00 | 45 |
| `battery_05` | 120 | 760 | 700 | 72 | 140 | 91,25 | 80 |
| `battery_06` | 140 | 850 | 790 | 86 | 70 | 95,62 | 55 |
| `battery_07` | 160 | 1080 | 960 | 98 | 110 | 93,12 | 35 |
| `battery_08` | 190 | 1320 | 1170 | 115 | 150 | 90,62 | 68 |
| `battery_09` | 220 | 1600 | 1390 | 132 | 90 | 94,38 | 50 |
| `battery_10` | 260 | 2000 | 1700 | 154 | 125 | 92,19 | 28 |

Cada arquivo individual em `batteries/` também contém os pontos completos da
curva `soc_efficiency_pct` usada na interpolação segundo a segundo.
