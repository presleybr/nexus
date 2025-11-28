@echo off
echo ============================================================
echo REINICIANDO SERVIDOR FLASK
echo ============================================================
echo.

echo [1/3] Encerrando processos Python...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Aguardando 3 segundos...
timeout /t 3 /nobreak >nul

echo [3/3] Iniciando servidor Flask...
cd /d "D:\Nexus\backend"
start "Flask Server" cmd /k "python app.py"

echo.
echo ============================================================
echo SERVIDOR REINICIADO!
echo ============================================================
echo.
echo Aguarde alguns segundos e acesse:
echo http://127.0.0.1:5000/crm/disparos
echo.
echo Pressione Ctrl+Shift+R no navegador para limpar o cache
echo.
pause
