@echo off
echo ============================================================
echo NEXUS CRM - Setup de Automacao Mensal
echo ============================================================
echo.

REM Ativa o ambiente virtual
echo [1/3] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instala dependências
echo.
echo [2/3] Instalando dependencias (apscheduler, pytz)...
pip install apscheduler pytz

REM Executa migration
echo.
echo [3/3] Aplicando migration no banco de dados...
python backend\scripts\aplicar_migration_automacao.py

echo.
echo ============================================================
echo Setup concluido!
echo ============================================================
echo.
echo Proximos passos:
echo 1. Reinicie a aplicacao Flask
echo 2. Acesse http://localhost:5000/crm/disparos
echo 3. Configure o dia do mes e ative a automacao
echo.
echo O scheduler sera iniciado automaticamente!
echo.
pause
