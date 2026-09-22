@echo off
REM Cria um ambiente virtual Python 3 (.venv) e instala as dependencias.
REM Uso: setup.bat (dar duplo-clique tambem funciona)

cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python3 >nul 2>nul
    if not errorlevel 1 (
        python3 -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python3"
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD goto :python_error

echo Usando:
%PYTHON_CMD% --version

echo Criando ambiente virtual Python 3 em .venv ...
%PYTHON_CMD% -m venv --clear .venv
if errorlevel 1 goto :setup_error

echo Instalando dependencias ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :setup_error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :setup_error

echo Verificando Python e bibliotecas ...
".venv\Scripts\python.exe" -c "import sys, numpy, scipy, fastapi, pydantic, uvicorn; print('OK:', sys.executable); print('Python', sys.version.split()[0]); print('NumPy', numpy.__version__)"
if errorlevel 1 goto :setup_error

echo.
echo Pronto! Rode o simulador diretamente com o Python da .venv:
echo     .venv\Scripts\python.exe src\run_from_config.py --config configs\example_config.json --output outputs\resultado.json
echo ou:
echo     .venv\Scripts\python.exe -m uvicorn api:app --app-dir src --reload --port 8000
pause
exit /b 0

:python_error
echo ERRO: Python 3.10 ou mais recente nao foi encontrado.
echo O comando "python" desta maquina pode estar apontando para Python 2.
echo Instale Python 3 em: https://www.python.org/downloads/
echo No Windows, marque "Add python.exe to PATH" e instale o Python Launcher.
pause
exit /b 1

:setup_error
echo.
echo ERRO: nao foi possivel preparar ou verificar o ambiente Python 3.
echo Consulte as mensagens acima.
pause
exit /b 1
