"""
Testa busca de credencial no banco
"""

import sys
from db_config import get_connection_params
import psycopg
from psycopg.rows import dict_row

def listar_credenciais():
    """Lista todas as credenciais cadastradas"""
    conn_params = get_connection_params()

    try:
        with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        c.id,
                        c.usuario,
                        c.codigo_empresa,
                        c.ativo,
                        pv.codigo as ponto_venda,
                        pv.nome as ponto_venda_nome,
                        LENGTH(c.senha_encrypted) as tamanho_senha
                    FROM credenciais_canopus c
                    JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    ORDER BY pv.codigo
                """)

                credenciais = cur.fetchall()

                print()
                print("=" * 80)
                print("CREDENCIAIS CADASTRADAS")
                print("=" * 80)
                print()

                if credenciais:
                    for cred in credenciais:
                        status = "ATIVO" if cred['ativo'] else "INATIVO"
                        print(f"ID: {cred['id']}")
                        print(f"  PV: {cred['ponto_venda']} - {cred['ponto_venda_nome']}")
                        print(f"  Usuario: {cred['usuario']}")
                        print(f"  Codigo Empresa: {cred['codigo_empresa']}")
                        print(f"  Senha criptografada: {cred['tamanho_senha']} bytes")
                        print(f"  Status: {status}")
                        print()
                else:
                    print("[ERRO] Nenhuma credencial cadastrada!")
                    print()
                    print("Execute: python cadastrar_credencial.py")

                print("=" * 80)

    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    listar_credenciais()
