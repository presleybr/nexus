/**
 * Script para instalar Chrome/Chromium no Render
 * Executado automaticamente após npm install (postinstall)
 */

const { execSync } = require('child_process');

console.log('📦 Instalando Chrome/Chromium para WPPConnect...');

try {
  // Instalar Chrome via Puppeteer
  execSync('npx puppeteer browsers install chrome', {
    stdio: 'inherit',
    env: {
      ...process.env,
      PUPPETEER_CACHE_DIR: process.env.PUPPETEER_CACHE_DIR || '/opt/render/.cache/puppeteer'
    }
  });

  console.log('✅ Chrome instalado com sucesso!');
} catch (error) {
  console.error('❌ Erro ao instalar Chrome:', error.message);
  console.log('⚠️ Tentando continuar mesmo assim...');
  // Não falhar o build se der erro
  process.exit(0);
}
