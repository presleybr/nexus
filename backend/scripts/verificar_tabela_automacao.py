"""
Script para verificar e corrigir a tabela configuracoes_automacao
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def verificar_e_corrigir():
    """Verifica e corrige a tabela configuracoes_automacao"""

    print("=" * 60)
    print("VERIFICANDO TABELA configuracoes_automacao")
    print("=" * 60)

    try:
        # 1. Verifica se a tabela existe
        print("\n[1/4] Verificando se a tabela existe...")
        tabela_existe = db.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'configuracoes_automacao'
            )
        """)

        if not tabela_existe or not tabela_existe[0]['exists']:
            print("[ERRO] Tabela configuracoes_automacao NAO existe!")
            print("Execute o script: backend/sql/criar_tabelas_portal.sql")
            return

        print("[OK] Tabela existe!")

        # 2. Verifica colunas
        print("\n[2/4] Verificando colunas...")
        colunas = db.execute_query("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'configuracoes_automacao'
            ORDER BY ordinal_position
        """)

        print(f"[INFO] Encontradas {len(colunas)} colunas:")
        for col in colunas:
            print(f"  - {col['column_name']:30} | {col['data_type']:15} | default: {col['column_default']}")

        # Verifica se dia_do_mes existe
        tem_dia_do_mes = any(col['column_name'] == 'dia_do_mes' for col in colunas)

        if not tem_dia_do_mes:
            print("\n[AVISO] Coluna 'dia_do_mes' NAO encontrada!")
            print("[INFO] Adicionando coluna...")

            db.execute_update("""
                ALTER TABLE configuracoes_automacao
                ADD COLUMN dia_do_mes INTEGER DEFAULT 1 CHECK (dia_do_mes >= 1 AND dia_do_mes <= 31)
            """)

            print("[OK] Coluna 'dia_do_mes' adicionada!")
        else:
            print("[OK] Coluna 'dia_do_mes' existe!")

        # 3. Verifica registros
        print("\n[3/4] Verificando registros existentes...")
        registros = db.execute_query("""
            SELECT ca.*, cn.nome_empresa
            FROM configuracoes_automacao ca
            LEFT JOIN clientes_nexus cn ON ca.cliente_nexus_id = cn.id
        """)

        if registros:
            print(f"[INFO] Encontrados {len(registros)} registros:")
            for reg in registros:
                print(f"  - Cliente: {reg.get('nome_empresa', 'N/A'):30} | Habilitado: {reg.get('disparo_automatico_habilitado')} | Dia: {reg.get('dia_do_mes', 'N/A')}")
        else:
            print("[INFO] Nenhum registro encontrado (normal para novos clientes)")

        # 4. Lista clientes sem configuração
        print("\n[4/4] Verificando clientes sem configuracao...")
        clientes_sem_config = db.execute_query("""
            SELECT cn.id, cn.nome_empresa
            FROM clientes_nexus cn
            LEFT JOIN configuracoes_automacao ca ON cn.id = ca.cliente_nexus_id
            WHERE ca.id IS NULL
            AND cn.ativo = true
        """)

        if clientes_sem_config:
            print(f"[INFO] Encontrados {len(clientes_sem_config)} clientes sem configuracao:")
            for cliente in clientes_sem_config:
                print(f"  - ID: {cliente['id']:3} | {cliente['nome_empresa']}")

            criar = input("\nDeseja criar configuracao padrao para estes clientes? (s/n): ")
            if criar.lower() == 's':
                for cliente in clientes_sem_config:
                    db.execute_update("""
                        INSERT INTO configuracoes_automacao (
                            cliente_nexus_id,
                            disparo_automatico_habilitado,
                            dia_do_mes,
                            mensagem_antibloqueio
                        ) VALUES (%s, false, 1, 'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!')
                        ON CONFLICT (cliente_nexus_id) DO NOTHING
                    """, (cliente['id'],))
                    print(f"[OK] Configuracao criada para: {cliente['nome_empresa']}")
        else:
            print("[OK] Todos os clientes ativos tem configuracao!")

        print("\n" + "=" * 60)
        print("VERIFICACAO CONCLUIDA!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERRO] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_e_corrigir()
