@echo off
cls
echo ============================================
echo   NEXUS - WPPConnect Server
echo ============================================
echo.
echo [1/3] Parando processos node antigos...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo.
echo [2/3] Verificando dependências...
if not exist "node_modules\" (
    echo Instalando dependências...
    call npm install
) else (
    echo Dependências OK!
)
echo.
echo [3/3] Iniciando servidor WPPConnect...
echo.
node server.js
