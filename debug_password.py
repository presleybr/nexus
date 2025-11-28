import psycopg
from psycopg.rows import dict_row
import bcrypt

try:
    conn = psycopg.connect(
        host='localhost',
        port=5434,
        dbname='nexus_crm',
        user='postgres',
        password='nexus2025',
        row_factory=dict_row
    )

    with conn.cursor() as cur:
        cur.execute("""
            SELECT email, password_hash, tipo
            FROM usuarios
            WHERE email = 'empresa1@nexus.com'
        """)

        usuario = cur.fetchone()

        if usuario:
            print(f"\n=== Dados do usuário ===")
            print(f"Email: {usuario['email']}")
            print(f"Tipo: {usuario['tipo']}")
            print(f"\nPassword Hash:")
            print(f"  Valor: {usuario['password_hash']}")
            print(f"  Tipo Python: {type(usuario['password_hash'])}")
            print(f"  Comprimento: {len(usuario['password_hash'])}")

            # Testar senha
            senha_teste = 'admin123'
            print(f"\n=== Teste de autenticação ===")
            print(f"Senha testando: {senha_teste}")

            password_hash = usuario['password_hash']

            # Verificar se já é bytes ou string
            if isinstance(password_hash, bytes):
                print("Hash é bytes - usando direto")
                hash_bytes = password_hash
            else:
                print("Hash é string - convertendo para bytes")
                hash_bytes = password_hash.encode('utf-8')

            print(f"Tipo após conversão: {type(hash_bytes)}")

            # Testar senha
            try:
                resultado = bcrypt.checkpw(senha_teste.encode('utf-8'), hash_bytes)
                print(f"\nResultado: {resultado}")

                if resultado:
                    print("SENHA CORRETA!")
                else:
                    print("Senha incorreta")

            except Exception as e:
                print(f"\nErro ao verificar senha: {e}")
                print(f"Tipo do erro: {type(e)}")
        else:
            print("Usuário não encontrado!")

    conn.close()

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
