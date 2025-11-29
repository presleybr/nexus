# WPPConnect Server - Nexus CRM

Servidor WhatsApp Web integrado ao Nexus CRM usando WPPConnect.

## Descrição

Este serviço roda separadamente do backend Flask e fornece endpoints para:
- Conectar ao WhatsApp Web
- Gerar QR Code
- Enviar mensagens
- Enviar arquivos (PDFs, imagens, etc)

## Estrutura

```
wppconnect/
├── server.js       # Servidor WPPConnect
├── package.json    # Dependências Node.js
├── .gitignore      # Arquivos ignorados
└── README.md       # Este arquivo
```

## Desenvolvimento Local

### 1. Instalar dependências

```bash
cd wppconnect
npm install
```

### 2. Configurar variáveis de ambiente

Crie `.env`:

```env
PORT=3001
SECRET_KEY=sua_chave_secreta_aqui
HOST=http://localhost
BASE_URL=http://localhost:3001
```

### 3. Iniciar servidor

```bash
npm start
```

O servidor estará disponível em `http://localhost:3001`

## Endpoints Principais

### Status do Servidor

```bash
GET /
```

Retorna:
```json
{
  "status": "running"
}
```

### Iniciar Sessão

```bash
POST /api/sessions/start
```

### Obter QR Code

```bash
GET /api/sessions/qrcode
```

Retorna QR Code em base64 para escanear com WhatsApp.

### Verificar Status da Sessão

```bash
GET /api/sessions/status
```

### Enviar Mensagem

```bash
POST /api/messages/send
Content-Type: application/json

{
  "phone": "5511999999999",
  "message": "Olá!"
}
```

### Enviar Arquivo

```bash
POST /api/messages/send-file
Content-Type: application/json

{
  "phone": "5511999999999",
  "filePath": "/path/to/file.pdf",
  "caption": "Segue anexo"
}
```

## Deploy no Render

O serviço é automaticamente deployed no Render junto com o backend Flask através do arquivo `render.yaml` na raiz do projeto.

### Configuração no Render

1. O Render detecta automaticamente o serviço `nexus-wppconnect`
2. Faz build com `npm install`
3. Inicia com `npm start`
4. Expõe na URL: `https://nexus-wppconnect.onrender.com`

### Variáveis de Ambiente

Definir no painel do Render:

- `PORT`: 10000 (padrão Render)
- `SECRET_KEY`: Gerado automaticamente
- `HOST`: https://nexus-wppconnect.onrender.com
- `BASE_URL`: https://nexus-wppconnect.onrender.com

## Integração com Backend Flask

O backend Flask se conecta ao WPPConnect através da variável `WPPCONNECT_URL`:

```python
# backend/config.py
WPPCONNECT_URL = os.getenv('WPPCONNECT_URL', 'http://localhost:3001')
```

Definir no Render (backend):
```
WPPCONNECT_URL=https://nexus-wppconnect.onrender.com
```

## Logs

### Desenvolvimento Local

```bash
npm start
# Logs aparecem no terminal
```

### Produção (Render)

Acesse os logs no dashboard do Render:
```
https://dashboard.render.com/web/[service-id]/logs
```

## Troubleshooting

### Erro: "Module not found"

```bash
rm -rf node_modules package-lock.json
npm install
```

### Erro: "Port already in use"

Mude a porta no `.env`:
```env
PORT=3002
```

### WhatsApp desconecta

- Verifique se há sessões antigas: delete a pasta `tokens/`
- Reconecte escaneando novo QR Code

## Segurança

- **SECRET_KEY**: Sempre use chave forte em produção
- **HTTPS**: Render fornece SSL automático
- **Tokens**: Armazenados localmente (persistent disk no Render)

## Documentação

- WPPConnect: https://wppconnect.io/
- API Docs: https://github.com/wppconnect-team/wppconnect-server

## Suporte

- Issues: https://github.com/presleybr/nexus/issues
- WPPConnect Issues: https://github.com/wppconnect-team/wppconnect-server/issues
