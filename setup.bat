@echo off
setlocal
REM Prepara Python 3 e as dependencias do simulador.
REM Uso: setup.bat (dar duplo-clique tambem funciona)

cd /d "%~dp0"

call :find_python3
if defined PYTHON_EXE goto :python_ready

echo Python 3.10 ou mais recente nao foi encontrado.
echo O comando "python" existente sera ignorado se apontar para Python 2.
echo Tentando instalar Python 3.12 automaticamente...
echo.

call :install_python3
if errorlevel 1 goto :python_install_error

call :find_python3
if not defined PYTHON_EXE goto :python_install_error

:python_ready
echo Usando:
"%PYTHON_EXE%" %PYTHON_ARGS% --version

echo Criando ambiente virtual Python 3 em .venv ...
"%PYTHON_EXE%" %PYTHON_ARGS% -m venv --clear .venv
if errorlevel 1 goto :setup_error

echo Instalando dependencias no Python da .venv ...
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

:find_python3
set "PYTHON_EXE="
set "PYTHON_ARGS="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
        exit /b 0
    )
)

where python3 >nul 2>nul
if not errorlevel 1 (
    python3 -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=python3"
        exit /b 0
    )
)

REM "python" pode ser Python 2: so e aceito depois da verificacao de versao.
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        exit /b 0
    )
)

REM Caminhos padrao usados pela instalacao automatica em modo de usuario.
for %%V in (314 313 312 311 310) do (
    if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
        "%LocalAppData%\Programs\Python\Python%%V\python.exe" -c "import sys; raise SystemExit(sys.version_info.major != 3 or sys.version_info.minor not in range(10, 100))" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python%%V\python.exe"
            exit /b 0
        )
    )
)
exit /b 0

:install_python3
where winget >nul 2>nul
if not errorlevel 1 (
    echo Instalando Python 3.12 com winget...
    winget install --exact --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
    if not errorlevel 1 exit /b 0
    echo O winget nao conseguiu instalar. Tentando o instalador oficial...
)

set "PYTHON_VERSION=3.12.10"
set "PYTHON_ARCH=amd64"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "PYTHON_ARCH=arm64"
set "PYTHON_INSTALLER=%TEMP%\python-%PYTHON_VERSION%-%PYTHON_ARCH%.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-%PYTHON_ARCH%.exe"

echo Baixando o instalador oficial de %PYTHON_URL% ...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
if errorlevel 1 exit /b 1

echo Instalando Python %PYTHON_VERSION% silenciosamente para o usuario atual...
start /wait "" "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=0 Include_launcher=1 Include_test=0 SimpleInstall=1
set "INSTALL_RESULT=%ERRORLEVEL%"
del /q "%PYTHON_INSTALLER%" >nul 2>nul
if not "%INSTALL_RESULT%"=="0" exit /b 1
exit /b 0

:python_install_error
echo.
echo ERRO: nao foi possivel instalar automaticamente o Python 3.
echo Verifique a conexao com a internet e se o Windows permite instalar aplicativos.
echo Nenhuma opcao "Add Python to PATH" e necessaria para este setup.
pause
exit /b 1

:setup_error
echo.
echo ERRO: nao foi possivel preparar ou verificar o ambiente Python 3.
echo Consulte as mensagens acima.
pause
exit /b 1
