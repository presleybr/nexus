# Como Editar WhatsApp dos Clientes no CRM

## Resumo

Foi implementado um sistema para vincular números de WhatsApp aos clientes que foram importados do Excel sem esse dado. Agora você pode:

1. ✅ Usar números de teste para validar os disparos
2. ✅ Editar os números de WhatsApp dos clientes no futuro
3. ✅ Inserir os números reais dos clientes quando disponíveis

---

## Situação Atual

### Números Vinculados

150 clientes foram atualizados com 11 números de WhatsApp de teste, distribuídos ciclicamente:

```
5567931224813  →  14 clientes
5567996376010  →  14 clientes
5567915342531  →  14 clientes
5567911629169  →  14 clientes
5567954436309  →  14 clientes
5567991478669  →  14 clientes
5567935799810  →  14 clientes
5567903377105  →  13 clientes
5567918669257  →  13 clientes
5567940544573  →  13 clientes
5567996600884  →  13 clientes
```

### Ver Distribuição Atual

Para ver quais clientes estão usando quais números:

```bash
cd D:\Nexus\backend
python scripts/vincular_whatsapp_teste.py --listar
```

---

## Como Editar WhatsApp de um Cliente

### Via API (Frontend)

Foi criada uma nova rota no backend para editar o WhatsApp de um cliente:

**Endpoint:** `PUT /api/crm/clientes-finais/<cliente_id>/whatsapp`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "whatsapp": "67996600884"
}
```

**Resposta de Sucesso (200):**
```json
{
  "success": true,
  "message": "WhatsApp atualizado com sucesso",
  "whatsapp": "5567996600884"
}
```

### Validações Automáticas

O sistema faz as seguintes validações e ajustes:

1. ✅ Remove caracteres especiais (parênteses, hífens, espaços)
2. ✅ Valida que tem pelo menos 10 dígitos
3. ✅ Adiciona o código do país (55) automaticamente se não tiver
4. ✅ Verifica se o cliente pertence ao cliente_nexus logado

### Exemplos de Uso

#### Exemplo 1: Atualizar WhatsApp via cURL

```bash
curl -X PUT http://127.0.0.1:5000/api/crm/clientes-finais/1/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"whatsapp": "67996600884"}'
```

#### Exemplo 2: Atualizar WhatsApp via JavaScript (Frontend)

```javascript
async function atualizarWhatsApp(clienteId, novoWhatsApp) {
  const response = await fetch(`/api/crm/clientes-finais/${clienteId}/whatsapp`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      whatsapp: novoWhatsApp
    })
  });

  const result = await response.json();

  if (result.success) {
    console.log('WhatsApp atualizado:', result.whatsapp);
  } else {
    console.error('Erro:', result.erro);
  }
}

// Uso:
atualizarWhatsApp(1, '67996600884');
```

---

## Como Atualizar em Massa

### Via Script Python

Se você tiver uma planilha com os números corretos, pode criar um script Python para atualizar em massa:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

# Exemplo: dicionário com CPF -> WhatsApp
clientes_whatsapp = {
    '12345678901': '67996600884',
    '98765432100': '67991234567',
    # ... adicione mais clientes
}

for cpf, whatsapp in clientes_whatsapp.items():
    db.execute_update("""
        UPDATE clientes_finais
        SET whatsapp = %s
        WHERE cpf = %s
    """, (whatsapp, cpf))
    print(f"Atualizado CPF {cpf} -> {whatsapp}")
```

### Via SQL Direto

Se preferir, pode atualizar diretamente no banco de dados:

```sql
-- Atualizar um cliente específico
UPDATE clientes_finais
SET whatsapp = '5567996600884'
WHERE cpf = '12345678901';

-- Atualizar vários clientes de uma vez
UPDATE clientes_finais
SET whatsapp = '5567996600884'
WHERE id IN (1, 2, 3, 4, 5);
```

---

## Testando os Disparos

Agora que os clientes têm WhatsApp cadastrado, você pode testar os disparos:

### 1. Teste Individual

Acesse: `http://127.0.0.1:5000/crm/disparos`

Selecione um cliente e clique em "Enviar Teste"

### 2. Teste em Massa (11 números)

O endpoint de teste já envia para os 11 números automaticamente:

```bash
POST http://127.0.0.1:5000/api/crm/scheduler/executar-agora
{
  "modo_teste": true
}
```

### 3. Verificar Logs

Acompanhe os logs do backend para ver se os disparos foram enviados com sucesso.

---

## Próximos Passos

1. ✅ **Testar Disparos**: Teste os disparos com os números de teste vinculados
2. 📝 **Coletar Números Reais**: Colete os números de WhatsApp reais dos clientes
3. 🔄 **Atualizar em Massa**: Use o script ou API para atualizar com números reais
4. 🚀 **Disparos Reais**: Quando tiver números reais, execute disparos em produção

---

## Notas Importantes

⚠️ **IMPORTANTE:**
- Os números atuais são de TESTE
- Alguns números podem não existir (números aleatórios gerados)
- Atualize com números reais antes de usar em produção
- A API valida e formata automaticamente os números

🔐 **Segurança:**
- A API verifica se o cliente pertence ao usuário logado
- Apenas clientes autenticados podem editar WhatsApp
- Validações automáticas previnem números inválidos

📊 **Performance:**
- Os números são distribuídos ciclicamente (round-robin)
- Cada número de teste é usado por ~13-14 clientes
- Isso permite testar os disparos sem números reais

---

## Suporte

Se tiver dúvidas ou problemas, verifique:

1. Logs do backend em `backend/logs/`
2. Console do navegador (F12) para erros de frontend
3. Status do WhatsApp Web conectado

**Arquivos Relacionados:**
- `backend/routes/crm.py` - Rota de atualização de WhatsApp (linha 1493)
- `backend/scripts/vincular_whatsapp_teste.py` - Script de vinculação
- `backend/models/cliente.py` - Modelo de cliente com campo WhatsApp
