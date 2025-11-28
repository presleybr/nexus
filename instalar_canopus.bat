@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cls

echo ============================================================
echo    INSTALACAO DAS DEPENDENCIAS CANOPUS
echo ============================================================
echo.

REM Mudar para o diretorio do script
cd /d "%~dp0"

REM Ativar ambiente virtual
if exist venv\Scripts\activate.bat (
    echo [OK] Ativando ambiente virtual...
    call venv\Scripts\activate.bat
) else (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute primeiro: iniciar.bat
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    INSTALANDO DEPENDENCIAS PYTHON
echo ============================================================
echo.

echo [1/3] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Instalando bibliotecas Python...
python -m pip install playwright pandas openpyxl xlrd cryptography python-dotenv beautifulsoup4 lxml

echo.
echo [3/3] Instalando navegadores do Playwright...
echo [INFO] Isso pode demorar 2-5 minutos...
python -m playwright install chromium

echo.
echo ============================================================
echo [OK] INSTALACAO CONCLUIDA!
echo ============================================================
echo.
echo As dependencias da Automacao Canopus foram instaladas.
echo Agora voce pode executar: iniciar.bat
echo.
pause
