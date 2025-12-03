# PROBLEMA: Login HTTP Canopus Falhou - Usuário Incorreto no Banco

## RESUMO DO PROBLEMA

O download de boletos via HTTP estava falhando no staging porque:
- **Usuário no banco (staging)**: "dener" ❌
- **Usuário correto**: "24627" (código do PV) ✅

## SINTOMAS

```
Usuário (banco): dener
🔍 DEBUG Login - URL final: https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx
🔍 DEBUG Login - Status: 200
📄 Título da página: Login - Newcon
❌ Login falhou - não detectou sucesso
```

O servidor aceita a conexão (sem erro de "Connection reset"), mas retorna para a página de login porque o usuário está incorreto.

## CAUSA RAIZ

No banco de dados de **staging**, a credencial do PV 24627 estava cadastrada com:
- `usuario = 'dener'` (incorreto)

Mas o sistema Canopus espera:
- `usuario = '24627'` (código do ponto de venda)

## SOLUÇÃO

### Opção 1: Executar script de atualização (RECOMENDADO)

1. Editar o arquivo `atualizar_credenciais_canopus.py`:
   ```python
   PONTO_VENDA_CODIGO = '24627'
   USUARIO = '24627'  # ← Já corrigido!
   SENHA = 'SUA_SENHA_REAL_AQUI'  # ← Editar com senha correta
   ```

2. Executar o script:
   ```bash
   python atualizar_credenciais_canopus.py
   ```

3. O script irá:
   - Conectar ao banco do Render (staging)
   - Buscar a credencial do PV 24627
   - Atualizar `usuario` de "dener" → "24627"
   - Criptografar e atualizar a senha
   - Confirmar a atualização

### Opção 2: Atualizar manualmente no banco

```sql
-- Conectar ao banco do Render
UPDATE credenciais_canopus
SET usuario = '24627',
    senha_encrypted = 'SENHA_CRIPTOGRAFADA_AQUI',
    updated_at = CURRENT_TIMESTAMP
WHERE ponto_venda_id = (
    SELECT id FROM pontos_venda WHERE codigo = '24627'
);
```

## VERIFICAÇÃO

Após atualizar a credencial, testar:

1. Acessar: https://nexus-staging-backend.onrender.com/crm/automacao-canopus
2. Selecionar método: 🌐 HTTP (Requisições Diretas)
3. Clicar em "Iniciar Download"
4. Verificar logs do Render

**Log esperado após correção**:
```
Usuário (banco): 24627
🔍 DEBUG Login - Status: 302 (redirect - sucesso!)
✅ Login bem-sucedido!
```

## OBSERVAÇÕES IMPORTANTES

1. **Usuário = Código do PV**: No Canopus, o username é sempre o código do ponto de venda (ex: "24627", não "0000024627" ou "dener")

2. **Não usar zfill**: O código já foi modificado para não adicionar zeros à esquerda:
   ```python
   # ANTES (ERRADO):
   usuario_login = ponto_venda.zfill(10)  # "24627" → "0000024627"

   # DEPOIS (CORRETO):
   usuario_login = usuario  # "24627" → "24627"
   ```

3. **Ambiente local vs staging**:
   - Local: credencial já está correta (usuario = "24627")
   - Staging: credencial estava incorreta (usuario = "dener")

## COMMITS RELACIONADOS

- `b489b7c` - fix: corrige username para usar valor do banco sem formatação
- `8e4b8b4` - debug: adiciona logs detalhados para investigar falha de login
- `37f3e1e` - fix: adiciona medidas anti-detecção avançadas (verify=True, Referer, delays)
- `f21d2fc` - fix: corrige import de CanopusConfig

## ARQUIVOS MODIFICADOS

1. `backend/routes/automation_canopus.py:4562`
   - Removido `ponto_venda.zfill(10)`
   - Usando `usuario` diretamente do banco

2. `automation/canopus/canopus_http_client.py:160`
   - Removido formatação com zfill
   - Usando username recebido como está

3. `atualizar_credenciais_canopus.py` (atualizado neste commit)
   - Corrigido para usar estrutura atual do banco
   - Adicionado criptografia Fernet
   - Usuário padrão alterado de "dener" → "24627"
