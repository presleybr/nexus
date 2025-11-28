@echo off
echo Parando Evolution API...

REM Tentar docker compose (versão nova)
docker compose down 2>nul

REM Se falhar, tentar docker-compose (versão antiga)
if errorlevel 1 (
    docker-compose down
)

echo ✅ Evolution API parado!
pause
