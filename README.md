# Modelo final calibrado Truck BEV — Hackathon EB

Esta é a versão final calibrada do simulador longitudinal quase-estático de um
caminhão elétrico a bateria. Ela inclui os 12 mapas de motor, as 10 baterias com
eficiência dependente do SOC, limites de massa e custo, envelopes de torque e
potência, saturação dinâmica e comparação entre velocidade de referência e
velocidade realizada.

A estratégia de análise, otimização e validação deve ser desenvolvida pela
equipe participante.

## Objetivo

Encontrar uma configuração que atenda simultaneamente aos limites técnicos
publicados. Entre eles estão autonomia mínima, limites de massa e
custo, capacidade de torque e potência, acompanhamento do ciclo de velocidade e
limites de SOC.

A configuração de exemplo é propositalmente inválida.

## Variáveis ajustáveis

Somente quatro entradas podem ser modificadas:

| Campo | Domínio |
|---|---|
| `final_drive_ratio` | número entre 3,0 e 14,0 |
| `initial_soc_pct` | número entre 20% e 100% |
| `em_map_id` | um dos 12 IDs retornados por `GET /maps` |
| `battery_id` | um dos 10 IDs retornados por `GET /batteries` |

As faixas, opções, valores iniciais e restrições do desafio estão disponíveis em
`GET /parameters`.

## Limites para validação

O simulador calcula as métricas físicas, mas não classifica a configuração como
válida ou inválida. A equipe deve implementar essa decisão comparando os
resultados com os limites públicos abaixo.

| Critério | Limite público | Métricas fornecidas pelo simulador |
|---|---|---|
| Torque | nenhuma saturação durante o ciclo | `any_torque_clipped`, `pct_time_torque_clipped` e torques demandado, entregue e disponível |
| Potência | demanda ≤ potência máxima do motor, com tolerância numérica de 0,1% | `max_power_demanded_kw` e `max_power_available_kw` |
| Velocidade | erro máximo absoluto ≤ 0,10 m/s | `max_speed_error_mps`, `speed_ref_mps` e `speed_sim_mps` |
| SOC | entre 10% e 100% durante todo o ciclo | `min_soc_pct`, `any_soc_violation` e `soc_pct` |
| Massa da bateria | ≤ 900 kg | `battery_mass_kg` |
| Custo do powertrain | ≤ 132 | `powertrain_cost_index` |
| Autonomia | ≥ 200 km | `autonomia_estimada_km` |

A massa total usada na dinâmica também é automática:
`3000 kg + massa do motor + massa da bateria`. O volume da bateria é informado,
mas não é uma restrição nesta versão.

## Dados dos motores

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

## Dados das baterias

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

Uma cópia de referência dessas tabelas, incluindo a origem de cada dado, está
em `data/REFERENCIA_COMPONENTES.md`. Os JSONs em `data/em_maps/` e
`data/batteries/` continuam sendo as fontes carregadas pelo simulador.

## Instalação

No Windows, use preferencialmente `setup.bat`. Ele procura explicitamente
Python 3.10 ou mais recente e ignora um eventual Python 2 associado ao comando
`python`. Se Python 3 não estiver instalado, o próprio script tenta instalar
Python 3.12 automaticamente pelo instalador oficial do python.org, somente no
perfil do usuário. Não exige conta de administrador, não altera o `PATH` global
e não é necessário configurar `Add Python to PATH`.

```bat
setup.bat
```

No Git Bash do Windows:

```bash
cmd.exe /c setup.bat
```

Instalação manual no Windows:

```bat
py -3 -m venv --clear .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Em Linux ou macOS:

```bash
bash setup.sh
```

Depois da instalação, os exemplos abaixo usam diretamente o Python da `.venv`,
evitando qualquer ambiguidade com outros Pythons instalados na máquina:

| Terminal | Executável da `.venv` |
|---|---|
| Prompt de Comando do Windows | `.venv\Scripts\python.exe` |
| PowerShell | `.\.venv\Scripts\python.exe` |
| Git Bash no Windows | `./.venv/Scripts/python.exe` |
| Linux ou macOS | `./.venv/bin/python` |

No Git Bash, não use barras invertidas (`\`), pois elas são interpretadas como
caracteres de escape.

## Execução pela CLI

```bat
.venv\Scripts\python.exe src\run_from_config.py --config configs\example_config.json --output outputs\resultado.json
```

No Git Bash, o mesmo comando é:

```bash
./.venv/Scripts/python.exe src/run_from_config.py --config configs/example_config.json --output outputs/resultado.json
```

O arquivo de configuração contém as quatro variáveis ajustáveis. O resultado é
gravado como JSON e inclui entradas, resumo, metadados e séries temporais. A
classificação final deve ser feita pela solução desenvolvida pela equipe.

## Execução pela API

```bat
.venv\Scripts\python.exe -m uvicorn api:app --app-dir src --reload --port 8000
```

No Git Bash:

```bash
./.venv/Scripts/python.exe -m uvicorn api:app --app-dir src --reload --port 8000
```

Depois de iniciar o servidor:

- documentação interativa: `http://localhost:8000/docs`
- `GET /parameters`
- `GET /maps` e `GET /maps/{map_id}`
- `GET /batteries` e `GET /batteries/{battery_id}`
- `GET /cycle`
- `POST /simulate`
- `GET /results` e `GET /results/{run_id}`

Exemplo de corpo para `POST /simulate`:

```json
{
  "final_drive_ratio": 8.0,
  "initial_soc_pct": 90.0,
  "em_map_id": "motor_04",
  "battery_id": "battery_04"
}
```

## Uso direto em Python

```python
from src.simulate_core import run_simulation

resultado = run_simulation(
    final_drive_ratio=8.0,
    initial_soc_pct=90.0,
    em_map_id="motor_04",
    battery_id="battery_04",
)
```

## Dashboard

Abra `dashboard/dashboard.html` no navegador e carregue um ou dois arquivos JSON
gerados pelo simulador. O dashboard funciona localmente e não exige servidor.

Para exportar a comparação entre velocidade de referência e velocidade
simulada:

```bash
./.venv/Scripts/python.exe src/export_speed_comparison.py --result outputs/resultado.json --output outputs/velocidade.svg
```

Em Linux ou macOS, use `./.venv/bin/python` no lugar de
`./.venv/Scripts/python.exe`.

## Estrutura do repositório

```text
configs/       configuração inicial
dashboard/     visualização local dos resultados
data/          ciclo de condução e mapas de eficiência
outputs/       resultados gerados localmente
src/           simulador, API e ferramentas de execução
GUIA_RAPIDO.md comandos essenciais
```

O repositório não inclui uma configuração final para o desafio.
