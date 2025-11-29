/**
 * WPPConnect Server para Nexus CRM
 * Servidor Express + WhatsApp Web
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const wppconnect = require('@wppconnect-team/wppconnect');

const app = express();
const PORT = process.env.PORT || 3001;
const SECRET_KEY = process.env.SECRET_KEY || 'CHANGE_SECRET_KEY';

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
    console.log('📊 Status da sessão:', statusSession, session);

    if (statusSession === 'isLogged') {
      isConnected = true;
      qrCode = null;
      console.log('✅ WhatsApp conectado!');
    } else if (statusSession === 'notLogged') {
      isConnected = false;
      console.log('⚠️ WhatsApp desconectado');
    } else if (statusSession === 'qrReadSuccess') {
      console.log('📱 QR Code lido com sucesso! Aguardando confirmação...');
    } else if (statusSession === 'qrReadFail') {
      console.log('❌ Falha ao ler QR Code');
    }
  },
  headless: true,
  devtools: false,
  useChrome: true,
  logQR: true,  // Mostrar QR no console também
  disableWelcome: true,
  updatesLog: false,
  autoClose: 120000,  // 2 minutos ao invés de 1
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

// Iniciar sessão (modo assíncrono - não bloqueia)
app.post('/start', async (req, res) => {
  try {
    if (client && isConnected) {
      return res.json({
        success: true,
        message: 'WhatsApp já está conectado',
        connected: true
      });
    }

    if (client) {
      return res.json({
        success: true,
        message: 'Sessão já está sendo iniciada. Use /qr para obter o QR Code.',
        connected: false,
        initializing: true
      });
    }

    console.log('🚀 Iniciando cliente WhatsApp de forma assíncrona...');

    // Responde IMEDIATAMENTE (não aguarda o Chromium iniciar)
    res.json({
      success: true,
      message: 'Iniciando sessão... Use /qr para obter o QR Code.',
      connected: false,
      initializing: true
    });

    // Inicializa em background (não bloqueia a resposta)
    wppconnect.create(clientOptions)
      .then(createdClient => {
        client = createdClient;
        console.log('✅ Cliente WhatsApp criado com sucesso!');

        // Adicionar listener para QR Code (fallback)
        if (client.onStateChange) {
          client.onStateChange(state => {
            console.log('🔄 Estado mudou:', state);
          });
        }

        // Verificar se há método alternativo para QR Code
        console.log('🔍 Métodos disponíveis no cliente:', Object.keys(client).filter(k => k.toLowerCase().includes('qr')));

        // Obter informações do número (se já conectado)
        client.getHostDevice()
          .then(hostDevice => {
            phoneNumber = hostDevice.id.user;
            console.log(`📱 Conectado como: ${phoneNumber}`);
          })
          .catch(err => {
            console.log('ℹ️ Aguardando conexão via QR Code...');
          });
      })
      .catch(error => {
        console.error('❌ Erro ao iniciar cliente WhatsApp:', error);
        console.error('Stack:', error.stack);
        client = null;
      });

  } catch (error) {
    console.error('❌ Erro ao processar requisição /start:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Obter QR Code
app.get('/qr', async (req, res) => {
  try {
    if (isConnected) {
      return res.json({
        success: true,
        connected: true,
        phone: phoneNumber,
        message: 'WhatsApp já está conectado'
      });
    }

    if (qrCode) {
      return res.json({
        success: true,
        qr: qrCode,
        connected: false
      });
    }

    res.json({
      success: true,
      connected: false,
      message: 'Aguardando QR Code... Chame /start primeiro.'
    });

  } catch (error) {
    console.error('❌ Erro ao obter QR Code:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Verificar status
app.get('/status', async (req, res) => {
  try {
    if (!client) {
      return res.json({
        success: true,
        connected: false,
        message: 'Cliente não inicializado'
      });
    }

    const connectionState = await client.getConnectionState();

    res.json({
      success: true,
      connected: isConnected && connectionState === 'CONNECTED',
      phone: phoneNumber,
      state: connectionState
    });

  } catch (error) {
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
    if (client) {
      await client.logout();
      client = null;
      isConnected = false;
      qrCode = null;
      phoneNumber = null;

      console.log('🔒 WhatsApp desconectado');
    }

    res.json({
      success: true,
      message: 'Desconectado com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao desconectar:', error);
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
});

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
