"""
Vincula os boletos do Canopus a um cliente Nexus
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("VINCULANDO BOLETOS DO CANOPUS AO CLIENTE NEXUS")
print("="*80 + "\n")

# Listar clientes Nexus disponíveis
clientes_nexus = db.execute_query("SELECT id, nome_empresa FROM clientes_nexus ORDER BY id")

if not clientes_nexus:
    print("[ERRO] Nenhum cliente Nexus encontrado!")
    sys.exit(1)

print("[INFO] Clientes Nexus disponíveis:\n")
for cn in clientes_nexus:
    print(f"  ID {cn['id']}: {cn['nome_empresa']}")

# Usar o primeiro cliente (ou você pode escolher outro)
cliente_nexus_id = clientes_nexus[0]['id']
print(f"\n[INFO] Usando Cliente Nexus ID {cliente_nexus_id}: {clientes_nexus[0]['nome_empresa']}\n")

# Vincular boletos do Canopus a este cliente
resultado = db.execute_update("""
    UPDATE boletos
    SET cliente_nexus_id = %s
    WHERE pdf_path LIKE '%%canopus%%'
    AND pdf_filename IS NOT NULL
""", (cliente_nexus_id,))

print(f"[OK] {resultado} boletos do Canopus vinculados ao cliente Nexus ID {cliente_nexus_id}\n")

# Verificar
boletos_vinculados = db.execute_query("""
    SELECT COUNT(*) as total
    FROM boletos
    WHERE pdf_path LIKE '%%canopus%%'
    AND cliente_nexus_id = %s
""", (cliente_nexus_id,))

print(f"[OK] Total de boletos do Canopus vinculados: {boletos_vinculados[0]['total']}")

print("\n" + "="*80)
print("[OK] Boletos do Canopus agora estao vinculados!")
print("="*80 + "\n")
