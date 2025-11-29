/**
 * Detecta o caminho correto do Chromium no Alpine Linux
 */

const fs = require('fs');
const { execSync } = require('child_process');

// Possíveis caminhos do Chromium no Alpine
const possiblePaths = [
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/usr/lib/chromium/chromium',
    '/usr/lib/chromium/chrome'
];

console.log('🔍 Procurando Chromium no Alpine Linux...');

// Tentar encontrar via 'which'
try {
    const whichResult = execSync('which chromium-browser || which chromium', { encoding: 'utf-8' }).trim();
    if (whichResult && fs.existsSync(whichResult)) {
        console.log(`✅ Chromium encontrado via 'which': ${whichResult}`);
        process.exit(0);
    }
} catch (e) {
    console.log('⚠️ Comando which falhou, tentando caminhos conhecidos...');
}

// Tentar caminhos conhecidos
for (const path of possiblePaths) {
    if (fs.existsSync(path)) {
        console.log(`✅ Chromium encontrado: ${path}`);

        // Verificar se tem permissão de execução
        try {
            fs.accessSync(path, fs.constants.X_OK);
            console.log(`✅ Permissão de execução: OK`);
            process.env.PUPPETEER_EXECUTABLE_PATH = path;
            process.exit(0);
        } catch (err) {
            console.log(`⚠️ Sem permissão de execução em: ${path}`);
        }
    }
}

console.log('❌ Chromium não encontrado em nenhum caminho conhecido!');
console.log('Caminhos verificados:', possiblePaths);
process.exit(1);
