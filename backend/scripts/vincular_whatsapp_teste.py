"""
Script para vincular números de WhatsApp de teste aos clientes sem WhatsApp cadastrado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

# Números de WhatsApp de teste (8 dígitos - sem o nono dígito)
NUMEROS_TESTE = [
    "556731224813",
    "556796376010",
    "556715342531",
    "556711629169",
    "556754436309",
    "556791478669",
    "556735799810",
    "556703377105",
    "556718669257",
    "556740544573",
    "556796600884"
]


def vincular_whatsapp_teste():
    """Vincula números de teste aos clientes sem WhatsApp"""

    print("\n" + "="*60)
    print("VINCULANDO NÚMEROS DE WHATSAPP DE TESTE AOS CLIENTES")
    print("="*60 + "\n")

    # 1. Buscar todos os clientes sem WhatsApp
    clientes_sem_whatsapp = db.execute_query("""
        SELECT id, nome_completo, cpf, cliente_nexus_id
        FROM clientes_finais
        WHERE (whatsapp IS NULL OR whatsapp = '')
        AND ativo = true
        ORDER BY id ASC
    """)

    if not clientes_sem_whatsapp:
        print("[OK] Todos os clientes ja possuem WhatsApp cadastrado!")
        return

    total_clientes = len(clientes_sem_whatsapp)
    print(f"[INFO] Encontrados {total_clientes} clientes sem WhatsApp cadastrado\n")

    # 2. Vincular números de forma cíclica
    atualizados = 0

    for idx, cliente in enumerate(clientes_sem_whatsapp):
        # Usa módulo para distribuir os números ciclicamente
        numero_teste = NUMEROS_TESTE[idx % len(NUMEROS_TESTE)]

        # Atualiza o cliente
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s
            WHERE id = %s
        """, (numero_teste, cliente['id']))

        atualizados += 1
        print(f"[OK] Cliente {cliente['nome_completo'][:30]:<30} -> {numero_teste}")

    print("\n" + "="*60)
    print(f"[OK] CONCLUIDO! {atualizados} clientes atualizados com numeros de teste")
    print("="*60)
    print("\n[IMPORTANTE]")
    print("   - Esses sao numeros de TESTE para validar os disparos")
    print("   - Voce pode editar os WhatsApps corretos depois no CRM")
    print("   - Os numeros foram distribuidos ciclicamente entre os clientes\n")


def listar_distribuicao():
    """Lista como os números foram distribuídos"""

    print("\n" + "="*60)
    print("DISTRIBUIÇÃO DOS NÚMEROS DE TESTE")
    print("="*60 + "\n")

    for numero in NUMEROS_TESTE:
        clientes = db.execute_query("""
            SELECT id, nome_completo
            FROM clientes_finais
            WHERE whatsapp = %s
            AND ativo = true
        """, (numero,))

        total = len(clientes) if clientes else 0
        print(f"[WhatsApp] {numero}: {total} cliente(s)")

        if clientes:
            for cliente in clientes[:3]:  # Mostra até 3 clientes
                print(f"   - {cliente['nome_completo'][:40]}")
            if total > 3:
                print(f"   ... e mais {total - 3} cliente(s)")
        print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Vincula números de teste aos clientes')
    parser.add_argument('--listar', action='store_true',
                       help='Lista a distribuição atual dos números')

    args = parser.parse_args()

    if args.listar:
        listar_distribuicao()
    else:
        vincular_whatsapp_teste()
        print("\n[INFO] Para ver a distribuicao, execute:")
        print("   python vincular_whatsapp_teste.py --listar\n")
