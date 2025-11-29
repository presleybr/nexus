/**
 * WhatsApp Server com Evolution API para Nexus CRM
 * Proxy/Gateway entre Nexus e Evolution API
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const axios = require('axios');
const { Pool } = require('pg');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3001;

// Configurações da Evolution API
const EVOLUTION_API_URL = process.env.EVOLUTION_API_URL || 'http://localhost:8080';
const EVOLUTION_API_KEY = process.env.EVOLUTION_API_KEY || 'CHANGE_API_KEY';
const EVOLUTION_INSTANCE_NAME = process.env.EVOLUTION_INSTANCE_NAME || 'nexus-crm';

console.log('🔧 [CONFIG] Evolution API URL:', EVOLUTION_API_URL);
console.log('🔧 [CONFIG] Instance Name:', EVOLUTION_INSTANCE_NAME);
console.log('🔧 [CONFIG] API Key:', EVOLUTION_API_KEY !== 'CHANGE_API_KEY' ? '✅ Configurado' : '❌ NÃO CONFIGURADO');

// Configuração do banco de dados PostgreSQL
let pool = null;
let dbConnectionRetries = 0;
const MAX_DB_RETRIES = 5;

/**
 * Axios instance para Evolution API
 */
const evolutionAPI = axios.create({
  baseURL: EVOLUTION_API_URL,
  headers: {
    'apikey': EVOLUTION_API_KEY,
    'Content-Type': 'application/json'
  },
  timeout: 30000
});

// Middlewares
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Estado global (cache)
let connectionStatus = {
  connected: false,
  phoneNumber: null,
  instanceName: EVOLUTION_INSTANCE_NAME,
  lastCheck: null
};

// ============================================================================
// FUNÇÕES DE BANCO DE DADOS
// ============================================================================

async function initializeDatabasePool() {
  if (!process.env.DATABASE_URL) {
    console.log('⚠️ [DB] DATABASE_URL não configurado');
    return;
  }

  try {
    console.log('📊 [DB] Conectando ao PostgreSQL...');

    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_URL.includes('render') || process.env.DATABASE_URL.includes('postgres')
        ? { rejectUnauthorized: false }
        : false,
      connectionTimeoutMillis: 10000,
      idleTimeoutMillis: 30000,
      max: 10,
      min: 2,
      keepAlive: true,
      keepAliveInitialDelayMillis: 10000
    });

    const result = await pool.query('SELECT NOW()');
    console.log('✅ [DB] Conectado:', result.rows[0].now);

    await criarTabelaWhatsAppSessions();

    pool.on('error', (err) => {
      console.error('❌ [DB] Erro:', err.message);
      setTimeout(() => {
        pool = null;
        initializeDatabasePool();
      }, 5000);
    });

  } catch (err) {
    console.error('❌ [DB] Erro:', err.message);
    dbConnectionRetries++;

    if (dbConnectionRetries < MAX_DB_RETRIES) {
      setTimeout(() => initializeDatabasePool(), 5000 * dbConnectionRetries);
    }
  }
}

async function criarTabelaWhatsAppSessions() {
  if (!pool) return;

  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS whatsapp_sessions (
        id SERIAL PRIMARY KEY,
        cliente_nexus_id INTEGER,
        instance_name VARCHAR(100) UNIQUE,
        phone_number VARCHAR(20),
        status VARCHAR(50) DEFAULT 'disconnected',
        qr_code TEXT,
        session_data JSONB,
        connected_at TIMESTAMP,
        disconnected_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    const result = await pool.query('SELECT id FROM whatsapp_sessions WHERE instance_name = $1', [EVOLUTION_INSTANCE_NAME]);

    if (result.rows.length === 0) {
      await pool.query('INSERT INTO whatsapp_sessions (instance_name, status) VALUES ($1, $2)', [EVOLUTION_INSTANCE_NAME, 'disconnected']);
    }
  } catch (err) {
    console.error('❌ [DB] Erro ao criar tabela:', err.message);
  }
}

async function saveWhatsAppStatus(connected, phone = null, qr = null) {
  if (!pool) return;

  try {
    const status = connected ? 'connected' : (qr ? 'qrcode' : 'disconnected');

    await pool.query(`
      INSERT INTO whatsapp_sessions (instance_name, phone_number, status, qr_code, connected_at, disconnected_at, updated_at)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
      ON CONFLICT (instance_name)
      DO UPDATE SET
        phone_number = $2,
        status = $3,
        qr_code = $4,
        connected_at = CASE WHEN $3 = 'connected' THEN NOW() ELSE whatsapp_sessions.connected_at END,
        disconnected_at = CASE WHEN $3 = 'disconnected' THEN NOW() ELSE whatsapp_sessions.disconnected_at END,
        updated_at = NOW()
    `, [EVOLUTION_INSTANCE_NAME, phone, status, qr, connected ? new Date() : null, !connected ? new Date() : null]);

    console.log('💾 [DB] Status salvo:', status);
  } catch (err) {
    console.error('❌ [DB] Erro ao salvar:', err.message);
  }
}

async function getWhatsAppStatus() {
  if (!pool) return null;

  try {
    const result = await pool.query('SELECT * FROM whatsapp_sessions WHERE instance_name = $1', [EVOLUTION_INSTANCE_NAME]);
    return result.rows.length > 0 ? result.rows[0] : null;
  } catch (err) {
    return null;
  }
}

// ============================================================================
// FUNÇÕES DA EVOLUTION API
// ============================================================================

async function createInstance() {
  try {
    const response = await evolutionAPI.post('/instance/create', {
      instanceName: EVOLUTION_INSTANCE_NAME,
      qrcode: true,
      integration: 'WHATSAPP-BAILEYS'
    });

    console.log('✅ [EVOLUTION] Instância criada');
    return response.data;
  } catch (error) {
    if (error.response?.status === 409) {
      console.log('ℹ️ [EVOLUTION] Instância já existe');
      return { message: 'Instance already exists' };
    }
    throw error;
  }
}

async function getConnectionState() {
  try {
    const response = await evolutionAPI.get(`/instance/connectionState/${EVOLUTION_INSTANCE_NAME}`);
    return response.data;
  } catch (error) {
    return null;
  }
}

async function connectInstance() {
  try {
    const response = await evolutionAPI.get(`/instance/connect/${EVOLUTION_INSTANCE_NAME}`);
    return response.data;
  } catch (error) {
    throw error;
  }
}

async function logoutInstance() {
  try {
    const response = await evolutionAPI.delete(`/instance/logout/${EVOLUTION_INSTANCE_NAME}`);
    return response.data;
  } catch (error) {
    throw error;
  }
}

// ============================================================================
// ROTAS
// ============================================================================

app.get('/', async (req, res) => {
  const state = await getConnectionState();
  res.json({
    status: 'running',
    service: 'Nexus WhatsApp Server (Evolution API)',
    connected: state?.instance?.state === 'open',
    evolutionAPI: EVOLUTION_API_URL
  });
});

app.post('/start', async (req, res) => {
  try {
    const state = await getConnectionState();

    if (state?.instance?.state === 'open') {
      return res.json({
        success: true,
        message: 'WhatsApp já conectado',
        connected: true
      });
    }

    await createInstance();
    const connectData = await connectInstance();

    res.json({
      success: true,
      message: 'Use /qr para obter QR Code',
      connected: false,
      qrcode: connectData.qrcode?.code || null
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.response?.data?.message || error.message
    });
  }
});

app.get('/qr', async (req, res) => {
  try {
    const state = await getConnectionState();

    if (state?.instance?.state === 'open') {
      return res.json({
        success: true,
        connected: true,
        message: 'WhatsApp já conectado'
      });
    }

    const connectData = await connectInstance();
    const qrCode = connectData.qrcode?.code;

    if (qrCode) {
      await saveWhatsAppStatus(false, null, qrCode);
      return res.json({
        success: true,
        qr: qrCode,
        connected: false
      });
    }

    res.json({
      success: true,
      connected: false,
      message: 'Aguardando QR Code...'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/status', async (req, res) => {
  try {
    const state = await getConnectionState();

    if (!state) {
      const dbStatus = await getWhatsAppStatus();
      return res.json({
        success: true,
        connected: false,
        phone: dbStatus?.phone_number || null
      });
    }

    const isConnected = state.instance?.state === 'open';

    if (isConnected) {
      connectionStatus.connected = true;
      connectionStatus.phoneNumber = state.instance?.owner;
      await saveWhatsAppStatus(true, connectionStatus.phoneNumber, null);
    }

    res.json({
      success: true,
      connected: isConnected,
      phone: connectionStatus.phoneNumber,
      state: state.instance?.state
    });
  } catch (error) {
    res.json({
      success: false,
      connected: false,
      error: error.message
    });
  }
});

app.post('/send-text', async (req, res) => {
  try {
    const { phone, message } = req.body;

    if (!phone || !message) {
      return res.status(400).json({
        success: false,
        error: 'Phone e message obrigatórios'
      });
    }

    const formattedNumber = phone.replace(/\D/g, '');

    const response = await evolutionAPI.post(`/message/sendText/${EVOLUTION_INSTANCE_NAME}`, {
      number: formattedNumber,
      text: message
    });

    res.json({
      success: true,
      messageId: response.data.key?.id,
      numero: phone
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/send-file', async (req, res) => {
  try {
    const { phone, filePath, caption, filename } = req.body;

    if (!phone || !filePath) {
      return res.status(400).json({
        success: false,
        error: 'Phone e filePath obrigatórios'
      });
    }

    const formattedNumber = phone.replace(/\D/g, '');
    let mediaBase64;
    let finalFilename = filename || path.basename(filePath);

    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
      mediaBase64 = filePath;
    } else {
      if (!fs.existsSync(filePath)) {
        return res.status(404).json({
          success: false,
          error: `Arquivo não encontrado: ${filePath}`
        });
      }
      const fileBuffer = fs.readFileSync(filePath);
      mediaBase64 = fileBuffer.toString('base64');
    }

    const response = await evolutionAPI.post(`/message/sendMedia/${EVOLUTION_INSTANCE_NAME}`, {
      number: formattedNumber,
      mediatype: 'document',
      media: mediaBase64,
      fileName: finalFilename,
      caption: caption || ''
    });

    res.json({
      success: true,
      messageId: response.data.key?.id,
      numero: phone,
      arquivo: finalFilename
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/logout', async (req, res) => {
  try {
    await logoutInstance();
    connectionStatus.connected = false;
    connectionStatus.phoneNumber = null;
    await saveWhatsAppStatus(false, null, null);

    res.json({
      success: true,
      message: 'Desconectado'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/webhook/whatsapp', async (req, res) => {
  try {
    const { event, data } = req.body;

    if (event === 'connection.update') {
      if (data.state === 'open') {
        connectionStatus.connected = true;
        connectionStatus.phoneNumber = data.jid?.split('@')[0];
        await saveWhatsAppStatus(true, connectionStatus.phoneNumber, null);
      } else if (data.state === 'close') {
        connectionStatus.connected = false;
        await saveWhatsAppStatus(false, null, null);
      }
    }

    res.json({ received: true });
  } catch (error) {
    res.json({ received: false });
  }
});

// ============================================================================
// INICIAR
// ============================================================================

async function startServer() {
  if (process.env.DATABASE_URL) {
    await initializeDatabasePool();
  }

  console.log('\n🔍 [STARTUP] Verificando Evolution API...');
  try {
    await evolutionAPI.get('/');
    console.log('✅ [STARTUP] Evolution API acessível');
  } catch (error) {
    console.error('❌ [STARTUP] Evolution API inacessível!');
    console.error('⚠️  URL:', EVOLUTION_API_URL);
  }

  const state = await getConnectionState();
  if (state?.instance?.state === 'open') {
    console.log('✅ [STARTUP] Instância já conectada');
    connectionStatus.connected = true;
  }

  app.listen(PORT, () => {
    console.log('\n🚀 WhatsApp Server - Evolution API');
    console.log(`📡 Porta: ${PORT}`);
    console.log(`🔗 Evolution API: ${EVOLUTION_API_URL}`);
    console.log(`📱 Instância: ${EVOLUTION_INSTANCE_NAME}`);
  });
}

startServer().catch(err => {
  console.error('❌ Erro:', err);
  process.exit(1);
});

process.on('unhandledRejection', (error) => console.error('❌ Unhandled:', error));
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
