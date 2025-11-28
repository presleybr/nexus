"""
Verificar boletos no banco de dados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("VERIFICANDO BOLETOS NO BANCO DE DADOS")
print("="*80 + "\n")

# Total de boletos
total = db.execute_query("""
    SELECT COUNT(*) as total
    FROM boletos
""")

print(f"Total de boletos no banco: {total[0]['total'] if total else 0}")

# Boletos por mês
por_mes = db.execute_query("""
    SELECT mes_referencia, COUNT(*) as total
    FROM boletos
    GROUP BY mes_referencia
    ORDER BY mes_referencia DESC
    LIMIT 5
""")

if por_mes:
    print("\nBoletos por mês:")
    for m in por_mes:
        print(f"  - {m['mes_referencia']}: {m['total']} boletos")
else:
    print("\n[AVISO] Nenhum boleto encontrado no banco!")

# Boletos de dezembro especificamente
dezembro = db.execute_query("""
    SELECT COUNT(*) as total
    FROM boletos
    WHERE mes_referencia = 'DEZEMBRO'
    OR mes_referencia = 'dezembro'
""")

print(f"\nBoletos de DEZEMBRO: {dezembro[0]['total'] if dezembro else 0}")

# Últimos 5 boletos cadastrados
ultimos = db.execute_query("""
    SELECT id, numero_boleto, mes_referencia, ano_referencia, cliente_final_id, created_at
    FROM boletos
    ORDER BY created_at DESC
    LIMIT 5
""")

if ultimos:
    print("\nÚltimos 5 boletos cadastrados:")
    for b in ultimos:
        print(f"  - ID {b['id']}: {b['numero_boleto']} | {b['mes_referencia']}/{b['ano_referencia']} | Cliente: {b['cliente_final_id']} | {b['created_at']}")

print("\n" + "="*80 + "\n")
