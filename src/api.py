"""
API REST do simulador longitudinal do Truck BEV.

Rodar com (a partir da raiz do projeto):
    uvicorn src.api:app --reload --port 8000

ou, a partir de dentro de src/:
    uvicorn api:app --reload --port 8000

Depois de iniciar o servidor, clientes HTTP podem:
    GET  /parameters          -> faixas/opções permitidas para os 4 parâmetros ajustáveis
    GET  /maps                -> mapas de eficiência da EM disponíveis + metadados
    GET  /batteries            -> opções de bateria disponíveis + especificações
    GET  /cycle                -> traço de tempo/velocidade do ciclo de referência
    POST /simulate             -> roda uma configuração, recebe os resultados
    GET  /results/{run_id}     -> busca de novo o resultado completo de uma execução anterior
    GET  /results              -> lista todas as execuções feitas até agora

O FastAPI gera automaticamente documentação interativa em /docs e um schema
OpenAPI em /openapi.json.
"""
import json
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    # Funciona tanto rodando de dentro de src/ (uvicorn api:app --app-dir src)
    # quanto rodando da raiz do projeto como pacote (uvicorn src.api:app)
    from simulate_core import run_simulation, load_cycle
    from vehicle_params import PARAM_RANGES
    from battery_options import BATTERIES
except ImportError:
    from src.simulate_core import run_simulation, load_cycle
    from src.vehicle_params import PARAM_RANGES
    from src.battery_options import BATTERIES

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
EM_MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "em_maps")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

app = FastAPI(
    title="Simulador Longitudinal Truck BEV",
    description="Hackathon EB — backend para simular configurações e fornecer métricas físicas.",
    version="1.3.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _read_result_json(path):
    """Lê resultados novos em UTF-8 e mantém compatibilidade com arquivos antigos do Windows."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, encoding="cp1252") as f:
            return json.load(f)


class SimulateRequest(BaseModel):
    final_drive_ratio: float = Field(..., description="Relação de transmissão final (voltas do motor por volta da roda).")
    initial_soc_pct: float = Field(..., description="SOC inicial da bateria, em porcentagem.")
    em_map_id: str = Field(..., description="Qual mapa de eficiência da máquina elétrica usar.")
    battery_id: str = Field(..., description="Qual opção de pacote de bateria usar.")


@app.get("/parameters")
def get_parameters():
    """Faixas/opções permitidas para os 4 parâmetros ajustáveis pela equipe."""
    return PARAM_RANGES


@app.get("/maps")
def list_maps():
    """Lista todos os mapas de eficiência da EM disponíveis, com seu envelope de torque/velocidade/potência."""
    with open(os.path.join(EM_MAP_DIR, "_index.json")) as f:
        return json.load(f)


@app.get("/maps/{map_id}")
def get_map(map_id: str):
    """Grade completa do mapa de eficiência (velocidade, torque, eficiência) para plotagem/análise."""
    path = os.path.join(EM_MAP_DIR, f"{map_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, f"map_id desconhecido '{map_id}'")
    with open(path) as f:
        return json.load(f)


@app.get("/batteries")
def list_batteries():
    """
    Lista as opções de bateria com capacidade, massa, volume, custo,
    resistência interna e curva de eficiência em função do SOC.
    """
    return list(BATTERIES.values())


@app.get("/batteries/{battery_id}")
def get_battery_detail(battery_id: str):
    if battery_id not in BATTERIES:
        raise HTTPException(404, f"battery_id desconhecido '{battery_id}'")
    return BATTERIES[battery_id]


@app.get("/cycle")
def get_cycle():
    """O ciclo de referência misto UDDS+Rodoviário (tempo vs. velocidade de referência)."""
    t, v, source = load_cycle()
    return {"time_s": t.tolist(), "speed_ref_mps": v.tolist(), "source": source}


def _validate(req: SimulateRequest):
    errors = []
    r = PARAM_RANGES["final_drive_ratio"]
    if not (r["min"] <= req.final_drive_ratio <= r["max"]):
        errors.append(f"final_drive_ratio deve estar em [{r['min']}, {r['max']}]")
    r = PARAM_RANGES["initial_soc_pct"]
    if not (r["min"] <= req.initial_soc_pct <= r["max"]):
        errors.append(f"initial_soc_pct deve estar em [{r['min']}, {r['max']}]")
    if req.em_map_id not in PARAM_RANGES["em_map_id"]["choices"]:
        errors.append(f"em_map_id deve ser um de {PARAM_RANGES['em_map_id']['choices']}")
    if req.battery_id not in PARAM_RANGES["battery_id"]["choices"]:
        errors.append(f"battery_id deve ser um de {PARAM_RANGES['battery_id']['choices']}")
    return errors


@app.post("/simulate")
def simulate(req: SimulateRequest):
    """
    Roda uma simulação do ciclo misto UDDS+Rodoviário com a relação de
    transmissão, SOC inicial, mapa de eficiência e bateria informados.
    Rejeita (422) qualquer requisição fora das faixas permitidas.
    """
    errors = _validate(req)
    if errors:
        raise HTTPException(422, {"errors": errors})

    result = run_simulation(
        final_drive_ratio=req.final_drive_ratio,
        initial_soc_pct=req.initial_soc_pct,
        em_map_id=req.em_map_id,
        battery_id=req.battery_id,
    )
    run_id = str(uuid.uuid4())[:8]
    result["run_id"] = run_id
    with open(os.path.join(OUTPUTS_DIR, f"{run_id}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    return result


@app.get("/results/{run_id}")
def get_result(run_id: str):
    path = os.path.join(OUTPUTS_DIR, f"{run_id}.json")
    if not os.path.exists(path):
        raise HTTPException(404, f"Nenhuma execução armazenada com id '{run_id}'")
    return _read_result_json(path)


@app.get("/results")
def list_results():
    runs = []
    for fname in sorted(os.listdir(OUTPUTS_DIR)):
        if fname.endswith(".json") and fname != "_index.json":
            d = _read_result_json(os.path.join(OUTPUTS_DIR, fname))
            runs.append({
                "run_id": d.get("run_id", fname.replace(".json", "")),
                "inputs": d["inputs"],
                "summary": d["summary"],
            })
    return runs


@app.get("/")
def root():
    return {
        "message": "API do Simulador Longitudinal Truck BEV — veja /docs para a documentação interativa.",
        "endpoints": ["/parameters", "/maps", "/maps/{map_id}", "/batteries", "/batteries/{battery_id}",
                      "/cycle", "/simulate (POST)", "/results", "/results/{run_id}"],
    }
