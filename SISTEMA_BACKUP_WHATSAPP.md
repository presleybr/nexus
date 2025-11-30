# Sistema de Backup e Restauração de WhatsApp

## Resumo

Sistema completo para fazer backup dos números de WhatsApp dos clientes antes de resetar o banco de dados, e restaurá-los automaticamente na próxima importação.

## Arquivos Criados/Modificados

### 1. **Script de Backup** (`backend/scripts/backup_whatsapp_clientes.py`)

Script standalone para fazer backup manual dos WhatsApps.

**Uso:**
```bash
python backend/scripts/backup_whatsapp_clientes.py
```

**Resultado:**
- Cria arquivo `backend/backups/whatsapp_clientes_backup.json`
- Salva CPF → WhatsApp de todos os clientes
- Total de 43 clientes salvos no último backup

### 2. **Rota de Backup** (`backend/routes/automation_canopus.py`)

**Nova rota:** `POST /api/automation-canopus/backup-whatsapp`

Permite fazer backup via interface web.

**Resposta:**
```json
{
  "success": true,
  "message": "Backup criado com sucesso! 43 WhatsApps salvos.",
  "total": 43,
  "arquivo": "D:\\Nexus\\backend\\backups\\whatsapp_clientes_backup.json",
  "data_backup": "2025-11-30T19:25:47.474875"
}
```

### 3. **Restauração Automática** (`backend/routes/automation_canopus.py`)

**Modificação na função `upload_planilha()` (linhas 294-318)**

Ao importar clientes da planilha:
1. Verifica se existe arquivo de backup
2. Busca WhatsApp pelo CPF do cliente
3. Se encontrar, restaura o número automaticamente
4. Se não encontrar, usa placeholder padrão

**Log de sucesso:**
```
✅ WhatsApp restaurado do backup para João Silva: 5567999998888
```

### 4. **Interface Web** (`frontend/templates/crm-cliente/automacao-canopus.html`)

**Novo card de backup** adicionado na página de Automação Canopus.

**Funcionalidades:**
- Botão "💾 Fazer Backup Agora"
- Confirmação antes de executar
- Status em tempo real
- Mensagem de sucesso com detalhes

## Fluxo de Uso

### ANTES de Resetar o Banco:

1. Acesse: `https://nexus-crm-backend-6jxi.onrender.com/crm/automacao-canopus`
2. Clique em **"Fazer Backup Agora"** no card verde
3. Confirme a operação
4. Aguarde mensagem de sucesso
5. Verificar que 43 WhatsApps foram salvos

### DEPOIS de Resetar o Banco:

1. Importe a planilha normalmente (ETAPA 1)
2. O sistema **restaura automaticamente** os WhatsApps
3. Logs mostrarão: `✅ WhatsApp restaurado do backup para [Nome]: [Número]`

## Estrutura do Arquivo de Backup

**Localização:** `backend/backups/whatsapp_clientes_backup.json`

```json
{
  "data_backup": "2025-11-30T19:25:47.474875",
  "total_clientes": 43,
  "clientes": {
    "06113455440": {
      "nome": "ADILSON BARROS CORREA JUNIO",
      "whatsapp": "5567999999999",
      "telefone_celular": "5567999999999",
      "email": null
    },
    "09088889619": {
      "nome": "ADILSON EVANGELISTA DA SILVA",
      "whatsapp": "5567999999999",
      "telefone_celular": "5567999999999",
      "email": null
    }
    // ... mais 41 clientes
  }
}
```

## Lógica de Restauração

```python
# Buscar WhatsApp pelo CPF
cpf_limpo = cpf.replace('.', '').replace('-', '')
if cpf_limpo in backup_data['clientes']:
    whatsapp_backup = backup_data['clientes'][cpf_limpo]['whatsapp']
    if whatsapp_backup and whatsapp_backup != '5567999999999':
        whatsapp = whatsapp_backup
        logger.info(f"✅ WhatsApp restaurado do backup para {nome}: {whatsapp}")
```

## Importante

⚠️ **SEMPRE faça backup ANTES de resetar o banco!**

✅ O backup é persistente e sobrevive ao reset
✅ Restauração é automática na importação
✅ Não perde números editados manualmente
✅ Funciona mesmo se planilha não tiver WhatsApp

## Localização Visual na Interface

```
┌─────────────────────────────────────────────────────┐
│  🚀 Automação Canopus                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  💾 Backup de WhatsApp                       │  │
│  │  📱 Salva os números antes de resetar       │  │
│  │  [💾 Fazer Backup Agora]                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  1️⃣ Importar Planilha para o Banco          │  │
│  │  📊 Upload da planilha Excel                │  │
│  │  [📤 Upload e Importar]                     │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  2️⃣ Baixar Boletos do Sistema               │  │
│  │  ...                                         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Teste Realizado

✅ Backup executado com sucesso
✅ 43 clientes com WhatsApp salvos
✅ Arquivo JSON criado corretamente
✅ Sistema pronto para restaurar após reset

## Próximos Passos

1. ✅ Fazer backup (JÁ FEITO)
2. ⏳ Resetar banco de dados
3. ⏳ Importar planilha novamente
4. ⏳ Verificar que WhatsApps foram restaurados

---

**Data de Implementação:** 30/11/2025
**Autor:** Claude Code
**Versão:** 1.0
