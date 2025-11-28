import makeWASocket, { useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } from '@whiskeysockets/baileys';
import express from 'express';
import cors from 'cors';
import QRCode from 'qrcode';
import { readFileSync, existsSync, rmSync } from 'fs';
import pino from 'pino';

const app = express();
app.use(cors());
app.use(express.json());

let sock = null;
let qrCodeData = null;
let isConnected = false;
let connectionAttempts = 0;
const MAX_ATTEMPTS = 3;

const logger = pino({ level: 'error' }); // Mudar para 'error' para reduzir logs

// Função para iniciar conexão
async function connectToWhatsApp() {
    try {
        if (connectionAttempts >= MAX_ATTEMPTS) {
            console.log('❌ Máximo de tentativas atingido. Aguarde requisição manual.');
            connectionAttempts = 0;
            return;
        }

        connectionAttempts++;
        console.log(`🔄 Tentativa ${connectionAttempts}/${MAX_ATTEMPTS} - Conectando ao WhatsApp...`);

        const { state, saveCreds } = await useMultiFileAuthState('./sessions');
        const { version } = await fetchLatestBaileysVersion();

        sock = makeWASocket({
            auth: state,
            version,
            logger,
            // NÃO usar printQRInTerminal - está deprecated
            browser: ['Nexus CRM', 'Chrome', '10.0.0'],
            connectTimeoutMs: 60000, // 60 segundos timeout
            defaultQueryTimeoutMs: 60000,
            keepAliveIntervalMs: 30000
        });

        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;

            if (qr) {
                console.log('📱 QR Code gerado!');
                try {
                    qrCodeData = await QRCode.toDataURL(qr);
                } catch (error) {
                    console.error('Erro ao gerar QR Code:', error);
                }
            }

            if (connection === 'close') {
                isConnected = false;
                qrCodeData = null;

                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

                console.log(`❌ Conexão fechada. Código: ${statusCode}`);

                // Tratamento específico para erro 401 (credenciais inválidas/expiradas)
                if (statusCode === 401) {
                    console.log('⚠️ Erro 401 - Credenciais inválidas ou expiradas');
                    console.log('🗑️ Limpando sessões antigas...');
                    try {
                        if (existsSync('./sessions')) {
                            rmSync('./sessions', { recursive: true, force: true });
                            console.log('✅ Sessões antigas removidas');
                            console.log('🔄 Chame /connect novamente para gerar novo QR Code');
                        }
                    } catch (error) {
                        console.error('❌ Erro ao limpar sessões:', error.message);
                    }
                    connectionAttempts = 0;
                }
                // Erro 515 - QR Code expirado
                else if (statusCode === 515) {
                    console.log('⏰ Erro 515 - QR Code expirou. Gere um novo QR Code.');
                    qrCodeData = null;
                    connectionAttempts = 0;
                }
                // Erro 405 - Muitas tentativas
                else if (statusCode === 405) {
                    console.log('⚠️ Erro 405 - Aguarde 30 segundos antes de tentar novamente');
                    connectionAttempts = 0; // Resetar contador
                }
                // Logout manual
                else if (statusCode === DisconnectReason.loggedOut) {
                    console.log('🔓 Logout detectado. Sessão encerrada.');
                    connectionAttempts = 0;
                }
                // Outros erros
                else if (shouldReconnect) {
                    console.log('⏳ Aguardando nova requisição de conexão...');
                } else {
                    console.log('🔌 Conexão encerrada');
                    connectionAttempts = 0;
                }
            } else if (connection === 'open') {
                isConnected = true;
                qrCodeData = null;
                connectionAttempts = 0;
                console.log('✅ Conectado ao WhatsApp!');
            } else if (connection === 'connecting') {
                console.log('🔄 Conectando...');
            }
        });

        sock.ev.on('creds.update', saveCreds);

    } catch (error) {
        console.error('❌ Erro ao conectar:', error.message);
        connectionAttempts = 0;
    }
}

// Rotas da API
app.post('/connect', async (req, res) => {
    try {
        if (isConnected) {
            return res.json({
                success: true,
                message: 'Já conectado!',
                connected: true
            });
        }

        if (connectionAttempts > 0) {
            return res.json({
                success: false,
                error: 'Conexão em andamento. Aguarde...'
            });
        }

        console.log('📲 Iniciando conexão...');
        connectToWhatsApp();

        res.json({ success: true, message: 'Iniciando conexão...' });
    } catch (error) {
        console.error('Erro ao iniciar conexão:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/qr', (req, res) => {
    if (isConnected) {
        res.json({ success: true, connected: true, qr: null });
    } else if (qrCodeData) {
        res.json({ success: true, connected: false, qr: qrCodeData });
    } else {
        res.json({ success: false, message: 'QR Code não disponível. Chame /connect primeiro.' });
    }
});

app.get('/status', (req, res) => {
    const status = isConnected ? 'connected' : (connectionAttempts > 0 ? 'connecting' : 'disconnected');
    res.json({
        connected: isConnected,
        status: status,
        phone: isConnected ? sock?.user?.id : null
    });
});

app.post('/send-text', async (req, res) => {
    try {
        if (!isConnected || !sock) {
            return res.status(400).json({ success: false, error: 'WhatsApp não conectado' });
        }

        const { phone, message } = req.body;

        if (!phone || !message) {
            return res.status(400).json({ success: false, error: 'Phone e message são obrigatórios' });
        }

        const jid = phone.includes('@') ? phone : `${phone}@s.whatsapp.net`;

        await sock.sendMessage(jid, { text: message });

        console.log(`✅ Mensagem enviada para ${phone}`);
        res.json({ success: true, message: 'Mensagem enviada!' });
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/send-file', async (req, res) => {
    try {
        if (!isConnected || !sock) {
            return res.status(400).json({ success: false, error: 'WhatsApp não conectado' });
        }

        const { phone, filePath, caption, filename } = req.body;

        if (!phone || !filePath) {
            return res.status(400).json({ success: false, error: 'Phone e filePath são obrigatórios' });
        }

        if (!existsSync(filePath)) {
            return res.status(404).json({ success: false, error: 'Arquivo não encontrado' });
        }

        const jid = phone.includes('@') ? phone : `${phone}@s.whatsapp.net`;
        const fileBuffer = readFileSync(filePath);

        await sock.sendMessage(jid, {
            document: fileBuffer,
            fileName: filename || 'document.pdf',
            caption: caption || '',
            mimetype: 'application/pdf'
        });

        console.log(`✅ Arquivo enviado para ${phone}`);
        res.json({ success: true, message: 'Arquivo enviado!' });
    } catch (error) {
        console.error('Erro ao enviar arquivo:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/send-image', async (req, res) => {
    try {
        if (!isConnected || !sock) {
            return res.status(400).json({ success: false, error: 'WhatsApp não conectado' });
        }

        const { phone, filePath, caption } = req.body;

        if (!phone || !filePath) {
            return res.status(400).json({ success: false, error: 'Phone e filePath são obrigatórios' });
        }

        if (!existsSync(filePath)) {
            return res.status(404).json({ success: false, error: 'Imagem não encontrada' });
        }

        const jid = phone.includes('@') ? phone : `${phone}@s.whatsapp.net`;
        const imageBuffer = readFileSync(filePath);

        await sock.sendMessage(jid, {
            image: imageBuffer,
            caption: caption || ''
        });

        console.log(`✅ Imagem enviada para ${phone}`);
        res.json({ success: true, message: 'Imagem enviada!' });
    } catch (error) {
        console.error('Erro ao enviar imagem:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/logout', async (req, res) => {
    try {
        if (sock) {
            await sock.logout();
        }
        isConnected = false;
        qrCodeData = null;
        connectionAttempts = 0;
        console.log('✅ Desconectado do WhatsApp');
        res.json({ success: true, message: 'Desconectado' });
    } catch (error) {
        console.error('Erro ao desconectar:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/', (req, res) => {
    res.json({
        service: 'Nexus WhatsApp Baileys',
        status: 'running',
        connected: isConnected,
        version: '1.0.0'
    });
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`
============================================
  🚀 Nexus WhatsApp Baileys Server
============================================
📡 Servidor rodando em http://localhost:${PORT}
📱 Status: ${isConnected ? 'connected ✅' : 'disconnected ❌'}
============================================
    `);
});
