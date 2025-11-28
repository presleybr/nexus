# Teste de Disparos com Boletos Reais

## O que foi implementado

O endpoint de teste agora envia **boletos reais dos primeiros 11 clientes** para os **11 números de teste fake**, simulando um disparo real completo com:

✅ Mensagem personalizada do boleto
✅ Arquivo PDF do boleto anexado
✅ Intervalos entre disparos (3-7s)
✅ Atualização do status do boleto para "enviado"

---

## Como funciona

### Fluxo do Teste

1. **Busca**: O sistema busca os 11 primeiros boletos pendentes com PDFs válidos
2. **Atribuição**: Cada boleto é atribuído a um número de teste diferente
3. **Disparo Completo**:
   - Envia mensagem personalizada com dados do cliente e boleto
   - Aguarda 2 segundos
   - Envia o PDF do boleto como anexo
   - Aguarda intervalo aleatório (3-7s) antes do próximo
4. **Atualização**: Marca o boleto como "enviado" no banco

### Números de Teste Utilizados

```
5567931224813  →  Cliente 1
5567996376010  →  Cliente 2
5567915342531  →  Cliente 3
5567911629169  →  Cliente 4
5567954436309  →  Cliente 5
5567991478669  →  Cliente 6
5567935799810  →  Cliente 7
5567903377105  →  Cliente 8
5567918669257  →  Cliente 9
5567940544573  →  Cliente 10
5567996600884  →  Cliente 11 (número real do sócio)
```

---

## Como Testar

### Opção 1: Via Frontend (Navegador)

1. Acesse: `http://127.0.0.1:5000/crm/disparos`
2. Clique no botão **"Executar Teste"** ou **"Disparar Teste"**
3. Aguarde o processamento (pode levar 1-2 minutos)
4. Verifique os resultados no console do backend

### Opção 2: Via cURL (Terminal)

```bash
curl -X POST http://127.0.0.1:5000/api/crm/scheduler/executar-agora \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<sua_sessao>" \
  -d '{"modo_teste": true}'
```

### Opção 3: Via Postman/Insomnia

**Endpoint:** `POST http://127.0.0.1:5000/api/crm/scheduler/executar-agora`

**Headers:**
```
Content-Type: application/json
Cookie: session=<sua_sessao>
```

**Body:**
```json
{
  "modo_teste": true
}
```

---

## Logs de Acompanhamento

Durante o teste, você verá logs detalhados no console do backend:

```
[TESTE] Buscando boletos pendentes para teste...
[TESTE] Encontrados 11 boletos para enviar

[TESTE] ===== Boleto 1/11 =====
[TESTE] Cliente: JEFFERSON DOURADO MENDES
[TESTE] Número fake: 5567931224813
[TESTE] Boleto ID: 123
[TESTE] Mensagem: Olá JEFFERSON! Tudo bem? Segue em anexo seu boleto...
[TESTE] Enviando mensagem de texto...
[TESTE] ✅ Mensagem enviada
[TESTE] Enviando PDF...
[TESTE] ✅ PDF enviado
[TESTE] Aguardando 5s até próximo envio...

[TESTE] ===== Boleto 2/11 =====
...
```

---

## Resposta da API

### Sucesso (200)

```json
{
  "success": true,
  "message": "Teste concluído: 11 boletos enviados, 0 erros",
  "stats": {
    "total": 11,
    "enviados": 11,
    "erros": 0,
    "numeros_testados": [
      "5567931224813",
      "5567996376010",
      ...
    ],
    "detalhes": [
      {
        "numero": "5567931224813",
        "cliente": "JEFFERSON DOURADO MENDES",
        "boleto_id": 123,
        "status": "sucesso"
      },
      ...
    ]
  }
}
```

### Erro (400/500)

```json
{
  "success": false,
  "message": "Nenhum boleto pendente encontrado para teste"
}
```

---

## Verificações Pós-Teste

### 1. Verificar Boletos Enviados no Banco

```sql
SELECT
    b.id,
    b.numero_boleto,
    cf.nome_completo,
    b.status_envio,
    b.data_envio,
    b.enviado_por
FROM boletos b
JOIN clientes_finais cf ON b.cliente_final_id = cf.id
WHERE b.enviado_por = 'TESTE_CRM'
ORDER BY b.data_envio DESC;
```

### 2. Verificar no WhatsApp Web

- Acesse o WhatsApp Web conectado
- Procure pelas conversas com os números de teste
- Você verá as mensagens e PDFs enviados

### 3. Verificar Logs do Backend

Procure por `[TESTE]` nos logs para ver o fluxo completo.

---

## Importante

### ⚠️ Atenção

- Os boletos enviados no teste serão marcados como **"enviados"** no banco
- Isso significa que eles **não aparecerão** mais na lista de pendentes
- Se quiser testar novamente, você precisará:
  - Resetar os status dos boletos para "nao_enviado"
  - Ou importar novos boletos

### 🔄 Resetar Boletos para Novo Teste

Se quiser fazer outro teste, execute:

```sql
UPDATE boletos
SET status_envio = 'nao_enviado',
    data_envio = NULL,
    enviado_por = NULL
WHERE enviado_por = 'TESTE_CRM';
```

---

## Diferenças do Teste Anterior

### ❌ Teste Antigo (Apenas Mensagens)
- Enviava apenas mensagens de texto simples
- Usava números aleatórios fake
- Não enviava PDFs
- Não atualizava status de boletos

### ✅ Teste Novo (Boletos Completos)
- ✅ Envia mensagem personalizada com dados reais
- ✅ Envia PDF do boleto como anexo
- ✅ Usa dados de clientes reais
- ✅ Atualiza status dos boletos
- ✅ Simula fluxo completo de produção

---

## Próximos Passos

1. ✅ **Execute o teste** via frontend ou API
2. 📊 **Verifique os logs** para garantir que tudo funcionou
3. 💬 **Confira o WhatsApp Web** para ver as mensagens e PDFs
4. 🔄 **Se necessário**, resete os boletos para testar novamente
5. 🚀 **Quando estiver pronto**, use o modo normal (sem `modo_teste: true`)

---

## Troubleshooting

### Erro: "Nenhum boleto pendente encontrado"

**Causa**: Não há boletos com `status_envio = 'nao_enviado'`

**Solução**:
```sql
-- Verificar quantos boletos pendentes existem
SELECT COUNT(*) FROM boletos WHERE status_envio = 'nao_enviado';

-- Se for 0, resetar alguns boletos
UPDATE boletos
SET status_envio = 'nao_enviado'
WHERE id IN (SELECT id FROM boletos ORDER BY created_at DESC LIMIT 11);
```

### Erro: "PDF não encontrado"

**Causa**: O caminho do PDF no banco não corresponde ao arquivo físico

**Solução**:
```bash
# Verificar se os PDFs existem
cd D:\Nexus
python -c "
import os
from backend.models.database import db

boletos = db.execute_query('SELECT id, pdf_path FROM boletos LIMIT 10')
for b in boletos:
    exists = os.path.exists(b['pdf_path'])
    print(f\"Boleto {b['id']}: {b['pdf_path']} - {'OK' if exists else 'FALTANDO'}\")
"
```

### Erro: "Erro ao enviar mensagem/PDF"

**Causa**: Servidor WhatsApp não está rodando ou não está conectado

**Solução**:
1. Verifique se o servidor WhatsApp está rodando: `http://localhost:3001/status`
2. Verifique se o WhatsApp Web está conectado
3. Reinicie o servidor se necessário

---

## Suporte

**Arquivos Relacionados:**
- `backend/routes/crm.py` - Endpoint de teste (linha 1144-1354)
- `backend/scripts/vincular_whatsapp_teste.py` - Script de vinculação de números
- `backend/services/mensagens_personalizadas.py` - Gerador de mensagens

**Logs:**
- Console do backend (stdout)
- `backend/logs/` (se configurado)

**Contato:**
- Verifique os logs primeiro
- Use o console do navegador (F12) para erros de frontend
- Verifique o status do WhatsApp Web
