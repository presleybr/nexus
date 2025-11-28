# 🎯 Próximo Passo: Ensinar o Robô

## ✅ Login Funcionando!

O login está funcionando perfeitamente. Agora precisamos ensinar o robô a fazer o resto do processo.

## 🤖 O Que o Robô Precisa Aprender

1. **Buscar cliente por CPF** → Encontrar o cliente no sistema
2. **Emitir boleto** → Gerar a cobrança/boleto
3. **Baixar PDF** → Fazer download do arquivo

## 📋 Método Interativo (RECOMENDADO)

Execute este script que vai te guiar passo a passo:

```cmd
python mapear_seletores_interativo.py
```

### O que vai acontecer:

1. **Login automático** → O robô faz login sozinho
2. **Pausa para você mapear BUSCA**:
   - Você navega até a tela de busca de cliente
   - Aperta F12, inspeciona os elementos
   - Anota os seletores (campo CPF, botão buscar, etc.)
   - Digita os seletores no terminal

3. **Testa a busca** → O robô tenta buscar um CPF de exemplo

4. **Pausa para você mapear EMISSÃO**:
   - Você vai até a tela de emissão de boleto
   - Mapeia seletor de parcela, botão emitir, etc.

5. **Pausa para você mapear DOWNLOAD**:
   - Você identifica o link/botão de download do PDF

6. **Salva tudo** → Gera arquivo `seletores_mapeados.json`

## 📝 Informações que Você Precisa Mapear

### 1. Busca de Cliente

```
[ ] Menu/Link para acessar busca de cliente
    Exemplo: a[href*="busca"], #menuBusca, .nav-busca

[ ] Campo de input do CPF
    Exemplo: input[name="cpf"], #txtCPF, input.cpf-input

[ ] Botão de buscar
    Exemplo: button[type="submit"], #btnBuscar, .btn-search

[ ] Lista de resultados (onde aparece o cliente)
    Exemplo: .resultado-lista, table.clientes, #gridResultados

[ ] Link para o cliente (para clicar e abrir detalhes)
    Exemplo: a.cliente-nome, .link-cliente
```

### 2. Emissão de Boleto

```
[ ] Menu/Link para emissão de cobrança
    Exemplo: a[href*="emissao"], #menuCobranca

[ ] Seletor de parcela/mês de referência
    Exemplo: select[name="parcela"], #cmbParcela

[ ] Botão de gerar/emitir boleto
    Exemplo: button#btnEmitir, .btn-gerar-boleto

[ ] Mensagem de sucesso
    Exemplo: .alert-success, .mensagem-ok, #msgSucesso
```

### 3. Download do PDF

```
[ ] Link/botão de download do PDF
    Exemplo: a[href*=".pdf"], button.btn-download, #linkPDF

[ ] Ou botão de imprimir/visualizar
    Exemplo: button.btn-imprimir, a[target="_blank"]
```

## 🔍 Como Encontrar os Seletores

### Passo 1: Abrir DevTools
- Pressione **F12** no navegador
- Clique na aba **Elements** (ou **Elementos**)

### Passo 2: Selecionar Elemento
- Clique no ícone **🔍** (Select element)
- Clique no campo/botão que você quer mapear

### Passo 3: Copiar Seletor
No HTML que aparecer, procure por:

```html
<input id="txtCPF" name="cpf" class="form-control" />
```

**Opções de seletor (da melhor para pior)**:
1. **Por ID** (melhor): `#txtCPF`
2. **Por name**: `input[name="cpf"]`
3. **Por class**: `input.form-control` (pode ter vários!)
4. **Copy selector**: Botão direito → Copy → Copy selector

## 📸 Screenshots Automáticos

O script tira screenshots automaticamente em:
- `D:\Nexus\automation\canopus\logs\`

Você pode revisar depois para ver se funcionou.

## ⚡ Método Manual (Alternativa)

Se preferir fazer manualmente:

1. **Execute o teste de login**:
   ```cmd
   python teste_automacao.py --teste login --usuario 24627 --senha Sonhorealizado2! --ponto-venda 17308
   ```

2. **Deixe o navegador aberto** (não feche!)

3. **Navegue manualmente** pelas telas

4. **Use F12** para inspecionar cada elemento

5. **Anote em um papel**:
   ```
   Busca CPF:
   - Campo CPF: _________________
   - Botão buscar: _________________

   Emissão:
   - Seletor parcela: _________________
   - Botão emitir: _________________

   Download:
   - Link PDF: _________________
   ```

6. **Edite config.py** manualmente com os seletores

## 🎯 Depois de Mapear

Quando terminar, você terá o arquivo `seletores_mapeados.json` com algo assim:

```json
{
  "data_mapeamento": "2025-11-25T22:30:00",
  "seletores": {
    "login": {
      "usuario_input": "#edtUsuario",
      "senha_input": "#edtSenha",
      "botao_entrar": "#btnLogin"
    },
    "busca": {
      "menu_busca": "a[href*='busca']",
      "cpf_input": "input[name='cpf']",
      "botao_buscar": "button#btnBuscar",
      "resultado_lista": ".grid-resultados"
    },
    "emissao": {
      "select_parcela": "select#cmbParcela",
      "botao_emitir": "button#btnEmitir",
      "mensagem_sucesso": ".alert-success"
    },
    "download": {
      "link_pdf": "a[href*='.pdf']"
    }
  }
}
```

Aí é só copiar para `config.py` e testar o download completo!

## 🚀 Execute Agora

```cmd
cd D:\Nexus\automation\canopus
python mapear_seletores_interativo.py
```

O script vai te guiar passo a passo! 🎯
