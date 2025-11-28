"""
Debug: Verificar formato da senha no banco
"""

import sys
from db_config import get_connection_params
import psycopg
from psycopg.rows import dict_row

conn_params = get_connection_params()

try:
    with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.senha_encrypted,
                    pv.codigo
                FROM credenciais_canopus c
                JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                WHERE pv.codigo = '17.308'
                LIMIT 1
            """)

            resultado = cur.fetchone()

            if resultado:
                senha_encrypted = resultado['senha_encrypted']

                print()
                print("=" * 80)
                print("DEBUG: Senha Encrypted")
                print("=" * 80)
                print()
                print(f"Tipo: {type(senha_encrypted)}")
                print(f"Tipo nome: {type(senha_encrypted).__name__}")
                print()

                if isinstance(senha_encrypted, memoryview):
                    print("É memoryview! Convertendo para bytes...")
                    senha_bytes = bytes(senha_encrypted)
                    print(f"Tamanho: {len(senha_bytes)} bytes")
                    print(f"Primeiros 50 chars: {senha_bytes[:50]}")
                elif isinstance(senha_encrypted, bytes):
                    print("Já é bytes!")
                    print(f"Tamanho: {len(senha_encrypted)} bytes")
                    print(f"Primeiros 50 chars: {senha_encrypted[:50]}")
                elif isinstance(senha_encrypted, str):
                    print("É string!")
                    print(f"Tamanho: {len(senha_encrypted)} chars")
                    print(f"Primeiros 50 chars: {senha_encrypted[:50]}")
                else:
                    print(f"Tipo desconhecido: {type(senha_encrypted)}")
                    print(f"Valor: {senha_encrypted}")

                print()
                print("=" * 80)
            else:
                print("[ERRO] Credencial não encontrada")

except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
