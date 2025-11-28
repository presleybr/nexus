const express = require('express');
const cors = require('cors');
const wppconnect = require('@wppconnect-team/wppconnect');
const QRCode = require('qrcode');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;
const SESSION_NAME = process.env.SESSION_NAME || 'nexus_session';

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Estado global
let client = null;
let qrCodeData = null;
let isConnected = false;
let phoneNumber = null;

// ============================================
// CRIAR CLIENTE WPPCONNECT
// ============================================

async function createClient() {
    try {
        console.log('🚀 Iniciando WPPConnect...');

        client = await wppconnect.create({
            session: SESSION_NAME,
            headless: 'new',
            devtools: false,
            useChrome: true,
            debug: false,
            logQR: false,
            browserArgs: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ],
            puppeteerOptions: {
                executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                args: ['--no-sandbox']
            },
            catchQR: (base64Qr, asciiQR) => {
                console.log('📱 QR Code gerado');
                qrCodeData = base64Qr;
            },
            statusFind: (statusSession, session) => {
                console.log(`📊 Status: ${statusSession}`);

                if (statusSession === 'qrReadSuccess' || statusSession === 'isLogged') {
                    isConnected = true;
                    qrCodeData = null;
                    console.log('✅ WhatsApp conectado!');
                }

                if (statusSession === 'notLogged' || statusSession === 'desconnectedMobile') {
                    isConnected = false;
                    phoneNumber = null;
                    console.log('❌ WhatsApp desconectado');
                }
            },
            onLoadingScreen: (percent, message) => {
                console.log(`⏳ Carregando: ${percent}% - ${message}`);
            }
        });

        console.log('✅ Cliente WPPConnect criado com sucesso');

        // Obter número conectado
        if (client.isConnected()) {
            const hostDevice = await client.getHostDevice();
            phoneNumber = hostDevice.id.user;
            isConnected = true;
            console.log(`📱 Conectado como: ${phoneNumber}`);
        }

        // Listener para mensagens recebidas
        client.onMessage(async (message) => {
            console.log('📩 Mensagem recebida:', message.from, message.body);

            // Enviar webhook (se configurado)
            if (process.env.WEBHOOK_ENABLED === 'true' && process.env.WEBHOOK_URL) {
                try {
                    const fetch = (await import('node-fetch')).default;
                    await fetch(process.env.WEBHOOK_URL, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            type: 'message',
                            from: message.from,
                            body: message.body,
                            timestamp: message.timestamp
                        })
                    });
                } catch (error) {
                    console.error('❌ Erro ao enviar webhook:', error.message);
                }
            }
        });

        // Listener para status de mensagens
        client.onAck((ack) => {
            console.log('📊 Status mensagem:', ack.id._serialized, ack.ack);
        });

        return client;

    } catch (error) {
        console.error('❌ Erro ao criar cliente:', error);
        throw error;
    }
}

// ============================================
// ROTAS DA API
// ============================================

// Health check
app.get('/', (req, res) => {
    res.json({
        service: 'Nexus WPPConnect Server',
        status: 'running',
        connected: isConnected,
        phone: phoneNumber,
        version: '1.0.0'
    });
});

// Iniciar conexão
app.post('/start', async (req, res) => {
    try {
        if (client && isConnected) {
            return res.json({
                success: true,
                message: 'Já está conectado',
                phone: phoneNumber
            });
        }

        if (client) {
            await client.close();
            client = null;
        }

        // Retorna imediatamente e inicia a conexão em background
        res.json({
            success: true,
            message: 'Conexão iniciada. Aguarde o QR Code.'
        });

        // Inicia a conexão de forma assíncrona
        createClient().catch(error => {
            console.error('❌ Erro ao iniciar:', error);
        });

    } catch (error) {
        console.error('❌ Erro ao iniciar:', error);
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
                phone: phoneNumber
            });
        }

        if (!qrCodeData) {
            return res.json({
                success: false,
                message: 'QR Code não disponível. Inicie a conexão primeiro.'
            });
        }

        res.json({
            success: true,
            connected: false,
            qr: qrCodeData
        });

    } catch (error) {
        console.error('❌ Erro ao obter QR:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Status da conexão
app.get('/status', async (req, res) => {
    try {
        let status = 'disconnected';

        if (client && isConnected) {
            const state = await client.getConnectionState();
            status = state === 'CONNECTED' ? 'connected' : 'connecting';
        }

        res.json({
            success: true,
            connected: isConnected,
            status: status,
            phone: phoneNumber
        });

    } catch (error) {
        console.error('❌ Erro ao verificar status:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Função auxiliar para normalizar número de telefone
function normalizePhoneNumber(phone) {
    // Remove tudo que não é dígito
    let cleaned = phone.replace(/\D/g, '');

    console.log(`📞 Normalizando número: ${phone} → ${cleaned}`);

    // Se começar com 0, remove
    if (cleaned.startsWith('0')) {
        cleaned = cleaned.substring(1);
    }

    // Se não começar com 55, adiciona
    if (!cleaned.startsWith('55')) {
        cleaned = '55' + cleaned;
    }

    // Validação de tamanho
    // Brasil: 55 (2) + DDD (2) + número (8 ou 9) = 12 ou 13 dígitos
    if (cleaned.length < 12 || cleaned.length > 13) {
        console.log(`⚠️  Número com tamanho inválido: ${cleaned} (${cleaned.length} dígitos)`);

        // Tenta corrigir números com problemas comuns
        if (cleaned.length === 14) {
            // Pode ter dígito extra, tenta remover
            cleaned = cleaned.substring(0, 13);
            console.log(`🔧 Ajustado para: ${cleaned}`);
        } else if (cleaned.length === 11) {
            // Falta o código do país, adiciona 55
            cleaned = '55' + cleaned;
            console.log(`🔧 Ajustado para: ${cleaned}`);
        }
    }

    console.log(`✅ Número normalizado final: ${cleaned}`);
    return cleaned;
}

// Função auxiliar para obter o ID correto do contato (LID ou c.us)
async function getCorrectContactId(phoneOriginal) {
    try {
        // Normaliza o número primeiro
        const phoneFormatted = normalizePhoneNumber(phoneOriginal);

        console.log(`\n🔍 Buscando contato: ${phoneOriginal} → ${phoneFormatted}`);

        // Método 1: Usa checkNumberStatus (método recomendado)
        try {
            console.log(`   Tentando checkNumberStatus...`);
            const numberCheck = await client.checkNumberStatus(phoneFormatted);

            console.log(`   Resultado checkNumberStatus:`, {
                numberExists: numberCheck?.numberExists,
                canReceiveMessage: numberCheck?.canReceiveMessage,
                id: numberCheck?.id?._serialized
            });

            if (numberCheck && numberCheck.numberExists && numberCheck.id && numberCheck.id._serialized) {
                console.log(`✅ Número VÁLIDO: ${numberCheck.id._serialized}`);
                return numberCheck.id._serialized;
            }

            if (numberCheck && numberCheck.numberExists === false) {
                console.log(`❌ Número NÃO EXISTE no WhatsApp: ${phoneFormatted}`);
                return null;
            }
        } catch (checkError) {
            console.log(`⚠️  checkNumberStatus falhou:`, checkError.message);
        }

        // Método 2: Tenta obter o contato diretamente (fallback)
        try {
            console.log(`   Tentando getContact como fallback...`);
            const contact = await client.getContact(`${phoneFormatted}@c.us`);
            if (contact && contact.id && contact.id._serialized) {
                console.log(`✅ ID obtido via getContact: ${contact.id._serialized}`);
                return contact.id._serialized;
            }
        } catch (contactError) {
            console.log(`⚠️  getContact falhou:`, contactError.message);
        }

        // Método 3: Força envio com @c.us (última tentativa - permite envio mesmo sem verificar)
        console.log(`⚠️  Tentando formato padrão @c.us (sem verificação)`);
        const forcedId = `${phoneFormatted}@c.us`;
        console.log(`⚠️  Usando ID forçado: ${forcedId}`);
        return forcedId;

    } catch (error) {
        console.error(`\n❌ ERRO CRÍTICO ao processar número ${phoneOriginal}:`, error);
        return null;
    }
}

// Enviar mensagem de texto
app.post('/send-text', async (req, res) => {
    try {
        const { phone, message } = req.body;

        if (!phone || !message) {
            return res.status(400).json({
                success: false,
                error: 'Telefone e mensagem são obrigatórios'
            });
        }

        if (!client || !isConnected) {
            return res.status(400).json({
                success: false,
                error: 'WhatsApp não está conectado'
            });
        }

        // Formatar número (remover caracteres especiais)
        let phoneFormatted = phone.replace(/\D/g, '');

        // Obter o ID correto do contato
        const numberId = await getCorrectContactId(phoneFormatted);

        if (!numberId) {
            return res.status(400).json({
                success: false,
                error: 'Não foi possível obter o ID correto do WhatsApp para este número. Verifique se o número está correto e tem WhatsApp ativo.'
            });
        }

        console.log(`📱 Enviando mensagem para: ${numberId}`);

        // Enviar mensagem usando o ID correto
        const result = await client.sendText(numberId, message);

        console.log('✅ Mensagem enviada:', numberId);

        res.json({
            success: true,
            messageId: result.id,
            to: numberId,
            status: 'sent'
        });

    } catch (error) {
        console.error('❌ Erro ao enviar mensagem:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Enviar arquivo (PDF, imagem, etc)
app.post('/send-file', async (req, res) => {
    try {
        const { phone, filePath, caption, filename } = req.body;

        if (!phone || !filePath) {
            return res.status(400).json({
                success: false,
                error: 'Telefone e caminho do arquivo são obrigatórios'
            });
        }

        if (!client || !isConnected) {
            return res.status(400).json({
                success: false,
                error: 'WhatsApp não está conectado'
            });
        }

        // Formatar número (remover caracteres especiais)
        let phoneFormatted = phone.replace(/\D/g, '');

        // Obter o ID correto do contato
        const numberId = await getCorrectContactId(phoneFormatted);

        if (!numberId) {
            return res.status(400).json({
                success: false,
                error: 'Não foi possível obter o ID correto do WhatsApp para este número. Verifique se o número está correto e tem WhatsApp ativo.'
            });
        }

        console.log(`📱 Enviando arquivo para: ${numberId}`);

        // Enviar arquivo usando o ID correto
        const result = await client.sendFile(
            numberId,
            filePath,
            filename || 'arquivo',
            caption || ''
        );

        console.log('✅ Arquivo enviado:', numberId);

        res.json({
            success: true,
            messageId: result.id,
            to: numberId,
            status: 'sent'
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
            await client.close();
            client = null;
            isConnected = false;
            phoneNumber = null;
            qrCodeData = null;

            console.log('🔌 WhatsApp desconectado');
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

// ============================================
// INICIAR SERVIDOR
// ============================================

app.listen(PORT, () => {
    console.log('╔════════════════════════════════════════╗');
    console.log('║                                        ║');
    console.log('║   🚀 NEXUS WPPCONNECT SERVER          ║');
    console.log('║                                        ║');
    console.log('╚════════════════════════════════════════╝');
    console.log('');
    console.log(`✅ Servidor rodando na porta ${PORT}`);
    console.log(`🌐 API: http://localhost:${PORT}`);
    console.log('');
    console.log('📝 Endpoints disponíveis:');
    console.log('   POST /start        - Iniciar conexão');
    console.log('   GET  /qr           - Obter QR Code');
    console.log('   GET  /status       - Status da conexão');
    console.log('   POST /send-text    - Enviar mensagem');
    console.log('   POST /send-file    - Enviar arquivo');
    console.log('   POST /logout       - Desconectar');
    console.log('');
    console.log('⌨️  Para parar: CTRL+C');
    console.log('');
});

// Tratamento de erros
process.on('unhandledRejection', (error) => {
    console.error('❌ Unhandled rejection:', error);
});

process.on('SIGINT', async () => {
    console.log('\n🛑 Encerrando servidor...');

    if (client) {
        try {
            await client.close();
        } catch (error) {
            console.error('Erro ao fechar cliente:', error);
        }
    }

    process.exit(0);
});
