#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica boletos registrados no banco de dados
"""
import sys
import psycopg
from psycopg.rows import dict_row
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("=" * 80)
print("VERIFICAÇÃO DE BOLETOS NO BANCO DE DADOS")
print("=" * 80)

try:
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    # 1. Verificar se tabela boletos existe
    print("\n🔍 Verificando estrutura da tabela boletos...")
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'boletos'
        ORDER BY ordinal_position
    """)
    colunas = cur.fetchall()

    if colunas:
        print(f"✅ Tabela 'boletos' existe com {len(colunas)} colunas:")
        for col in colunas[:10]:  # Mostrar primeiras 10 colunas
            print(f"   - {col['column_name']}: {col['data_type']}")
    else:
        print("❌ Tabela 'boletos' não existe!")
        sys.exit(1)

    # 2. Contar total de boletos
    print("\n📊 Contando boletos no banco...")
    cur.execute("SELECT COUNT(*) as total FROM boletos")
    total = cur.fetchone()['total']
    print(f"✅ Total de boletos no banco: {total}")

    if total == 0:
        print("\n⚠️ NENHUM BOLETO REGISTRADO NO BANCO!")
        print("\nPossíveis causas:")
        print("  1. A importação automática não está funcionando")
        print("  2. O PDF extractor está falhando")
        print("  3. Os PDFs não estão sendo salvos")
        print("  4. Erro silencioso durante a importação")
    else:
        # 3. Mostrar últimos boletos registrados
        print("\n📋 Últimos 10 boletos registrados:")
        cur.execute("""
            SELECT
                b.id,
                b.numero_boleto,
                b.valor,
                b.data_vencimento,
                b.mes_referencia,
                b.ano_referencia,
                b.arquivo_pdf,
                b.status,
                b.created_at,
                cf.nome_completo as cliente_nome,
                cf.cpf
            FROM boletos b
            LEFT JOIN clientes_finais cf ON cf.id = b.cliente_final_id
            ORDER BY b.created_at DESC
            LIMIT 10
        """)
        boletos = cur.fetchall()

        for i, boleto in enumerate(boletos, 1):
            print(f"\n{i}. Boleto ID: {boleto['id']}")
            print(f"   Cliente: {boleto['cliente_nome']} (CPF: {boleto['cpf']})")
            print(f"   Número: {boleto['numero_boleto']}")
            print(f"   Valor: R$ {boleto['valor']}")
            print(f"   Vencimento: {boleto['data_vencimento']}")
            print(f"   Referência: {boleto['mes_referencia']}/{boleto['ano_referencia']}")
            print(f"   Arquivo: {boleto['arquivo_pdf']}")
            print(f"   Status: {boleto['status']}")
            print(f"   Registrado em: {boleto['created_at']}")

        # 4. Estatísticas por mês
        print("\n📈 Estatísticas por mês/ano:")
        cur.execute("""
            SELECT
                mes_referencia,
                ano_referencia,
                COUNT(*) as total,
                SUM(valor) as valor_total,
                status
            FROM boletos
            GROUP BY mes_referencia, ano_referencia, status
            ORDER BY ano_referencia DESC, mes_referencia DESC
        """)
        stats = cur.fetchall()

        for stat in stats:
            print(f"   {stat['mes_referencia']}/{stat['ano_referencia']}: {stat['total']} boletos | "
                  f"Total: R$ {stat['valor_total']:.2f} | Status: {stat['status']}")

        # 5. Verificar boletos de DEZEMBRO/2025
        print("\n🎯 Boletos de DEZEMBRO/2025:")
        cur.execute("""
            SELECT COUNT(*) as total
            FROM boletos
            WHERE mes_referencia = 12 AND ano_referencia = 2025
        """)
        dez_2025 = cur.fetchone()['total']
        print(f"   Total: {dez_2025} boletos")

        # 6. Verificar boletos sem arquivo_pdf
        print("\n⚠️ Boletos sem arquivo PDF vinculado:")
        cur.execute("""
            SELECT COUNT(*) as total
            FROM boletos
            WHERE arquivo_pdf IS NULL OR arquivo_pdf = ''
        """)
        sem_pdf = cur.fetchone()['total']
        print(f"   Total: {sem_pdf} boletos")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ Verificação concluída!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ Erro ao conectar no banco: {e}")
    import traceback
    traceback.print_exc()
