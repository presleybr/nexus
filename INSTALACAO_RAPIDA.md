# ⚡ Instalação Rápida - Nexus CRM

## 🚀 Passos para Rodar o Sistema

### 1️⃣ Instalar Dependências Python (IMPORTANTE)

```bash
# Ative o ambiente virtual (se ainda não ativou)
venv\Scripts\activate

# IMPORTANTE: Desinstale psycopg2 se estiver instalado
pip uninstall psycopg2 psycopg2-binary -y

# Instale as dependências corretas (psycopg versão 3)
pip install -r backend/requirements.txt
```

### 2️⃣ Configurar .env

O arquivo `.env` já está configurado com:
- PostgreSQL porta: **5434**
- Banco: **nexus_crm**
- Senha: **nexus2025**

### 3️⃣ Iniciar o Sistema

```bash
python start.py
```

O sistema irá:
1. ✅ Verificar PostgreSQL
2. ✅ Criar banco de dados (se não existir)
3. ✅ Criar todas as tabelas automaticamente
4. ❓ Perguntar se deseja popular com dados fake (digite **s**)
5. 🚀 Iniciar Flask em http://localhost:5000

### 4️⃣ Acessar o Sistema

Abra o navegador em: **http://localhost:5000**

**Login:**
- Email: `empresa1@nexus.com`
- Senha: `empresa123`

---

## 📋 O que foi corrigido:

✅ **Database.py** - Migrado para psycopg v3 (ConnectionPool)
✅ **schema.sql** - Schema simplificado com 8 tabelas
✅ **seed_data.py** - População automática com dados realistas
✅ **init_db.py** - Inicialização automática
✅ **start.py** - Verificação e criação automática de tabelas
✅ **requirements.txt** - psycopg[binary,pool]==3.1.18

---

## 🗄️ Tabelas Criadas Automaticamente:

1. **usuarios** - Login e autenticação
2. **clientes_nexus** - Empresas clientes da Nexus
3. **boletos** - Boletos gerados
4. **disparos** - Registro de disparos WhatsApp
5. **configuracoes_cliente** - Configurações personalizadas
6. **whatsapp_sessions** - Sessões WhatsApp
7. **logs_sistema** - Logs do sistema
8. **status_sistema** - Status geral

---

## 🔐 Logins Disponíveis (após popular):

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | admin@nexus.com | admin123 |
| Cliente | empresa1@nexus.com | empresa123 |
| Cliente | empresa2@nexus.com | empresa123 |
| Cliente | empresa3@nexus.com | empresa123 |

---

## 📊 Dados Fake Incluídos:

- **3 empresas** (Tech Solutions, Marketing Pro, Consultoria)
- **600 boletos** (200 por empresa)
- CPFs, telefones e nomes brasileiros realistas
- Status variados (pago, pendente, vencido, enviado)

---

## ⚠️ Troubleshooting:

### Erro: "No module named 'psycopg'"
**Solução:**
```bash
pip uninstall psycopg2 psycopg2-binary -y
pip install psycopg[binary,pool]==3.1.18
```

### Erro: "relation 'usuarios' does not exist"
**Solução:**
As tabelas serão criadas automaticamente ao rodar `python start.py`

### Erro: "PostgreSQL não está acessível"
**Solução:**
Verifique se o PostgreSQL está rodando na porta **5434**

---

**✅ Pronto! Sistema funcionando com tabelas criadas automaticamente!**
