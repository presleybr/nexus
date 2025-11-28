#!/usr/bin/env python3
"""Script para atualizar senha do admin do Portal"""

import sys
import os
import bcrypt

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import execute_query, fetch_one, Database

def atualizar_senha():
    try:
        # Inicializar pool de conexões
        print("[INFO] Inicializando conexão...")
        Database.initialize_pool()

        # Gerar novo hash para senha admin123
        senha = 'admin123'
        salt = bcrypt.gensalt()
        hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt)
        hash_str = hash_senha.decode('utf-8')

        print(f"\n[INFO] Nova senha gerada:")
        print(f"  Senha: {senha}")
        print(f"  Hash: {hash_str}")

        # Atualizar no banco
        print(f"\n[INFO] Atualizando no banco de dados...")
        execute_query(
            "UPDATE usuarios_portal SET senha = %s WHERE email = %s",
            (hash_str, 'admin@portal.com'),
            fetch=False
        )

        print(f"[SUCCESS] Senha atualizada com sucesso!")

        # Verificar
        print(f"\n[INFO] Verificando...")
        usuario = fetch_one("SELECT senha FROM usuarios_portal WHERE email = %s", ('admin@portal.com',))

        # Testar
        if bcrypt.checkpw(senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
            print("[SUCCESS] Verificação OK - Senha funcionando!")
            return True
        else:
            print("[ERROR] Verificação falhou!")
            return False

    except Exception as e:
        print(f"\n[ERROR] Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Database.close_all_connections()

if __name__ == '__main__':
    atualizar_senha()
