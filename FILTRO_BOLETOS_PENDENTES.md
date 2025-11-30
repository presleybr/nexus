# Filtro de Disparos - Apenas Clientes com Boletos Pendentes

## Resumo das Mudanças

O sistema foi modificado para **disparar WhatsApp apenas para clientes que realmente têm boletos pendentes** na tabela `boletos`. Antes, o sistema disparava para todos os clientes com WhatsApp válido, independentemente de terem boletos.

## Modificações Implementadas

### 1. **backend/services/automation_service.py** (linhas 58-140)

#### Antes:
- Buscava **todos os clientes** com WhatsApp válido
- **Gerava novos boletos** para todos esses clientes
- Disparava para todos

#### Depois:
- Busca **apenas clientes que têm boletos pendentes** na tabela `boletos`
- **Não gera novos boletos**, apenas usa os existentes
- Dispara **somente para quem tem boleto**

#### Query implementada:
```sql
SELECT DISTINCT
    cf.id,
    cf.nome_completo as nome,
    cf.whatsapp,
    cf.cpf,
    COUNT(b.id) as total_boletos_pendentes
FROM clientes_finais cf
INNER JOIN boletos b ON b.cliente_final_id = cf.id
WHERE cf.cliente_nexus_id = %s
    AND b.status_envio IN ('nao_enviado', 'pendente')
    AND cf.whatsapp IS NOT NULL
    AND LENGTH(cf.whatsapp) >= 10
GROUP BY cf.id, cf.nome_completo, cf.whatsapp, cf.cpf
ORDER BY cf.nome_completo
```

### 2. **Script de Verificação Criado**

Arquivo: `backend/scripts/verificar_filtro_boletos_pendentes.py`

Este script permite verificar:
- Quantos clientes têm boletos pendentes
- Quantos clientes **não** receberão disparos (sem boletos)
- Total de boletos pendentes no sistema
- Valor total dos boletos

## Como Funciona Agora

### Fluxo de Disparo Atual:

1. **Importação de Boletos**
   - Os boletos são importados de `downloads_canopus` para a tabela `boletos`
   - Isso é feito pelo botão no frontend CRM

2. **Filtro Automático**
   - O sistema verifica quais clientes têm boletos com `status_envio IN ('nao_enviado', 'pendente')`
   - Apenas esses clientes são incluídos no disparo

3. **Disparo**
   - WhatsApp é enviado **apenas** para clientes com boletos pendentes
   - Após o envio, o `status_envio` é atualizado para `'enviado'`

## Teste Realizado

Executamos o script de verificação e confirmamos:

```
[OK] CLIENTES COM BOLETOS PENDENTES: 3
- ADILSON BARROS CORREA JUNIO (1 boleto - R$ 964.31)
- ADILSON EVANGELISTA DA SILVA (1 boleto - R$ 1578.88)
- ALINE CRISTINA SILVA (1 boleto - R$ 1821.30)

[X] CLIENTES SEM BOLETOS PENDENTES: 40
(Estes NÃO receberão disparos)

Total de boletos pendentes: 3
```

## Benefícios

✅ **Economia de custos**: Não dispara para quem não tem boleto
✅ **Precisão**: Cliente só recebe se realmente houver cobrança
✅ **Confiabilidade**: Dados sempre sincronizados com a tabela `boletos`
✅ **Rastreabilidade**: Tudo registrado no banco de dados

## Como Usar

### Para verificar o filtro:
```bash
python backend/scripts/verificar_filtro_boletos_pendentes.py
```

### Para disparar boletos:
1. Acesse o frontend do CRM
2. Importe os boletos de `downloads_canopus` (botão "Importar Boletos")
3. Execute a automação de disparos
4. Sistema enviará **apenas** para clientes com boletos pendentes

## Estrutura das Tabelas Envolvidas

### Tabela `downloads_canopus`
- Armazena PDFs de boletos baixados do Canopus
- Origem dos dados de boletos

### Tabela `boletos`
- Registros de boletos importados
- Campos importantes:
  - `status_envio`: 'nao_enviado', 'pendente', 'enviado'
  - `cliente_final_id`: Relacionamento com cliente
  - `pdf_path`: Caminho do PDF
  - `valor_original`, `data_vencimento`

### Tabela `clientes_finais`
- Dados dos clientes finais
- Campo `whatsapp` é obrigatório para disparo

## Arquivos Modificados

1. `backend/services/automation_service.py` - Lógica principal de automação
2. `backend/scripts/verificar_filtro_boletos_pendentes.py` - Script de verificação (novo)
3. `FILTRO_BOLETOS_PENDENTES.md` - Esta documentação (novo)

## Notas Importantes

⚠️ **Status de Envio**: Após o disparo bem-sucedido, o `status_envio` do boleto é atualizado para `'enviado'`. Isso garante que o mesmo boleto não seja enviado duas vezes.

⚠️ **WhatsApp Obrigatório**: Clientes sem WhatsApp válido (NULL ou menos de 10 caracteres) são automaticamente excluídos.

⚠️ **Fluxo de Importação**: Os boletos devem ser importados da tabela `downloads_canopus` para a tabela `boletos` antes do disparo.

## Data da Implementação

- Data: 30/11/2025
- Autor: Claude Code
- Versão: 1.0
