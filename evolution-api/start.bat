@echo off
echo ============================================
echo   NEXUS - Evolution API com Docker
echo ============================================
echo.
echo Iniciando Evolution API...

REM Tentar docker compose (versão nova)
docker compose up -d 2>nul

REM Se falhar, tentar docker-compose (versão antiga)
if errorlevel 1 (
    echo Tentando comando alternativo...
    docker-compose up -d
)

echo.
echo Aguardando Evolution API inicializar...
timeout /t 15 /nobreak >nul
echo.
echo ✅ Evolution API iniciado!
echo 🌐 Acesse: http://localhost:8080
echo 🔑 API Key: nexus-evolution-key-2025-secure
echo.
echo Comandos úteis:
echo   Parar:     docker compose down
echo   Ver logs:  docker compose logs -f
echo   Status:    docker ps
echo.
pause
