@echo off
echo ============================================
echo   Limpando Sessoes WhatsApp Baileys
echo ============================================
echo.
echo Este script vai limpar todas as sessoes antigas
echo para permitir uma nova conexao com QR Code.
echo.
pause

cd /d "%~dp0"

if exist "sessions" (
    echo Removendo pasta sessions...
    rmdir /s /q sessions
    echo Pasta sessions removida!
) else (
    echo Pasta sessions nao existe.
)

echo.
echo ============================================
echo   Sessoes limpas com sucesso!
echo ============================================
echo.
echo Proximos passos:
echo 1. Execute: npm start
echo 2. Acesse: http://localhost:5000/crm/whatsapp
echo 3. Clique em "Conectar WhatsApp"
echo 4. Escaneie o QR Code
echo.
pause
