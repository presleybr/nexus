@echo off
echo ============================================================
echo REINICIANDO SERVIDOR FLASK - NEXUS CRM
echo ============================================================
echo.
echo [INFO] Parando processos Flask antigos...

REM Mata processos Python rodando Flask
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *flask*" 2>nul
timeout /t 2 >nul

echo.
echo [INFO] Limpando cache Python...
del /s /q backend\__pycache__ 2>nul
del /s /q backend\routes\__pycache__ 2>nul
del /s /q backend\services\__pycache__ 2>nul
del /s /q backend\models\__pycache__ 2>nul

echo.
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo [INFO] Iniciando servidor...
echo.
python backend\app.py

pause
