/**
 * WPPConnect Server para Nexus CRM
 * Servidor Express + WhatsApp Web
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const wppconnect = require('@wppconnect-team/wppconnect');
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3001;
const SECRET_KEY = process.env.SECRET_KEY || 'CHANGE_SECRET_KEY';

// Configuração do banco de dados PostgreSQL (OPCIONAL)
let pool = null;

if (process.env.DATABASE_URL) {
  console.log('📊 [DB] DATABASE_URL detectado, conectando ao PostgreSQL...');
  pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.DATABASE_URL.includes('render') || process.env.DATABASE_URL.includes('postgres')
      ? { rejectUnauthorized: false }
      : false
  });

  // Testar conexão
  pool.query('SELECT NOW()', (err, res) => {
    if (err) {
      console.error('❌ [DB] Erro ao conectar ao PostgreSQL:', err.message);
      pool = null; // Desabilitar pool se falhar
    } else {
      console.log('✅ [DB] Conectado ao PostgreSQL:', res.rows[0].now);
    }
  });
} else {
  console.log('⚠️ [DB] DATABASE_URL não configurado - funcionando SEM persistência no banco');
}

// Middlewares
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Estado global
let client = null;
let isConnected = false;
let qrCode = null;
let phoneNumber = null;

// Configurações do WhatsApp otimizadas para Render/Alpine
const clientOptions = {
  session: 'nexus-crm',
  // Callback para capturar QR Code
  catchQR: (base64Qr, asciiQR, attempt, urlCode) => {
    console.log('📱 QR Code gerado via catchQR! Tentativa:', attempt);
    console.log('📱 Base64 length:', base64Qr ? base64Qr.length : 0);
    qrCode = base64Qr;
  },
  // Callback de status da sessão
  statusFind: (statusSession, session) => {
    console.log('========================================');
    console.log('📊 [STATUS-CALLBACK] statusFind CHAMADO!');
    console.log('📊 [STATUS-CALLBACK] statusSession:', statusSession);
    console.log('📊 [STATUS-CALLBACK] session:', session);
    console.log('📊 [STATUS-CALLBACK] Type:', typeof statusSession);
    console.log('========================================');

    if (statusSession === 'isLogged') {
      isConnected = true;
      qrCode = null;
      console.log('✅✅✅ [STATUS-CALLBACK] WhatsApp CONECTADO! isConnected = true');
      saveWhatsAppStatus(true, phoneNumber, null);
    } else if (statusSession === 'notLogged') {
      isConnected = false;
      console.log('⚠️ [STATUS-CALLBACK] WhatsApp desconectado, isConnected = false');
      saveWhatsAppStatus(false, null, null);
    } else if (statusSession === 'qrReadSuccess') {
      console.log('📱 [STATUS-CALLBACK] QR Code lido! Aguardando confirmação...');
      // Iniciar polling para verificar conexão
      setTimeout(() => checkConnectionStatus(), 2000);
    } else if (statusSession === 'qrReadFail') {
      console.log('❌ [STATUS-CALLBACK] Falha ao ler QR Code');
    } else if (statusSession === 'autocloseCalled') {
      console.log('🔄 [STATUS-CALLBACK] AutoClose chamado');
    } else if (statusSession === 'desconnectedMobile') {
      isConnected = false;
      console.log('📱 [STATUS-CALLBACK] Desconectado do celular');
      saveWhatsAppStatus(false, null, null);
    } else if (statusSession === 'browserClose') {
      console.log('🌐 [STATUS-CALLBACK] Browser fechado');
    } else {
      console.log('⚠️ [STATUS-CALLBACK] Status desconhecido:', statusSession);
    }
  },
  headless: true,
  devtools: false,
  useChrome: true,
  logQR: true,  // Mostrar QR no console também
  disableWelcome: true,
  updatesLog: false,
  autoClose: false,  // DESABILITADO - não fechar automaticamente
  // Configurações do Puppeteer para Alpine Linux (Render)
  puppeteerOptions: {
    headless: true,
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || process.env.CHROME_BIN || '/usr/bin/chromium-browser',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--disable-software-rasterizer',
      '--disable-dev-tools',
      '--disable-extensions',
      '--disable-background-timer-throttling',
      '--disable-backgrounding-occluded-windows',
      '--disable-renderer-backgrounding',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process',
      '--window-size=1920,1080',
      '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ],
    defaultViewport: null,
    ignoreHTTPSErrors: true
  }
};

// ============================================================================
// ROTAS
// ============================================================================

// Health check
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    connected: isConnected,
    service: 'Nexus WPPConnect Server'
  });
});

// Iniciar sessão (agora apenas verifica/retorna status)
app.post('/start', async (req, res) => {
  try {
    console.log('📥 [START] Requisição recebida');

    if (client && isConnected) {
      console.log('✅ [START] Já conectado');
      return res.json({
        success: true,
        message: 'WhatsApp já está conectado',
        connected: true,
        phone: phoneNumber
      });
    }

    if (client) {
      console.log('⏳ [START] Cliente inicializado, aguardando QR Code');
      return res.json({
        success: true,
        message: 'Cliente inicializado. Use /qr para obter o QR Code.',
        connected: false,
        initializing: true
      });
    }

    // Se não tem cliente, iniciar agora
    console.log('🚀 [START] Cliente não existe, iniciando...');
    initializeWhatsAppClient();

    res.json({
      success: true,
      message: 'Inicializando cliente WhatsApp... Use /qr para obter o QR Code.',
      connected: false,
      initializing: true
    });

  } catch (error) {
    console.error('❌ [START-ERROR] Erro:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Função para capturar QR Code agressivamente
function startQRCodeCapture() {
  console.log('🎯 [QR-CAPTURE] Iniciando captura agressiva de QR Code...');

  let attempts = 0;
  const maxAttempts = 20; // 20 tentativas = ~60 segundos

  const captureInterval = setInterval(async () => {
    attempts++;
    console.log(`🔄 [QR-CAPTURE] Tentativa ${attempts}/${maxAttempts}...`);

    if (qrCode) {
      console.log('✅ [QR-CAPTURE] QR Code já capturado! Parando...');
      clearInterval(captureInterval);
      return;
    }

    if (isConnected) {
      console.log('✅ [QR-CAPTURE] WhatsApp conectado! Parando...');
      clearInterval(captureInterval);
      return;
    }

    if (!client || !client.page) {
      console.log('⚠️ [QR-CAPTURE] Cliente ou página não disponível ainda');
      return;
    }

    try {
      // Tentar capturar canvas
      console.log('📸 [QR-CAPTURE] Procurando elemento canvas...');
      const qrElement = await client.page.$('canvas');

      if (qrElement) {
        console.log('✅ [QR-CAPTURE] Canvas encontrado! Tirando screenshot...');
        const screenshot = await qrElement.screenshot({ encoding: 'base64' });
        const qrDataUrl = `data:image/png;base64,${screenshot}`;

        console.log('📱 [QR-CAPTURE] QR Code capturado! Length:', qrDataUrl.length);
        console.log('🎉 [QR-CAPTURE] QR Code salvo com sucesso!');

        qrCode = qrDataUrl;
        clearInterval(captureInterval);

        // Tentar exibir QR Code no console (opcional)
        try {
          const qrcode = require('qrcode-terminal');
          console.log('\n📱 QR CODE GERADO:');
          // Aqui você poderia decodificar o QR e exibir, mas é complexo
          console.log('✅ QR Code disponível em /qr\n');
        } catch (e) {
          console.log('✅ QR Code disponível em /qr');
        }
      } else {
        console.log('⚠️ [QR-CAPTURE] Canvas não encontrado na tentativa', attempts);
      }
    } catch (err) {
      console.error(`❌ [QR-CAPTURE] Erro na tentativa ${attempts}:`, err.message);
    }

    if (attempts >= maxAttempts) {
      console.error('❌ [QR-CAPTURE] Máximo de tentativas atingido. Parando...');
      clearInterval(captureInterval);
    }
  }, 3000); // A cada 3 segundos
}

// Obter QR Code (com captura via screenshot se callback falhar)
app.get('/qr', async (req, res) => {
  try {
    console.log('📥 [/qr] Requisição recebida');
    console.log('📊 [/qr] Estado:', { isConnected, hasQR: !!qrCode, hasClient: !!client, hasPage: !!(client && client.page) });

    if (isConnected) {
      console.log('✅ [/qr] Já conectado');
      return res.json({
        success: true,
        connected: true,
        phone: phoneNumber,
        message: 'WhatsApp já está conectado'
      });
    }

    // Se já temos QR Code, retorna
    if (qrCode) {
      console.log('✅ [/qr] Retornando QR Code existente (length:', qrCode.length, ')');
      return res.json({
        success: true,
        qr: qrCode,
        connected: false,
        source: 'cached'
      });
    }

    // FALLBACK: Tentar capturar via screenshot se cliente existe
    if (client && client.page) {
      console.log('🔍 [/qr] Cliente disponível, tentando capturar screenshot...');

      try {
        // Capturar screenshot do QR Code
        console.log('📸 [/qr] Procurando elemento canvas...');
        const qrElement = await client.page.$('canvas');

        if (qrElement) {
          console.log('✅ [/qr] Canvas encontrado! Tirando screenshot...');
          const screenshot = await qrElement.screenshot({ encoding: 'base64' });
          const qrDataUrl = `data:image/png;base64,${screenshot}`;

          console.log('📱 [/qr] QR Code capturado via screenshot! Length:', qrDataUrl.length);

          // Salvar para próximas requisições
          qrCode = qrDataUrl;

          return res.json({
            success: true,
            qr: qrDataUrl,
            connected: false,
            source: 'screenshot'
          });
        } else {
          console.log('⚠️ [/qr] Elemento canvas não encontrado na página');
        }
      } catch (screenshotError) {
        console.error('❌ [/qr] Erro ao capturar screenshot:', screenshotError.message);
      }
    } else {
      console.log('⚠️ [/qr] Cliente não disponível ainda');
    }

    console.log('⏳ [/qr] Aguardando QR Code...');
    res.json({
      success: true,
      connected: false,
      message: 'Aguardando QR Code... Chame /start primeiro.'
    });

  } catch (error) {
    console.error('❌ [/qr] Erro:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Verificar status
app.get('/status', async (req, res) => {
  try {
    console.log('🔍 [/status] Verificando status...');
    console.log('🔍 [/status] isConnected:', isConnected);
    console.log('🔍 [/status] client exists:', !!client);
    console.log('🔍 [/status] phoneNumber:', phoneNumber);

    if (!client) {
      console.log('⚠️ [/status] Cliente não inicializado, consultando banco...');

      // Tentar carregar do banco de dados
      const dbStatus = await getWhatsAppStatus();
      if (dbStatus) {
        console.log('📊 [/status] Status do banco:', {
          connected: dbStatus.is_connected,
          phone: dbStatus.phone_number
        });

        return res.json({
          success: true,
          connected: dbStatus.is_connected,
          phone: dbStatus.phone_number,
          message: 'Status do banco de dados (cliente não inicializado)'
        });
      }

      return res.json({
        success: true,
        connected: false,
        message: 'Cliente não inicializado'
      });
    }

    const connectionState = await client.getConnectionState();
    console.log('🔍 [/status] connectionState:', connectionState);

    // Verificar se está realmente conectado
    try {
      const hostDevice = await client.getHostDevice();
      console.log('📱 [/status] hostDevice obtido:', hostDevice.id.user);
      phoneNumber = hostDevice.id.user;
      isConnected = true;
      qrCode = null; // Limpar QR Code quando conectado

      // Salvar status atualizado no banco
      await saveWhatsAppStatus(true, phoneNumber, null);
    } catch (err) {
      console.log('⚠️ [/status] Não foi possível obter hostDevice:', err.message);
    }

    const finalConnected = isConnected && connectionState === 'CONNECTED';
    console.log('✅ [/status] Retornando connected:', finalConnected);

    res.json({
      success: true,
      connected: finalConnected,
      phone: phoneNumber,
      state: connectionState,
      hasQR: !!qrCode
    });

  } catch (error) {
    console.error('❌ [/status] Erro:', error.message);
    res.json({
      success: false,
      connected: false,
      error: error.message
    });
  }
});

// Enviar mensagem de texto
app.post('/send-text', async (req, res) => {
  try {
    const { phone, message } = req.body;

    if (!phone || !message) {
      return res.status(400).json({
        success: false,
        error: 'Phone e message são obrigatórios'
      });
    }

    if (!client || !isConnected) {
      return res.status(400).json({
        success: false,
        error: 'WhatsApp não está conectado'
      });
    }

    // Formatar número
    const formattedNumber = phone.includes('@c.us') ? phone : `${phone}@c.us`;

    const result = await client.sendText(formattedNumber, message);

    console.log(`✅ Mensagem enviada para ${phone}`);

    res.json({
      success: true,
      messageId: result.id,
      numero: phone
    });

  } catch (error) {
    console.error('❌ Erro ao enviar mensagem:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Enviar arquivo
app.post('/send-file', async (req, res) => {
  try {
    const { phone, filePath, caption } = req.body;

    if (!phone || !filePath) {
      return res.status(400).json({
        success: false,
        error: 'Phone e filePath são obrigatórios'
      });
    }

    if (!client || !isConnected) {
      return res.status(400).json({
        success: false,
        error: 'WhatsApp não está conectado'
      });
    }

    // Formatar número
    const formattedNumber = phone.includes('@c.us') ? phone : `${phone}@c.us`;

    const result = await client.sendFile(
      formattedNumber,
      filePath,
      null,
      caption || ''
    );

    console.log(`✅ Arquivo enviado para ${phone}`);

    res.json({
      success: true,
      messageId: result.id,
      numero: phone
    });

  } catch (error) {
    console.error('❌ Erro ao enviar arquivo:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Desconectar
app.post('/logout', async (req, res) => {
  try {
    console.log('🔒 [LOGOUT] Desconectando WhatsApp...');

    if (client) {
      await client.logout();
      client = null;
    }

    // Atualizar estado
    isConnected = false;
    qrCode = null;
    const oldPhone = phoneNumber;
    phoneNumber = null;

    // Salvar desconexão no banco de dados
    await saveWhatsAppStatus(false, null, null);
    console.log(`🔒 [LOGOUT] WhatsApp desconectado (era: ${oldPhone})`);
    console.log('💾 [LOGOUT] Status atualizado no banco de dados');

    res.json({
      success: true,
      message: 'Desconectado com sucesso'
    });

  } catch (error) {
    console.error('❌ [LOGOUT] Erro ao desconectar:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ============================================================================
// INICIAR SERVIDOR
// ============================================================================

app.listen(PORT, () => {
  console.log('🚀 WPPConnect Server para Nexus CRM');
  console.log(`📡 Servidor rodando na porta: ${PORT}`);
  console.log(`🔑 Secret Key: ${SECRET_KEY !== 'CHANGE_SECRET_KEY' ? 'Configurada ✅' : 'ALTERE! ⚠️'}`);
  console.log('📱 Pronto para conectar WhatsApp!');
  console.log('\nEndpoints disponíveis:');
  console.log('  GET  / - Health check');
  console.log('  POST /start - Iniciar sessão');
  console.log('  GET  /qr - Obter QR Code');
  console.log('  GET  /status - Status da conexão');
  console.log('  POST /send-text - Enviar mensagem');
  console.log('  POST /send-file - Enviar arquivo');
  console.log('  POST /logout - Desconectar');

  // INICIAR CLIENTE AUTOMATICAMENTE AO SUBIR O SERVIDOR
  console.log('\n🔄 [AUTO-START] Iniciando cliente WhatsApp automaticamente...');
  console.log('🔧 [AUTO-START] Opções:', {
    session: clientOptions.session,
    headless: clientOptions.headless,
    logQR: clientOptions.logQR,
    autoClose: clientOptions.autoClose
  });

  // Limpar lock files antes de iniciar
  cleanChromiumLocks();

  initializeWhatsAppClient();
});

/**
 * Limpa lock files do Chromium para evitar erros de "browser já rodando"
 */
function cleanChromiumLocks() {
  const tokensDir = path.join(process.cwd(), 'tokens', 'nexus-crm');

  if (!fs.existsSync(tokensDir)) {
    console.log('⚠️ [CLEANUP] Pasta tokens não existe ainda');
    return;
  }

  console.log('🧹 [CLEANUP] Limpando lock files do Chromium...');

  const lockFiles = [
    'SingletonLock',
    'SingletonSocket',
    'SingletonCookie',
    '.com.google.Chrome.SingletonSocket'
  ];

  lockFiles.forEach(lockFile => {
    const lockPath = path.join(tokensDir, lockFile);
    if (fs.existsSync(lockPath)) {
      try {
        fs.unlinkSync(lockPath);
        console.log(`✅ [CLEANUP] Removido: ${lockFile}`);
      } catch (err) {
        console.log(`⚠️ [CLEANUP] Erro ao remover ${lockFile}:`, err.message);
      }
    }
  });

  console.log('✅ [CLEANUP] Limpeza concluída');
}

/**
 * Salva o status do WhatsApp no banco de dados
 */
async function saveWhatsAppStatus(connected, phone = null, qr = null) {
  if (!pool) {
    console.log('⚠️ [DB] Pool de conexão não disponível');
    return;
  }

  try {
    console.log(`💾 [DB] Salvando status: connected=${connected}, phone=${phone ? phone.substring(0, 5) + '...' : null}`);

    const query = `
      INSERT INTO whatsapp_status (session_name, is_connected, phone_number, qr_code, last_connected_at, last_disconnected_at, updated_at)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
      ON CONFLICT (session_name)
      DO UPDATE SET
        is_connected = $2,
        phone_number = $3,
        qr_code = $4,
        last_connected_at = CASE WHEN $2 = TRUE THEN NOW() ELSE whatsapp_status.last_connected_at END,
        last_disconnected_at = CASE WHEN $2 = FALSE THEN NOW() ELSE whatsapp_status.last_disconnected_at END,
        updated_at = NOW()
    `;

    await pool.query(query, [
      'nexus-crm',
      connected,
      phone,
      qr,
      connected ? new Date() : null,
      !connected ? new Date() : null
    ]);

    console.log('✅ [DB] Status salvo no banco');
  } catch (err) {
    console.error('❌ [DB] Erro ao salvar status:', err.message);
  }
}

/**
 * Recupera o status do WhatsApp do banco de dados
 */
async function getWhatsAppStatus() {
  if (!pool) {
    console.log('⚠️ [DB] Pool de conexão não disponível');
    return null;
  }

  try {
    const result = await pool.query(
      'SELECT * FROM whatsapp_status WHERE session_name = $1',
      ['nexus-crm']
    );

    if (result.rows.length > 0) {
      return result.rows[0];
    }

    return null;
  } catch (err) {
    console.error('❌ [DB] Erro ao recuperar status:', err.message);
    return null;
  }
}

/**
 * Verifica periodicamente se a conexão foi estabelecida
 */
function checkConnectionStatus() {
  console.log('🔄 [CHECK-CONN] Verificando conexão...');

  if (!client) {
    console.log('⚠️ [CHECK-CONN] Cliente não disponível');
    return;
  }

  let attempts = 0;
  const maxAttempts = 10;

  const checkInterval = setInterval(async () => {
    attempts++;
    console.log(`🔄 [CHECK-CONN] Tentativa ${attempts}/${maxAttempts}`);

    try {
      const connectionState = await client.getConnectionState();
      console.log(`🔍 [CHECK-CONN] connectionState: ${connectionState}`);

      if (connectionState === 'CONNECTED') {
        console.log('✅✅✅ [CHECK-CONN] CONECTADO DETECTADO!');
        clearInterval(checkInterval);

        try {
          const hostDevice = await client.getHostDevice();
          phoneNumber = hostDevice.id.user;
          isConnected = true;
          qrCode = null;
          console.log(`📱 [CHECK-CONN] Número: ${phoneNumber}`);
          console.log('✅ [CHECK-CONN] isConnected = true, qrCode = null');

          // Salvar status no banco de dados
          await saveWhatsAppStatus(true, phoneNumber, null);
        } catch (err) {
          console.error('❌ [CHECK-CONN] Erro ao obter hostDevice:', err.message);
        }
      } else if (attempts >= maxAttempts) {
        console.log('⏱️ [CHECK-CONN] Timeout - max tentativas atingido');
        clearInterval(checkInterval);
      }
    } catch (err) {
      console.error(`❌ [CHECK-CONN] Erro:`, err.message);
    }
  }, 2000); // Verificar a cada 2 segundos
}

// Função para inicializar cliente WhatsApp
async function initializeWhatsAppClient() {
  console.log('🚀 [INIT] Criando cliente WhatsApp...');

  // Verificar se há sessão salva no banco de dados
  const statusDB = await getWhatsAppStatus();
  if (statusDB && statusDB.is_connected) {
    console.log('📊 [INIT] Sessão conectada encontrada no banco!');
    console.log(`📱 [INIT] Número salvo: ${statusDB.phone_number}`);
    phoneNumber = statusDB.phone_number;
    isConnected = true;
  } else {
    console.log('🔄 [INIT] Nenhuma sessão conectada no banco, iniciando nova...');
    if (!client) {
      isConnected = false;
      qrCode = null;
      phoneNumber = null;
    }
  }

  // Limpar lock files antes de tentar criar cliente
  cleanChromiumLocks();

  wppconnect.create(clientOptions)
    .then(createdClient => {
      console.log('✅ [INIT-THEN] wppconnect.create() RESOLVIDO!');
      console.log('📦 [INIT-THEN] Cliente criado com sucesso!');
      console.log('🔍 [INIT-THEN] Cliente tem página?', !!createdClient.page);

      client = createdClient;

      // Adicionar listeners de eventos
      console.log('📡 [INIT] Registrando event listeners...');

      // Listener para mudanças de estado
      if (client.onStateChange) {
        client.onStateChange((state) => {
          console.log('🔔 [EVENT] onStateChange:', state);
          if (state === 'CONNECTED') {
            isConnected = true;
            qrCode = null;
            console.log('✅ [EVENT] Conectado via onStateChange!');
          }
        });
      }

      // Listener para quando autenticado
      if (client.onAuthenticated) {
        client.onAuthenticated(() => {
          console.log('🔔 [EVENT] onAuthenticated disparado!');
          isConnected = true;
          qrCode = null;
          checkConnectionStatus();
        });
      }

      // Iniciar captura agressiva de QR Code
      console.log('🎯 [INIT] Iniciando captura de QR Code...');
      startQRCodeCapture();

      // Tentar obter informações (se já conectado)
      client.getHostDevice()
        .then(hostDevice => {
          phoneNumber = hostDevice.id.user;
          isConnected = true;
          qrCode = null;
          console.log(`📱 [INIT] Conectado como: ${phoneNumber}`);
          console.log('💾 [INIT] Salvando status no banco...');
          saveWhatsAppStatus(true, phoneNumber, null);
        })
        .catch(err => {
          console.log('ℹ️ [INIT] Aguardando conexão via QR Code...');
        });

      // Polling ativo para detectar conexão
      console.log('🔄 [INIT] Iniciando polling para detectar conexão...');
      const pollInterval = setInterval(async () => {
        if (!client) {
          console.log('⚠️ [POLL] Cliente não existe mais, parando polling');
          clearInterval(pollInterval);
          return;
        }

        try {
          const state = await client.getConnectionState();

          // Só logar se houver mudança de estado
          if (state === 'CONNECTED' && !isConnected) {
            console.log('🎉🎉🎉 [POLL] CONEXÃO DETECTADA!');
            const hostDevice = await client.getHostDevice();
            phoneNumber = hostDevice.id.user;
            isConnected = true;
            qrCode = null;
            console.log(`📱 [POLL] Número conectado: ${phoneNumber}`);
            await saveWhatsAppStatus(true, phoneNumber, null);
          }

          // Se estiver conectado, parar polling
          if (state === 'CONNECTED') {
            clearInterval(pollInterval);
            console.log('✅ [POLL] Conexão estável, polling finalizado');
          }
        } catch (err) {
          // Ainda não conectou, continuar polling silenciosamente
        }
      }, 3000); // Verificar a cada 3 segundos
    })
    .catch(error => {
      console.error('❌ [INIT-CATCH] ERRO ao criar cliente:', error.message);
      console.error('📋 [INIT-CATCH] Stack:', error.stack);
      client = null;

      // Tentar novamente em 10 segundos
      console.log('⏳ [INIT] Tentando novamente em 10 segundos...');
      setTimeout(() => {
        initializeWhatsAppClient();
      }, 10000);
    });
}

// Tratamento de erros
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled Rejection:', error);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error);
});

process.on('SIGTERM', async () => {
  console.log('🔄 SIGTERM recebido. Encerrando...');
  if (client) {
    await client.close();
  }
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('🔄 SIGINT recebido. Encerrando...');
  if (client) {
    await client.close();
  }
  process.exit(0);
});
