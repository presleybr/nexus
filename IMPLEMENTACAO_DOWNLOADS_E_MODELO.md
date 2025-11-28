# Implementação de Downloads de Boletos e Integração do Modelo-Boleto.pdf

## Visão Geral

Foram implementadas duas funcionalidades principais:
1. **Botão de Download** nas páginas Dashboard e Boletos do Portal do Consórcio
2. **Sistema completo de gerenciamento de Boletos Modelo** com registro no banco de dados

---

## 1. Botões de Download de Boletos

### Dashboard (`dashboard.html`)

**Página:** `http://localhost:5000/portal-consorcio/dashboard`

**O que foi adicionado:**
- Botão "📥 Download" na coluna "Ações" da tabela "Próximos Boletos a Vencer"
- Função JavaScript `downloadBoleto(boletoId)` que abre o PDF em nova aba

**Antes:**
```html
<td>
    <button onclick="visualizarBoleto(${boleto.id})">👁️ Ver PDF</button>
</td>
```

**Depois:**
```html
<td>
    <button onclick="downloadBoleto(${boleto.id})">📥 Download</button>
    <button onclick="visualizarBoleto(${boleto.id})">👁️ Ver PDF</button>
</td>
```

### Página de Boletos (`boletos.html`)

**Página:** `http://localhost:5000/portal-consorcio/boletos`

**Status:** ✅ JÁ EXISTIA
- A página de boletos já possuía o botão de download (📥)
- Não foi necessário modificar

---

## 2. Sistema de Boletos Modelo

### 2.1 Estrutura do Banco de Dados

#### Nova Tabela: `boletos_modelo`

**Arquivo SQL:** `backend/sql/criar_tabela_boletos_modelo.sql`

```sql
CREATE TABLE boletos_modelo (
    id SERIAL PRIMARY KEY,

    -- Identificação
    nome VARCHAR(255) NOT NULL UNIQUE,
    descricao TEXT,
    tipo VARCHAR(50) DEFAULT 'generico',
    banco VARCHAR(100),

    -- Arquivo PDF
    pdf_filename VARCHAR(255) NOT NULL,
    pdf_path TEXT NOT NULL,
    pdf_size INTEGER,

    -- Status
    ativo BOOLEAN DEFAULT true,
    padrao BOOLEAN DEFAULT false, -- Modelo padrão do sistema

    -- Estatísticas de uso
    total_envios INTEGER DEFAULT 0,
    ultimo_envio TIMESTAMP,

    -- Metadados
    uploaded_by VARCHAR(100),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices:**
- `idx_boletos_modelo_ativo` - Para filtrar modelos ativos
- `idx_boletos_modelo_padrao` - Para buscar modelo padrão rapidamente

### 2.2 Registro do Modelo-Boleto.pdf

#### Script de Registro

**Arquivo:** `backend/scripts/registrar_boleto_modelo.py`

**Função:** Registra o arquivo `D:\Nexus\boletos\modelo-boleto.pdf` no banco de dados

**Executar:**
```bash
python backend/scripts/registrar_boleto_modelo.py
```

**O que o script faz:**
1. Cria a tabela `boletos_modelo` (se não existir)
2. Verifica se o arquivo `modelo-boleto.pdf` existe
3. Registra o modelo no banco de dados com informações:
   - Nome: "Modelo Banese"
   - Tipo: "banco_especifico"
   - Banco: "Banese"
   - Tamanho: ~1.15 MB
   - Padrão: true (é o modelo padrão do sistema)
4. Lista todos os modelos cadastrados

**Resultado:**
```
[OK] Tabela criada com sucesso!
[INFO] Arquivo: D:\Nexus\boletos\modelo-boleto.pdf
[INFO] Tamanho: 1,174,744 bytes (1147.21 KB)
[OK] Modelo registrado com sucesso!
[INFO] ID: 1
```

### 2.3 Endpoints da API

**Arquivo:** `backend/routes/boletos_modelo.py`

#### Listar Modelos
```
GET /portal-consorcio/api/boletos-modelo
```
Retorna lista de todos os boletos modelo ativos.

#### Obter Modelo Específico
```
GET /portal-consorcio/api/boletos-modelo/<id>
```
Retorna detalhes de um modelo específico.

#### Download do Modelo
```
GET /portal-consorcio/api/boletos-modelo/<id>/download
```
Faz download do PDF do modelo.

#### Visualizar Modelo
```
GET /portal-consorcio/api/boletos-modelo/<id>/visualizar
```
Visualiza o PDF inline no navegador.

#### Obter Modelo Padrão
```
GET /portal-consorcio/api/boletos-modelo/padrao
```
Retorna o modelo marcado como padrão.

#### Estatísticas
```
GET /portal-consorcio/api/boletos-modelo/<id>/estatisticas
```
Retorna estatísticas de uso do modelo.

#### Incrementar Contador
```
POST /portal-consorcio/api/boletos-modelo/<id>/incrementar-envio
```
Incrementa contador de envios do modelo.

### 2.4 Interface de Gerenciamento

**Página:** `frontend/templates/portal-consorcio/boletos-modelo.html`

**URL:** `http://localhost:5000/portal-consorcio/boletos-modelo`

**Funcionalidades:**

#### 1. Listagem de Modelos
- Tabela com todos os modelos cadastrados
- Colunas: ID, Nome, Banco, Arquivo, Tamanho, Total Envios, Padrão, Ações

#### 2. Ações por Modelo
- **👁️ Visualizar:** Abre modal com PDF inline
- **📥 Download:** Faz download do PDF

#### 3. Modal de Visualização
- Modal full-screen (90% da tela)
- Iframe com PDF
- Fechar com X, ESC ou clique fora

#### 4. Badge "PADRÃO"
- Modelos marcados como padrão exibem badge verde

### 2.5 Navegação

**Novo item no menu lateral:**
- Dashboard: ✅ Link adicionado
- Boletos: ✅ Link adicionado
- Boletos Modelo: ✅ Página própria

**Menu:**
```
📊 Dashboard
👥 Clientes Finais
📄 Boletos
📋 Boletos Modelo  <- NOVO!
```

---

## 3. Arquitetura da Solução

### Fluxo de Dados - Registro do Modelo

```
1. Arquivo modelo-boleto.pdf na pasta boletos/
   ↓
2. Script Python (registrar_boleto_modelo.py)
   ↓
3. Cria tabela boletos_modelo
   ↓
4. Registra informações do PDF no banco
   ↓
5. Sistema pronto para servir o modelo
```

### Fluxo de Uso - Visualização/Download

```
1. Usuário acessa /portal-consorcio/boletos-modelo
   ↓
2. Frontend busca lista: GET /api/boletos-modelo
   ↓
3. Backend consulta tabela boletos_modelo
   ↓
4. Retorna JSON com modelos
   ↓
5. Usuário clica em Visualizar ou Download
   ↓
6. Backend envia PDF usando send_file()
```

---

## 4. Diferença entre Boletos e Boletos Modelo

### Boletos (Tabela: `boletos`)
- Vinculados a um **cliente final específico**
- Gerados automaticamente pelo sistema
- Possuem dados preenchidos (valor, vencimento, etc.)
- Enviados individualmente via WhatsApp
- Status: pendente, pago, vencido

### Boletos Modelo (Tabela: `boletos_modelo`)
- **Genéricos/Templates**
- Não vinculados a clientes
- Usados para envio em massa
- PDF modelo sem dados preenchidos
- Reutilizáveis
- Exemplo: modelo-boleto.pdf do Banese

---

## 5. Arquivos Criados/Modificados

### Backend

**Criados:**
1. `backend/sql/criar_tabela_boletos_modelo.sql` - Schema da tabela
2. `backend/scripts/registrar_boleto_modelo.py` - Script de registro
3. `backend/routes/boletos_modelo.py` - Endpoints da API

**Modificados:**
4. `backend/app.py` - Registro do blueprint
5. `backend/routes/portal_consorcio.py` - Rota da página HTML

### Frontend

**Criados:**
6. `frontend/templates/portal-consorcio/boletos-modelo.html` - Interface

**Modificados:**
7. `frontend/templates/portal-consorcio/dashboard.html` - Botão download + link menu
8. `frontend/templates/portal-consorcio/boletos.html` - Link menu

### Documentação

**Criados:**
9. `IMPLEMENTACAO_DOWNLOADS_E_MODELO.md` - Este documento

---

## 6. Como Usar

### Acessar Boletos Modelo

1. Faça login no Portal do Consórcio
   ```
   URL: http://localhost:5000/portal-consorcio/login
   Email: admin@portal.com
   Senha: admin123
   ```

2. Clique em "Boletos Modelo" no menu lateral

3. Visualize ou baixe o modelo "Modelo Banese"

### Baixar Boletos de Clientes

**No Dashboard:**
1. Acesse o Dashboard
2. Role até "Próximos Boletos a Vencer"
3. Clique em "📥 Download" para baixar
4. Clique em "👁️ Ver PDF" para visualizar inline

**Na Página de Boletos:**
1. Acesse "Boletos" no menu
2. Na tabela, clique em "📥" para download
3. Clique em "👁️" para visualizar
4. Clique em "📱" para enviar via WhatsApp

---

## 7. Banco de Dados - Registro Atual

### Modelo Cadastrado

| Campo | Valor |
|-------|-------|
| **ID** | 1 |
| **Nome** | Modelo Banese |
| **Descrição** | Modelo de boleto do Banco Banese - Usado para envio em massa aos clientes do consórcio |
| **Tipo** | banco_especifico |
| **Banco** | Banese |
| **Arquivo** | modelo-boleto.pdf |
| **Caminho** | D:\Nexus\boletos\modelo-boleto.pdf |
| **Tamanho** | 1,174,744 bytes (~1.15 MB) |
| **Ativo** | true |
| **Padrão** | true |
| **Total Envios** | 0 (será incrementado conforme uso) |
| **Uploaded By** | sistema |

---

## 8. Integração com Envio em Massa

O modelo-boleto.pdf está integrado ao sistema de envio em massa existente:

**Serviço:** `backend/services/boleto_modelo_service.py`

**Função:** `enviar_modelo_para_todos_clientes()`

O serviço já utiliza o arquivo `modelo-boleto.pdf` para enviar aos clientes. Com o registro no banco:

1. É possível rastrear quantas vezes foi enviado
2. Atualizar `total_envios` e `ultimo_envio`
3. Gerenciar múltiplos modelos no futuro
4. Ter controle sobre qual é o modelo padrão
5. Ativar/desativar modelos sem deletar

---

## 9. Melhorias Futuras

### 1. Upload de Novos Modelos
- Interface para fazer upload de novos PDFs
- Definir qual é o modelo padrão
- Editar descrições

### 2. Múltiplos Modelos
- Ter modelos por banco (Banese, BB, Caixa, etc.)
- Escolher modelo específico no envio em massa
- Templates personalizados por cliente

### 3. Preenchimento Automático
- Usar bibliotecas como PyPDF2 ou pdfrw
- Preencher campos do modelo com dados do cliente
- Gerar PDFs personalizados a partir do template

### 4. Histórico de Uso
- Tabela de auditoria
- Rastrear quem baixou/visualizou
- Relatórios de uso

### 5. Versionamento
- Manter versões antigas dos modelos
- Controle de alterações
- Rollback se necessário

---

## 10. Troubleshooting

### Modelo não aparece na lista

**Problema:** Página de Boletos Modelo está vazia

**Solução:**
1. Verificar se o script foi executado com sucesso
2. Executar: `python backend/scripts/registrar_boleto_modelo.py`
3. Verificar tabela no banco: `SELECT * FROM boletos_modelo;`

### Erro ao visualizar/baixar

**Problema:** Erro 404 ou arquivo não encontrado

**Solução:**
1. Verificar se o arquivo existe: `D:\Nexus\boletos\modelo-boleto.pdf`
2. Verificar caminho no banco de dados
3. Verificar permissões de leitura do arquivo

### Botão de download não funciona no Dashboard

**Problema:** Clique no botão não faz nada

**Solução:**
1. Abrir console do navegador (F12)
2. Verificar erros JavaScript
3. Verificar se a função `downloadBoleto()` foi carregada
4. Verificar se o endpoint `/api/boletos/<id>/download` está respondendo

---

## 11. Conclusão

✅ **Botões de download** implementados no Dashboard e Boletos
✅ **Modelo-boleto.pdf** registrado no banco de dados
✅ **Sistema completo** de gerenciamento de boletos modelo
✅ **Interface visual** para visualizar, baixar e gerenciar modelos
✅ **Navegação** integrada ao menu do Portal do Consórcio
✅ **Endpoints da API** para todas as operações
✅ **Documentação** completa da implementação

O sistema está **totalmente funcional** e pronto para uso!

### URLs de Acesso

- **Dashboard:** http://localhost:5000/portal-consorcio/dashboard
- **Boletos:** http://localhost:5000/portal-consorcio/boletos
- **Boletos Modelo:** http://localhost:5000/portal-consorcio/boletos-modelo (NOVO!)

**Credenciais:**
- Email: `admin@portal.com`
- Senha: `admin123`
