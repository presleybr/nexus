"""
Reseta o status dos boletos do Canopus para permitir novos testes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("RESETANDO BOLETOS DO CANOPUS PARA TESTE")
print("="*80 + "\n")

# Resetar apenas boletos do Canopus
resultado = db.execute_update("""
    UPDATE boletos
    SET status_envio = 'nao_enviado',
        data_envio = NULL,
        enviado_por = NULL
    WHERE pdf_path LIKE '%canopus%'
    AND pdf_filename IS NOT NULL
""")

print(f"[OK] {resultado} boletos do Canopus resetados para 'nao_enviado'\n")

# Verificar quais boletos estão prontos agora
boletos_prontos = db.execute_query("""
    SELECT
        b.id,
        b.pdf_filename,
        cf.nome_completo,
        b.status_envio
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.pdf_path LIKE '%canopus%'
    AND b.pdf_filename IS NOT NULL
    ORDER BY b.data_vencimento ASC
    LIMIT 15
""")

if boletos_prontos:
    print(f"[INFO] Primeiros {len(boletos_prontos)} boletos do Canopus:\n")
    for b in boletos_prontos:
        status = "[PRONTO]" if b['status_envio'] == 'nao_enviado' else f"[{b['status_envio']}]"
        print(f"{status} ID {b['id']}: {b['nome_completo'][:35]:<35} ({b['pdf_filename']})")

print("\n" + "="*80)
print("[OK] Boletos do Canopus prontos para teste!")
print("="*80 + "\n")
