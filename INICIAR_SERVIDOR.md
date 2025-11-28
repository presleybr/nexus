# 🚀 Como Iniciar o Servidor Nexus CRM

## Passo a Passo

### 1. Ativar o Ambiente Virtual

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Iniciar o Servidor Flask

```bash
python backend/app.py
```

Você verá mensagens como:
```
[OK] Aplicacao Flask inicializada com sucesso
[OK] Scheduler de automação iniciado - Verificações a cada hora (08:00-18:00)
============================================================
NEXUS CRM - SISTEMA DE AUTOMACAO DE BOLETOS
   Aqui seu tempo vale ouro
============================================================
Servidor rodando em: http://localhost:5000
```

### 3. Acessar a Interface

**Login do Cliente:**
- URL: http://localhost:5000/login-cliente
- Acesse: Dashboard → Disparos

**Página de Disparos:**
- URL: http://localhost:5000/crm/disparos

## ✅ Verificar se o Scheduler Está Funcionando

### Método 1: Via Logs do Console
Ao iniciar o servidor, procure por:
```
[OK] Scheduler de automação iniciado - Verificações a cada hora (08:00-18:00)
```

### Método 2: Via API
Abra no navegador:
```
http://localhost:5000/api/crm/scheduler/status
```

Resposta esperada:
```json
{
  "success": true,
  "scheduler": {
    "running": true,
    "jobs": [
      {
        "id": "verificar_automacoes_mensais",
        "name": "Verificar Automações Mensais",
        "next_run": "2025-01-16T14:00:00-04:00"
      }
    ],
    "timezone": "America/Campo_Grande"
  }
}
```

### Método 3: Testar Manualmente
1. Acesse: http://localhost:5000/crm/disparos
2. Configure o dia do mês
3. Clique em "Ativar"
4. Clique em "🧪 Testar Agora"
5. Verifique o histórico de disparos na mesma página

## 🔧 Configurar Automação Mensal

1. **Escolher o Dia do Mês:**
   - Dropdown com dias 1-31
   - Exemplo: "Dia 15" para disparar todo dia 15

2. **Ativar/Desativar:**
   - Botão verde = Ativado
   - Botão vermelho = Desativado

3. **Ver Próximo Disparo:**
   - Calculado automaticamente
   - Mostra data e horário

## 📊 Monitorar Execuções

### Via Interface
- Seção "Histórico de Automações" na página de disparos
- Mostra: data, tipo, sucessos, erros, tempo

### Via Banco de Dados
```sql
-- Verificar disparos automáticos
SELECT * FROM historico_disparos
WHERE tipo_disparo = 'automatico_mensal'
ORDER BY horario_execucao DESC;

-- Verificar logs do scheduler
SELECT * FROM logs_sistema
WHERE categoria = 'scheduler'
ORDER BY created_at DESC
LIMIT 20;
```

## ⚠️ Solução de Problemas

### Erro: "No module named 'pytz'"
```bash
pip install apscheduler pytz
```

### Erro: "Scheduler já está rodando"
- Normal se reiniciar o servidor rapidamente
- Aguarde 10 segundos e tente novamente

### Scheduler não executa
1. Verifique se está habilitado:
```sql
SELECT * FROM configuracoes_automacao;
```

2. Verifique o horário:
- Scheduler só roda das 08:00 às 18:00 (MS)

3. Verifique se já executou hoje:
```sql
SELECT * FROM historico_disparos
WHERE DATE(horario_execucao) = CURRENT_DATE;
```

### Testar Fora do Horário Comercial
Use o endpoint de teste:
```bash
curl -X POST http://localhost:5000/api/crm/scheduler/executar-agora \
  -H "Cookie: session=..."
```

Ou clique no botão "🧪 Testar Agora" na interface.

## 📝 Notas Importantes

- ⏰ **Horário:** Disparos ocorrem entre 08:00-18:00 (horário de MS)
- 📅 **Frequência:** Apenas 1x por dia, no dia configurado
- 🔄 **Automático:** Scheduler verifica a cada hora
- ✅ **Seguro:** Não executa duas vezes no mesmo dia

## 🎯 Próximos Passos

1. Configure o dia do mês desejado
2. Ative a automação
3. Aguarde o dia configurado ou teste manualmente
4. Monitore os resultados no histórico

---

**Nexus CRM - Aqui seu tempo vale ouro** ⏱️
