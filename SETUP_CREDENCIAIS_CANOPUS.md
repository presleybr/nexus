# 🔐 Configurar Credenciais Canopus no Render

## Passo a Passo

### 1. Executar script de configuração

Execute o script localmente conectado ao banco do Render:

```bash
python configurar_credenciais_canopus_render.py
```

Este script irá:
- ✅ Criar a tabela `credenciais_canopus` se não existir
- ✅ Verificar credenciais existentes
- ✅ Inserir credenciais padrão (se não houver nenhuma)

### 2. Editar e configurar credenciais reais

**IMPORTANTE**: O script insere credenciais placeholder. Você precisa atualizá-las com as credenciais reais.

#### Opção A: Pelo DBeaver (Recomendado)

1. Abra DBeaver
2. Conecte ao banco do Render usando a URL:
   ```
   postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2
   ```

3. Execute a query:
   ```sql
   -- Ver credenciais atuais
   SELECT * FROM credenciais_canopus;

   -- Atualizar com credenciais reais do PV 24627
   UPDATE credenciais_canopus
   SET
       usuario = 'seu_usuario_real',
       senha = 'sua_senha_real',
       codigo_empresa = '0101'  -- ou o código correto
   WHERE ponto_venda = '24627';
   ```

4. **IMPORTANTE**: A senha deve estar em texto plano no banco (será usada para login no portal)

#### Opção B: Script Python

Crie um arquivo `atualizar_credenciais.py`:

```python
#!/usr/bin/env python3
import psycopg

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

# Suas credenciais reais
USUARIO = 'dener'  # ← EDITE AQUI
SENHA = 'sua_senha_aqui'  # ← EDITE AQUI
CODIGO_EMPRESA = '0101'  # ← EDITE AQUI se necessário

cur.execute("""
    UPDATE credenciais_canopus
    SET
        usuario = %s,
        senha = %s,
        codigo_empresa = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE ponto_venda = '24627'
""", (USUARIO, SENHA, CODIGO_EMPRESA))

conn.commit()
print(f"✅ Credenciais atualizadas para PV 24627")

cur.close()
conn.close()
```

Execute:
```bash
python atualizar_credenciais.py
```

### 3. Verificar credenciais

Execute novamente o script de configuração para verificar:

```bash
python configurar_credenciais_canopus_render.py
```

Você deve ver:
```
✅ 1 credencial(is) encontrada(s):
  PV: 24627      | Usuário: dener         | Código Empresa: 0101   | ATIVO
```

### 4. Estrutura da tabela

A tabela `credenciais_canopus` tem a seguinte estrutura:

| Coluna          | Tipo         | Descrição                           |
|-----------------|--------------|-------------------------------------|
| id              | SERIAL       | ID único (auto incremento)          |
| ponto_venda     | VARCHAR(20)  | Ponto de venda (ex: '24627')        |
| usuario         | VARCHAR(255) | Usuário para login no portal        |
| senha           | VARCHAR(255) | Senha em texto plano                |
| codigo_empresa  | VARCHAR(10)  | Código da empresa (padrão '0101')   |
| ativo           | BOOLEAN      | Se a credencial está ativa          |
| created_at      | TIMESTAMP    | Data de criação                     |
| updated_at      | TIMESTAMP    | Data da última atualização          |

### 5. Adicionar mais pontos de venda (opcional)

Se você tiver outro ponto de venda (ex: PV 17308):

```sql
INSERT INTO credenciais_canopus (
    ponto_venda,
    usuario,
    senha,
    codigo_empresa,
    ativo
) VALUES (
    '17308',
    'usuario_pv17308',
    'senha_pv17308',
    '0101',
    TRUE
);
```

## ⚠️ Segurança

**IMPORTANTE**: As senhas estão em texto plano no banco de dados porque são necessárias para fazer login automatizado no portal Canopus.

**Boas práticas**:
1. Use senhas específicas para automação (não compartilhe com usuários humanos)
2. Mantenha o acesso ao banco restrito
3. Considere rotacionar as senhas periodicamente
4. Monitore os logs de acesso

## ✅ Próximos Passos

Após configurar as credenciais:

1. Aguarde o deploy do Render concluir (o push já foi feito)
2. Acesse o frontend: https://seu-app.onrender.com
3. Faça login
4. Vá para Automação Canopus → ETAPA 3
5. Clique em "Iniciar Download"

O Chromium deve abrir em background no servidor e começar a baixar os boletos! 🚀

## 🐛 Troubleshooting

### Erro: "Credenciais não encontradas para PV 24627"

**Solução**: Execute novamente o script de configuração e verifique que as credenciais foram inseridas:
```bash
python configurar_credenciais_canopus_render.py
```

### Erro: "Login falhou no portal Canopus"

**Possíveis causas**:
1. Usuário ou senha incorretos → Verifique no banco
2. Código da empresa incorreto → Verifique se é '0101' ou outro
3. Credenciais expiradas → Atualize a senha no portal e no banco

### Erro: "ModuleNotFoundError: No module named 'automation'"

**Solução**: Já foi corrigido no último push! Aguarde o deploy do Render concluir.

## 📞 Suporte

Se tiver problemas, verifique:
1. Logs do Render (procure por "🔑 Buscando credenciais...")
2. Tabela no banco: `SELECT * FROM credenciais_canopus;`
3. Conexão com o banco está funcionando
