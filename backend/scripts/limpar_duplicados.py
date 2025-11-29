#!/usr/bin/env python3
"""
Script para remover boletos duplicados do banco de dados
Mantém apenas o boleto mais antigo (menor ID) de cada cliente/mês/ano
"""

import sys
import os
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db

def main():

    print("=" * 70)
    print("🔍 ANÁLISE DE BOLETOS DUPLICADOS")
    print("=" * 70)

    # 1. Verificar quantos duplicados existem
    print("\n1️⃣ Verificando duplicados...")
    duplicados = db.execute_query("""
        SELECT
            cliente_final_id,
            mes_referencia,
            ano_referencia,
            COUNT(*) as quantidade,
            STRING_AGG(id::text, ', ' ORDER BY id) as ids_duplicados
        FROM boletos
        GROUP BY cliente_final_id, mes_referencia, ano_referencia
        HAVING COUNT(*) > 1
        ORDER BY quantidade DESC
        LIMIT 10
    """)

    if duplicados:
        print(f"\n⚠️  Encontrados grupos de boletos duplicados:")
        print(f"\n{'Cliente ID':<12} {'Mês/Ano':<10} {'Qtd':<6} IDs Duplicados")
        print("-" * 70)
        for dup in duplicados:
            print(f"{dup['cliente_final_id']:<12} {dup['mes_referencia']:02d}/{dup['ano_referencia']:<6} {dup['quantidade']:<6} {dup['ids_duplicados']}")
    else:
        print("\n✅ Nenhum boleto duplicado encontrado!")
        return

    # Contar total de duplicados
    total_stats = db.execute_query("""
        SELECT
            COUNT(*) as grupos_duplicados,
            SUM(quantidade - 1) as total_para_deletar
        FROM (
            SELECT
                cliente_final_id,
                mes_referencia,
                ano_referencia,
                COUNT(*) as quantidade
            FROM boletos
            GROUP BY cliente_final_id, mes_referencia, ano_referencia
            HAVING COUNT(*) > 1
        ) subq
    """)

    if total_stats:
        stats = total_stats[0]
        print(f"\n📊 Estatísticas:")
        print(f"   • Grupos de duplicados: {stats['grupos_duplicados']}")
        print(f"   • Boletos a serem deletados: {stats['total_para_deletar']}")

    # 2. Confirmar deleção
    print("\n" + "=" * 70)
    resposta = input("\n⚠️  Deseja DELETAR os boletos duplicados? (Digite 'SIM' para confirmar): ")

    if resposta.strip().upper() != 'SIM':
        print("\n❌ Operação cancelada pelo usuário")
        return

    # 3. Deletar duplicados
    print("\n2️⃣ Deletando boletos duplicados...")
    print("   (Mantendo apenas o mais antigo de cada grupo)")

    resultado = db.execute_query("""
        WITH duplicados AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY cliente_final_id, mes_referencia, ano_referencia
                    ORDER BY id ASC
                ) as rn
            FROM boletos
        )
        DELETE FROM boletos
        WHERE id IN (
            SELECT id FROM duplicados WHERE rn > 1
        )
        RETURNING id
    """)

    if resultado:
        print(f"\n✅ {len(resultado)} boletos duplicados foram deletados!")
    else:
        print("\n✅ Nenhum boleto foi deletado")

    # 4. Verificar resultado
    print("\n3️⃣ Verificando resultado...")
    duplicados_restantes = db.execute_query("""
        SELECT
            cliente_final_id,
            mes_referencia,
            ano_referencia,
            COUNT(*) as quantidade
        FROM boletos
        GROUP BY cliente_final_id, mes_referencia, ano_referencia
        HAVING COUNT(*) > 1
    """)

    if duplicados_restantes:
        print(f"\n⚠️  ATENÇÃO: Ainda existem {len(duplicados_restantes)} grupos de duplicados!")
    else:
        print("\n✅ Sucesso! Não há mais boletos duplicados no banco de dados")

    # 5. Estatísticas finais
    total_boletos = db.execute_query("SELECT COUNT(*) as total FROM boletos")
    if total_boletos:
        print(f"\n📊 Total de boletos restantes: {total_boletos[0]['total']}")

    print("\n" + "=" * 70)
    print("✅ PROCESSO CONCLUÍDO")
    print("=" * 70)

if __name__ == '__main__':
    main()
