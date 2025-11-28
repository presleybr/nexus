@echo off
chcp 65001 >nul
title NEXUS CRM - Menu Principal
color 0A

:inicio
cls
echo ================================================================================
echo                          NEXUS CRM - MENU PRINCIPAL
echo                          Aqui seu tempo vale ouro
echo ================================================================================
echo.
echo Selecione uma opção:
echo.
echo [1] Iniciar Sistema Completo Backend + WhatsApp
echo [2] Iniciar Apenas Backend Flask
echo [3] Iniciar Apenas WhatsApp WPPConnect
echo [4] Menu Automação Canopus
echo [5] Verificar Dependências
echo [6] Configurar Automação Canopus Setup
echo [7] Sair
echo.
set /p opcao="Digite a opção: "

if "%opcao%"=="1" goto :sistema_completo
if "%opcao%"=="2" goto :apenas_backend
if "%opcao%"=="3" goto :apenas_whatsapp
if "%opcao%"=="4" goto :menu_automacao
if "%opcao%"=="5" goto :verificar_deps
if "%opcao%"=="6" goto :setup_canopus
if "%opcao%"=="7" exit

echo.
echo [ERRO] Opcao invalida!
timeout /t 2 >nul
goto :inicio

:sistema_completo
cls
echo ================================================================================
echo                      INICIANDO SISTEMA COMPLETO
echo ================================================================================
echo.
echo Iniciando Backend + WhatsApp...
call iniciar.bat
goto :fim

:apenas_backend
cls
echo ================================================================================
echo                      INICIANDO APENAS BACKEND
echo ================================================================================
echo.
call venv\Scripts\activate
python start.py
goto :fim

:apenas_whatsapp
cls
echo ================================================================================
echo                      INICIANDO APENAS WHATSAPP
echo ================================================================================
echo.
if not exist "wppconnect-server\node_modules" (
    echo [ERRO] WPPConnect nao instalado!
    echo.
    echo Execute primeiro:
    echo    cd wppconnect-server
    echo    npm install
    pause
    goto :inicio
)
cd wppconnect-server
npm start
cd ..
goto :fim

:menu_automacao
cls
echo ================================================================================
echo                      AUTOMAÇÃO CANOPUS - MENU
echo ================================================================================
echo.
echo [1] Importar Planilhas Excel
echo [2] Sincronizar Clientes Staging para CRM
echo [3] Baixar Boletos do Canopus
echo [4] Importar Boletos Baixados para CRM
echo [5] Fluxo Completo 1+2+3+4
echo [6] Testar Conexão Banco de Dados
echo [7] Testar Importação Excel
echo [8] Testar Login Canopus MAPEAR SELETORES
echo [9] Ver Status Execuções
echo [0] Voltar
echo.
set /p opcao_auto="Digite a opção: "

call venv\Scripts\activate
cd automation\canopus

if "%opcao_auto%"=="1" (
    echo.
    echo [*] Importando planilhas...
    python orquestrador.py importar --diretorio ..\..\planilhas
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="2" (
    echo.
    echo [*] Sincronizando clientes...
    python orquestrador.py sincronizar
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="3" (
    echo.
    set /p consultor="Digite o nome do consultor Dayler, Neto, etc: "
    set /p mes="Digite o mes DEZEMBRO, JANEIRO, etc: "
    echo.
    echo [*] Baixando boletos...
    python orquestrador.py download --consultor !consultor! --mes !mes!
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="4" (
    echo.
    echo [*] Importando boletos para CRM...
    python orquestrador.py importar-crm
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="5" (
    echo.
    set /p consultor="Digite o nome do consultor ou deixe vazio para todos: "
    set /p mes="Digite o mes DEZEMBRO, JANEIRO, etc: "
    echo.
    echo [*] Executando fluxo completo...
    python orquestrador.py completo --consultor !consultor! --mes !mes!
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="6" (
    echo.
    echo [*] Testando conexao com banco...
    python teste_automacao.py --teste conexao
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="7" (
    echo.
    echo Planilhas disponiveis em D:\Nexus\planilhas\
    dir ..\..\planilhas\*.xlsx /b
    echo.
    set /p planilha="Digite o nome da planilha ex: Dayler.xlsx: "
    echo.
    echo [*] Testando importacao...
    python teste_automacao.py --teste excel --arquivo ..\..\planilhas\!planilha!
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="8" (
    echo.
    echo [AVISO] Este teste VAI FALHAR - e para MAPEAR os seletores CSS!
    echo.
    set /p usuario="Digite o usuario do Canopus: "
    set /p senha="Digite a senha: "
    set /p ponto="Digite o ponto de venda padrao 17.308: "
    echo.
    echo [*] Testando login abrira navegador visivel...
    python teste_automacao.py --teste login --usuario !usuario! --senha !senha! --ponto-venda !ponto!
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="9" (
    echo.
    echo [*] Status das execucoes...
    python orquestrador.py status
    echo.
    pause
    cd ..\..
    goto :menu_automacao
)

if "%opcao_auto%"=="0" (
    cd ..\..
    goto :inicio
)

echo.
echo [ERRO] Opcao invalida!
timeout /t 2 >nul
cd ..\..
goto :menu_automacao

:verificar_deps
cls
echo ================================================================================
echo                      VERIFICANDO DEPENDÊNCIAS
echo ================================================================================
echo.
call venv\Scripts\activate
python verificar_dependencias.py
echo.
pause
goto :inicio

:setup_canopus
cls
echo ================================================================================
echo                      SETUP AUTOMAÇÃO CANOPUS
echo ================================================================================
echo.
call setup_canopus.bat
goto :inicio

:fim
echo.
echo ================================================================================
echo Pressione qualquer tecla para voltar ao menu ou feche esta janela
echo ================================================================================
pause >nul
goto :inicio
