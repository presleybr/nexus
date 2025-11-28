@echo off
cls
echo ============================================
echo   NEXUS - Iniciando Evolution API
echo ============================================
echo.

cd /d "D:\Nexus\evolution-api"

REM Tentar com docker compose (versão nova)
echo Tentando iniciar Evolution API...
docker compose up -d 2>nul

REM Se falhar, tentar docker-compose (versão antiga)
if errorlevel 1 (
    echo Tentando comando alternativo...
    docker-compose up -d 2>nul
)

REM Verificar se funcionou
if errorlevel 1 (
    echo.
    echo ❌ ERRO: Não foi possível iniciar o Evolution API
    echo.
    echo Verifique:
    echo   1. Docker Desktop está rodando?
    echo   2. Abra o Docker Desktop e aguarde inicializar
    echo   3. Tente novamente
    echo.
    pause
    exit /b 1
)

echo.
echo ⏳ Aguardando Evolution API inicializar (15 segundos)...
timeout /t 15 /nobreak >nul

echo.
echo ✅ Evolution API iniciado!
echo 🌐 URL: http://localhost:8080
echo 🔑 API Key: nexus-evolution-key-2025-secure
echo.
echo Comandos úteis:
echo   Ver logs:    docker compose logs -f
echo   Parar:       docker compose down
echo   Reiniciar:   docker compose restart
echo   Status:      docker ps
echo.
pause
