# 📱 Nexus CRM - Evolution API WhatsApp

Sistema de integração com WhatsApp usando Evolution API para disparo automático de boletos.

---

## 🚀 Instalação e Inicialização

### 1️⃣ Pré-requisitos

- **Docker Desktop** instalado e rodando
- **PostgreSQL** rodando na porta **5434** (já configurado no Nexus CRM)
- **Backend Flask** do Nexus CRM rodando na porta **5000**

### 2️⃣ Iniciar Evolution API

```bash
# Navegue até a pasta whatsapp-api
cd D:\Nexus\whatsapp-api

# Inicie o Docker Compose
docker-compose up -d
```

### 3️⃣ Verificar se está Rodando

```bash
# Verificar status do container
docker ps

# Deve aparecer: nexus-evolution-api rodando na porta 8080

# Verificar logs
docker logs nexus-evolution-api

# Acessar API no navegador
http://localhost:8080
```

### 4️⃣ Testar Conexão

```bash
# No PowerShell ou CMD
curl http://localhost:8080

# Deve retornar: Welcome to the Evolution API
```

---

## 📋 Comandos Úteis

### Gerenciamento do Container

```bash
# Iniciar serviço
docker-compose up -d

# Parar serviço
docker-compose down

# Reiniciar serviço
docker-compose restart

# Ver logs em tempo real
docker logs -f nexus-evolution-api

# Ver últimas 100 linhas de logs
docker logs --tail 100 nexus-evolution-api

# Parar e remover volumes (CUIDADO: apaga todas as sessões)
docker-compose down -v
```

### Verificação de Status

```bash
# Status do container
docker ps | findstr nexus-evolution

# Uso de recursos
docker stats nexus-evolution-api

# Informações detalhadas
docker inspect nexus-evolution-api
```

---

## 🔧 Configuração

### Variáveis de Ambiente

Arquivo: `whatsapp-api\.env`

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=nexus-evolution-key-2025
DATABASE_CONNECTION_URI=postgresql://postgres:nexus2025@host.docker.internal:5434/nexus_crm
WEBHOOK_URL=http://host.docker.internal:5000/api/webhook/whatsapp
INSTANCE_PREFIX=nexus_cliente_
```

### Porta da API

- **Porta padrão**: 8080
- **URL base**: http://localhost:8080
- **Autenticação**: Header `apikey: nexus-evolution-key-2025`

### Banco de Dados

A Evolution API usa o **mesmo banco PostgreSQL** do Nexus CRM:

- **Host**: host.docker.internal (acessa o host Windows de dentro do Docker)
- **Porta**: 5434
- **Database**: nexus_crm
- **User**: postgres
- **Password**: nexus2025

### Webhooks

A Evolution API envia eventos para o backend Flask:

- **URL**: http://host.docker.internal:5000/api/webhook/whatsapp
- **Eventos**:
  - QR Code gerado
  - Conexão estabelecida
  - Desconexão
  - Mensagens recebidas
  - Mensagens enviadas

---

## 📡 Endpoints da Evolution API

### Criar Instância

```http
POST http://localhost:8080/instance/create
Headers:
  apikey: nexus-evolution-key-2025
  Content-Type: application/json
Body:
{
  "instanceName": "nexus_cliente_1",
  "qrcode": true,
  "integration": "WHATSAPP-BAILEYS"
}
```

### Conectar (Gerar QR Code)

```http
GET http://localhost:8080/instance/connect/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
```

Retorna:
```json
{
  "qrcode": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "code": "ABCD-EFGH-IJKL-MNOP"
}
```

### Verificar Status

```http
GET http://localhost:8080/instance/connectionState/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
```

Retorna:
```json
{
  "instance": {
    "instanceName": "nexus_cliente_1",
    "state": "open"
  }
}
```

Estados possíveis:
- `close` - Desconectado
- `connecting` - Conectando
- `open` - Conectado

### Enviar Mensagem de Texto

```http
POST http://localhost:8080/message/sendText/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
  Content-Type: application/json
Body:
{
  "number": "5567999887766",
  "text": "Olá! Você receberá seu boleto em instantes."
}
```

### Enviar Arquivo (PDF)

```http
POST http://localhost:8080/message/sendMedia/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
  Content-Type: application/json
Body:
{
  "number": "5567999887766",
  "mediatype": "document",
  "mimetype": "application/pdf",
  "caption": "Segue anexo o boleto",
  "fileName": "boleto.pdf",
  "media": "data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKMy..."
}
```

### Desconectar

```http
DELETE http://localhost:8080/instance/logout/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
```

### Deletar Instância

```http
DELETE http://localhost:8080/instance/delete/nexus_cliente_1
Headers:
  apikey: nexus-evolution-key-2025
```

---

## 🔍 Troubleshooting

### Container não inicia

```bash
# Verificar se a porta 8080 está livre
netstat -ano | findstr :8080

# Se estiver ocupada, matar o processo ou mudar a porta no docker-compose.yml

# Verificar logs de erro
docker logs nexus-evolution-api
```

### Erro de conexão com PostgreSQL

```bash
# Verificar se PostgreSQL está rodando na porta 5434
netstat -ano | findstr :5434

# Testar conexão manualmente
psql -U postgres -d nexus_crm -p 5434
# Senha: nexus2025

# Verificar se o host.docker.internal está resolvendo
docker exec nexus-evolution-api ping host.docker.internal
```

### QR Code não aparece

```bash
# Verificar se a instância foi criada
curl -H "apikey: nexus-evolution-key-2025" http://localhost:8080/instance/fetchInstances

# Deletar e recriar a instância
curl -X DELETE -H "apikey: nexus-evolution-key-2025" http://localhost:8080/instance/delete/nexus_cliente_1

# Verificar logs
docker logs -f nexus-evolution-api
```

### Mensagens não são enviadas

```bash
# Verificar status da conexão
curl -H "apikey: nexus-evolution-key-2025" http://localhost:8080/instance/connectionState/nexus_cliente_1

# Deve retornar "state": "open"

# Verificar formato do telefone (deve ser: 5567999887766)
# 55 = Brasil
# 67 = DDD
# 999887766 = Número (9 dígitos)

# Verificar logs de erro
docker logs --tail 50 nexus-evolution-api
```

### Webhook não está funcionando

```bash
# Verificar se o Flask está rodando na porta 5000
curl http://localhost:5000

# Testar rota do webhook
curl -X POST http://localhost:5000/api/webhook/whatsapp

# Verificar logs do Flask
# Deve aparecer: POST /api/webhook/whatsapp

# Verificar configuração do webhook no docker-compose.yml
# WEBHOOK_GLOBAL_URL=http://host.docker.internal:5000/api/webhook/whatsapp
```

### Limpar tudo e recomeçar

```bash
# Parar e remover container + volumes
docker-compose down -v

# Remover imagem
docker rmi atendai/evolution-api:latest

# Baixar imagem novamente
docker pull atendai/evolution-api:latest

# Iniciar novamente
docker-compose up -d

# Verificar logs
docker logs -f nexus-evolution-api
```

---

## 📊 Estrutura de Dados

### Tabela: whatsapp_sessions

```sql
CREATE TABLE whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id),
    instance_name VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'disconnected',
    qr_code TEXT,
    session_data JSONB,
    connected_at TIMESTAMP,
    disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Status possíveis:
- `disconnected` - Desconectado
- `qrcode` - Aguardando leitura do QR Code
- `connecting` - Conectando
- `connected` - Conectado e pronto para uso

---

## 🔐 Segurança

### API Key

- **Chave atual**: `nexus-evolution-key-2025`
- **Uso**: Enviar no header `apikey` em todas as requisições
- **Trocar chave**: Editar `docker-compose.yml` e `.env`, depois `docker-compose restart`

### Isolamento

- Evolution API roda em container Docker isolado
- Comunicação apenas via portas expostas (8080)
- Acesso ao banco via `host.docker.internal` (não expõe porta externamente)

### Dados Sensíveis

- QR Codes são temporários (30 segundos)
- Sessões WhatsApp criptografadas
- Logs não contêm números de telefone completos

---

## 📈 Monitoramento

### Logs em Tempo Real

```bash
# Seguir logs
docker logs -f nexus-evolution-api

# Filtrar apenas erros
docker logs nexus-evolution-api 2>&1 | findstr ERROR

# Salvar logs em arquivo
docker logs nexus-evolution-api > evolution-logs.txt
```

### Métricas

```bash
# Uso de CPU e memória
docker stats nexus-evolution-api

# Espaço em disco dos volumes
docker system df -v
```

### Saúde do Container

```bash
# Verificar se está rodando
docker ps | findstr nexus-evolution

# Reiniciar se travar
docker restart nexus-evolution-api

# Ver tempo de uptime
docker inspect nexus-evolution-api | findstr StartedAt
```

---

## 🎯 Uso no Nexus CRM

### Fluxo Completo

1. **Cliente acessa**: `/crm/whatsapp-conexao`
2. **Cria instância**: `nexus_cliente_{id}`
3. **Gera QR Code**: Escaneia com WhatsApp
4. **Conecta**: Status muda para `connected`
5. **Dispara boletos**: `/crm/disparos`
6. **Mensagem anti-bloqueio**: Enviada primeiro
7. **Delay 3-7s**: Simula comportamento humano
8. **PDF do boleto**: Enviado em seguida
9. **Registro**: Salvo em `disparos` e `boletos`

### Mensagem Anti-Bloqueio

Configurável em: `/crm/configuracoes`

Padrão: "Olá! Você receberá seu boleto em instantes."

Objetivo: Reduzir chance de ser bloqueado pelo WhatsApp

### Intervalo Entre Disparos

Configurável em: `/crm/configuracoes`

- **Mínimo**: 5 segundos
- **Máximo**: 30 segundos
- **Padrão**: 5 segundos
- **Aleatório**: 3-7 segundos (anti-detecção)

### Pausa Automática

- **A cada**: 20 mensagens
- **Tempo de pausa**: 60 segundos
- **Objetivo**: Evitar bloqueio por spam

---

## 📞 Suporte

### Documentação Oficial

- Evolution API: https://doc.evolution-api.com
- Docker: https://docs.docker.com
- WhatsApp Business API: https://developers.facebook.com/docs/whatsapp

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| Container não inicia | Verificar porta 8080 livre, reiniciar Docker Desktop |
| Erro de banco | Confirmar PostgreSQL na porta 5434, senha correta |
| QR Code não aparece | Deletar instância, criar novamente |
| Mensagem não envia | Verificar status=connected, formato telefone |
| WhatsApp desconecta | Reconectar via `/crm/whatsapp-conexao` |

---

## ✅ Checklist de Funcionamento

- [ ] Docker Desktop instalado e rodando
- [ ] Container `nexus-evolution-api` ativo
- [ ] API responde em http://localhost:8080
- [ ] PostgreSQL acessível na porta 5434
- [ ] Backend Flask rodando na porta 5000
- [ ] Instância criada com sucesso
- [ ] QR Code gerado e visível
- [ ] WhatsApp conectado (status=open)
- [ ] Mensagem de teste enviada
- [ ] Webhook recebendo eventos
- [ ] Disparos sendo registrados no banco

---

**🚀 Evolution API rodando! Sistema pronto para disparos automáticos de boletos via WhatsApp!**
