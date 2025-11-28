# Diagnóstico: Por que mensagens não são disparadas

## ✅ STATUS DO SISTEMA

### Dados encontrados:
- **18 boletos pendentes** (cliente_nexus_id=2)
- **PDFs existem** na pasta Canopus
- **7 clientes COM WhatsApp válido**
- **11 clientes SEM WhatsApp** ou com número incompleto

## ❌ PROBLEMAS IDENTIFICADOS

### 1. Clientes sem WhatsApp (11 casos)
```
ID: 1198 | ADILSON EVANGELISTA DA SILVA | WhatsApp: (vazio)
ID: 1222 | EDUARDO JOSE MENDONCA JUNIOR | WhatsApp: (vazio)
ID: 1200 | GABRIEL DE OLIVEIRA BORGES | WhatsApp: (vazio)
+ 8 outros
```

### 2. WhatsApp mal formatados (3 casos)
```
ID: 518 | ZACARIAS DOS SANTOS ARCANJO | WhatsApp: 556793265 (incompleto)
ID: 510 | SERGIO CANDIDO DE ARAUJO | WhatsApp: 55679901133 (falta 1 dígito)
```

### 3. Query muito restritiva
**Localização**: `backend/routes/crm.py` linhas 1273-1294 e 1497-1518

```python
# Query atual (elimina clientes sem WhatsApp)
WHERE b.cliente_nexus_id = %s
AND b.status_envio = 'nao_enviado'
AND cf.whatsapp IS NOT NULL    ← Elimina 11 clientes
AND cf.whatsapp != ''           ← Elimina clientes sem número
AND cf.ativo = true
```

**Resultado**: Sistema não dispara para 11 clientes porque não têm WhatsApp cadastrado.

## 🎯 SOLUÇÕES

### SOLUÇÃO 1: Cadastrar WhatsApp dos clientes (RECOMENDADO)
Use a interface CRM para adicionar o WhatsApp dos 11 clientes:

```
1. Acesse: http://localhost:5000/clientes-finais
2. Clique em cada cliente sem WhatsApp
3. Adicione o número no formato: 5567999999999
4. Sistema irá normalizar automaticamente
```

### SOLUÇÃO 2: Script automático de correção
Execute o script de correção de WhatsApp:

```bash
cd D:\Nexus\backend\scripts
python normalizar_todos_whatsapp.py
```

### SOLUÇÃO 3: Buscar telefones da base
Se os clientes têm telefone celular cadastrado, use-o como WhatsApp:

```sql
-- Copiar telefone_celular para whatsapp (se vazio)
UPDATE clientes_finais
SET whatsapp = telefone_celular
WHERE (whatsapp IS NULL OR whatsapp = '')
AND telefone_celular IS NOT NULL
AND telefone_celular != '';
```

## 📊 ESTATÍSTICAS

### Boletos por status:
- ✅ **7 boletos prontos** (cliente COM WhatsApp válido)
- ⚠️ **11 boletos bloqueados** (cliente SEM WhatsApp)
- 📱 **Taxa de cobertura: 38.9%** (7/18)

### Taxa de sucesso esperada:
- **Cenário atual**: 7 disparos (38.9%)
- **Após cadastrar WhatsApp**: 18 disparos (100%)

## 🔍 COMO TESTAR O DISPARO

### Teste 1: Verificar boletos prontos
```bash
cd D:\Nexus\backend\scripts
python verificar_boletos_para_disparo.py
```

### Teste 2: Executar disparo manual (CRM)
```
1. Acesse: http://localhost:5000
2. Login com cliente_nexus_id=2
3. Menu: "Disparo Automático"
4. Botão: "Executar Disparo Agora"
```

### Teste 3: Verificar WPPConnect rodando
```bash
# O servidor WPPConnect deve estar rodando na porta 3001
curl http://localhost:3001/status
```

## 📝 ARQUIVOS RELEVANTES

### Backend:
- `backend/routes/crm.py` - Rotas de disparo (linhas 1265-1693)
- `backend/services/whatsapp_service.py` - Serviço de envio
- `backend/services/mensagens_personalizadas.py` - Mensagens aleatórias

### Query de disparo:
```python
# backend/routes/crm.py:1273 e 1497
boletos_reais = db.execute_query("""
    SELECT b.*, cf.nome_completo, cf.whatsapp
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.cliente_nexus_id = %s
    AND b.status_envio = 'nao_enviado'
    AND cf.whatsapp IS NOT NULL    ← FILTRO AQUI
    AND cf.whatsapp != ''           ← FILTRO AQUI
    AND cf.ativo = true
""", (cliente_nexus_id,))
```

## ✨ PRÓXIMOS PASSOS

1. **Imediato**: Cadastrar WhatsApp dos 11 clientes sem número
2. **Curto prazo**: Corrigir números mal formatados (ZACARIAS, SERGIO)
3. **Médio prazo**: Implementar validação de WhatsApp no cadastro
4. **Longo prazo**: Dashboard com alertas de clientes sem WhatsApp

## 💡 DICA EXTRA

O sistema usa **mensagens personalizadas aleatórias** (10 variações) para parecer mais humano e evitar bloqueio do WhatsApp. Veja em:
- `backend/services/mensagens_personalizadas.py:68-207`
