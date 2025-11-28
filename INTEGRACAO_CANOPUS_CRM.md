# Integração Canopus - Dashboard CRM

## 📋 Resumo

Sistema completo de download automático de boletos do Canopus integrado ao CRM Nexus.

## 🚀 Funcionalidades

- ✅ Download automático de boletos por CPF
- ✅ Busca de nome do cliente na planilha Excel
- ✅ Extração automática do mês do boleto da página
- ✅ Nomenclatura automática: `{NOME_CLIENTE}_{MES}.pdf`
- ✅ API REST completa para gerenciamento
- ✅ Widget de interface para dashboard
- ✅ Download em massa por ponto de venda
- ✅ Progresso em tempo real
- ✅ Log de execução

---

## 📁 Estrutura de Arquivos

```
D:\Nexus\
├── automation\canopus\
│   ├── canopus_automation.py          # Automação principal
│   ├── canopus_automation_optimized.py # Versão otimizada
│   ├── orquestrador.py                 # Orquestrador de downloads em massa
│   ├── config.py                       # Configurações
│   ├── db_config.py                    # Configuração do banco
│   ├── testar_busca_cpf.py            # Script de teste
│   └── excel_files\
│       └── DENER__PLANILHA_GERAL.xlsx  # Planilha com dados dos clientes
│
├── backend\routes\
│   └── automation_canopus.py           # API REST
│
└── frontend\templates\crm-cliente\
    └── widget-canopus-downloads.html   # Widget do dashboard
```

---

## 🔧 Instalação e Configuração

### 1. Dependências Python

Já instaladas no ambiente:
```
playwright==1.40.0
pandas==2.1.4
openpyxl==3.1.2
psycopg[binary]==3.1.16
cryptography==41.0.7
```

### 2. Estrutura do Banco de Dados

Tabelas necessárias (já criadas):
- `pontos_venda`
- `consultores`
- `credenciais_canopus`
- `clientes_finais`
- `log_downloads_boletos`
- `execucoes_automacao`

### 3. Credenciais Canopus

As credenciais estão armazenadas na tabela `credenciais_canopus`:
- **Ponto de Venda**: 17.308
- **Usuário**: 24627
- **Senha**: Criptografada com Fernet

---

## 🌐 API REST

### Base URL
```
http://localhost:5000/api/automation
```

### Endpoints Principais

#### 1. Processar Downloads por Ponto de Venda (NOVO)

```http
POST /api/automation/processar-downloads-ponto-venda
Content-Type: application/json

{
  "ponto_venda": "17.308",
  "ano": 2025,
  "limite": 100          // opcional - deixe null para todos
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Downloads processados para 150 clientes",
  "data": {
    "automacao_id": "uuid-da-execucao",
    "ponto_venda": "17.308",
    "total_clientes": 150,
    "sucessos": 142,
    "erros": 5,
    "cpf_nao_encontrado": 2,
    "sem_boleto": 1
  }
}
```

#### 2. Consultar Execução

```http
GET /api/automation/execucoes/{automacao_id}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "execucao": {
      "automacao_id": "uuid",
      "tipo": "download_boletos",
      "status": "concluida",
      "total_clientes": 150,
      "processados_sucesso": 142,
      "processados_erro": 5,
      "iniciado_em": "2025-11-26T01:30:00",
      "finalizado_em": "2025-11-26T02:15:00"
    },
    "logs_stats": [...]
  }
}
```

#### 3. Listar Execuções

```http
GET /api/automation/execucoes?limite=10&status=concluida
```

#### 4. Estatísticas Gerais

```http
GET /api/automation/estatisticas
```

#### 5. Health Check

```http
GET /api/automation/health
```

---

## 🎨 Integração no Dashboard

### Opção 1: Incluir Widget Diretamente

Edite `D:\Nexus\frontend\templates\crm-cliente\dashboard.html`:

```html
<!-- Adicione após os outros widgets -->
{% include 'crm-cliente/widget-canopus-downloads.html' %}
```

### Opção 2: Código Manual

Adicione o seguinte código ao dashboard:

```html
<!-- No final do body, antes de fechar </body> -->
<div class="container">
    {% include 'crm-cliente/widget-canopus-downloads.html' %}
</div>
```

---

## 📊 Como Funciona

### Fluxo de Download

1. **Usuário acessa o dashboard**
2. **Seleciona o ponto de venda** (ex: 17.308)
3. **Define ano e limite** (opcional)
4. **Clica em "Iniciar Downloads"**
5. **Backend processa:**
   - Busca todos os CPFs do ponto de venda no banco
   - Inicia automação Playwright
   - Para cada cliente:
     - Busca nome na planilha Excel
     - Faz login no Canopus
     - Busca cliente por CPF
     - Navega para emissão de cobrança
     - Extrai mês do boleto da página
     - Baixa o boleto com nome: `{NOME_CLIENTE}_{MES}.pdf`
     - Salva em: `D:\Nexus\automation\canopus\downloads\{CONSULTOR}\`
6. **Frontend atualiza progresso em tempo real** (polling a cada 3s)
7. **Exibe estatísticas ao concluir**

### Exemplo de Nomenclatura

**Entrada:**
- CPF: `708.990.571-36`
- Nome na planilha: `WESLEY JUNIOR DIDEROT CHERISCAR - 70%`
- Mês na página: `NOVEMBRO`

**Saída:**
- Arquivo: `WESLEY_JUNIOR_DIDEROT_CHERISCAR_NOVEMBRO.pdf`

---

## 🧪 Testes

### Teste Manual Individual

```bash
cd D:\Nexus\automation\canopus
python testar_busca_cpf.py --cpf 708.990.571-36
```

### Teste via API (Postman/cURL)

```bash
curl -X POST http://localhost:5000/api/automation/processar-downloads-ponto-venda \
  -H "Content-Type: application/json" \
  -d '{
    "ponto_venda": "17.308",
    "ano": 2025,
    "limite": 5
  }'
```

---

## 🔐 Segurança

- ✅ Senhas criptografadas com Fernet
- ✅ Anti-detecção Playwright (remove webdriver flag)
- ✅ Validação de entrada na API
- ✅ Tratamento de erros robusto
- ✅ Logs de auditoria

---

## 📈 Performance

### Métricas Atuais

- **Login**: ~3-5 segundos
- **Busca de cliente**: ~2-3 segundos
- **Download de boleto**: ~8-12 segundos
- **Total por cliente**: ~15-20 segundos

### Otimizações Implementadas

- ✅ Reutilização de sessão de navegador
- ✅ Interceptação de PDF direto da resposta
- ✅ Processamento assíncrono com asyncio
- ✅ Delays humanizados
- ✅ Anti-detecção para evitar bloqueios

### Estimativa de Tempo

- **10 clientes**: ~3-5 minutos
- **50 clientes**: ~15-20 minutos
- **100 clientes**: ~30-40 minutos
- **500 clientes**: ~2h30-3h30

---

## 🐛 Troubleshooting

### Erro: "Cliente não encontrado na planilha"

**Causa**: CPF não existe na planilha Excel

**Solução**:
1. Verificar se a planilha está atualizada
2. Verificar formatação do CPF na planilha
3. Caminho: `D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx`

### Erro: "Target page, context or browser has been closed"

**Causa**: Tab do boleto fecha muito rápido

**Solução**: Já implementado - captura URL e reabre em aba controlada

### Erro: "Login falhou"

**Causa**: Credenciais incorretas ou expiradas

**Solução**:
1. Verificar credenciais no banco: tabela `credenciais_canopus`
2. Testar login manual no Canopus
3. Atualizar senha se necessário

### Performance lenta

**Solução**:
1. Usar `headless=True` para mais velocidade
2. Implementar paralelização (múltiplas instâncias)
3. Processar em lotes menores

---

## 🔮 Próximas Melhorias

### Curto Prazo
- [ ] WebSocket para progresso em tempo real (substituir polling)
- [ ] Notificação por WhatsApp ao concluir
- [ ] Agendamento de downloads automáticos
- [ ] Dashboard de estatísticas avançado

### Médio Prazo
- [ ] Paralelização com múltiplas instâncias do navegador
- [ ] Upload automático para cloud (S3/Google Drive)
- [ ] OCR para extrair dados dos boletos
- [ ] Integração com sistema de cobrança

### Longo Prazo
- [ ] Machine Learning para predição de falhas
- [ ] Auto-recuperação de erros
- [ ] Multi-tenancy (múltiplos pontos de venda simultâneos)

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs: `D:\Nexus\automation\canopus\logs\`
2. Consultar tabela `log_downloads_boletos` no banco
3. Verificar screenshots: `D:\Nexus\automation\canopus\screenshots\`

---

## ✅ Checklist de Implantação

- [x] Automação desenvolvida e testada
- [x] API REST implementada
- [x] Widget de interface criado
- [ ] Widget integrado ao dashboard.html
- [ ] Teste em produção
- [ ] Documentação interna
- [ ] Treinamento de usuários

---

**Desenvolvido para Nexus CRM**
**Data**: 26/11/2025
**Versão**: 1.0.0
