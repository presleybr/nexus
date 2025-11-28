#!/usr/bin/env python3
"""Script para criar tabelas do Portal Consórcio usando database.py existente"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.models.database import db

def criar_tabelas():
    try:
        print("[INFO] Lendo arquivo SQL...")
        with open('backend/sql/criar_tabelas_portal.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("[INFO] Executando SQL...")

        # Separar comandos SQL
        comandos = []
        comando_atual = []

        for linha in sql_script.split('\n'):
            linha = linha.strip()

            # Ignorar comentários e linhas vazias
            if not linha or linha.startswith('--'):
                continue

            comando_atual.append(linha)

            # Se termina com ;, é fim do comando
            if linha.endswith(';'):
                comando = ' '.join(comando_atual)
                if comando and not comando.startswith('--'):
                    comandos.append(comando)
                comando_atual = []

        # Executar cada comando
        total = len(comandos)
        print(f"[INFO] Total de comandos SQL: {total}")

        for i, comando in enumerate(comandos, 1):
            # Mostrar progresso
            if i % 5 == 0 or i == total:
                print(f"[INFO] Executando {i}/{total}...")

            try:
                db.execute_update(comando)
            except Exception as e:
                # Ignorar erros de "já existe"
                if 'already exists' in str(e) or 'already defined' in str(e):
                    continue
                else:
                    print(f"[WARN] Erro no comando {i}: {str(e)[:100]}")

        print("\n[OK] Comandos SQL executados!")

        # Verificar tabelas criadas
        print("\n[INFO] Verificando tabelas...")
        tabelas = db.execute_query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('clientes_finais', 'boletos', 'usuarios_portal',
                               'pastas_digitais', 'historico_disparos', 'configuracoes_automacao')
            ORDER BY table_name
        """)

        for tabela in tabelas:
            print(f"  [OK] {tabela['table_name']}")

        # Verificar dados
        print("\n[INFO] Dados iniciais:")

        result = db.execute_query("SELECT COUNT(*) as total FROM usuarios_portal")
        print(f"  Usuarios Portal: {result[0]['total'] if result else 0}")

        result = db.execute_query("SELECT COUNT(*) as total FROM clientes_finais")
        print(f"  Clientes Finais: {result[0]['total'] if result else 0}")

        result = db.execute_query("SELECT COUNT(*) as total FROM configuracoes_automacao")
        print(f"  Configuracoes: {result[0]['total'] if result else 0}")

        print("\n[SUCCESS] Tabelas criadas com sucesso!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = criar_tabelas()
    sys.exit(0 if success else 1)
