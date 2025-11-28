# 🎯 Como Adicionar Widget Canopus no Dashboard

## Passo a Passo - Edição Manual

### 1️⃣ Abra o arquivo do dashboard

```
D:\Nexus\frontend\templates\crm-cliente\dashboard.html
```

### 2️⃣ Localize a linha ~287 (Widget de Automação Mensal)

Procure por:
```html
<!-- Widget de Automação Mensal -->
<div class="widget-automacao">
```

### 3️⃣ ADICIONE o widget Canopus ANTES do widget de Automação Mensal

Insira o seguinte código **ANTES** da linha `<!-- Widget de Automação Mensal -->`:

```html
<!-- ============================================ -->
<!-- WIDGET CANOPUS - DOWNLOAD DE BOLETOS -->
<!-- ============================================ -->
{% include 'crm-cliente/widget-canopus-downloads.html' %}

<!-- Espaçamento -->
<div style="margin-bottom: 2rem;"></div>
```

### Resultado Final

O código ficará assim:

```html
        </div>

        <!-- ============================================ -->
        <!-- WIDGET CANOPUS - DOWNLOAD DE BOLETOS -->
        <!-- ============================================ -->
        {% include 'crm-cliente/widget-canopus-downloads.html' %}

        <!-- Espaçamento -->
        <div style="margin-bottom: 2rem;"></div>

        <!-- Widget de Automação Mensal -->
        <div class="widget-automacao">
            <div class="widget-header">
```

---

## ✅ Verificação

### 1. Reinicie o servidor Flask

```bash
# Se estiver rodando, pare com Ctrl+C
# Depois inicie novamente
cd D:\Nexus\backend
python app.py
```

### 2. Acesse o dashboard

```
http://localhost:5000/crm/dashboard
```

### 3. Verifique se o widget apareceu

Você deve ver:
- ✅ Título: "📥 Download Automático de Boletos"
- ✅ Dropdown para selecionar ponto de venda
- ✅ Campo para ano
- ✅ Campo para limite (opcional)
- ✅ Botão "🚀 Iniciar Downloads"

---

## 🧪 Teste Rápido

### 1. Selecione o ponto de venda `17.308`
### 2. Mantenha o ano `2025`
### 3. Digite `5` no campo limite (para testar com apenas 5 clientes)
### 4. Clique em "Iniciar Downloads"

### Resultado Esperado:

- Botão muda para "⏹ Cancelar"
- Aparece barra de progresso
- Aparece log de execução
- Após alguns minutos, mostra estatísticas:
  - Sucesso: X
  - Erros: Y
  - Não encontrados: Z
  - Sem boleto: W

---

## 📁 Arquivos Criados

1. **Widget HTML/CSS/JS**:
   ```
   D:\Nexus\frontend\templates\crm-cliente\widget-canopus-downloads.html
   ```

2. **API Backend** (já existe):
   ```
   D:\Nexus\backend\routes\automation_canopus.py
   ```
   - Nova rota: `/api/automation/processar-downloads-ponto-venda`

3. **Documentação**:
   ```
   D:\Nexus\INTEGRACAO_CANOPUS_CRM.md
   ```

---

## 🔧 Configurações Adicionais (Opcional)

### Adicionar Mais Pontos de Venda

Edite o widget (`widget-canopus-downloads.html`), linha ~24:

```html
<select id="ponto-venda-select" class="form-control">
    <option value="">Selecione...</option>
    <option value="17.308">17.308 - CredMS</option>
    <option value="17.309">17.309 - Semicrédito</option>
    <!-- ADICIONE MAIS AQUI -->
    <option value="16.254">16.254 - Outro Ponto</option>
</select>
```

### Alterar Intervalo de Polling

No widget, linha ~510:

```javascript
}, 3000); // Polling a cada 3 segundos
```

Altere `3000` para outro valor em milissegundos:
- `1000` = 1 segundo (mais rápido, mais requisições)
- `5000` = 5 segundos (mais lento, menos requisições)

---

## 🎨 Personalização Visual

### Alterar Cor do Widget

No widget, linha ~114:

```css
.widget-automacao-canopus {
    border-left: 4px solid #39FF14;  /* Verde neon */
}
```

Opções de cores:
- `#39FF14` - Verde neon (padrão)
- `#00D9FF` - Azul ciano
- `#FF6B35` - Laranja
- `#9D4EDD` - Roxo

### Alterar Cor do Botão

Linha ~241:

```css
.btn-primary {
    background: linear-gradient(135deg, #39FF14 0%, #2ad100 100%);
}
```

---

## 🚨 Solução de Problemas

### Widget não aparece no dashboard

1. **Verificar sintaxe**:
   - Certifique-se que o `{% include %}` está correto
   - Verifique se não há erros no console do Flask

2. **Limpar cache do navegador**:
   - Ctrl + F5 (forçar reload)
   - Ou Ctrl + Shift + Delete (limpar cache)

3. **Verificar caminho do arquivo**:
   ```bash
   # Deve retornar: arquivo existe
   ls "D:\Nexus\frontend\templates\crm-cliente\widget-canopus-downloads.html"
   ```

### Erro 404 na API

1. **Verificar se backend está rodando**:
   ```bash
   curl http://localhost:5000/api/automation/health
   ```

2. **Verificar se rota existe**:
   ```bash
   # Deve listar a rota
   grep "processar-downloads-ponto-venda" D:\Nexus\backend\routes\automation_canopus.py
   ```

### Downloads não iniciam

1. **Verificar credenciais no banco**:
   ```sql
   SELECT * FROM credenciais_canopus WHERE ativo = TRUE;
   ```

2. **Verificar se há clientes cadastrados**:
   ```sql
   SELECT COUNT(*)
   FROM clientes_finais cf
   JOIN consultores c ON c.id = cf.consultor_id
   JOIN pontos_venda pv ON pv.id = c.ponto_venda_id
   WHERE pv.codigo = '17.308' AND cf.ativo = TRUE;
   ```

3. **Ver logs da automação**:
   ```
   D:\Nexus\automation\canopus\logs\canopus_automation.log
   ```

---

## 📞 Próximos Passos

1. ✅ Adicionar widget no dashboard (seguir este guia)
2. ✅ Testar com 5 clientes (limite pequeno)
3. ✅ Verificar boletos baixados em:
   ```
   D:\Nexus\automation\canopus\downloads\Danner\
   ```
4. ✅ Verificar nomenclatura dos arquivos:
   ```
   NOME_CLIENTE_NOVEMBRO.pdf
   ```
5. ✅ Testar download em massa (sem limite)
6. ✅ Configurar agendamento automático (se necessário)

---

**Precisa de ajuda?**

Consulte a documentação completa:
```
D:\Nexus\INTEGRACAO_CANOPUS_CRM.md
```

Ou verifique os logs:
```
D:\Nexus\automation\canopus\logs\
```
