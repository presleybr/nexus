# Diagnóstico: Por Que o Servidor Reiniciou?

## 🎯 Resposta Curta
O servidor **NÃO deveria reiniciar** sozinho. Você está no **plano Starter** que não tem timeout de idle. Se reiniciou, foi por **crash** (não intencional).

---

## 🔍 Causas Prováveis do Reinício

### 1. **MEMÓRIA INSUFICIENTE (OOM Kill)** 🔴 MAIS PROVÁVEL

**O Problema:**
- **Plano Starter**: 512 MB RAM máximo
- **Chromium**: 300-500 MB
- **Python + Flask**: ~100 MB
- **Total**: Pode ultrapassar 512 MB

**O Que Acontece:**
1. Sistema começa a processar boletos
2. Chromium abre e consome 400 MB
3. Após ~20 downloads, memória chega a 510 MB
4. Container tenta alocar mais memória
5. **Render mata o processo (OOM killed)**
6. Container reinicia automaticamente

**Como Identificar nos Logs:**
```
📊 MONITORAMENTO DE RECURSOS (Cliente 20/43)
   Memória RAM: 498.5 MB
⚠️ MEMÓRIA ALTA! 498.5 MB / 512 MB limite

[Logs param aqui - não vê "EXECUÇÃO FINALIZADA NORMALMENTE"]
```

**Se você NÃO vê** esta mensagem no final dos logs:
```
✅ EXECUÇÃO FINALIZADA NORMALMENTE (SEM CRASH)
```
→ **O servidor crashou!**

---

### 2. **Exception Não Capturada** ⚠️

**O Problema:**
Algum erro no código Python mata o processo inteiro.

**Como Identificar:**
```
ERROR:automation.canopus.canopus_automation:❌ Erro ao ...
Traceback (most recent call last):
  ...
Exception: ...

[Servidor reinicia - Render detecta que processo morreu]
```

---

### 3. **Timeout de Operação** ⏱️ (Menos Provável)

**O Problema:**
Downloads muito lentos podem causar timeout em alguma operação.

**Como Identificar:**
```
TimeoutError: ...
playwright._impl._api_types.TimeoutError: ...
```

---

## 🛠️ Solução Implementada

### **Monitoramento de Memória Automático**

**A cada 5 clientes processados:**
```
📊 MONITORAMENTO DE RECURSOS (Cliente 5/43)
   Memória RAM: 380.2 MB

📊 MONITORAMENTO DE RECURSOS (Cliente 10/43)
   Memória RAM: 425.8 MB
⚠️ MEMÓRIA ALTA! 425.8 MB / 512 MB limite
   Executando garbage collection...
   Memória após GC: 385.3 MB  ← Liberou 40 MB!
```

**Ao finalizar:**
```
🎉 DOWNLOADS CONCLUÍDOS!
   ...
   📊 Memória final: 350.2 MB
✅ EXECUÇÃO FINALIZADA NORMALMENTE (SEM CRASH)
```

---

## 📊 Como Diagnosticar o Próximo Reinício

### **Passo 1: Acessar Logs do Render**
1. Dashboard do Render → Selecione o backend
2. Aba "Logs"
3. Procure pela última execução

### **Passo 2: Procurar Indicadores**

**A) Crash por Memória (OOM):**
```
📊 MONITORAMENTO DE RECURSOS (Cliente 20/43)
   Memória RAM: 498.5 MB

[Logs param aqui sem "FINALIZADA NORMALMENTE"]
```
→ Memória encheu e processo foi morto

**B) Execução Normal:**
```
📊 Memória final: 350.2 MB
✅ EXECUÇÃO FINALIZADA NORMALMENTE (SEM CRASH)
```
→ Completou sem problemas

**C) Erro de Código:**
```
ERROR: ...
Traceback:
  File "...", line X
    ...
Exception: ...
```
→ Bug no código

### **Passo 3: Identificar Último Boleto Baixado**

Procure nos logs:
```
💾 ✅ Download registrado no banco: NOME_CLIENTE_DEZEMBRO.pdf
```

O último que aparece = último sucesso antes do crash

---

## 🚀 Próximas Ações Recomendadas

### **Se for OOM (Memória):**

**Opção 1: Upgrade de Plano (RECOMENDADO)**
- Starter: 512 MB → $7/mês
- Standard: 2 GB → $25/mês
- Processa 100+ boletos sem problemas

**Opção 2: Processar em Lotes**
- Dividir 43 clientes em 2 lotes de ~20
- Processar primeiro lote, esperar concluir
- Processar segundo lote
- Memória é limpa entre lotes

**Opção 3: Otimizar Chromium** (mais complexo)
- Usar flags de economia de memória
- Fechar/reabrir navegador a cada 10 downloads
- Sacrifica velocidade por estabilidade

### **Se for Exception:**
- Me envie o traceback completo
- Corrigiremos o bug específico

### **Se for Timeout:**
- Aumentar timeouts no Playwright
- Verificar velocidade da conexão com Canopus

---

## 📋 Checklist de Verificação

Quando o servidor reiniciar novamente:

- [ ] Acessei os logs do Render?
- [ ] Vi mensagem "EXECUÇÃO FINALIZADA NORMALMENTE"?
  - **SIM** → Completou normal, não foi crash
  - **NÃO** → Foi crash, continuar checklist
- [ ] Vi avisos "MEMÓRIA ALTA" nos logs?
  - **SIM** → Provável OOM, considerar upgrade
  - **NÃO** → Outro problema
- [ ] Vi Traceback de erro?
  - **SIM** → Erro de código, reportar
  - **NÃO** → Provável OOM
- [ ] Encontrei último boleto baixado?
  - Procurar: "Download registrado no banco"
  - Sistema retoma do próximo automaticamente

---

## 🎯 Resumo

**Servidor reiniciou após ~21 downloads:**
- ✅ Sistema de retomada já implementado
- ✅ Monitoramento de memória adicionado
- ✅ Garbage collection automático
- ⚠️ Plano Starter (512MB) pode ser insuficiente
- 💡 Considerar upgrade para Standard (2GB)

**Próximo teste:**
1. Faça deploy desta versão
2. Inicie downloads
3. Monitore logs em tempo real
4. Se crashar:
   - Verifique última memória reportada
   - Veja se tem "FINALIZADA NORMALMENTE"
   - Sistema retoma automaticamente
