"""
Script de Inicialização do Banco de Dados
Cria o banco, tabelas e chama seed_data se necessário
"""

import sys
import os

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from models.database import (
    check_database_exists,
    create_database,
    Database,
    init_schema,
    check_tables_exist
)


def inicializar_banco():
    """Inicializa o banco de dados completo"""

    print("=" * 60)
    print("🗄️  INICIALIZANDO BANCO DE DADOS - NEXUS CRM")
    print("=" * 60)

    try:
        # Passo 1: Verificar se o banco existe
        print("\n📌 Passo 1: Verificando se o banco de dados existe...")

        if not check_database_exists():
            print("❌ Banco de dados não encontrado")
            print("📝 Criando banco de dados...")
            create_database()
            print("✅ Banco de dados criado com sucesso!")
        else:
            print("✅ Banco de dados já existe")

        # Passo 2: Inicializar pool de conexões
        print("\n📌 Passo 2: Inicializando pool de conexões...")
        Database.initialize_pool()
        print("✅ Pool de conexões inicializado")

        # Passo 3: Verificar se as tabelas existem
        print("\n📌 Passo 3: Verificando tabelas...")

        if not check_tables_exist():
            print("❌ Tabelas não encontradas")
            print("📝 Criando tabelas (executando schema.sql)...")
            init_schema()
            print("✅ Tabelas criadas com sucesso!")
            return 'created'  # Retorna 'created' para indicar que precisa popular
        else:
            print("✅ Tabelas já existem")
            return 'exists'

    except Exception as e:
        print(f"\n❌ ERRO durante a inicialização: {e}")
        import traceback
        traceback.print_exc()
        return 'error'

    finally:
        try:
            Database.close_all_connections()
        except:
            pass


if __name__ == '__main__':
    resultado = inicializar_banco()

    if resultado == 'created':
        print("\n" + "=" * 60)
        print("💡 Tabelas criadas! Execute agora:")
        print("   python database/seed_data.py")
        print("=" * 60)

    sys.exit(0 if resultado != 'error' else 1)
