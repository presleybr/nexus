@echo off
echo TESTE 1: Script iniciado
echo TESTE 2: Pasta atual: %CD%

where node >nul 2>&1
if errorlevel 1 (
    echo TESTE 3: Node.js NAO encontrado
) else (
    echo TESTE 3: Node.js encontrado
)

if exist "wppconnect-server\node_modules\express" (
    echo TESTE 4: Express encontrado
) else (
    echo TESTE 4: Express NAO encontrado
)

if exist "start.py" (
    echo TESTE 5: start.py encontrado
) else (
    echo TESTE 5: start.py NAO encontrado
)

echo.
echo TESTE CONCLUIDO
pause
