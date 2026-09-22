#!/usr/bin/env bash
# Cria um ambiente virtual (.venv) e instala as dependências do projeto.
# Uso: bash setup.sh
set -e

cd "$(dirname "$0")"

PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERRO: Python 3.10 ou mais recente não foi encontrado."
    echo "O comando 'python' desta máquina pode estar apontando para Python 2."
    echo "Baixe e instale o Python em: https://www.python.org/downloads/"
    exit 1
fi

echo "Usando: $($PYTHON_BIN --version)"
echo "Criando ambiente virtual Python 3 em .venv ..."
"$PYTHON_BIN" -m venv --clear .venv

echo "Instalando dependências ..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "Verificando Python e bibliotecas ..."
.venv/bin/python -c "import sys, numpy, scipy, fastapi, pydantic, uvicorn; print('OK:', sys.executable); print('Python', sys.version.split()[0]); print('NumPy', numpy.__version__)"

echo ""
echo "Pronto! Rode o simulador diretamente com o Python da .venv:"
echo "    .venv/bin/python src/run_from_config.py --config configs/example_config.json --output outputs/resultado.json"
echo "ou:"
echo "    .venv/bin/python -m uvicorn api:app --app-dir src --reload --port 8000"
