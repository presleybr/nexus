# Funcionalidade: Envio de Boleto Modelo via WhatsApp

## Visão Geral

Esta funcionalidade permite enviar o **boleto modelo** (arquivo `modelo-boleto.pdf` localizado em `D:\Nexus\boletos\`) para todos os clientes ativos do consórcio via WhatsApp, de forma automatizada.

## Localização do Boleto Modelo

O arquivo PDF modelo deve estar localizado em:
```
D:\Nexus\boletos\modelo-boleto.pdf
```

Este arquivo será enviado para todos os clientes cadastrados no sistema.

## Como Usar

### 1. No CRM do Cliente

**Acesso:** `http://localhost:5000/crm/disparos`

1. Faça login no CRM do Cliente
2. Acesse o menu **"Disparos"**
3. Clique no botão **"Enviar Modelo"** no card "Enviar Boleto Modelo"
4. Digite uma mensagem personalizada (opcional) ou deixe em branco para usar a mensagem padrão
5. Confirme o envio
6. Aguarde o processamento e veja o resumo dos envios

**Mensagem Padrão:**
```
Olá! 👋

Segue em anexo o boleto do seu consórcio.

📄 Por favor, verifique os dados e efetue o pagamento até a data de vencimento.

Qualquer dúvida, estamos à disposição!

_Mensagem automática - Sistema Nexus CRM_
```

### 2. No Portal do Consórcio

**Acesso:** `http://localhost:5000/portal-consorcio/boletos`

1. Faça login no Portal do Consórcio
2. Acesse a página **"Boletos"**
3. Clique no botão **"📋 Enviar Modelo para Todos"**
4. Digite o **ID do Cliente Nexus** (empresa) para filtrar os clientes
5. Digite uma mensagem personalizada (opcional)
6. Confirme o envio
7. Aguarde o processamento e veja o resumo dos envios

## Requisitos

### 1. WhatsApp Conectado

O WhatsApp deve estar conectado e ativo. Para verificar:
- No CRM: Acesse **WhatsApp** > Verifique se o status está "Conectado"
- Servidor Baileys deve estar rodando na porta 3000

### 2. Clientes Cadastrados

Os clientes devem:
- Estar **ativos** no sistema (`ativo = true`)
- Ter **WhatsApp cadastrado** (campo `whatsapp` preenchido)
- Pertencer ao cliente Nexus correto (filtragem por `cliente_nexus_id`)

### 3. Arquivo Modelo Existe

O arquivo `D:\Nexus\boletos\modelo-boleto.pdf` deve existir.

## Endpoints da API

### CRM do Cliente

**Endpoint:** `POST /api/crm/boletos-modelo/enviar-massa`

**Payload:**
```json
{
  "mensagem": "Mensagem personalizada (opcional)"
}
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "total_clientes": 50,
  "total_enviados": 48,
  "total_erros": 2,
  "resultados": [
    {
      "cliente_id": 1,
      "nome": "João Silva",
      "whatsapp": "11999999999",
      "status": "enviado",
      "erro": null
    },
    {
      "cliente_id": 2,
      "nome": "Maria Santos",
      "whatsapp": "11888888888",
      "status": "erro",
      "erro": "Número não existe no WhatsApp"
    }
  ],
  "message": "Boleto modelo enviado para 48 clientes!"
}
```

### Portal do Consórcio

**Endpoint:** `POST /portal-consorcio/api/boletos/enviar-modelo-massa`

**Payload:**
```json
{
  "cliente_nexus_id": 1,
  "mensagem": "Mensagem personalizada (opcional)"
}
```

**Resposta:** Mesma estrutura do endpoint do CRM

## Funcionalidades de Segurança

### 1. Sistema Anti-Bloqueio

O sistema possui delays automáticos entre envios para evitar bloqueio do WhatsApp:
- **2 segundos** de delay entre mensagem de texto e PDF
- **5 segundos** de delay entre cada cliente

### 2. Tratamento de Erros

O sistema continua enviando mesmo se houver erros em alguns clientes, e retorna um relatório detalhado ao final.

### 3. Filtragem Automática

Apenas clientes **ativos** e com **WhatsApp cadastrado** recebem o boleto.

## Estrutura de Dados

### Cliente Final

```sql
SELECT id, nome_completo, cpf, whatsapp, numero_contrato
FROM clientes_finais
WHERE cliente_nexus_id = ?
  AND ativo = true
  AND whatsapp IS NOT NULL
```

## Serviço Backend

### Arquivo: `backend/services/boleto_modelo_service.py`

**Classe:** `BoletoModeloService`

**Métodos Principais:**

1. **`verificar_modelo_existe()`**
   - Verifica se o arquivo modelo existe
   - Retorna: `bool`

2. **`preparar_boleto_para_cliente(cliente_final)`**
   - Prepara uma cópia do boleto modelo para um cliente específico
   - Retorna: `dict` com informações do arquivo

3. **`enviar_modelo_para_todos_clientes(cliente_nexus_id, mensagem_personalizada=None)`**
   - Envia o boleto modelo para todos os clientes ativos
   - Retorna: `dict` com resultado dos envios

## Fluxo de Execução

```
1. Usuário clica em "Enviar Modelo"
   ↓
2. Sistema verifica se modelo-boleto.pdf existe
   ↓
3. Sistema busca todos os clientes ativos com WhatsApp
   ↓
4. Para cada cliente:
   a. Monta mensagem personalizada com nome do cliente
   b. Envia mensagem de texto via WhatsApp
   c. Aguarda 2 segundos
   d. Envia PDF do boleto
   e. Aguarda 5 segundos (anti-bloqueio)
   ↓
5. Sistema retorna relatório com sucessos e erros
```

## Logs

Os logs são gravados no console do backend:

```
[OK] Boleto modelo enviado para João Silva (11999999999)
[ERROR] Erro ao enviar para Maria Santos: Número não existe no WhatsApp
```

## Personalização da Mensagem

### Variáveis Automáticas

O sistema automaticamente adiciona à mensagem:
- Nome do cliente (em negrito)
- Número do contrato (se disponível)

**Exemplo:**

Se você digitar:
```
Segue o boleto deste mês!
```

O cliente receberá:
```
*João Silva*

Segue o boleto deste mês!

📋 *Contrato:* 12345
```

## Troubleshooting

### Erro: "Arquivo modelo-boleto.pdf não encontrado"

**Solução:** Verifique se o arquivo existe em `D:\Nexus\boletos\modelo-boleto.pdf`

### Erro: "Nenhum cliente ativo com WhatsApp encontrado"

**Solução:**
- Verifique se há clientes cadastrados
- Verifique se os clientes estão ativos
- Verifique se o campo WhatsApp está preenchido

### Erro: "Erro ao enviar mensagem WhatsApp"

**Solução:**
- Verifique se o servidor Baileys está rodando (`http://localhost:3000`)
- Verifique se o WhatsApp está conectado no CRM
- Verifique os logs do servidor Node.js

### Número de WhatsApp inválido

**Solução:**
- O número deve estar no formato internacional: `5511999999999`
- Não usar caracteres especiais: `()`, `-`, espaços
- O sistema limpa automaticamente, mas verifique se o número está correto no cadastro

## Melhorias Futuras

1. **Preenchimento Automático de Campos**
   - Usar PyPDF2 ou similar para preencher dados do cliente no PDF

2. **Agendamento de Envios**
   - Permitir agendar envios para data/hora específica

3. **Templates de Mensagem**
   - Criar múltiplos templates de mensagem salvos

4. **Relatórios Detalhados**
   - Salvar histórico de envios no banco de dados
   - Gerar relatórios em PDF/Excel

5. **Confirmação de Leitura**
   - Verificar se o cliente visualizou a mensagem

## Arquivos Modificados/Criados

1. **Backend:**
   - `backend/services/boleto_modelo_service.py` (CRIADO)
   - `backend/routes/portal_consorcio.py` (MODIFICADO)
   - `backend/routes/crm.py` (MODIFICADO)

2. **Frontend:**
   - `frontend/templates/crm-cliente/disparos.html` (MODIFICADO)
   - `frontend/templates/portal-consorcio/boletos.html` (MODIFICADO)

3. **Documentação:**
   - `ENVIO_BOLETO_MODELO.md` (CRIADO)

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do backend (console do Flask)
2. Verifique os logs do WhatsApp Baileys (console do Node.js)
3. Verifique se todos os serviços estão rodando:
   - PostgreSQL (porta 5434)
   - Flask (porta 5000)
   - WhatsApp Baileys (porta 3000)
