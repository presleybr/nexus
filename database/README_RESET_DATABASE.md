# 🔄 Scripts de Reset e Backup do Banco de Dados

Este diretório contém scripts para resetar o banco de dados mantendo as sessões WhatsApp.

## 📋 Scripts Disponíveis

### 1. `reset_database_with_whatsapp_backup.py` ⭐ PRINCIPAL

**O que faz:**
- ✅ Faz backup de todas as sessões WhatsApp
- ✅ Reseta COMPLETAMENTE o banco de dados
- ✅ Recria todas as tabelas do schema.sql
- ✅ Restaura as sessões WhatsApp

**Quando usar:**
- Quando você quer começar do zero com o banco limpo
- Para testes iniciais do sistema
- Para distribuir o sistema zerado mas com WhatsApp já conectado

**Como usar:**
```bash
cd D:\Nexus\database
python reset_database_with_whatsapp_backup.py
```

**⚠️ ATENÇÃO:**
Este script vai **APAGAR TODOS OS DADOS** exceto sessões WhatsApp:
- ❌ Usuários
- ❌ Clientes Nexus
- ❌ Clientes Finais
- ❌ Boletos
- ❌ Disparos
- ❌ Configurações
- ❌ Logs
- ❌ Consultores
- ❌ Pontos de venda
- ❌ Histórico
- ✅ Sessões WhatsApp (PRESERVADAS)

---

### 2. `backup_whatsapp_only.py` - Apenas Backup

**O que faz:**
- Faz backup das sessões WhatsApp em arquivo JSON com timestamp
- NÃO altera o banco de dados

**Quando usar:**
- Antes de fazer alterações importantes
- Para ter um backup preventivo
- Para manter histórico de sessões

**Como usar:**
```bash
python backup_whatsapp_only.py
```

**Arquivo gerado:**
`whatsapp_backup_YYYYMMDD_HHMMSS.json`

---

### 3. `restore_whatsapp_only.py` - Apenas Restauração

**O que faz:**
- Restaura sessões WhatsApp de um arquivo de backup
- Lista todos os backups disponíveis
- NÃO altera outros dados do banco

**Quando usar:**
- Para restaurar sessões de um backup antigo
- Após resetar manualmente o banco
- Para migrar sessões entre ambientes

**Como usar:**
```bash
python restore_whatsapp_only.py
```

O script vai:
1. Listar todos os backups disponíveis
2. Pedir para você escolher qual backup usar
3. Restaurar as sessões (ignorando duplicadas)

---

## 🎯 Cenários de Uso

### Cenário 1: Reset completo do sistema (MAIS COMUM)

```bash
# Um único comando faz tudo
python reset_database_with_whatsapp_backup.py
```

Este é o cenário que você quer: banco zerado mas com WhatsApp funcionando.

---

### Cenário 2: Backup preventivo antes de mudanças

```bash
# Faz backup antes de alterar algo importante
python backup_whatsapp_only.py

# Se algo der errado, restaura
python restore_whatsapp_only.py
```

---

### Cenário 3: Reset manual do banco

```bash
# 1. Faz backup primeiro
python backup_whatsapp_only.py

# 2. Reseta manualmente o banco (via pgAdmin ou psql)
# ... executa DROP DATABASE / CREATE DATABASE ...

# 3. Restaura as sessões
python restore_whatsapp_only.py
```

---

## 📁 Arquivos de Backup

Os backups são salvos como arquivos JSON:

```json
[
  {
    "id": 1,
    "cliente_nexus_id": null,
    "instance_name": "nexus_whatsapp",
    "phone_number": "5567999887766",
    "status": "connected",
    "qr_code": null,
    "session_data": {...},
    "connected_at": "2025-01-15T10:30:00",
    "provider": "baileys",
    ...
  }
]
```

**Localização:**
- Backups automáticos: `whatsapp_sessions_backup.json`
- Backups manuais: `whatsapp_backup_YYYYMMDD_HHMMSS.json`

**💡 Dica:** Guarde esses arquivos de backup! Você pode precisar deles.

---

## ⚙️ Configurações do Banco

Os scripts usam estas configurações (de `DB_CONFIG`):

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'dbname': 'nexus_crm',
    'user': 'postgres',
    'password': 'nexus2025'
}
```

Se suas configurações forem diferentes, edite os scripts antes de executar.

---

## 🔒 Segurança

**IMPORTANTE:**
- ⚠️ Sempre confirme que você quer resetar o banco
- ⚠️ Mantenha backups dos arquivos JSON em local seguro
- ⚠️ Não compartilhe os arquivos de backup (contêm dados sensíveis)
- ⚠️ Execute estes scripts apenas em desenvolvimento/testes

---

## ✅ Checklist antes de Resetar

Antes de executar `reset_database_with_whatsapp_backup.py`:

- [ ] Tenho certeza que quero apagar todos os dados?
- [ ] Fiz backup manual de dados importantes (se necessário)?
- [ ] Estou executando no banco correto (nexus_crm)?
- [ ] As sessões WhatsApp estão conectadas e funcionando?
- [ ] Tenho o arquivo `schema.sql` no diretório?

---

## 🆘 Problemas Comuns

### Erro: "Não foi possível conectar ao banco"
- Verifique se o PostgreSQL está rodando na porta 5434
- Verifique usuário e senha em DB_CONFIG

### Erro: "schema.sql não encontrado"
- Coloque o arquivo schema.sql no mesmo diretório dos scripts
- Caminho: `D:\Nexus\database\schema.sql`

### Backup vazio (0 sessões)
- Normal se você ainda não conectou nenhum WhatsApp
- O script vai continuar e resetar o banco normalmente

### Sessão não restaurada
- Verifique se a tabela `cliente_nexus_id` tem o ID correto
- Se `cliente_nexus_id` não existir mais, a sessão ficará sem vínculo (OK)

---

## 📞 Próximos Passos Após Reset

Depois de resetar o banco com `reset_database_with_whatsapp_backup.py`:

1. ✅ **Criar usuário admin:**
   ```python
   # Execute via Python ou crie manualmente no banco
   INSERT INTO usuarios (email, password_hash, tipo, ativo)
   VALUES ('admin@nexus.com', 'hash_aqui', 'admin', true);
   ```

2. ✅ **Criar cliente Nexus** (empresa que vai usar o sistema)

3. ✅ **Importar clientes finais** (via planilha ou API)

4. ✅ **Testar WhatsApp** - As sessões devem continuar funcionando!

5. ✅ **Configurar automações** conforme necessário

---

## 📊 Log de Execução

Exemplo de saída do `reset_database_with_whatsapp_backup.py`:

```
============================================================
🚨 RESET DO BANCO DE DADOS COM BACKUP WHATSAPP 🚨
============================================================

⚠️  ATENÇÃO: Este script vai:
  1. Fazer backup das sessões WhatsApp
  2. APAGAR TODOS OS DADOS do banco de dados
  ...

⚠️  Tem certeza absoluta que deseja continuar? (digite 'SIM TENHO CERTEZA' para confirmar): SIM TENHO CERTEZA

============================================================
📦 ETAPA 1: BACKUP DAS SESSÕES WHATSAPP
============================================================
✅ Backup concluído: 1 sessão(ões) salva(s)
📄 Arquivo: D:\Nexus\database\whatsapp_sessions_backup.json

📊 Resumo do backup:
  🟢 nexus_whatsapp - 5567999887766 (connected)

============================================================
🔄 ETAPA 2: RESETANDO BANCO DE DADOS
============================================================
⚠️  Dropando todas as tabelas...
  🗑️  Dropando usuarios...
  🗑️  Dropando clientes_nexus...
  ...
✅ Tabelas, views e funções dropadas com sucesso

📝 Executando schema.sql...
✅ Schema criado com sucesso!

============================================================
♻️  ETAPA 3: RESTAURANDO SESSÕES WHATSAPP
============================================================
  🟢 Restaurado: nexus_whatsapp - 5567999887766

✅ Restauração concluída!
  📊 Total restaurado: 1

============================================================
✅ PROCESSO CONCLUÍDO COM SUCESSO!
============================================================

📋 Próximos passos:
  1. O banco de dados foi resetado
  2. As sessões WhatsApp foram preservadas
  3. Você pode importar novos clientes e dados
  4. As sessões WhatsApp continuarão funcionando

💾 Backup salvo em: whatsapp_sessions_backup.json
   (Guarde este arquivo caso precise restaurar no futuro)

✅ Sistema pronto para uso!
```

---

## 🎓 Resumo Rápido

**Para resetar o banco AGORA mantendo WhatsApp:**

```bash
cd D:\Nexus\database
python reset_database_with_whatsapp_backup.py
# Digite: SIM TENHO CERTEZA
```

Pronto! Banco zerado, WhatsApp funcionando. 🎉
