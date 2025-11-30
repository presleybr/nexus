"""
Script para fazer backup dos números de WhatsApp dos clientes
Salva em JSON para restaurar depois do reset
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def fazer_backup_whatsapp():
    """Faz backup de todos os WhatsApps dos clientes"""

    print("=" * 80)
    print("BACKUP DE WHATSAPP DOS CLIENTES")
    print("=" * 80)

    # Buscar todos os clientes com WhatsApp
    clientes = db.execute_query("""
        SELECT
            cpf,
            nome_completo,
            whatsapp,
            telefone_celular,
            email
        FROM clientes_finais
        WHERE whatsapp IS NOT NULL
        AND whatsapp != ''
        AND whatsapp != '0000000000'
        AND whatsapp != '55679999999999'
        ORDER BY nome_completo
    """)

    if not clientes:
        print("\n[ERRO] Nenhum cliente com WhatsApp encontrado!")
        return

    # Preparar dados para backup
    backup_data = {
        'data_backup': datetime.now().isoformat(),
        'total_clientes': len(clientes),
        'clientes': {}
    }

    for cliente in clientes:
        cpf = cliente['cpf']
        backup_data['clientes'][cpf] = {
            'nome': cliente['nome_completo'],
            'whatsapp': cliente['whatsapp'],
            'telefone_celular': cliente.get('telefone_celular'),
            'email': cliente.get('email')
        }

    # Salvar arquivo de backup
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = os.path.join(backup_dir, 'whatsapp_clientes_backup.json')

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] BACKUP CONCLUIDO!")
    print(f"[ARQUIVO] {backup_file}")
    print(f"[TOTAL] {len(clientes)} clientes salvos")
    print(f"[DATA] {backup_data['data_backup']}")

    # Mostrar alguns exemplos
    print("\n[EXEMPLOS SALVOS]")
    for i, (cpf, dados) in enumerate(list(backup_data['clientes'].items())[:5]):
        print(f"  {i+1}. {dados['nome']}")
        print(f"     CPF: {cpf}")
        print(f"     WhatsApp: {dados['whatsapp']}")
        print()

    if len(clientes) > 5:
        print(f"  ... e mais {len(clientes) - 5} clientes")

    print("\n" + "=" * 80)
    print("[OK] Backup salvo! Agora voce pode resetar o banco de dados.")
    print("Os WhatsApps serao restaurados automaticamente na proxima importacao.")
    print("=" * 80)

if __name__ == '__main__':
    fazer_backup_whatsapp()
