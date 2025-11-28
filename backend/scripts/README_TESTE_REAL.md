# Script de Teste com Dados Reais

## 🎯 Uso Rápido

```bash
cd D:\Nexus\backend\scripts

# Configurar teste (interativo)
python configurar_teste_real.pyW

# Após teste, restaurar WhatsApp
python configurar_teste_real.py --restaurar-ultimo
```

## 📋 Comandos Disponíveis

```bash
# Listar boletos PDFs disponíveis
python configurar_teste_real.py --listar-boletos

# Listar clientes do banco
python configurar_teste_real.py --listar-clientes

# Listar testes ativos
python configurar_teste_real.py --listar-testes

# Restaurar último teste
python configurar_teste_real.py --restaurar-ultimo

# Restaurar manualmente
python configurar_teste_real.py --restaurar 1077 556796600884

# Resetar boleto para testar novamente
python configurar_teste_real.py --resetar-boleto 523
```

## ✅ O Que o Script Faz

1. Lista boletos PDFs reais da pasta Canopus
2. Você escolhe qual boleto usar
3. Busca cliente correspondente no banco
4. **Modifica WhatsApp** (adiciona "9" após DDD = número diferente)
5. Vincula PDF ao boleto no banco
6. Salva info para restaurar depois

## ⚠️ IMPORTANTE

- WhatsApp modificado: `5567841266146` → `556799841266146` (DDD 67 + 9)
- Número válido mas diferente = envio para outro número (seguro!)
- **SEMPRE restaurar** após teste!

## 📚 Documentação Completa

Ver: `D:\Nexus\GUIA_TESTE_REAL.md`
