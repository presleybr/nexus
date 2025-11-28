# 🎯 Guia para Mapear Seletores CSS do Canopus

## O Que São Seletores?

Seletores CSS são como "endereços" dos elementos na página web. Precisamos deles para que o Playwright saiba onde clicar, digitar, etc.

**Exemplo:**
- `input[name="usuario"]` → Campo de entrada com atributo name="usuario"
- `#btnLogin` → Elemento com ID="btnLogin"
- `.btn-entrar` → Elemento com classe="btn-entrar"

## 📋 Passo a Passo

### 1. Executar Teste de Login

```cmd
cd D:\Nexus\automation\canopus
python teste_automacao.py --teste login --usuario SEU_USUARIO --senha SUA_SENHA --ponto-venda 17308
```

⚠️ **IMPORTANTE**: Este teste vai **FALHAR** propositalmente! É normal!

### 2. O Navegador Vai Abrir

O Playwright abrirá um navegador Chromium **visível** (não headless).

Você verá a página de login do Canopus.

### 3. Abrir DevTools (F12)

1. Com o navegador aberto, aperte **F12**
2. Isso abre as ferramentas de desenvolvedor do Chrome
3. Clique na aba **"Elements"** ou **"Elementos"**

### 4. Inspecionar Cada Campo

No canto superior esquerdo do DevTools, clique no ícone: 🔍 (Select an element)

Agora você pode **clicar em qualquer campo** da página e o DevTools vai mostrar o código HTML daquele elemento.

### 5. Mapear os Seletores

Para cada campo abaixo, clique nele com a ferramenta de inspeção e anote:

#### 📝 Campo: Código da Empresa

**Como identificar:**
- Procure por atributos: `id`, `name`, `class`
- Exemplo de HTML: `<input id="codigoEmpresa" name="empresa" />`

**Seletor recomendado:**
- Se tem `id`: use `#codigoEmpresa`
- Se tem `name`: use `input[name="empresa"]`

**Anote aqui:**
```
Código Empresa: _______________________
```

#### 📝 Campo: Ponto de Venda

**Anote aqui:**
```
Ponto de Venda: _______________________
```

#### 📝 Campo: Usuário

**Anote aqui:**
```
Usuario: _______________________
```

#### 📝 Campo: Senha

**Anote aqui:**
```
Senha: _______________________
```

#### 📝 Botão: Entrar/Login

**Anote aqui:**
```
Botao Login: _______________________
```

## 📄 Exemplo Real

Vamos supor que você encontrou:

```html
<input id="empresa" type="text" name="codigoEmpresa" />
<input id="pv" type="text" name="pontoVenda" />
<input id="user" type="text" name="usuario" />
<input id="pwd" type="password" name="senha" />
<button id="btnEntrar" type="submit">Entrar</button>
```

**Seletores seriam:**
```python
'empresa_input': '#empresa',          # ou 'input[name="codigoEmpresa"]'
'ponto_venda_input': '#pv',           # ou 'input[name="pontoVenda"]'
'usuario_input': '#user',             # ou 'input[name="usuario"]'
'senha_input': '#pwd',                # ou 'input[name="senha"]'
'botao_entrar': '#btnEntrar',         # ou 'button[type="submit"]'
```

## ✏️ Atualizar config.py

Depois de mapear, abra: `D:\Nexus\automation\canopus\config.py`

Procure pela linha **140** (seção `SELECTORS`):

```python
SELECTORS = {
    # Login
    'login': {
        'empresa_input': 'input[name="empresa"]',  # ⬅️ ATUALIZAR AQUI
        'ponto_venda_input': 'input[name="pontoVenda"]',  # ⬅️ ATUALIZAR AQUI
        'usuario_input': 'input[name="usuario"]',  # ⬅️ ATUALIZAR AQUI
        'senha_input': 'input[name="senha"]',  # ⬅️ ATUALIZAR AQUI
        'botao_entrar': 'button[type="submit"]',  # ⬅️ ATUALIZAR AQUI
        'erro_login': '.error-message, .alert-danger',
    },
```

Substitua pelos seletores que você mapeou.

## 🧪 Testar Novamente

Após atualizar, execute novamente:

```cmd
python teste_automacao.py --teste login --usuario X --senha Y --ponto-venda 17308
```

Agora deve funcionar! Se o login for bem-sucedido, você verá:
```
[OK] Login realizado com sucesso!
```

## 🔍 Dica: Tipos de Seletores

### Por ID (Melhor opção)
```python
'#meuId'              # Elemento com id="meuId"
```

### Por Name (Segunda melhor)
```python
'input[name="usuario"]'  # Input com name="usuario"
```

### Por Class (Pode ter vários elementos)
```python
'.btn-primary'        # Elemento com class="btn-primary"
```

### Por Tipo (Menos específico)
```python
'button[type="submit"]'  # Botão do tipo submit
```

## 🎯 Próximos Passos

Após mapear e testar o **login**:

1. ✅ Login funcionando
2. 🔜 Mapear seletores de **busca de cliente** (CPF)
3. 🔜 Mapear seletores de **emissão de boleto**
4. 🔜 Mapear seletores de **download do PDF**

Cada tela precisará de seus próprios seletores.

## 📞 Precisa de Ajuda?

Se encontrar dificuldades:

1. **Tire um print** do HTML no DevTools
2. **Anote** todos os atributos (id, name, class)
3. **Teste** diferentes seletores até achar um que funcione

**Exemplo de teste direto no console do navegador:**
```javascript
// No console do DevTools (F12 → Console):
document.querySelector('#usuario')  // Testa se encontra o elemento
```

Se retornar o elemento, o seletor está correto!

---

**Boa sorte no mapeamento!** 🚀

Depois de mapear, você poderá executar o download real de boletos.
