# HTTP TURBO - PRÓXIMOS PASSOS

## STATUS ATUAL
✅ Playwright otimizado: 8-15s por boleto (~8min para 43 boletos)
⏳ HTTP Turbo: Aguardando implementação

## PARA IMPLEMENTAR HTTP TURBO

### Passo 1: Capturar Requisições
```bash
cd automation/canopus
set CANOPUS_USUARIO=seu_usuario
set CANOPUS_SENHA=sua_senha
set CANOPUS_CPF_TESTE=12345678901
python capturar_requisicoes.py
```

### Passo 2: Analisar Resultados
- Abrir: `requisicoes_capturadas.json`
- Identificar:
  - URLs de POST (busca, emissão)
  - Campos do formulário ASP.NET
  - Estrutura de dados

### Passo 3: Implementar HTTP Turbo
- Completar `canopus_http_turbo.py`
- Implementar métodos de busca e download
- Testar com 5-10 clientes

### Passo 4: Integrar com Backend
- Adicionar rota `/baixar-boletos-turbo`
- Adicionar botão no frontend

## PERFORMANCE ESPERADA
- Playwright otimizado: ~8min para 43 boletos
- HTTP Turbo: ~30seg para 43 boletos
- Ganho: 16x mais rápido

