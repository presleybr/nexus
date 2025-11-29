/**
 * WPPConnect Server para Nexus CRM
 * Servidor WhatsApp Web integrado ao Nexus CRM
 */

const wppconnect = require('@wppconnect-team/wppconnect-server');

// Configuração do servidor
const serverOptions = {
  // Chave secreta para autenticação
  secretKey: process.env.SECRET_KEY || 'CHANGE_HERE_YOUR_SECRET_KEY',

  // Host e porta
  host: process.env.HOST || 'http://localhost',
  port: parseInt(process.env.PORT) || 3001,

  // Configurações do WhatsApp
  deviceName: 'Nexus CRM',
  poweredBy: 'Nexus CRM - Sistema de Gestão',

  // Iniciar todas as sessões ao startar
  startAllSession: true,

  // Tipo de armazenamento de tokens
  tokenStoreType: 'file',

  // Configurações de sessão
  maxListeners: 15,

  // Webhook (opcional - para receber eventos)
  webhook: {
    url: process.env.WEBHOOK_URL || null,
    autoDownload: true,
    uploadS3: false
  },

  // Configurações de log
  log: {
    level: 'info',
    logger: ['console']
  },

  // Configurações do navegador
  createOptions: {
    browserArgs: [
      '--disable-web-security',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu'
    ]
  }
};

// Iniciar servidor
console.log('🚀 Iniciando WPPConnect Server para Nexus CRM...');
console.log(`📡 Porta: ${serverOptions.port}`);
console.log(`🔑 Secret Key configurada: ${serverOptions.secretKey !== 'CHANGE_HERE_YOUR_SECRET_KEY' ? 'SIM' : 'NÃO (ALTERE!)'}`);

wppconnect.create(serverOptions)
  .then((server) => {
    console.log('✅ WPPConnect Server iniciado com sucesso!');
    console.log(`🌐 Servidor rodando em: ${serverOptions.host}:${serverOptions.port}`);
    console.log('📱 Pronto para conectar WhatsApp!');
  })
  .catch((error) => {
    console.error('❌ Erro ao iniciar WPPConnect Server:', error);
    process.exit(1);
  });

// Tratamento de erros não capturados
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🔄 SIGTERM recebido. Encerrando servidor...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🔄 SIGINT recebido. Encerrando servidor...');
  process.exit(0);
});
