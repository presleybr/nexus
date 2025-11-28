# Evolution API - Integração Nexus CRM

## Visão Geral

O Nexus CRM agora utiliza **Evolution API** como provedor WhatsApp, substituindo completamente o Baileys anterior. Evolution API é uma solução mais robusta, estável e com suporte a múltiplas instâncias.

---

## Pré-requisitos

- **Docker Desktop** instalado e rodando
- **PostgreSQL** rodando na porta 5434
- Nexus CRM configurado

---

## Instalação e Configuração

### 1. Instalar Docker Desktop

Se ainda não tiver o Docker instalado:

1. Baixe em: https://www.docker.com/products/docker-desktop/
2. Execute o instalador
3. Reinicie o computador se solicitado
4. Abra o Docker Desktop e aguarde inicializar

### 2. Primeira Inicialização

#### Método 1: Script Completo (Recomendado)

```bash
# Executa tudo automaticamente
D:\Nexus\start-nexus-completo.bat
```

#### Método 2: Passo a Passo

**Passo 1: Iniciar Evolution API**
```bash
cd D:\Nexus\evolution-api
docker-compose up -d
```

**Passo 2: Verificar se está rodando**
```bash
# Acessar no navegador
http://localhost:8080
```

**Passo 3: Iniciar Flask**
```bash
cd D:\Nexus
venv\Scripts\activate
python start.py
```

---

## Uso no CRM

### Conectar WhatsApp

1. Acesse: http://localhost:5000/crm/whatsapp
2. Clique em **"Conectar WhatsApp"**
3. Aguarde o QR Code aparecer
4. Abra o WhatsApp no celular
5. Vá em **Dispositivos Conectados** → **Conectar Dispositivo**
6. Escaneie o QR Code
7. Aguarde confirmação de conexão

### Enviar Mensagens

Após conectado, você pode:
- Enviar mensagens de texto
- Enviar PDFs
- Enviar boletos com delay anti-bloqueio
- Fazer disparos em massa

Todas as funcionalidades anteriores do Baileys foram mantidas!

---

## Comandos Úteis

### Ver logs do Evolution API
```bash
cd D:\Nexus\evolution-api
docker-compose logs -f
```

### Parar Evolution API
```bash
cd D:\Nexus\evolution-api
docker-compose down
```

### Reiniciar Evolution API
```bash
cd D:\Nexus\evolution-api
docker-compose restart
```

### Verificar status dos containers
```bash
docker ps
```

### Parar tudo
```bash
# Use o script
D:\Nexus\stop-nexus-completo.bat

# Ou manualmente
cd D:\Nexus\evolution-api
docker-compose down
```

---

## Estrutura de Arquivos

```
D:\Nexus\
├── evolution-api/
│   ├── docker-compose.yml    # Configuração do Docker
│   ├── .env                   # Variáveis de ambiente
│   ├── start.bat              # Iniciar Evolution API
│   └── stop.bat               # Parar Evolution API
│
├── backend/
│   └── services/
│       ├── whatsapp_evolution.py   # Serviço Evolution API (NOVO)
│       └── whatsapp_baileys.py     # Serviço Baileys (DESATIVADO)
│
├── start-nexus-completo.bat  # Inicia tudo
└── stop-nexus-completo.bat   # Para tudo
```

---

## Troubleshooting

### Porta 8080 já em uso

```bash
# Ver processo usando porta 8080
netstat -ano | findstr :8080

# Matar processo (substitua <PID> pelo número encontrado)
taskkill /PID <PID> /F

# Ou mudar porta no docker-compose.yml
# Altere "8080:8080" para "8081:8080"
```

### Erro de conexão com PostgreSQL

1. Verifique se PostgreSQL está rodando:
   ```bash
   # Windows
   services.msc
   # Procure por "postgresql"
   ```

2. Verifique a porta no `.env`:
   ```
   DB_PORT=5434
   ```

3. Teste conexão:
   ```bash
   psql -h localhost -p 5434 -U postgres -d nexus_crm
   ```

### QR Code não aparece

1. Verifique logs:
   ```bash
   cd D:\Nexus\evolution-api
   docker-compose logs -f
   ```

2. Reinicie o container:
   ```bash
   docker-compose restart
   ```

3. Se persistir, delete e recrie:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Docker não inicia

1. Verifique se Docker Desktop está rodando
2. Reinicie o Docker Desktop
3. Verifique WSL2 (Windows):
   ```bash
   wsl --status
   ```

### Evolution API não conecta ao banco

1. Verifique se PostgreSQL aceita conexões externas
2. No `docker-compose.yml`, use:
   - Windows/Mac: `host.docker.internal`
   - Linux: `172.17.0.1` (IP do Docker bridge)

---

## API Endpoints (Evolution)

**Base URL:** http://localhost:8080

**Headers necessários:**
```
Content-Type: application/json
apikey: nexus-evolution-key-2025-secure
```

### Endpoints Principais

#### Criar Instância
```bash
POST /instance/create
{
  "instanceName": "nexus_whatsapp",
  "qrcode": true,
  "integration": "WHATSAPP-BAILEYS"
}
```

#### Conectar
```bash
GET /instance/connect/nexus_whatsapp
```

#### Obter QR Code
```bash
GET /instance/qrcode/nexus_whatsapp
```

#### Status da Conexão
```bash
GET /instance/connectionState/nexus_whatsapp
```

#### Enviar Texto
```bash
POST /message/sendText/nexus_whatsapp
{
  "number": "5567999887766@s.whatsapp.net",
  "text": "Olá! Mensagem de teste."
}
```

#### Enviar Arquivo
```bash
POST /message/sendMedia/nexus_whatsapp
{
  "number": "5567999887766@s.whatsapp.net",
  "mediatype": "document",
  "mimetype": "application/pdf",
  "caption": "Segue documento",
  "fileName": "documento.pdf",
  "media": "<base64_do_arquivo>"
}
```

#### Desconectar
```bash
DELETE /instance/logout/nexus_whatsapp
```

#### Deletar Instância
```bash
DELETE /instance/delete/nexus_whatsapp
```

---

## Webhooks

O Evolution API envia webhooks para o Flask em eventos como:

- **QR Code atualizado:** `QRCODE_UPDATED`
- **Mensagem recebida:** `MESSAGES_UPSERT`
- **Status de conexão:** `CONNECTION_UPDATE`
- **Mensagem enviada:** `SEND_MESSAGE`

**URL do Webhook:** http://host.docker.internal:5000/api/webhook/whatsapp

Você pode criar rotas no Flask para processar esses eventos.

---

## Segurança

### API Key

A chave de API está configurada em:
- `D:\Nexus\evolution-api\docker-compose.yml`
- `D:\Nexus\.env`

**Valor padrão:** `nexus-evolution-key-2025-secure`

Para produção, **altere** para uma chave forte:
```bash
# Gerar chave aleatória
openssl rand -base64 32
```

### Rede

Por padrão, Evolution API aceita conexões de qualquer origem (`CORS_ORIGIN: "*"`).

Para produção, limite as origens:
```yaml
CORS_ORIGIN: "http://localhost:5000"
```

---

## Backup e Migração

### Backup de Sessões

Sessões WhatsApp são salvas em:
- **PostgreSQL:** Tabelas gerenciadas pela Evolution API
- **Volumes Docker:** `evolution_instances` e `evolution_store`

Para backup:
```bash
# Backup PostgreSQL
pg_dump -h localhost -p 5434 -U postgres nexus_crm > backup.sql

# Backup volumes Docker
docker run --rm -v evolution_instances:/data -v D:\backup:/backup alpine tar czf /backup/instances.tar.gz /data
```

### Migração do Baileys

Se você tinha dados no Baileys anterior, será necessário reconectar o WhatsApp escaneando o QR Code novamente. Não há migração automática de sessões.

---

## Diferenças: Baileys vs Evolution API

| Aspecto | Baileys (Antigo) | Evolution API (Novo) |
|---------|------------------|----------------------|
| **Instalação** | Node.js manual | Docker (simples) |
| **Estabilidade** | Médio | Alto |
| **Múltiplas instâncias** | Não | Sim |
| **Banco de dados** | Não integrado | PostgreSQL nativo |
| **Webhooks** | Limitado | Completo |
| **Documentação** | Escassa | Completa |
| **Manutenção** | Manual | Automatizada |

---

## Suporte

Para problemas ou dúvidas:

1. Verifique os logs:
   ```bash
   docker-compose logs -f
   ```

2. Consulte documentação oficial:
   - Evolution API: https://doc.evolution-api.com/

3. Issues no GitHub do projeto

---

## Changelog

### Versão 2.0 (Migração Evolution API)
- ✅ Substituído Baileys por Evolution API
- ✅ Integração com Docker
- ✅ Salvamento de sessões no PostgreSQL
- ✅ Scripts de inicialização automatizados
- ✅ Webhooks completos
- ✅ Todas funcionalidades anteriores mantidas

### Versão 1.0 (Baileys)
- ✅ Integração inicial com Baileys
- ✅ Envio de mensagens e PDFs
- ✅ Sistema de delays anti-bloqueio
