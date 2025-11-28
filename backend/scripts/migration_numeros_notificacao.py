"""
Migration: Criar tabela numeros_notificacao
Data: 2025-11-27
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def criar_tabela_numeros_notificacao():
    """Cria tabela para armazenar números que recebem notificações"""

    print("=" * 60)
    print("MIGRATION: Criar tabela numeros_notificacao")
    print("=" * 60)

    # Criar tabela
    db.execute_update("""
        CREATE TABLE IF NOT EXISTS numeros_notificacao (
            id SERIAL PRIMARY KEY,
            cliente_nexus_id INTEGER NOT NULL REFERENCES clientes_nexus(id) ON DELETE CASCADE,
            nome VARCHAR(100) NOT NULL,
            whatsapp VARCHAR(20) NOT NULL,
            ativo BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("[OK] Tabela 'numeros_notificacao' criada/verificada")

    # Criar índice
    db.execute_update("""
        CREATE INDEX IF NOT EXISTS idx_numeros_notificacao_cliente
        ON numeros_notificacao(cliente_nexus_id)
    """)

    print("[OK] Índice criado")

    # Inserir números padrão para o cliente_nexus_id = 2
    numeros_padrao = [
        (2, 'Empresário 1', '556796600884'),
        (2, 'Empresário 2', '556798905585')
    ]

    for cliente_nexus_id, nome, whatsapp in numeros_padrao:
        # Verificar se já existe
        existe = db.execute_query("""
            SELECT id FROM numeros_notificacao
            WHERE cliente_nexus_id = %s AND whatsapp = %s
        """, (cliente_nexus_id, whatsapp))

        if not existe:
            db.execute_update("""
                INSERT INTO numeros_notificacao (cliente_nexus_id, nome, whatsapp)
                VALUES (%s, %s, %s)
            """, (cliente_nexus_id, nome, whatsapp))
            print(f"[OK] Número inserido: {nome} - {whatsapp}")
        else:
            print(f"[SKIP] Número já existe: {nome} - {whatsapp}")

    print("\n" + "=" * 60)
    print("MIGRATION CONCLUÍDA COM SUCESSO!")
    print("=" * 60)

if __name__ == '__main__':
    criar_tabela_numeros_notificacao()
