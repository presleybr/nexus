# ⚡ Guia Rápido de Início - Nexus CRM

## 🚀 5 Minutos para Começar

### Pré-requisitos
- ✅ Python 3.10+ instalado
- ✅ PostgreSQL instalado e rodando
- ✅ Terminal/PowerShell aberto em `D:\Nexus`

---

## 📝 Passo a Passo

### 1️⃣ Instalar Dependências (1 min)

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Instalar pacotes
pip install -r backend/requirements.txt
```

### 2️⃣ Configurar Banco de Dados (30 seg)

Edite o arquivo `.env` e configure sua senha do PostgreSQL:

```env
DB_PASSWORD=sua_senha_postgres_aqui
```

### 3️⃣ Inicializar Sistema (2 min)

```bash
# Inicia o sistema (cria banco, popula dados, inicia Flask)
python start.py
```

Quando perguntado "Deseja popular com dados fake?", digite: **s**

### 4️⃣ Acessar o Sistema (30 seg)

Abra seu navegador em: **http://localhost:5000**

### 5️⃣ Fazer Login (30 seg)

Use um dos usuários de teste:

**Cliente:**
- Email: `empresa1@nexus.com`
- Senha: `empresa123`

**Admin:**
- Email: `admin@nexus.com`
- Senha: `admin123`

---

## 🎯 Primeiros Passos no Sistema

### 1. Cadastrar um Cliente
1. Clique em "Clientes" no menu
2. Preencha o formulário
3. Clique em "Cadastrar Cliente"

### 2. Gerar Boletos
1. Vá para "Disparos"
2. Clique em "Gerar Boletos"
3. Aguarde a geração

### 3. Conectar WhatsApp
1. Vá para "WhatsApp"
2. Clique em "Gerar QR Code"
3. Escaneie com seu WhatsApp
4. Confirme a conexão

### 4. Enviar Boletos
1. Vá para "Disparos"
2. Clique em "Iniciar Automação"
3. Acompanhe o progresso

---

## 📊 Dados Fake Incluídos

Após executar `seed_data.py`, você terá:

- **3 empresas** cadastradas
- **~50 clientes finais** distribuídos
- **~200 boletos** com status variados
- **1 admin** para gerenciamento

### Logins de Teste:

| Usuário | Email | Senha |
|---------|-------|-------|
| Empresa 1 | empresa1@nexus.com | empresa123 |
| Empresa 2 | empresa2@nexus.com | empresa223 |
| Empresa 3 | empresa3@nexus.com | empresa323 |
| Admin | admin@nexus.com | admin123 |

---

## 🔧 Comandos Úteis

### Reiniciar Banco de Dados
```bash
python database/init_db.py
python database/seed_data.py
```

### Iniciar Apenas o Servidor
```bash
python backend/app.py
```

### Gerar Boletos Via Script
```bash
python automation/boleto_generator.py
```

### Executar Automação Completa
```bash
python automation/whatsapp_dispatcher.py
```

---

## ❓ Problemas Comuns

### "PostgreSQL não está acessível"
**Solução:** Inicie o serviço PostgreSQL
- Windows: Abra "Serviços" e inicie "postgresql"
- Linux: `sudo systemctl start postgresql`

### "Módulo não encontrado"
**Solução:** Ative o ambiente virtual
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### "Porta 5000 já em uso"
**Solução:** Altere a porta no `.env`
```env
FLASK_PORT=8080
```

---

## 📁 Estrutura de Pastas

Após iniciar, você verá:

```
D:\Nexus\
├── boletos/               # PDFs gerados aparecem aqui
├── logs/                  # Logs do sistema
├── whatsapp_sessions/     # Sessões WhatsApp
└── (resto dos arquivos)
```

---

## 🎓 Próximos Passos

1. ✅ Explore o Dashboard
2. ✅ Cadastre seus próprios clientes
3. ✅ Gere boletos personalizados
4. ✅ Configure mensagens anti-bloqueio
5. ✅ Execute a automação completa

---

## 📚 Documentação Completa

- **README.md** - Documentação geral
- **docs/MANUAL.md** - Manual das 33 etapas
- **Código comentado** - Todo código está documentado

---

## 🆘 Suporte

Encontrou um problema?

1. Verifique os logs no terminal
2. Consulte o README.md
3. Leia o MANUAL.md
4. Verifique os comentários no código

---

**🎉 Pronto! Você já pode usar o Nexus CRM!**

*Aqui seu tempo vale ouro ⏱️*
