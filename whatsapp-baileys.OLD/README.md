# WhatsApp Baileys - Nexus CRM

Servidor Node.js com Baileys para integração WhatsApp local (sem APIs externas).

## Características

- **Baileys** v6.6.0 - Biblioteca Node.js para WhatsApp Web
- **Express** - API REST para comunicação com backend Python
- **QR Code** - Autenticação via QR Code
- **Sessões Persistentes** - Salva sessão localmente (não precisa escanear sempre)
- **Multi-envio** - Texto, PDF, Imagens
- **Anti-bloqueio** - Delays configuráveis entre mensagens

## Requisitos

- Node.js 20.18.0 (via NVM)
- NPM

## Instalação

```bash
# Instalar dependências
npm install
```

## Inicialização

### Opção 1: Via script (recomendado)
```bash
# Execute do diretório raiz do Nexus
start-whatsapp-baileys.bat
```

### Opção 2: Manual
```bash
# Entre no diretório
cd whatsapp-baileys

# Configure Node.js 20.18.0
nvm use 20.18.0

# Inicie o servidor
npm start
```

## API Endpoints

### POST /connect
Inicia conexão com WhatsApp
```json
Response: {"success": true, "message": "Conectando..."}
```

### GET /qr
Obtém QR Code em base64
```json
Response: {
  "success": true,
  "qr": "data:image/png;base64,..."
}
```

### GET /status
Verifica status da conexão
```json
Response: {
  "connected": true,
  "status": "connected",
  "phone": "5567999887766@s.whatsapp.net"
}
```

### POST /send-text
Envia mensagem de texto
```json
Request: {
  "phone": "5567999887766",
  "message": "Olá!"
}
Response: {"success": true}
```

### POST /send-file
Envia arquivo PDF
```json
Request: {
  "phone": "5567999887766",
  "filePath": "D:/Nexus/boletos/boleto.pdf",
  "caption": "Seu boleto",
  "filename": "boleto.pdf"
}
Response: {"success": true}
```

### POST /send-image
Envia imagem
```json
Request: {
  "phone": "5567999887766",
  "filePath": "D:/Nexus/imagens/foto.jpg",
  "caption": "Foto"
}
Response: {"success": true}
```

### POST /logout
Desconecta e limpa sessão
```json
Response: {"success": true, "message": "Desconectado com sucesso"}
```

## Integração com Backend Python

O backend Python se comunica com este servidor via requisições HTTP:

```python
from services.whatsapp_baileys import whatsapp_service

# Conectar
whatsapp_service.conectar()

# Verificar status
status = whatsapp_service.verificar_status()

# Enviar mensagem
whatsapp_service.enviar_mensagem("+55 67 99988-7766", "Olá!")

# Enviar PDF
whatsapp_service.enviar_pdf(
    telefone="+55 67 99988-7766",
    caminho_pdf="D:/Nexus/boletos/boleto.pdf",
    caption="Seu boleto"
)

# Enviar boleto completo (mensagem + delay + PDF)
whatsapp_service.enviar_boleto_completo(
    telefone="+55 67 99988-7766",
    pdf_path="D:/Nexus/boletos/boleto.pdf",
    mensagem_antibloqueio="Olá! Segue seu boleto..."
)
```

## Estrutura de Arquivos

```
whatsapp-baileys/
├── server.js          # Servidor Express + Baileys
├── package.json       # Dependências
├── sessions/          # Sessões salvas (não versionar)
├── .gitignore         # Arquivos ignorados
└── README.md          # Esta documentação
```

## Sessões WhatsApp

As sessões são salvas em `./sessions/` e persistem entre reinicializações.

- **Primeira conexão**: Escaneia QR Code
- **Conexões seguintes**: Conecta automaticamente (se sessão válida)
- **Logout**: Remove sessão, precisa escanear QR novamente

## Reconexão Automática

O servidor reconecta automaticamente em caso de:
- Perda de conexão temporária
- Restart do servidor (se sessão válida)
- Erro de rede

**Exceção**: Não reconecta após logout intencional.

## Logs

O servidor exibe logs úteis:
- 📱 QR Code gerado
- ✅ Conectado
- ❌ Desconectado
- 📩 Mensagem recebida
- 🔄 Reconectando

## Solução de Problemas

### Porta 3000 já está em uso
```bash
# Verifique processos usando a porta
netstat -ano | findstr :3000

# Mate o processo
taskkill /PID [PID_NUMBER] /F
```

### QR Code não aparece
- Verifique se o servidor está rodando
- Acesse http://localhost:3000/qr
- Restart do servidor: Ctrl+C e inicie novamente

### Não envia mensagens
- Verifique status: http://localhost:3000/status
- Certifique-se de que `connected: true`
- Verifique se o telefone está formatado corretamente (DDI + DDD + número)

### Sessão expirada
- Execute logout via API ou frontend
- Reconecte escaneando novo QR Code

## Segurança

- ⚠️ **Não versione** a pasta `sessions/` (contém credenciais)
- ⚠️ **Não compartilhe** sessões ativas
- ⚠️ **Use apenas** em ambiente controlado
- ⚠️ **Respeite** limites do WhatsApp para evitar bloqueios

## Limites do WhatsApp

Para evitar bloqueios:
- Máximo 50-100 mensagens/dia para novos números
- Delay de 3-7s entre mensagens
- Não envie spam
- Use mensagens personalizadas

## Tecnologias

- [@whiskeysockets/baileys](https://github.com/WhiskeySockets/Baileys) - Biblioteca WhatsApp Web
- [Express](https://expressjs.com/) - Framework web
- [QRCode](https://www.npmjs.com/package/qrcode) - Geração de QR Code
- [Pino](https://getpino.io/) - Logger

## Autor

Sistema Nexus CRM - "Aqui seu tempo vale ouro"

## Licença

Uso interno - Nexus CRM
