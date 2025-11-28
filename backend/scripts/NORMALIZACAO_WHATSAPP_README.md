# Normalização de WhatsApp - Sistema Nexus

## Objetivo
Garantir que TODOS os números de WhatsApp no sistema sigam o padrão da automação:
- **Formato:** Apenas dígitos (sem +, -, espaços, parênteses)
- **Código do país:** Sempre com 55 no início
- **Exemplo:** `5567963911866`

## O que foi feito

### 1. Normalização do banco de dados existente

**Script:** `normalizar_whatsapp_formatados.py`

Normalizado 2 números que estavam com formatação manual:
- ADILSON EVANGELISTA: `+55 67 9812-1311` → `556798121311`
- MARCELO CANDIDO: `+55 67 9669-5041` → `556796695041`

### 2. Normalização automática no backend

**Arquivo modificado:** `backend/routes/crm.py`

#### Endpoint de criação de cliente (linha 243)
```python
# Normalizar WhatsApp se presente (padrão da automação: apenas dígitos)
whatsapp_normalizado = None
if data.get('whatsapp'):
    import re
    whatsapp_limpo = re.sub(r'[^\d]', '', str(data['whatsapp']))

    # Adicionar código do país se não tiver
    if whatsapp_limpo and not whatsapp_limpo.startswith('55'):
        whatsapp_limpo = '55' + whatsapp_limpo

    whatsapp_normalizado = whatsapp_limpo if whatsapp_limpo else None
```

#### Endpoint de atualização de cliente (linha 290)
```python
# Normalizar WhatsApp se presente (padrão da automação: apenas dígitos)
if 'whatsapp' in data and data['whatsapp']:
    import re
    whatsapp_limpo = re.sub(r'[^\d]', '', str(data['whatsapp']))

    # Adicionar código do país se não tiver
    if whatsapp_limpo and not whatsapp_limpo.startswith('55'):
        whatsapp_limpo = '55' + whatsapp_limpo

    data['whatsapp'] = whatsapp_limpo
```

#### Endpoint específico de WhatsApp (linha 1762)
JÁ tinha normalização implementada, mantido como está.

## Scripts de teste e verificação

### `testar_normalizacao_whatsapp.py`
Testa diversos formatos de entrada e valida a normalização:
```
[OK] +55 67 9309-3265 → 556793093265
[OK] (67) 99999-9999 → 5567999999999
[OK] 67 9 9999-9999 → 5567999999999
[OK] 67999999999 → 5567999999999
```

### `verificar_todos_whatsapp.py`
Verifica TODOS os WhatsApp no banco e mostra estatísticas:
```
Total de clientes: 34
Padrão correto: 34 (100%)
Com formatação: 0
Sem código do país: 0
```

## Resultado final

✅ **100% dos números normalizados**
- 34 clientes com WhatsApp
- Todos no formato correto: apenas dígitos com código 55
- Nenhum número com formatação (+, -, espaços, etc)

## Comportamento do sistema

### Quando um número é adicionado/editado manualmente:
1. **Frontend** envia o número no formato que o usuário digitou
2. **Backend** automaticamente normaliza antes de salvar no banco
3. **Banco** sempre armazena no formato da automação (apenas dígitos)
4. **Frontend** exibe exatamente como está no banco

### Exemplos de conversão automática:
- `+55 67 9999-9999` → `556799999999`
- `(67) 9 9999-9999` → `5567999999999`
- `67999999999` → `5567999999999` (adiciona código do país)
- `5567999999999` → `5567999999999` (já está correto)

## Compatibilidade

✅ **Automação de disparos:** Usa formato correto
✅ **Criação manual:** Normaliza automaticamente
✅ **Edição manual:** Normaliza automaticamente
✅ **Importação via planilha:** Números adicionados já são normalizados pela automação
✅ **API WhatsApp:** Recebe números no formato esperado

## Manutenção

Para verificar a qualidade dos números no banco, execute:
```bash
python backend/scripts/verificar_todos_whatsapp.py
```

Se algum número com formatação for encontrado no futuro, execute:
```bash
python backend/scripts/normalizar_whatsapp_formatados.py
```

---

**Data da implementação:** 2024
**Status:** ✅ Implementado e testado
**Cobertura:** 100% dos números normalizados
