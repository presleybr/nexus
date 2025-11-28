@echo off
chcp 65001 >nul
cls

echo ============================================================
echo    NEXUS CRM - Parar Todos os Servicos
echo    "Aqui seu tempo vale ouro"
echo ============================================================
echo.

REM Parar WPPConnect Server (Node.js)
echo [1/3] Parando WPPConnect Server...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq WPPConnect*" >nul 2>&1
if errorlevel 1 (
    echo [INFO] WPPConnect Server nao estava rodando
) else (
    echo [OK] WPPConnect Server parado
)

REM Parar Flask (Python)
echo.
echo [2/3] Parando Flask...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *start.py*" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Flask nao estava rodando
) else (
    echo [OK] Flask parado
)

REM Parar qualquer outro processo Python relacionado
echo.
echo [3/3] Limpando processos Python...
taskkill /F /IM python.exe /FI "IMAGENAME eq python.exe" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Nenhum processo Python adicional encontrado
) else (
    echo [OK] Processos Python encerrados
)

echo.
echo ============================================================
echo    TODOS OS SERVICOS FORAM PARADOS
echo ============================================================
echo.
echo [OK] Sistema Nexus CRM encerrado com sucesso!
echo.
pause
