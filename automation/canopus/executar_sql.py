"""
Executa SQL para criar tabelas da automação Canopus
Usa psycopg para executar o script SQL

Uso: python executar_sql.py
"""

import sys
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

# Importar configurações do banco
from db_config import get_connection_params, get_connection_info


def executar_sql():
    """Executa o script SQL para criar tabelas"""

    print("=" * 80)
    print("EXECUTAR SQL - CRIAR TABELAS AUTOMACAO CANOPUS")
    print("=" * 80)
    print()

    # Caminho do arquivo SQL
    sql_file = Path(__file__).resolve().parent.parent.parent / "backend" / "sql" / "criar_tabelas_automacao.sql"

    if not sql_file.exists():
        print(f"[ERRO] Arquivo SQL nao encontrado!")
        print(f"Esperado: {sql_file}")
        return False

    print(f"[OK] Arquivo SQL encontrado: {sql_file}")
    print()

    # Ler conteúdo do SQL
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"[OK] Arquivo SQL lido ({len(sql_content)} caracteres)")
    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo SQL: {e}")
        return False

    # Conectar ao banco
    print()
    print("Conectando ao PostgreSQL...")
    print(get_connection_info())

    conn_params = get_connection_params()

    try:
        conn = psycopg.connect(**conn_params, row_factory=dict_row)
        print("[OK] Conectado ao PostgreSQL")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        print()
        print("Verifique:")
        print("  1. PostgreSQL esta rodando?")
        print("  2. Porta 5434 esta correta?")
        print("  3. Banco nexus_crm existe?")
        print("  4. Senha postgres esta correta?")
        return False

    # Executar SQL
    print()
    print("Executando comandos SQL...")
    print()

    try:
        with conn.cursor() as cur:
            # Executar todo o conteúdo
            cur.execute(sql_content)
            conn.commit()

        print("[OK] Comandos SQL executados com sucesso!")
        print()

        # Verificar tabelas criadas
        print("Verificando tabelas criadas...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN (
                      'consultores',
                      'pontos_venda',
                      'credenciais_canopus',
                      'clientes_planilha_staging',
                      'log_downloads_boletos',
                      'execucoes_automacao'
                  )
                ORDER BY table_name
            """)

            tabelas = cur.fetchall()

            if tabelas:
                print(f"[OK] {len(tabelas)} tabelas encontradas:")
                for t in tabelas:
                    print(f"  - {t['table_name']}")
            else:
                print("[AVISO] Nenhuma tabela encontrada (pode ser normal se ja existiam)")

        print()
        print("=" * 80)
        print("SQL EXECUTADO COM SUCESSO!")
        print("=" * 80)
        print()
        print("Proximos passos:")
        print("  1. Cadastrar pontos de venda e consultor Dener")
        print("  2. Cadastrar credenciais do Canopus")
        print("  3. Testar importacao da planilha")
        print()

        conn.close()
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao executar SQL: {e}")
        print()
        conn.rollback()
        conn.close()
        return False


def inserir_dados_dener():
    """Insere dados iniciais do Dener no banco"""

    print()
    print("=" * 80)
    print("INSERIR DADOS DO DENER")
    print("=" * 80)
    print()

    conn_params = get_connection_params()

    try:
        conn = psycopg.connect(**conn_params, row_factory=dict_row)
    except Exception as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        return False

    try:
        with conn.cursor() as cur:
            # Inserir pontos de venda
            print("[*] Inserindo pontos de venda...")
            cur.execute("""
                INSERT INTO pontos_venda (codigo, nome, empresa, url_base, ativo)
                VALUES
                    ('17308', 'CredMS - Ponto 17308', 'credms', 'https://cnp3.consorciocanopus.com.br', TRUE),
                    ('24627', 'CM CRED MS - Ponto 24627', 'credms', 'https://cnp3.consorciocanopus.com.br', TRUE)
                ON CONFLICT (codigo) DO UPDATE
                    SET nome = EXCLUDED.nome,
                        empresa = EXCLUDED.empresa,
                        url_base = EXCLUDED.url_base,
                        ativo = EXCLUDED.ativo
            """)
            print("[OK] Pontos de venda inseridos: 17308, 24627")

            # Inserir consultor Dener
            print("[*] Inserindo consultor Dener...")
            cur.execute("""
                INSERT INTO consultores (nome, empresa, ponto_venda, pasta_boletos, cor_identificacao, ativo)
                VALUES ('Dener', 'credms', '17308', 'Dener', NULL, TRUE)
                ON CONFLICT (nome) DO UPDATE
                    SET empresa = EXCLUDED.empresa,
                        ponto_venda = EXCLUDED.ponto_venda,
                        pasta_boletos = EXCLUDED.pasta_boletos,
                        ativo = EXCLUDED.ativo
                RETURNING id, nome
            """)

            consultor = cur.fetchone()
            print(f"[OK] Consultor inserido: ID={consultor['id']}, Nome={consultor['nome']}")

            conn.commit()

        print()
        print("=" * 80)
        print("DADOS DO DENER INSERIDOS COM SUCESSO!")
        print("=" * 80)
        print()

        conn.close()
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao inserir dados: {e}")
        conn.rollback()
        conn.close()
        return False


if __name__ == '__main__':
    print()

    # Executar SQL
    if not executar_sql():
        sys.exit(1)

    # Perguntar se quer inserir dados do Dener
    print()
    resposta = input("Deseja inserir os dados do Dener agora? (S/N): ").strip().upper()

    if resposta == 'S':
        if inserir_dados_dener():
            print()
            print("Tudo pronto!")
            print()
            print("Proximos passos:")
            print("  1. python cadastrar_credencial.py")
            print("  2. python testar_dener.py")
            print()
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print()
        print("OK. Execute depois: python executar_sql.py")
        print()
        sys.exit(0)
