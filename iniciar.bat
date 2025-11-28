@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cls

REM Mudar para o diretorio do script
cd /d "%~dp0"

echo ============================================================
echo    NEXUS CRM - Inicializacao Automatica
echo    "Aqui seu tempo vale ouro"
echo ============================================================
echo.
echo [INFO] Pasta atual: %CD%
echo.

REM Verificar se esta na pasta correta
if not exist "start.py" (
    echo [ERRO] Arquivo start.py nao encontrado!
    echo.
    echo Este script deve estar na pasta raiz do Nexus
    echo Pasta atual: %CD%
    echo.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
if exist venv\Scripts\activate.bat (
    echo [OK] Ativando ambiente virtual...
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERRO] Falha ao ativar ambiente virtual
        pause
        exit /b 1
    )
) else (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo.
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo [OK] Ambiente virtual criado e ativado
)

REM Verificar e instalar dependencias Python
echo.
echo [OK] Verificando dependencias Python do CRM...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -q reportlab python-barcode Pillow python-dateutil psycopg[binary] flask requests >nul 2>&1

if errorlevel 1 (
    echo [AVISO] Algumas dependencias podem nao ter sido instaladas
    echo O sistema tentara continuar...
) else (
    echo [OK] Dependencias Python do CRM verificadas
)

REM Verificar e instalar dependencias da Automacao Canopus
echo.
echo [OK] Verificando dependencias da Automacao Canopus...
python -m pip install -q playwright pandas openpyxl xlrd cryptography python-dotenv beautifulsoup4 lxml >nul 2>&1

if errorlevel 1 (
    echo [AVISO] Algumas dependencias da Automacao Canopus podem nao ter sido instaladas
    echo [INFO] O sistema continuara normalmente...
    echo [INFO] Para instalar manualmente: instalar_canopus.bat
) else (
    echo [OK] Dependencias da Automacao Canopus verificadas
)

REM Verificar se Playwright browsers estao instalados (nao bloqueia se falhar)
echo.
echo [OK] Verificando navegadores do Playwright...
python -c "from playwright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Playwright nao encontrado ou navegadores nao instalados
    echo [INFO] Execute 'instalar_canopus.bat' para instalar a automacao Canopus
    echo [INFO] O CRM continuara funcionando normalmente (sem automacao)
) else (
    echo [OK] Playwright verificado - Automacao Canopus disponivel
)

REM Verificar Node.js e WPPConnect
echo.
echo [OK] Verificando WPPConnect Server...
where node >nul 2>&1
if errorlevel 1 goto :sem_nodejs

REM Node.js encontrado
echo [OK] Node.js encontrado

REM Verificar se WPPConnect esta instalado
if not exist "wppconnect-server\node_modules\express" goto :sem_wppconnect

REM WPPConnect instalado - iniciar
echo [OK] WPPConnect Server instalado
echo.
echo ============================================================
echo    INICIANDO WPPCONNECT SERVER
echo ============================================================
echo.
echo [INFO] Iniciando servidor WhatsApp na porta 3001...

REM Mata processo anterior se existir
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Inicia WPPConnect em nova janela (SEM /MIN para ver os logs)
start "WPPConnect Server - NEXUS" cmd /c "cd /d %~dp0wppconnect-server && node server.js"

echo [OK] WPPConnect Server iniciado em janela separada
echo [INFO] Para ver logs: Procure janela "WPPConnect Server - NEXUS"
echo [INFO] API rodando em: http://localhost:3001

REM Aguarda 5 segundos para servidor iniciar
timeout /t 5 /nobreak >nul
echo.
goto :iniciar_flask

:sem_nodejs
echo [AVISO] Node.js nao encontrado!
echo [INFO] WPPConnect Server nao sera iniciado
echo [INFO] Para usar WhatsApp, instale Node.js 16+ e execute:
echo        cd wppconnect-server
echo        npm install
echo.
goto :iniciar_flask

:sem_wppconnect
echo [AVISO] WPPConnect Server nao instalado
echo [INFO] Para instalar, execute:
echo        cd wppconnect-server
echo        npm install --legacy-peer-deps --force
echo.

:iniciar_flask

REM Iniciar sistema Flask
echo ============================================================
echo    INICIANDO NEXUS CRM (FLASK)
echo ============================================================
echo.
echo [INFO] Flask rodando em: http://localhost:5000
echo.
python start.py

REM Manter janela aberta em caso de erro
if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERRO] Sistema encerrou com erro
    echo ============================================================
    echo.
    echo Verifique os logs acima para detalhes do erro
    echo.
    pause
)
