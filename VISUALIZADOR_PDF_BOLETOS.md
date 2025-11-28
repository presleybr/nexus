# Visualizador de PDF de Boletos no Portal do Consórcio

## Visão Geral

Foi implementada uma funcionalidade para visualizar os boletos em PDF **diretamente no frontend** do Portal do Consórcio, sem necessidade de fazer download. O PDF é exibido em um modal elegante com iframe.

## Funcionalidades Implementadas

### 1. Endpoint de Visualização
**Arquivo:** `backend/routes/portal_consorcio.py`

**Novo Endpoint:**
```
GET /portal-consorcio/api/boletos/<boleto_id>/visualizar
```

**Descrição:**
- Retorna o PDF do boleto para visualização inline no navegador
- **Diferença do endpoint `/download`:** O endpoint de download (`as_attachment=True`) força o download do arquivo, enquanto o de visualização (`as_attachment=False`) exibe o PDF diretamente no navegador
- Requer autenticação (decorator `@login_required_portal`)
- Valida se o arquivo PDF existe antes de retornar

### 2. Visualização no Dashboard

**Página:** `frontend/templates/portal-consorcio/dashboard.html`

**Localização:** `http://localhost:5000/portal-consorcio/dashboard`

**Recursos Adicionados:**

#### Modal de Visualização
- Modal full-screen responsivo (90% da tela)
- Design com identidade visual Nexus (borda verde neon)
- Iframe para exibir PDF inline
- Botão de fechar (X)
- Fechar ao clicar fora do modal
- Fechar ao pressionar ESC

#### Tabela de Boletos
- Nova coluna "Ações" adicionada
- Botão "👁️ Ver PDF" para cada boleto
- Ao clicar, abre o modal com o PDF do boleto

**Código da Coluna Ações:**
```html
<td>
    <button onclick="visualizarBoleto(${boleto.id})" class="btn-action" title="Visualizar PDF">
        👁️ Ver PDF
    </button>
</td>
```

### 3. Visualização na Página de Boletos

**Página:** `frontend/templates/portal-consorcio/boletos.html`

**Localização:** `http://localhost:5000/portal-consorcio/boletos`

**Recursos Adicionados:**

#### Modal de Visualização
- Mesmo design do dashboard
- Modal com z-index alto (10000) para sobrepor outros modais
- Responsivo e adaptável

#### Tabela de Boletos
- Botão "👁️" já existia na coluna "Ações"
- Funcionalidade **modificada** de `window.open()` para abrir modal inline
- Agora exibe PDF no modal ao invés de abrir nova aba

**Antes:**
```javascript
async function visualizarBoleto(id) {
    window.open(`/portal-consorcio/api/boletos/${id}/download`, '_blank');
}
```

**Depois:**
```javascript
function visualizarBoleto(id) {
    const modal = document.getElementById('modalVisualizadorPDF');
    const iframe = document.getElementById('iframePDF');

    // Usar endpoint de visualização inline
    iframe.src = `/portal-consorcio/api/boletos/${id}/visualizar`;

    // Mostrar modal
    modal.style.display = 'flex';
}
```

### 4. Botões de Ação na Tabela de Boletos

**Página de Boletos** possui 3 botões para cada boleto:

1. **📥 Download** - Faz download do PDF
2. **📱 WhatsApp** - Envia boleto via WhatsApp
3. **👁️ Visualizar** - Exibe PDF no modal (NOVO comportamento)

## Design e Estilo

### Modal PDF
```css
.modal-overlay {
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(5px);
    z-index: 9999; /* Dashboard */
    z-index: 10000; /* Boletos - sobrepõe outros modais */
}

.modal-content-pdf {
    background: var(--nexus-bg-secondary);
    border: 2px solid var(--nexus-green);
    border-radius: var(--nexus-radius-lg);
    width: 90%;
    max-width: 1200px;
    height: 90vh;
    box-shadow: 0 0 40px rgba(57, 255, 20, 0.3);
}
```

### Botões de Ação

**Dashboard:**
```css
.btn-action {
    background: transparent;
    border: 1px solid var(--nexus-green);
    color: var(--nexus-green);
    padding: 6px 12px;
    border-radius: var(--nexus-radius-sm);
}

.btn-action:hover {
    background: var(--nexus-green);
    color: var(--nexus-bg-primary);
    box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
}
```

**Página Boletos:**
```css
.btn-icon {
    background: transparent;
    border: 1px solid var(--nexus-border-color);
    padding: 6px 10px;
    font-size: 1rem;
}

.btn-icon:hover {
    border-color: var(--nexus-green);
    background: rgba(57, 255, 20, 0.1);
}
```

## Fluxo de Funcionamento

### Visualização de Boleto

```
1. Usuário clica em "👁️ Ver PDF" na tabela
   ↓
2. JavaScript chama visualizarBoleto(boletoId)
   ↓
3. Define src do iframe: /portal-consorcio/api/boletos/{id}/visualizar
   ↓
4. Exibe modal com display: flex
   ↓
5. Backend (Flask) retorna PDF com as_attachment=False
   ↓
6. Navegador renderiza PDF dentro do iframe
   ↓
7. Usuário visualiza PDF no modal
   ↓
8. Usuário fecha modal (X, ESC ou clicar fora)
   ↓
9. JavaScript limpa iframe.src e esconde modal
```

## Funções JavaScript

### visualizarBoleto(boletoId)
Abre o modal e carrega o PDF no iframe.

```javascript
function visualizarBoleto(boletoId) {
    const modal = document.getElementById('modalVisualizadorPDF');
    const iframe = document.getElementById('iframePDF');

    iframe.src = `/portal-consorcio/api/boletos/${boletoId}/visualizar`;
    modal.style.display = 'flex';
}
```

### fecharModalPDF()
Fecha o modal e limpa o iframe.

```javascript
function fecharModalPDF() {
    const modal = document.getElementById('modalVisualizadorPDF');
    const iframe = document.getElementById('iframePDF');

    iframe.src = '';
    modal.style.display = 'none';
}
```

### Event Listeners

#### Fechar ao clicar fora do modal
```javascript
modal.addEventListener('click', function(e) {
    if (e.target === modal) {
        fecharModalPDF();
    }
});
```

#### Fechar com tecla ESC
```javascript
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.style.display === 'flex') {
        fecharModalPDF();
    }
});
```

## Compatibilidade

### Navegadores que Suportam PDF em Iframe
- ✅ **Google Chrome** - Suporte nativo
- ✅ **Microsoft Edge** - Suporte nativo
- ✅ **Firefox** - Suporte nativo
- ✅ **Safari** - Suporte nativo
- ⚠️ **Internet Explorer** - Pode requerer plugin

### Fallback
Se o navegador não suportar visualização de PDF em iframe, o usuário pode usar o botão de **Download** (📥) que continua funcionando normalmente.

## Diferenças entre Endpoints

| Endpoint | Rota | as_attachment | Comportamento |
|----------|------|---------------|---------------|
| **Download** | `/api/boletos/<id>/download` | `True` | Força download do arquivo |
| **Visualizar** | `/api/boletos/<id>/visualizar` | `False` | Exibe PDF inline no navegador |

Ambos retornam o mesmo arquivo PDF, mas com headers HTTP diferentes:

**Download:**
```
Content-Disposition: attachment; filename="boleto.pdf"
```

**Visualizar:**
```
Content-Disposition: inline
```

## Arquivos Modificados/Criados

### Backend
1. **`backend/routes/portal_consorcio.py`** (MODIFICADO)
   - Novo endpoint: `/api/boletos/<id>/visualizar`

### Frontend
2. **`frontend/templates/portal-consorcio/dashboard.html`** (MODIFICADO)
   - Modal de visualização adicionado
   - Coluna "Ações" adicionada na tabela de boletos
   - Funções JavaScript: `visualizarBoleto()`, `fecharModalPDF()`
   - Event listeners para fechar modal

3. **`frontend/templates/portal-consorcio/boletos.html`** (MODIFICADO)
   - Modal de visualização adicionado
   - Função `visualizarBoleto()` modificada (window.open → modal)
   - Função `fecharModalPDF()` adicionada
   - Event listeners para fechar modal
   - Estilos CSS para botões e modal

### Documentação
4. **`VISUALIZADOR_PDF_BOLETOS.md`** (CRIADO)
   - Documentação completa da funcionalidade

## Vantagens da Implementação

### 1. **Melhor UX**
- Usuário não precisa sair da página
- Visualização rápida sem downloads
- Navegação fluida

### 2. **Economia de Tempo**
- Não precisa abrir nova aba
- Não precisa gerenciar múltiplas janelas
- Fechamento rápido com ESC

### 3. **Identidade Visual**
- Modal com design Nexus (verde neon)
- Consistente com o resto do sistema
- Animações suaves

### 4. **Acessibilidade**
- Múltiplas formas de fechar modal
- Tecla ESC
- Clique fora
- Botão X
- Responsivo para diferentes tamanhos de tela

## Melhorias Futuras

1. **Controles de Zoom**
   - Adicionar botões +/- para zoom
   - Ajustar visualização

2. **Navegação entre Boletos**
   - Botões "Anterior" e "Próximo"
   - Visualizar múltiplos boletos sem fechar modal

3. **Download Direto do Modal**
   - Botão de download dentro do modal
   - Facilitar acesso

4. **Impressão Direta**
   - Botão de impressão no modal
   - Facilitar impressão sem abrir nova aba

5. **Loading State**
   - Mostrar spinner enquanto PDF carrega
   - Melhor feedback visual

## Troubleshooting

### PDF não carrega no modal
**Problema:** Iframe fica em branco

**Possíveis Causas:**
1. Arquivo PDF não existe no servidor
2. Caminho do arquivo está incorreto no banco de dados
3. Permissões de arquivo incorretas
4. Navegador bloqueando conteúdo

**Soluções:**
- Verificar console do navegador (F12) para erros
- Verificar se `pdf_path` está correto no banco de dados
- Verificar permissões da pasta `boletos/`
- Tentar acessar o endpoint diretamente: `/portal-consorcio/api/boletos/<id>/visualizar`

### Modal não fecha
**Problema:** Modal fica aberto ao clicar fora ou pressionar ESC

**Solução:**
- Verificar se `DOMContentLoaded` está sendo executado
- Abrir console (F12) e verificar erros JavaScript
- Verificar se `modalVisualizadorPDF` tem o ID correto

### PDF baixa ao invés de visualizar
**Problema:** Ao clicar em "Ver PDF", o arquivo é baixado

**Causa:** Navegador não suporta visualização inline de PDF

**Solução:**
- Atualizar navegador para versão mais recente
- Usar Chrome/Edge/Firefox para melhor compatibilidade
- Usar botão de Download se necessário

## Conclusão

A funcionalidade de visualização de PDF foi implementada com sucesso nas duas páginas principais do Portal do Consórcio:
- ✅ Dashboard
- ✅ Página de Boletos

Os usuários agora podem visualizar boletos diretamente no frontend, sem necessidade de downloads ou abrir novas abas, proporcionando uma experiência mais fluida e profissional.
