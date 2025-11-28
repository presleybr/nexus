"""
Cadastra credenciais do Canopus de forma interativa
Salva criptografado na tabela credenciais_canopus

Uso: python cadastrar_credencial.py
"""

import sys
import getpass
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    print("[ERRO] psycopg nao instalado!")
    print("Execute: pip install psycopg psycopg-binary")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("[ERRO] cryptography nao instalado!")
    print("Execute: pip install cryptography")
    sys.exit(1)

# Importar configurações do banco
from db_config import get_connection_params

# Chave de criptografia (IMPORTANTE: Em produção, use variável de ambiente!)
# Esta é apenas para demonstração - você deve gerar sua própria chave
ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='  # Exemplo


def gerar_chave():
    """Gera uma nova chave de criptografia"""
    return Fernet.generate_key()


def criptografar_senha(senha: str, key: bytes) -> bytes:
    """Criptografa a senha"""
    cipher = Fernet(key)
    return cipher.encrypt(senha.encode())


def descriptografar_senha(senha_encrypted: bytes, key: bytes) -> str:
    """Descriptografa a senha"""
    cipher = Fernet(key)
    return cipher.decrypt(senha_encrypted).decode()


def conectar_banco():
    """Conecta ao banco de dados"""
    conn_params = get_connection_params()

    try:
        conn = psycopg.connect(**conn_params, row_factory=dict_row)
        return conn
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao banco: {e}")
        return None


def listar_pontos_venda(conn):
    """Lista pontos de venda cadastrados"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, codigo, nome, empresa
                FROM pontos_venda
                WHERE ativo = TRUE
                ORDER BY codigo
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"[ERRO] Falha ao listar pontos de venda: {e}")
        return []


def cadastrar_credencial(conn, ponto_venda_id: int, usuario: str, senha: str, codigo_empresa: str = '0101'):
    """Cadastra credencial no banco"""

    # Criptografar senha
    senha_encrypted = criptografar_senha(senha, ENCRYPTION_KEY)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO credenciais_canopus (
                    ponto_venda_id,
                    usuario,
                    senha_encrypted,
                    codigo_empresa,
                    ativo
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ponto_venda_id, usuario)
                DO UPDATE SET
                    senha_encrypted = EXCLUDED.senha_encrypted,
                    codigo_empresa = EXCLUDED.codigo_empresa,
                    ativo = EXCLUDED.ativo,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (ponto_venda_id, usuario, senha_encrypted, codigo_empresa, True))

            cred_id = cur.fetchone()['id']
            conn.commit()

        return cred_id
    except Exception as e:
        print(f"[ERRO] Falha ao cadastrar credencial: {e}")
        conn.rollback()
        return None


def main():
    print()
    print("=" * 80)
    print("CADASTRAR CREDENCIAIS CANOPUS")
    print("=" * 80)
    print()

    # Conectar ao banco
    print("[*] Conectando ao banco de dados...")
    conn = conectar_banco()
    if not conn:
        return 1

    print("[OK] Conectado ao PostgreSQL")
    print()

    # Listar pontos de venda
    print("[*] Pontos de venda disponiveis:")
    pontos = listar_pontos_venda(conn)

    if not pontos:
        print("[ERRO] Nenhum ponto de venda cadastrado!")
        print()
        print("Execute primeiro: python executar_sql.py")
        conn.close()
        return 1

    for i, ponto in enumerate(pontos, 1):
        print(f"  {i}. [{ponto['codigo']}] {ponto['nome']} ({ponto['empresa']})")

    print()

    # Selecionar ponto de venda
    while True:
        try:
            opcao = input("Selecione o ponto de venda (numero): ").strip()
            opcao_idx = int(opcao) - 1

            if 0 <= opcao_idx < len(pontos):
                ponto_selecionado = pontos[opcao_idx]
                break
            else:
                print("[ERRO] Opcao invalida!")
        except ValueError:
            print("[ERRO] Digite um numero!")
        except KeyboardInterrupt:
            print("\n[CANCELADO]")
            conn.close()
            return 0

    print()
    print(f"[OK] Ponto selecionado: {ponto_selecionado['codigo']} - {ponto_selecionado['nome']}")
    print()

    # Solicitar usuário
    usuario = input("Usuario do Canopus: ").strip()
    if not usuario:
        print("[ERRO] Usuario nao pode ser vazio!")
        conn.close()
        return 1

    # Solicitar senha (não mostra na tela)
    senha = getpass.getpass("Senha do Canopus: ")
    if not senha:
        print("[ERRO] Senha nao pode ser vazia!")
        conn.close()
        return 1

    # Solicitar código empresa
    codigo_empresa = input("Codigo empresa (default: 0101): ").strip() or '0101'

    print()
    print("[*] Cadastrando credencial...")

    # Cadastrar
    cred_id = cadastrar_credencial(
        conn,
        ponto_selecionado['id'],
        usuario,
        senha,
        codigo_empresa
    )

    if cred_id:
        print(f"[OK] Credencial cadastrada com sucesso! (ID: {cred_id})")
        print()
        print("=" * 80)
        print("CREDENCIAL SALVA!")
        print("=" * 80)
        print()
        print(f"Ponto de Venda: {ponto_selecionado['codigo']} - {ponto_selecionado['nome']}")
        print(f"Usuario: {usuario}")
        print(f"Codigo Empresa: {codigo_empresa}")
        print(f"Senha: ********** (criptografada)")
        print()
        print("Proximos passos:")
        print("  1. python testar_dener.py")
        print("  2. python processar_dener.py --listar")
        print()

        conn.close()
        return 0
    else:
        print("[ERRO] Falha ao cadastrar credencial!")
        conn.close()
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO pelo usuario]")
        sys.exit(0)
