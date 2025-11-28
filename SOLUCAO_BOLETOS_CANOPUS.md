# Solução: Disparos com Boletos REAIS do Canopus

## Problema Identificado

Os disparos de teste estavam enviando boletos **fake/antigos** (`boleto.pdf`) em vez dos boletos **REAIS do Canopus** (`CLIENTE_NOME_NOVEMBRO.pdf`).

## Causa Raiz

1. ❌ Boletos do Canopus não tinham `cliente_nexus_id` definido (estava NULL)
2. ❌ Boletos do Canopus estavam marcados como "enviados" de testes anteriores
3. ❌ Query não filtrava apenas boletos do Canopus

## Solução Implementada

### 1. Filtro na Query (crm.py:1197)

Adicionado filtro para garantir que APENAS boletos do Canopus sejam enviados:

```sql
AND b.pdf_path LIKE '%canopus%'
AND b.pdf_filename IS NOT NULL
```

### 2. Vinculação ao Cliente Nexus

Todos os 36 boletos do Canopus foram vinculados ao Cliente Nexus ID 2 (Tech Solutions Ltda):

```bash
python backend/scripts/vincular_boletos_canopus_cliente.py
```

### 3. Reset de Status

Boletos do Canopus foram resetados para `status_envio = 'nao_enviado'`:

```bash
python backend/scripts/resetar_boletos_canopus.py
```

### 4. Logs Detalhados (crm.py:1242-1243)

Adicionados logs mostrando o nome do arquivo sendo enviado:

```python
print(f"[TESTE] PDF Filename: {boleto_info['pdf_filename']}")
print(f"[TESTE] PDF Path: {boleto_info['pdf_path']}")
```

---

## Scripts Criados

### 1. `verificar_pdfs_canopus.py`
Verifica se os PDFs dos boletos do Canopus existem fisicamente.

```bash
cd D:\Nexus\backend
python scripts/verificar_pdfs_canopus.py
```

### 2. `testar_query_boletos.py`
Testa a query SQL e mostra quais boletos serão enviados no teste.

```bash
cd D:\Nexus\backend
python scripts/testar_query_boletos.py
```

### 3. `resetar_boletos_canopus.py`
Reseta o status dos boletos do Canopus para permitir novos testes.

```bash
cd D:\Nexus\backend
python scripts/resetar_boletos_canopus.py
```

### 4. `vincular_boletos_canopus_cliente.py`
Vincula os boletos do Canopus a um cliente Nexus.

```bash
cd D:\Nexus\backend
python scripts/vincular_boletos_canopus_cliente.py
```

---

## Resultado Final

### ✅ Boletos que SERÃO enviados agora:

```
1. ZACARIAS_DOS_SANTOS_ARCANJO_IMOVEL_NOVEMBRO.pdf (171.3KB)
2. DIEGO_VICTOR_LINO_NOVEMBRO.pdf (171.8KB)
3. ADILSON_BARROS_CORREA_JUNIO_NOVEMBRO.pdf (172.1KB)
4. VANDERSON_SANTANA_NOVEMBRO.pdf (171.0KB)
5. VICTOR_WANDER_GOMES_DIAS_NOVEMBRO.pdf (172.2KB)
6. ANTONIO_DOS_SANTOS_SOBRINHO_JUNIOR_NOVEMBRO.pdf (171.1KB)
7. VICTOR_AUGUSTO_E_SILVA_NOVEMBRO.pdf (171.3KB)
8. ALLAN_DA_COSTA_ARAUJO_NOVEMBRO.pdf (171.2KB)
9. LUCAS_ROBERTO_RODRIGUES_HAAK_NOVEMBRO.pdf (171.6KB)
10. LENILDA_DA_SILVA_NOVEMBRO.pdf (171.3KB)
11. WESLEY_JUNIOR_DIDEROT_CHERISCAR_NOVEMBRO.pdf (172.4KB)
```

**Todos os arquivos:**
- ✅ Existem fisicamente em `D:\Nexus\automation\canopus\downloads\Danner\`
- ✅ São boletos REAIS baixados pela automação Canopus
- ✅ Têm o nome do cliente no arquivo
- ✅ Estão vinculados ao Cliente Nexus ID 2
- ✅ Têm status `nao_enviado` (prontos para teste)

---

## Como Testar AGORA

### Opção 1: Via Frontend

```
http://127.0.0.1:5000/crm/disparos
```

Clique em "Executar Teste" ou "Disparar Teste"

### Opção 2: Via cURL

```bash
curl -X POST http://127.0.0.1:5000/api/crm/scheduler/executar-agora \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<sua_sessao>" \
  -d '{"modo_teste": true}'
```

### O que vai acontecer:

1. ✅ Busca os 11 primeiros boletos do Canopus (listados acima)
2. ✅ Atribui um número fake para cada cliente
3. ✅ Envia mensagem personalizada com dados do cliente
4. ✅ Envia PDF REAL do Canopus (171-172KB cada)
5. ✅ Marca boleto como "enviado" no banco

### Logs que você verá:

```
[TESTE] Buscando boletos pendentes para teste...
[TESTE] Encontrados 11 boletos para enviar

[TESTE] ===== Boleto 1/11 =====
[TESTE] Cliente: ZACARIAS DOS SANTOS ARCANJO IMOVEL
[TESTE] Número fake: 5567931224813
[TESTE] Boleto ID: 107
[TESTE] PDF Filename: ZACARIAS_DOS_SANTOS_ARCANJO_IMOVEL_NOVEMBRO.pdf
[TESTE] PDF Path: D:\Nexus\automation\canopus\downloads\Danner\ZACARIAS_DOS_SANTOS_ARCANJO_IMOVEL_NOVEMBRO.pdf
[TESTE] Mensagem: Olá ZACARIAS! ...
[TESTE] Enviando mensagem de texto...
[TESTE] ✅ Mensagem enviada
[TESTE] Enviando PDF...
[TESTE] ✅ PDF enviado
```

---

## Mapeamento Cliente → Número Fake

```
5567931224813 → ZACARIAS DOS SANTOS ARCANJO IMOVEL
5567996376010 → DIEGO VICTOR LINO
5567915342531 → ADILSON BARROS CORREA JUNIO
5567911629169 → VANDERSON SANTANA
5567954436309 → VICTOR WANDER GOMES DIAS
5567991478669 → ANTONIO DOS SANTOS SOBRINHO JUNIOR
5567935799810 → VICTOR AUGUSTO E SILVA
5567903377105 → ALLAN DA COSTA ARAUJO
5567918669257 → LUCAS ROBERTO RODRIGUES HAAK
5567940544573 → LENILDA DA SILVA
5567996600884 → WESLEY JUNIOR DIDEROT CHERISCAR (número real do sócio)
```

---

## Resetar para Novo Teste

Se quiser testar novamente depois:

```bash
cd D:\Nexus\backend
python scripts/resetar_boletos_canopus.py
```

Ou via SQL direto:

```sql
UPDATE boletos
SET status_envio = 'nao_enviado',
    data_envio = NULL,
    enviado_por = NULL
WHERE pdf_path LIKE '%canopus%';
```

---

## Remover Boletos Fake/Antigos (Opcional)

Se quiser limpar os boletos fake antigos do banco:

```sql
DELETE FROM boletos
WHERE pdf_path NOT LIKE '%canopus%'
AND pdf_filename IS NULL;
```

Isso vai remover ~50 boletos fake que não são mais necessários.

---

## Arquivos Modificados

1. `backend/routes/crm.py:1197-1199` - Filtro para boletos do Canopus
2. `backend/routes/crm.py:1242-1243` - Logs detalhados com nome do arquivo
3. `backend/scripts/verificar_pdfs_canopus.py` - Script de verificação (novo)
4. `backend/scripts/testar_query_boletos.py` - Script de teste de query (novo)
5. `backend/scripts/resetar_boletos_canopus.py` - Script de reset (novo)
6. `backend/scripts/vincular_boletos_canopus_cliente.py` - Script de vinculação (novo)

---

## Verificações Finais

### ✅ Checklist

- [x] Boletos do Canopus vinculados ao cliente_nexus_id = 2
- [x] Boletos do Canopus com status "nao_enviado"
- [x] Query filtrando apenas boletos do Canopus
- [x] PDFs físicos existem na pasta
- [x] Nomes dos arquivos estão corretos (CLIENTE_NOME_NOVEMBRO.pdf)
- [x] Logs detalhados mostrando nome do arquivo
- [x] 11 boletos prontos para teste

---

## Está Tudo Pronto! 🚀

O sistema agora vai enviar os **boletos REAIS do Canopus** (com nome do cliente no arquivo) e não mais os boletos fake antigos!

Execute o teste e confira no WhatsApp Web os PDFs sendo enviados com os nomes corretos dos clientes! 📱✅
