#!/usr/bin/env python3
"""
TESTE: Upload manual de planilha Excel para o Render
Simula o que o endpoint de upload faria
"""
import sys
from pathlib import Path

# Adicionar paths
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("="*80)
print("TESTE DE UPLOAD E PROCESSAMENTO DE PLANILHA")
print("="*80)

# Importar extrator
from services.excel_extractor import extrair_clientes_planilha

# Caminho da planilha local (você vai fazer upload depois)
planilha_local = Path("D:/Nexus/automation/canopus/excel_files")
planilhas_disponiveis = list(planilha_local.glob("*__PLANILHA_GERAL.xlsx"))

if not planilhas_disponiveis:
    print(f"\nNenhuma planilha encontrada em: {planilha_local}")
    print("\nColoque uma planilha com nome *__PLANILHA_GERAL.xlsx no diretorio")
    sys.exit(1)

planilha = planilhas_disponiveis[0]
print(f"\nPlanilha encontrada: {planilha.name}")
print(f"Caminho: {planilha}")

# Extrair dados
print("\nExtraindo dados da planilha...")
resultado = extrair_clientes_planilha(
    arquivo_excel=str(planilha),
    pontos_venda=['17308', '24627']  # Ambos
)

if not resultado['sucesso']:
    print(f"\nErro na extracao: {resultado.get('erro')}")
    sys.exit(1)

clientes = resultado['clientes']
print(f"\n{len(clientes)} clientes extraidos!")
print(f"\nEstatisticas por PV:")
for pv, qtd in resultado['estatisticas_pv'].items():
    print(f"   PV {pv}: {qtd} clientes")

# Mostrar primeiros 5
print(f"\nPrimeiros 5 clientes:")
for i, cliente in enumerate(clientes[:5], 1):
    print(f"\n{i}. {cliente['nome']}")
    print(f"   CPF: {cliente['cpf_formatado']}")
    print(f"   PV: {cliente['ponto_venda']}")
    print(f"   Grupo: {cliente.get('grupo', 'N/A')}")
    print(f"   Cota: {cliente.get('cota', 'N/A')}")

# Agora simular importação para o banco do Render
print(f"\n" + "="*80)
print("IMPORTANDO PARA O BANCO DO RENDER")
print("="*80)

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
cur = conn.cursor()

importados = 0
atualizados = 0
erros = 0

for idx, cliente in enumerate(clientes, 1):
    try:
        cpf = cliente['cpf']
        nome = cliente['nome']
        pv = cliente['ponto_venda']

        # Verificar se já existe
        cur.execute("""
            SELECT id FROM clientes_finais
            WHERE cpf = %s AND ponto_venda = %s
        """, (cpf, pv))

        existing = cur.fetchone()

        if existing:
            # Atualizar
            cur.execute("""
                UPDATE clientes_finais
                SET nome_completo = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (nome, existing['id']))
            atualizados += 1
            if idx <= 5:
                print(f"   OK [{idx}/{len(clientes)}] Atualizado: {nome} (PV {pv})")
        else:
            # Buscar cliente_nexus
            cur.execute("SELECT id FROM clientes_nexus LIMIT 1")
            cliente_nexus_row = cur.fetchone()
            cliente_nexus_id = cliente_nexus_row['id'] if cliente_nexus_row else None

            # Inserir novo
            numero_contrato = f"CANOPUS-{pv}-{cpf}"
            whatsapp = '5567999999999'  # Placeholder

            cur.execute("""
                INSERT INTO clientes_finais (
                    cliente_nexus_id,
                    nome_completo,
                    cpf,
                    telefone_celular,
                    whatsapp,
                    ponto_venda,
                    numero_contrato,
                    ativo,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (cliente_nexus_id, nome, cpf, whatsapp, whatsapp, pv, numero_contrato))

            importados += 1
            if idx <= 5:
                print(f"   + [{idx}/{len(clientes)}] Criado: {nome} (PV {pv})")

        # Commit a cada 100
        if idx % 100 == 0:
            conn.commit()
            print(f"\n   Checkpoint: {idx}/{len(clientes)} processados...")

    except Exception as e:
        erros += 1
        print(f"   ERRO ao processar {nome}: {e}")
        continue

# Commit final
conn.commit()
cur.close()
conn.close()

print(f"\n" + "="*80)
print("RESULTADO FINAL")
print("="*80)
print(f"Novos clientes importados: {importados}")
print(f"Clientes atualizados: {atualizados}")
print(f"Erros: {erros}")
print(f"Total processado: {importados + atualizados}")
print("="*80)
