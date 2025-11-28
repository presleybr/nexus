@echo off
title Limpar Cache Pip - Nexus CRM

echo.
echo ================================================================================
echo                      LIMPANDO CACHE DO PIP
echo ================================================================================
echo.

call venv\Scripts\activate

echo [*] Limpando cache do pip...
python -m pip cache purge

echo.
echo [OK] Cache limpo!
echo.
echo Agora execute: setup_canopus_simples.bat
echo.
pause
