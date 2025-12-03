# ANÁLISE DO FLUXO DE NAVEGAÇÃO CANOPUS

## Objetivo
Documentar o fluxo HTTP completo usado pelo Playwright para identificar requisições que podem ser replicadas diretamente com aiohttp (HTTP Turbo).

---

## URLs PRINCIPAIS (do canopus_config.py)

```python
URLS = {
    'login': 'https://cnp3.consorciocanopus.com.br/',
    'busca': 'https://cnp3.consorciocanopus.com.br/WWW/CONCM/frmConCmBuscaAvancada.aspx',
    'emissao': 'https://cnp3.consorciocanopus.com.br/WWW/CONCM/frmConCmImpressao.aspx'
}
```

---

## FLUXO COMPLETO (Playwright - canopus_automation.py)

### 1. LOGIN
**Arquivo:** automation/canopus/canopus_automation.py:428-517

**Passos:**
1. Navegar para: `https://cnp3.consorciocanopus.com.br/`
2. Preencher campos:
   - Usuario input: `SELECTORS['login']['usuario_input']`
   - Senha input: `SELECTORS['login']['senha_input']`
3. Clicar: `SELECTORS['login']['botao_entrar']`
4. Aguardar: URL mudar (sair de /login)

**Requisições HTTP esperadas:**
- `GET /` (página inicial)
- `POST /login.aspx` ou similar (enviar credenciais)
- Cookies de sessão são salvos

---

### 2. BUSCA DE CLIENTE POR CPF
**Arquivo:** automation/canopus/canopus_automation.py:573-714

**Passos:**
1. Clicar ícone de Atendimento: `SELECTORS['busca']['icone_atendimento']`
2. Clicar "Busca avançada": `SELECTORS['busca']['botao_busca_avancada']`
3. Selecionar tipo de busca "CPF": `SELECTORS['busca']['select_tipo_busca']` value='F'
4. Preencher CPF: `SELECTORS['busca']['cpf_input']`
5. Clicar Buscar: `SELECTORS['busca']['botao_buscar']`
6. Aguardar resultados
7. Clicar no ÚLTIMO link de resultado: `SELECTORS['busca']['cliente_link']`

**Requisições HTTP esperadas:**
- `POST /frmConCmBuscaAvancada.aspx` (buscar CPF)
  - Dados do formulário ASP.NET:
    - `__VIEWSTATE`
    - `__VIEWSTATEGENERATOR`
    - `__EVENTVALIDATION`
    - Tipo de busca: CPF (F)
    - CPF digitado
- Resposta: HTML com tabela de resultados
- `GET /frmConCmCliente.aspx?id=...` (abrir cliente)

---

### 3. EMISSÃO DE COBRANÇA
**Arquivo:** automation/canopus/canopus_automation.py:719-746

**Passos:**
1. Clicar "Emissão de Cobrança": `SELECTORS['emissao']['menu_emissao']`
2. Aguardar página carregar (networkidle)

**Requisições HTTP esperadas:**
- `GET /frmConCmEmissao.aspx` ou similar
- Resposta: HTML com checkboxes de parcelas

---

### 4. DOWNLOAD DO BOLETO PDF
**Arquivo:** automation/canopus/canopus_automation.py:781-1701

**Passos:**
1. Aguardar checkboxes aparecerem: `SELECTORS['emissao']['checkbox_boleto']`
2. Selecionar ÚLTIMA checkbox (última parcela)
3. Clicar "Emitir Cobrança": `SELECTORS['emissao']['botao_emitir']`
4. Nova aba abre com PDF
5. Extrair PDF via JavaScript (fetch da URL do embed)

**Requisições HTTP esperadas:**
- `POST /frmConCmEmissao.aspx` (emitir boleto)
  - Dados do formulário:
    - `__VIEWSTATE`
    - Checkbox selecionada
- Resposta: abre popup/aba nova
- `GET /frmConCmImpressao.aspx?...` (PDF do boleto)
  - Content-Type: `application/pdf`
  - Tamanho esperado: ~170 KB

---

## TOKENS ASP.NET

O site usa ASP.NET WebForms, que exige tokens em TODOS os POSTs:

- `__VIEWSTATE`: Estado da página (grande string base64)
- `__VIEWSTATEGENERATOR`: ID do gerador
- `__EVENTVALIDATION`: Validação de evento

**Estes tokens precisam ser:**
1. Extraídos do HTML de cada página (via regex)
2. Enviados de volta em formulários POST

---

## ESTRATÉGIA HTTP TURBO

### Abordagem Híbrida (Recomendada)
1. **Login via Playwright** (1 vez apenas)
   - Capturar cookies de sessão
   - Capturar tokens iniciais

2. **Busca/Download via aiohttp** (paralelo)
   - Usar cookies capturados
   - Fazer requisições HTTP diretas
   - Processar 20-50 clientes simultaneamente

### Requisições Críticas para Replicar
1. POST busca CPF
2. GET página do cliente
3. GET página de emissão
4. POST emitir boleto
5. GET PDF

---

## PRÓXIMOS PASSOS

1. ✅ Executar `capturar_requisicoes.py` com CPF de teste
2. ⏳ Analisar `requisicoes_capturadas.json` gerado
3. ⏳ Identificar URLs e payloads exatos dos POSTs
4. ⏳ Implementar `CanopusHTTPTurbo` com aiohttp
5. ⏳ Testar com 5-10 clientes
6. ⏳ Ajustar paralelismo para máxima velocidade

---

## PERFORMANCE ESPERADA

| Método | Tempo/Boleto | 43 Boletos | RAM |
|--------|--------------|------------|-----|
| Playwright Original | 30-60s | ~30min | 1-2GB |
| Playwright Otimizado | 8-15s | ~8min | 1-2GB |
| HTTP Turbo (20 parallel) | 1-2s | ~30seg | 200MB |

---

**Data:** 2025-12-03
**Autor:** Claude Code
