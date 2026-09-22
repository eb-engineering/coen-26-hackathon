# Guia rápido

## 1. Instalar

No Windows, execute `setup.bat`. Ele seleciona explicitamente Python 3.10 ou
mais recente, ignorando um eventual Python 2. Se necessário, instala Python
3.12 automaticamente, sem depender da opção `Add Python to PATH`. Em seguida,
recria a `.venv`, instala as dependências no ambiente correto e confere a
importação do NumPy.

```bat
setup.bat
```

Em Linux ou macOS, execute `bash setup.sh`.

Nos comandos abaixo, Linux e macOS devem usar `.venv/bin/python` no lugar de
`.venv\Scripts\python.exe`.

## 2. Rodar uma configuração

Edite somente estes campos em `configs/example_config.json`:

- `final_drive_ratio`
- `initial_soc_pct`
- `em_map_id`
- `battery_id`

Execute:

```bash
.venv\Scripts\python.exe src/run_from_config.py --config configs/example_config.json --output outputs/resultado.json
```

## 3. Usar a API

```bash
.venv\Scripts\python.exe -m uvicorn api:app --app-dir src --reload --port 8000
```

Acesse `http://localhost:8000/docs`. Consulte `GET /parameters`, `GET /maps` e
`GET /batteries` antes de enviar uma configuração para `POST /simulate`.

## 4. Conferir o resultado

O resultado contém:

- `inputs`: configuração executada;
- `summary`: métricas calculadas;
- metadados do motor, da bateria e do ciclo;
- `trace`: séries temporais do ciclo.

Os limites e as tabelas de motores e baterias estão em
`data/REFERENCIA_COMPONENTES.md`. O simulador não informa se a solução é válida:
a equipe deve comparar as métricas do resultado com os limites publicados.

Para visualizar resultados, abra `dashboard/dashboard.html`.
