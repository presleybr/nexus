# GUIA DE TESTE COM DADOS REAIS

**Sistema:** Nexus CRM - Teste de Disparo de Boletos
**Objetivo:** Testar fluxo completo com cliente e PDF reais, mas sem enviar para cliente verdadeiro

---

## 🎯 CONCEITO

Ao invés de criar dados fake:
1. ✅ Usa cliente REAL do banco
2. ✅ Usa boleto PDF REAL da pasta Canopus
3. ✅ Modifica WhatsApp temporariamente (adiciona "9" após o DDD)
4. ✅ Testa disparo completo
5. ✅ Envio SUCESSO mas para número diferente (seguro!)
6. ✅ Restaura WhatsApp original após teste

**Exemplo:**
- WhatsApp original: `5567841266146` (DDD 67)
- WhatsApp teste: `556799841266146` (adiciona 9 após DDD - envia para outro número)

---

## 📋 PRÉ-REQUISITOS

### 1. Boletos PDFs Reais
``` 
Pasta: D:\Nexus\automation\canopus\downloads\Danner\
```

Se não tem PDFs, execute primeiro:
```bash
# Baixar boletos reais do Canopus
python automation/canopus/orquestrador.py
```

### 2. Clientes no Banco
Deve ter pelo menos 1 cliente com WhatsApp cadastrado:
```sql
SELECT id, nome_completo, whatsapp
FROM clientes_finais
WHERE whatsapp IS NOT NULL
LIMIT 10;
```

---

## 🚀 USO BÁSICO

### Opção 1: Configuração Automática (Recomendado)

```bash
cd D:\Nexus\backend\scripts

# Executar script interativo
python configurar_teste_real.py
```

**O script vai:**
1. Listar boletos PDFs disponíveis
2. Você escolhe qual boleto usar
3. Busca automaticamente o cliente pelo nome do PDF
4. Modifica WhatsApp (adiciona "9" no final)
5. Vincula o PDF ao registro de boleto no banco
6. Salva info em `ultimo_teste.txt` para restaurar depois

---

### Opção 2: Comandos Específicos

#### Listar Boletos Disponíveis
```bash
python configurar_teste_real.py --listar-boletos
```

**Output:**
```
[BOLETOS] Boletos disponiveis em D:\Nexus\automation\canopus\downloads\Danner:
------------------------------------------------------------
  [1] JOAO_SILVA_11_2024.pdf                         (245.3 KB)
  [2] MARIA_SANTOS_11_2024.pdf                       (238.7 KB)
  [3] PEDRO_OLIVEIRA_11_2024.pdf                     (241.2 KB)
------------------------------------------------------------
  Total: 150 boletos
```

#### Listar Clientes Disponíveis
```bash
python configurar_teste_real.py --listar-clientes
```

**Output:**
```
[CLIENTES] Clientes reais disponiveis para teste:
--------------------------------------------------------------------------------
ID    Nome                                WhatsApp        Boletos
--------------------------------------------------------------------------------
1077  JEFFERSON DOURADO MENDES            556796600884    3
1078  JOSE DE ALMEIDA                     556796600884    2
1079  OSMAR CAVASSANI                     556796600884    1
--------------------------------------------------------------------------------
```

#### Listar Testes Ativos
```bash
python configurar_teste_real.py --listar-testes
```

**Output:**
```
[TESTES] Boletos de teste ativos:
----------------------------------------------------------------------------------------------------
ID     Numero Boleto        Cliente                        WhatsApp        Status
----------------------------------------------------------------------------------------------------
523    TESTE-1077-11-2024   JEFFERSON DOURADO MENDES       5567966008849   nao_enviado
----------------------------------------------------------------------------------------------------
```

#### Restaurar WhatsApp Após Teste
```bash
# Restaurar último teste
python configurar_teste_real.py --restaurar-ultimo

# Ou restaurar manualmente
python configurar_teste_real.py --restaurar 1077 556796600884
```

#### Resetar Boleto para Testar Novamente
```bash
# Resetar boleto específico
python configurar_teste_real.py --resetar-boleto 523

# Resetar todos os boletos de teste
python configurar_teste_real.py --resetar-boleto
```

---

## 📝 FLUXO COMPLETO DO TESTE

### Passo 1: Configurar Teste
```bash
cd D:\Nexus\backend\scripts
python configurar_teste_real.py
```

**Interação:**
```
==============================================================
CONFIGURAR TESTE COM CLIENTE E BOLETO REAIS
==============================================================

[BOLETOS] Boletos disponiveis em D:\Nexus\automation\canopus\downloads\Danner:
------------------------------------------------------------
  [1] JEFFERSON_DOURADO_MENDES_11_2024.pdf          (245.3 KB)
  [2] JOSE_DE_ALMEIDA_11_2024.pdf                   (238.7 KB)
------------------------------------------------------------
  Total: 150 boletos

Escolha o numero do boleto (ou ENTER para o primeiro): 1

[OK] Boleto selecionado: JEFFERSON_DOURADO_MENDES_11_2024.pdf

[BUSCA] Procurando cliente: JEFFERSON DOURADO MENDES
   [OK] Encontrado: JEFFERSON DOURADO MENDES

[CLIENTE] Cliente selecionado:
   ID: 1077
   Nome: JEFFERSON DOURADO MENDES
   CPF: 123.456.789-01
   WhatsApp: 556796600884

==============================================================
[ATENCAO] Vamos modificar o WhatsApp temporariamente!
          O numero original sera salvo para restaurar depois.
==============================================================

Continuar? (s/N): s

[WHATSAPP] WhatsApp modificado para teste:
   Original: 556796600884
   Teste:    5567966008849 (numero INVALIDO)

[BOLETO] Boleto criado:
   ID: 523
   Cliente ID: 1077
   PDF: JEFFERSON_DOURADO_MENDES_11_2024.pdf
   Mes/Ano: 11/2024
   Status envio: nao_enviado

==============================================================
[SUCESSO] TESTE CONFIGURADO COM SUCESSO!
==============================================================

Cliente ID:     1077
Nome:           JEFFERSON DOURADO MENDES
WhatsApp teste: 5567966008849 (invalido - nao envia)
Boleto ID:      523
PDF:            JEFFERSON_DOURADO_MENDES_11_2024.pdf

PROXIMOS PASSOS:
1. Acesse http://127.0.0.1:5000/crm/dashboard
2. Execute o disparo de boletos
3. Verifique os logs no terminal
4. O envio vai FALHAR (numero invalido) - isso e esperado!
5. Apos teste, execute:
   python configurar_teste_real.py --restaurar-ultimo

[SALVO] Info salva em ultimo_teste.txt para restaurar depois
```

---

### Passo 2: Executar Disparo no Dashboard

1. Abra navegador: `http://127.0.0.1:5000/crm/dashboard`
2. Faça login com suas credenciais
3. Vá em "Disparos" ou "Automação Completa"
4. Clique em "Executar Disparo"

---

### Passo 3: Verificar Logs no Terminal

**Logs esperados:**
```
[INFO] 🚀 Iniciando disparos para 1 clientes COM WhatsApp
[INFO] 📱 [1/1] Processando: JEFFERSON DOURADO MENDES → 5567966008849
[INFO] 📤 [1/1] Enviando boleto para JEFFERSON DOURADO MENDES (5567966008849)
[ERROR] ❌ [1/1] ERRO ao enviar boleto para JEFFERSON DOURADO MENDES: Número inválido
```

**✅ Isso é ESPERADO!** O número com "9" extra é inválido propositalmente.

**O importante é verificar:**
- ✅ Sistema identificou o cliente
- ✅ Sistema encontrou o boleto
- ✅ Sistema tentou enviar (mas falhou - esperado)
- ✅ Logs estão detalhados

---

### Passo 4: Restaurar WhatsApp Original

**IMPORTANTE:** Sempre restaurar após o teste!

```bash
python configurar_teste_real.py --restaurar-ultimo
```

**Output:**
```
[OK] WhatsApp restaurado: 556796600884
[OK] Arquivo ultimo_teste.txt removido
```

---

## 🔄 TESTAR NOVAMENTE

Se quiser testar de novo com o mesmo boleto:

```bash
# 1. Resetar status do boleto
python configurar_teste_real.py --resetar-boleto 523

# 2. Executar disparo novamente no dashboard
```

---

## 🐛 DEBUG E TROUBLESHOOTING

### Problema: "Nenhum PDF encontrado"

**Solução:**
```bash
# Verificar se pasta existe
dir "D:\Nexus\automation\canopus\downloads\Danner"

# Se vazia, executar automação Canopus para baixar boletos
python automation/canopus/orquestrador.py
```

---

### Problema: "Cliente não encontrado no banco"

**Solução 1:** Usar cliente existente
```bash
# Listar clientes disponíveis
python configurar_teste_real.py --listar-clientes

# Escolher ID manualmente durante setup
```

**Solução 2:** Adicionar WhatsApp aos clientes
```bash
python backend/scripts/adicionar_whatsapp_teste.py
```

---

### Problema: Disparo não aparece nos logs

**Verificar:**
1. ✅ Boleto está com `status_envio = 'nao_enviado'`
2. ✅ Cliente tem WhatsApp cadastrado
3. ✅ PDF existe no caminho especificado

```bash
# Verificar status do boleto
python backend/scripts/diagnostico_disparo_urgente.py
```

---

### Problema: WhatsApp não foi restaurado

**Restaurar manualmente:**
```bash
# Se sabe o número original
python configurar_teste_real.py --restaurar 1077 556796600884

# Ou verificar no banco
SELECT id, nome_completo, whatsapp FROM clientes_finais WHERE id = 1077;

# E atualizar manualmente
UPDATE clientes_finais SET whatsapp = '556796600884' WHERE id = 1077;
```

---

## 📊 VERIFICAÇÕES DE SEGURANÇA

### Antes de Executar Teste:
```sql
-- Ver WhatsApp do cliente
SELECT id, nome_completo, whatsapp FROM clientes_finais WHERE id = 1077;
```

### Após Restaurar:
```sql
-- Confirmar que voltou ao normal
SELECT id, nome_completo, whatsapp FROM clientes_finais WHERE id = 1077;
```

### Verificar Boletos de Teste:
```sql
-- Listar todos os boletos de teste
SELECT
    b.id,
    b.numero_boleto,
    b.status_envio,
    cf.nome_completo,
    cf.whatsapp
FROM boletos b
JOIN clientes_finais cf ON b.cliente_final_id = cf.id
WHERE b.numero_boleto LIKE 'TESTE-%';
```

---

## ⚠️ AVISOS IMPORTANTES

### ✅ FAZER:
- ✅ Sempre restaurar WhatsApp após teste
- ✅ Verificar logs detalhadamente
- ✅ Usar número inválido (com "9" extra)
- ✅ Testar em horário de baixo movimento
- ✅ Documentar resultados do teste

### ❌ NÃO FAZER:
- ❌ **NUNCA** usar WhatsApp real de cliente para teste
- ❌ **NUNCA** esquecer de restaurar WhatsApp original
- ❌ **NUNCA** executar teste em produção sem backup
- ❌ **NUNCA** testar com múltiplos clientes reais simultaneamente
- ❌ **NUNCA** modificar dados sem ter `ultimo_teste.txt` salvo

---

## 📁 ARQUIVOS ENVOLVIDOS

### Script Principal:
```
D:\Nexus\backend\scripts\configurar_teste_real.py
```

### Arquivo de Backup (gerado automaticamente):
```
D:\Nexus\backend\scripts\ultimo_teste.txt
```

**Formato:** `cliente_id,whatsapp_original`
**Exemplo:** `1077,556796600884`

### PDFs de Boletos:
```
D:\Nexus\automation\canopus\downloads\Danner\*.pdf
```

---

## 🎓 EXEMPLOS DE USO REAL

### Cenário 1: Teste Rápido com Primeiro Boleto
```bash
# Setup
python configurar_teste_real.py
# Pressionar ENTER para usar primeiro boleto
# Digitar 's' para confirmar

# Testar no dashboard
# (executar disparo)

# Restaurar
python configurar_teste_real.py --restaurar-ultimo
```

### Cenário 2: Escolher Boleto Específico
```bash
# Listar boletos
python configurar_teste_real.py --listar-boletos

# Setup escolhendo boleto #5
python configurar_teste_real.py
# Digitar: 5
# Digitar: s

# Testar e restaurar
python configurar_teste_real.py --restaurar-ultimo
```

### Cenário 3: Testar Múltiplas Vezes
```bash
# Setup inicial
python configurar_teste_real.py

# Teste 1
# (executar disparo no dashboard)

# Resetar para testar novamente
python configurar_teste_real.py --resetar-boleto 523

# Teste 2
# (executar disparo no dashboard)

# Restaurar
python configurar_teste_real.py --restaurar-ultimo
```

---

## 📞 SUPORTE

**Problemas?** Execute diagnóstico completo:
```bash
python backend/scripts/diagnostico_disparo_urgente.py
```

**Dúvidas?** Consulte:
- `D:\Nexus\MAPA_SISTEMA.md` - Mapa completo do sistema
- `D:\Nexus\CORRECAO_DISPARO_BOLETOS.md` - Correção recente

---

**Versão:** 1.0
**Data:** 2025-11-27
**Status:** ✅ Testado e funcional
