import psycopg
from psycopg.rows import dict_row

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
        # Primeiro, verificar colunas da tabela
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'usuarios'
            ORDER BY ordinal_position
        """)

        colunas = [row['column_name'] for row in cur.fetchall()]
        print(f"\nColunas da tabela usuarios: {colunas}\n")

        # Buscar usuários
        cur.execute("""
            SELECT *
            FROM usuarios
            WHERE tipo IN ('cliente', 'admin')
            ORDER BY tipo, id
            LIMIT 10
        """)

        usuarios = cur.fetchall()

        print("\n" + "="*80)
        print("USUÁRIOS DO SISTEMA NEXUS CRM")
        print("="*80)
        print()

        if usuarios:
            for u in usuarios:
                print(f"ID: {u.get('id')}")
                print(f"Email: {u.get('email')}")
                print(f"Tipo: {u.get('tipo')}")
                print(f"Ativo: {u.get('ativo')}")
                # Mostrar todas as colunas
                print(f"Dados completos: {dict(u)}")
                print("-" * 80)
        else:
            print("Nenhum usuário encontrado!")
            print()
            print("Criando usuário de teste...")

            # Criar usuário teste
            cur.execute("""
                INSERT INTO usuarios (email, senha, nome, tipo, ativo)
                VALUES ('cliente@nexus.com', 'senha123', 'Cliente Teste', 'cliente', TRUE)
                RETURNING id, email, nome
            """)

            novo = cur.fetchone()
            conn.commit()

            print()
            print("✅ Usuário criado:")
            print(f"   Email: {novo['email']}")
            print(f"   Senha: senha123")
            print(f"   Nome: {novo['nome']}")

    conn.close()

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
