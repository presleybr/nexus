@echo off
echo ============================================
echo   LIMPAR SESSAO WPPCONNECT
echo ============================================
echo.
echo Este script vai limpar a sessao do WhatsApp
echo Voce precisara escanear o QR Code novamente
echo.
pause

echo.
echo Limpando sessao...
rmdir /s /q tokens\nexus_session 2>nul
mkdir tokens\nexus_session

echo.
echo ✅ Sessao limpa com sucesso!
echo.
echo Agora você pode:
echo 1. Iniciar o servidor: npm start
echo 2. Acessar: http://localhost:5000/crm/whatsapp
echo 3. Escanear novo QR Code
echo.
pause
