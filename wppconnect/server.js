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
    console.log('📥 [START] Requisição recebida');

    if (client && isConnected) {
      console.log('✅ [START] Já conectado');
      return res.json({
        success: true,
        message: 'WhatsApp já está conectado',
        connected: true
      });
    }

    if (client) {
      console.log('⏳ [START] Cliente já está inicializando');
      return res.json({
        success: true,
        message: 'Sessão já está sendo iniciada. Use /qr para obter o QR Code.',
        connected: false,
        initializing: true
      });
    }

    console.log('🚀 [START] Iniciando cliente WhatsApp de forma assíncrona...');
    console.log('🔧 [START] Opções do cliente:', {
      session: clientOptions.session,
      headless: clientOptions.headless,
      logQR: clientOptions.logQR,
      autoClose: clientOptions.autoClose
    });

    // Responde IMEDIATAMENTE (não aguarda o Chromium iniciar)
    res.json({
      success: true,
      message: 'Iniciando sessão... Use /qr para obter o QR Code.',
      connected: false,
      initializing: true
    });

    // Inicializa em background (não bloqueia a resposta)
    console.log('🔄 [START] Chamando wppconnect.create()...');

    wppconnect.create(clientOptions)
      .then(createdClient => {
        console.log('✅ [THEN] wppconnect.create() resolvido!');
        console.log('📦 [THEN] Tipo do cliente:', typeof createdClient);
        console.log('🔍 [THEN] Cliente tem página?', !!createdClient.page);

        client = createdClient;
        console.log('✅ Cliente WhatsApp criado com sucesso!');

        // Iniciar captura agressiva de QR Code
        startQRCodeCapture();

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
        console.error('❌ [CATCH] Erro ao iniciar cliente WhatsApp:', error);
        console.error('📋 [CATCH] Stack:', error.stack);
        client = null;
      });

  } catch (error) {
    console.error('❌ [ERROR] Erro ao processar requisição /start:', error);
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
