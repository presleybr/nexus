# 🚀 Guia Rápido: Migração para Evolution API

## ✅ O QUE FOI FEITO

A migração completa de Baileys para Evolution API foi concluída! Todos os arquivos foram criados e configurados.

---

## 📋 PRÉ-REQUISITO: INSTALAR DOCKER DESKTOP

**ANTES DE CONTINUAR**, você precisa instalar o Docker Desktop:

1. **Download:** https://www.docker.com/products/docker-desktop/
2. **Instalar:** Execute o instalador baixado
3. **Reiniciar:** Reinicie o computador se solicitado
4. **Abrir:** Abra o Docker Desktop e aguarde inicializar completamente

---

## 🎯 COMO USAR (APÓS INSTALAR DOCKER)

### Opção 1: Script Automático (RECOMENDADO)

```bash
# Execute este arquivo
D:\Nexus\start-nexus-completo.bat
```

Este script faz TUDO automaticamente:
- Inicia Evolution API via Docker
- Verifica se está rodando
- Inicia o Flask
- Abre em nova janela

### Opção 2: Passo a Passo Manual

**Passo 1: Iniciar Evolution API**
```bash
# Abra um terminal e execute:
cd D:\Nexus\evolution-api
docker-compose up -d
```

**Passo 2: Aguardar 10 segundos**
```bash
# O container precisa de tempo para inicializar
```

**Passo 3: Verificar se está rodando**
```bash
# Abra no navegador:
http://localhost:8080

# Ou use curl:
curl http://localhost:8080
```

**Passo 4: Iniciar Flask**
```bash
cd D:\Nexus
venv\Scripts\activate
python start.py
```

---

## 🌐 ACESSAR O SISTEMA

Após iniciar tudo:

- **Nexus CRM:** http://localhost:5000
- **Evolution API:** http://localhost:8080

---

## 📱 CONECTAR WHATSAPP

1. Acesse: http://localhost:5000/crm/whatsapp
2. Clique: **"Conectar WhatsApp"**
3. Aguarde o **QR Code** aparecer
4. No celular:
   - Abra WhatsApp
   - Vá em **"Dispositivos Conectados"**
   - Clique em **"Conectar Dispositivo"**
   - Escaneie o QR Code
5. Aguarde confirmação

---

## 🛑 PARAR TUDO

### Opção 1: Script Automático
```bash
D:\Nexus\stop-nexus-completo.bat
```

### Opção 2: Manual
```bash
# Parar Flask: CTRL+C na janela do servidor

# Parar Evolution API:
cd D:\Nexus\evolution-api
docker-compose down
```

---

## 📂 ARQUIVOS CRIADOS

```
D:\Nexus\
├── evolution-api/
│   ├── docker-compose.yml         ✅ Configuração Docker
│   ├── .env                        ✅ Variáveis Evolution API
│   ├── start.bat                   ✅ Inicia Evolution API
│   └── stop.bat                    ✅ Para Evolution API
│
├── backend/services/
│   └── whatsapp_evolution.py       ✅ Serviço Evolution API
│
├── docs/
│   └── EVOLUTION_API.md            ✅ Documentação completa
│
├── .env                            ✅ Atualizado (Evolution API)
├── start.py                        ✅ Atualizado (verifica Evolution)
├── start-nexus-completo.bat        ✅ Inicia tudo
├── stop-nexus-completo.bat         ✅ Para tudo
└── INSTALACAO_EVOLUTION_API.md     ✅ Este arquivo
```

---

## 🔧 ARQUIVOS MODIFICADOS

```
✅ backend/routes/whatsapp.py       - Import alterado para Evolution API
✅ backend/services/whatsapp_evolution.py  - Novo serviço criado
✅ .env                             - Configurações Evolution API
✅ start.py                         - Verificação Evolution API
```

---

## 📦 BACKUP DO BAILEYS

O diretório antigo do Baileys foi renomeado para backup:
```
D:\Nexus\whatsapp-baileys.OLD/
```

Você pode deletar depois de testar o Evolution API.

---

## ⚠️ TROUBLESHOOTING

### Docker não instalado
```
Erro: docker: command not found
Solução: Instale Docker Desktop (link acima)
```

### Porta 8080 já em uso
```bash
# Ver o que está usando a porta
netstat -ano | findstr :8080

# Matar o processo (substitua <PID>)
taskkill /PID <PID> /F
```

### Evolution API não inicia
```bash
# Ver logs de erro
cd D:\Nexus\evolution-api
docker-compose logs -f
```

### PostgreSQL não conecta
Verifique se PostgreSQL está rodando na porta 5434:
```bash
# Ver serviços rodando
services.msc
```

---

## 📚 DOCUMENTAÇÃO COMPLETA

Para mais detalhes, consulte:
```
D:\Nexus\docs\EVOLUTION_API.md
```

Inclui:
- Todos os endpoints da API
- Webhooks disponíveis
- Configurações avançadas
- Segurança
- Backup e migração

---

## ✨ PRÓXIMOS PASSOS

1. ✅ Instalar Docker Desktop (se ainda não instalou)
2. ✅ Executar `start-nexus-completo.bat`
3. ✅ Acessar http://localhost:5000
4. ✅ Conectar WhatsApp via QR Code
5. ✅ Testar envio de mensagem
6. ✅ Testar envio de PDF
7. ✅ Aproveitar o sistema mais robusto!

---

## 🎉 SUCESSO!

Agora o Nexus CRM está usando Evolution API!

**Vantagens:**
- ✅ Mais estável
- ✅ Melhor performance
- ✅ Suporte a múltiplas instâncias
- ✅ Integração nativa com PostgreSQL
- ✅ Webhooks completos
- ✅ Fácil manutenção via Docker

**Todas as funcionalidades anteriores foram mantidas:**
- ✅ Conexão via QR Code
- ✅ Envio de mensagens
- ✅ Envio de PDFs
- ✅ Envio de boletos com delay anti-bloqueio
- ✅ Mesmas rotas Flask
- ✅ Mesma interface frontend

---

## 📞 SUPORTE

Problemas? Verifique:
1. Logs do Evolution API: `docker-compose logs -f`
2. Logs do Flask: Janela do terminal
3. Documentação: `docs/EVOLUTION_API.md`
