# 📅 Automação Mensal de Disparos - Nexus CRM

## Visão Geral

Sistema de agendamento automático de disparos de boletos via WhatsApp, configurável por dia do mês.

## Funcionalidades

### ✨ Características Principais

1. **Agendamento por Dia do Mês**
   - Cliente escolhe um dia específico do mês (1-31)
   - Disparos ocorrem automaticamente neste dia
   - Horário fixo: 08:00 às 18:00 (horário de Mato Grosso do Sul)

2. **Controle Liga/Desliga**
   - Botão simples para ativar/desativar a automação
   - Status visível na interface
   - Mudanças instantâneas

3. **Execução Automática**
   - Scheduler roda a cada hora durante horário comercial (08h-18h)
   - Verifica se hoje é o dia configurado
   - Executa apenas uma vez por dia
   - Registra no histórico de disparos

4. **Teste Manual**
   - Botão "Testar Agora" para executar imediatamente
   - Útil para validar configurações
   - Não depende do agendamento

## Instalação

### 1. Aplicar Migration no Banco de Dados

Execute o script SQL de migration:

```bash
psql -U postgres -d nexus_crm -f database/migrations/003_add_dia_do_mes_automacao.sql
```

Ou conecte ao banco e execute manualmente:

```sql
ALTER TABLE configuracoes_automacao
ADD COLUMN IF NOT EXISTS dia_do_mes INTEGER DEFAULT 1 CHECK (dia_do_mes >= 1 AND dia_do_mes <= 31);
```

### 2. Instalar Dependências

O scheduler usa APScheduler e pytz:

```bash
cd backend
pip install apscheduler pytz
```

### 3. Reiniciar a Aplicação

O scheduler é inicializado automaticamente quando o Flask inicia:

```bash
python backend/app.py
```

Você verá a mensagem:
```
[OK] Scheduler de automação iniciado - Verificações a cada hora (08:00-18:00)
```

## Como Usar

### Interface Web

1. **Acessar a Página de Disparos**
   - Login no sistema: http://localhost:5000/login-cliente
   - Menu lateral: "Disparos"

2. **Configurar Agendamento**
   - Seção "Agendamento Mensal Automático" no topo
   - Escolha o dia do mês (1-31)
   - Clique em "Ativar" para habilitar

3. **Verificar Próximo Disparo**
   - Informação exibida automaticamente quando ativado
   - Mostra data e horário do próximo disparo

4. **Testar Configuração**
   - Botão "Testar Agora" executa imediatamente
   - Verifique os logs e histórico

### API Endpoints

#### Obter Configurações
```bash
GET /api/crm/configuracoes-automacao
```

Resposta:
```json
{
  "success": true,
  "configuracao": {
    "disparo_automatico_habilitado": true,
    "dia_do_mes": 5,
    "mensagem_antibloqueio": "Olá! Tudo bem?...",
    "intervalo_min_segundos": 3,
    "intervalo_max_segundos": 7
  }
}
```

#### Atualizar Configurações
```bash
PUT /api/crm/configuracoes-automacao
Content-Type: application/json

{
  "disparo_automatico_habilitado": true,
  "dia_do_mes": 10
}
```

#### Executar Agora (Teste)
```bash
POST /api/crm/scheduler/executar-agora
```

#### Verificar Status do Scheduler
```bash
GET /api/crm/scheduler/status
```

Resposta:
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

## Funcionamento Interno

### Fluxo de Execução

1. **Scheduler Verifica** (a cada hora, 08h-18h)
   ```
   ├─ Busca clientes com automação habilitada
   ├─ Verifica se dia_do_mes == dia atual
   ├─ Verifica se já executou hoje
   └─ Executa automação se necessário
   ```

2. **Execução da Automação**
   ```
   ├─ Chama automation_service.executar_automacao_completa()
   ├─ Gera boletos para todos os clientes
   ├─ Envia via WhatsApp
   ├─ Registra no histórico_disparos
   └─ Envia notificação ao empresário
   ```

3. **Registro no Histórico**
   ```sql
   INSERT INTO historico_disparos (
     tipo_disparo = 'automatico_mensal',
     total_envios,
     envios_sucesso,
     envios_erro,
     horario_execucao,
     executado_por = 'scheduler_automatico'
   )
   ```

### Estrutura de Arquivos

```
backend/
├── services/
│   ├── automation_scheduler.py     # Novo: Scheduler principal
│   └── automation_service.py       # Existente: Lógica de automação
├── routes/
│   └── crm.py                      # Atualizado: Novos endpoints
└── app.py                          # Atualizado: Inicializa scheduler

database/
└── migrations/
    └── 003_add_dia_do_mes_automacao.sql  # Novo: Migration

frontend/
└── templates/
    └── crm-cliente/
        └── disparos.html           # Atualizado: Interface
```

## Logs e Monitoramento

### Visualizar Logs

Os logs são salvos na tabela `logs_sistema` com categoria `'scheduler'`:

```sql
SELECT * FROM logs_sistema
WHERE categoria = 'scheduler'
ORDER BY created_at DESC
LIMIT 50;
```

### Verificar Histórico de Execuções

```sql
SELECT * FROM historico_disparos
WHERE tipo_disparo = 'automatico_mensal'
ORDER BY horario_execucao DESC;
```

### Logs no Console

Ao iniciar o sistema, você verá:
```
[OK] Scheduler de automação iniciado - Verificações a cada hora (08:00-18:00)
```

Durante execução:
```
[INFO] Verificando automações agendadas para dia 15
[INFO] Encontrados 2 clientes para processamento
[SUCCESS] Automação mensal concluída para Empresa X
```

## Configurações Avançadas

### Alterar Horário Comercial

Edite `backend/services/automation_scheduler.py`:

```python
# Linha ~44-45
horario_inicio = time(8, 0)   # 08:00
horario_fim = time(18, 0)     # 18:00
```

### Alterar Frequência de Verificação

No mesmo arquivo:

```python
# Linha ~135
CronTrigger(hour='8-18', minute='0')  # A cada hora
# Altere para:
CronTrigger(hour='8-18', minute='*/30')  # A cada 30 minutos
```

### Alterar Timezone

```python
# Linha ~28
self.scheduler = BackgroundScheduler(timezone='America/Campo_Grande')
```

## Solução de Problemas

### Scheduler não está rodando

Verifique os logs:
```bash
grep "scheduler" backend/logs/app.log
```

Restart o serviço Flask.

### Automação não executou no dia esperado

1. Verifique se está habilitada:
   ```sql
   SELECT * FROM configuracoes_automacao WHERE cliente_nexus_id = X;
   ```

2. Verifique se já executou hoje:
   ```sql
   SELECT * FROM historico_disparos
   WHERE cliente_nexus_id = X
   AND DATE(horario_execucao) = CURRENT_DATE;
   ```

3. Verifique os logs de erro:
   ```sql
   SELECT * FROM logs_sistema
   WHERE tipo = 'error' AND categoria = 'scheduler';
   ```

### Teste manual falha

Use o endpoint com curl:
```bash
curl -X POST http://localhost:5000/api/crm/scheduler/executar-agora \
  -H "Cookie: session=..." \
  -v
```

## Segurança

- ✅ Requer autenticação (@login_required)
- ✅ Verifica cliente_nexus_id da sessão
- ✅ Validação de dia_do_mes (1-31)
- ✅ Confirmação antes de ativar/desativar
- ✅ Logs de todas as operações

## Performance

- Scheduler leve, roda em background
- Verificação rápida (query simples)
- Executa apenas uma vez por dia
- Não impacta requisições HTTP

## Próximos Passos (Melhorias Futuras)

1. ⚡ Notificações push quando automação executar
2. 📊 Dashboard de estatísticas de automação
3. 📧 Envio de relatório por email
4. 🔔 Alertas se automação falhar
5. 📅 Múltiplos agendamentos por mês
6. ⏰ Horário personalizável por cliente

## Suporte

Para dúvidas ou problemas:
- Verifique os logs em `logs_sistema`
- Consulte `historico_disparos`
- Entre em contato com o suporte técnico

---

**Nexus CRM - Aqui seu tempo vale ouro** ⏱️✨
