@echo off
chcp 65001 >nul
color 0B
title Setup Automacao Canopus - Nexus CRM

echo.
echo ================================================================================
echo                      SETUP AUTOMACAO CANOPUS - NEXUS CRM
echo ================================================================================
echo.
echo Este script ira configurar a automacao de download de boletos do Canopus.
echo.
echo Etapas:
echo   [1/5] Ativar ambiente virtual Python
echo   [2/5] Instalar dependencias Python
echo   [3/5] Instalar navegador Playwright Chromium
echo   [4/5] Criar estrutura de pastas
echo   [5/5] Criar tabelas no banco de dados PostgreSQL
echo.
echo Pressione qualquer tecla para continuar ou CTRL+C para cancelar...
pause >nul

echo.
echo ================================================================================
echo [1/5] Ativando ambiente virtual Python...
echo ================================================================================

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERRO] Ambiente virtual nao encontrado!
    echo.
    echo Crie o ambiente virtual primeiro:
    echo    python -m venv venv
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate

echo [OK] Ambiente virtual ativado

echo.
echo ================================================================================
echo [2/5] Instalando dependências Python...
echo ================================================================================
echo.
echo Instalando pacotes do requirements.txt...
echo Isso pode levar alguns minutos
echo.

pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo [OK] Dependencias Python instaladas

echo.
echo ================================================================================
echo [3/5] Instalando navegador Playwright Chromium...
echo ================================================================================
echo.
echo Baixando e instalando Chromium...
echo Isso pode levar alguns minutos na primeira vez
echo.

playwright install chromium

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] Erro ao instalar Playwright
    echo Voce pode instalar manualmente depois: playwright install chromium
    echo.
) else (
    echo.
    echo [OK] Chromium instalado com sucesso
)

echo.
echo ================================================================================
echo [4/5] Criando estrutura de pastas...
echo ================================================================================

if not exist "automation\canopus\logs" (
    mkdir automation\canopus\logs
    echo [OK] Criado: automation\canopus\logs
)

if not exist "automation\canopus\downloads" (
    mkdir automation\canopus\downloads
    echo [OK] Criado: automation\canopus\downloads
)

if not exist "automation\canopus\excel_files" (
    mkdir automation\canopus\excel_files
    echo [OK] Criado: automation\canopus\excel_files
)

if not exist "automation\canopus\temp" (
    mkdir automation\canopus\temp
    echo [OK] Criado: automation\canopus\temp
)

if not exist "planilhas" (
    mkdir planilhas
    echo [OK] Criado: planilhas pasta raiz
)

if not exist "boletos\canopus" (
    mkdir boletos\canopus
    echo [OK] Criado: boletos\canopus
)

for %%C in (Dayler Neto Mirelli Danner) do (
    if not exist "automation\canopus\downloads\%%C" (
        mkdir automation\canopus\downloads\%%C
        echo [OK] Criado: downloads\%%C
    )
)

echo.
echo [OK] Estrutura de pastas criada

echo.
echo ================================================================================
echo [5/5] Criando tabelas no banco de dados PostgreSQL...
echo ================================================================================
echo.
echo Conectando ao PostgreSQL localhost:5434...
echo.

if not exist "backend\sql\criar_tabelas_automacao.sql" (
    echo [ERRO] Arquivo SQL nao encontrado!
    echo    Esperado: backend\sql\criar_tabelas_automacao.sql
    pause
    exit /b 1
)

set PGPASSWORD=postgres

psql -h localhost -p 5434 -U postgres -d nexus_crm -f backend\sql\criar_tabelas_automacao.sql

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] Erro ao executar SQL
    echo.
    echo Possiveis causas:
    echo   1. PostgreSQL nao esta rodando
    echo   2. Porta 5434 incorreta
    echo   3. Senha incorreta edite setup_canopus.bat linha 146
    echo   4. Banco nexus_crm nao existe
    echo.
    echo Voce pode executar o SQL manualmente:
    echo    psql -h localhost -p 5434 -U postgres -d nexus_crm -f backend\sql\criar_tabelas_automacao.sql
    echo.
) else (
    echo.
    echo [OK] Tabelas criadas com sucesso
)

echo.
echo ================================================================================
echo                           SETUP CONCLUIDO!
echo ================================================================================
echo.
echo [OK] Dependencias Python instaladas
echo [OK] Navegador Playwright configurado
echo [OK] Estrutura de pastas criada
echo [OK] Tabelas do banco de dados criadas
echo.
echo ================================================================================
echo                            PROXIMOS PASSOS
echo ================================================================================
echo.
echo 1. CONFIGURE AS CREDENCIAIS DO CANOPUS
echo    cd automation\canopus
echo    python gerenciar_credenciais.py --adicionar --ponto 17.308 --usuario X --senha Y
echo.
echo 2. COLOQUE AS PLANILHAS EXCEL
echo    Copie as planilhas dos consultores para:
echo       D:\Nexus\planilhas\Dayler.xlsx
echo       D:\Nexus\planilhas\Neto.xlsx
echo       D:\Nexus\planilhas\Mirelli.xlsx
echo       D:\Nexus\planilhas\Danner.xlsx
echo.
echo 3. TESTE A AUTOMACAO
echo    cd automation\canopus
echo    python teste_automacao.py --teste all
echo.
echo 4. INICIE O SISTEMA
echo    iniciar.bat
echo.
echo ================================================================================
echo.
echo Pressione qualquer tecla para sair...
pause
