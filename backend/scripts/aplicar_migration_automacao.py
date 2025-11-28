"""
Script para aplicar a migration de automacao mensal
Adiciona o campo dia_do_mes na tabela configuracoes_automacao
"""

import os
import sys

# Adiciona o diretorio backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db, log_sistema
from models import Database

def aplicar_migration():
    """Aplica a migration para adicionar dia_do_mes"""

    print("=" * 60)
    print("APLICANDO MIGRATION: Automacao Mensal")
    print("=" * 60)

    try:
        # Verifica se a coluna ja existe
        verificacao = db.execute_query("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'configuracoes_automacao'
            AND column_name = 'dia_do_mes'
        """)

        if verificacao:
            print("[OK] Coluna 'dia_do_mes' ja existe. Migration nao necessaria.")
            return

        print("[1/4] Adicionando coluna 'dia_do_mes'...")

        # Adiciona a coluna
        db.execute_update("""
            ALTER TABLE configuracoes_automacao
            ADD COLUMN dia_do_mes INTEGER DEFAULT 1 CHECK (dia_do_mes >= 1 AND dia_do_mes <= 31)
        """)

        print("[OK] Coluna 'dia_do_mes' adicionada com sucesso!")

        # Adiciona comentarios
        print("[2/4] Adicionando comentarios...")

        db.execute_update("""
            COMMENT ON COLUMN configuracoes_automacao.dia_do_mes
            IS 'Dia do mes (1-31) para execucao automatica dos disparos'
        """)

        db.execute_update("""
            COMMENT ON COLUMN configuracoes_automacao.disparo_automatico_habilitado
            IS 'Liga/Desliga o disparo automatico mensal'
        """)

        print("[OK] Comentarios adicionados!")

        # Atualiza configuracoes existentes
        print("[3/4] Atualizando configuracoes existentes...")

        db.execute_update("""
            UPDATE configuracoes_automacao
            SET dia_do_mes = 1
            WHERE dia_do_mes IS NULL
        """)

        print("[OK] Configuracoes atualizadas!")

        # Registra no log do sistema
        print("[4/4] Registrando no log do sistema...")

        log_sistema('success',
                   'Migration de automacao mensal aplicada com sucesso',
                   'sistema')

        print("[OK] Log registrado!")

        print("\n" + "=" * 60)
        print("MIGRATION APLICADA COM SUCESSO!")
        print("=" * 60)
        print("\nProximos passos:")
        print("1. Reinicie a aplicacao Flask")
        print("2. Acesse /crm/disparos para configurar")
        print("3. O scheduler sera iniciado automaticamente")

    except Exception as e:
        print(f"\n[ERRO] Erro ao aplicar migration: {str(e)}")
        log_sistema('error',
                   f'Erro ao aplicar migration de automacao: {str(e)}',
                   'sistema')
        raise

if __name__ == '__main__':
    aplicar_migration()
