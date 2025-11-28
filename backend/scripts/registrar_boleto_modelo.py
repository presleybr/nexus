"""
Script para registrar o boleto modelo no banco de dados
Executa a criação da tabela e registra o modelo-boleto.pdf
"""

import os
import sys
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.models.database import db


def criar_tabela_boletos_modelo():
    """Cria a tabela boletos_modelo se não existir"""
    print("[INFO] Criando tabela boletos_modelo...")

    sql_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'sql',
        'criar_tabela_boletos_modelo.sql'
    )

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_commands = f.read()

    try:
        # Usar a função execute_query diretamente
        from backend.models.database import execute_query, get_db_connection, Database

        # Obter conexão
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_commands)
            conn.commit()
        finally:
            Database.return_connection(conn)

        print("[OK] Tabela criada com sucesso!")
        return True
    except Exception as e:
        print(f"[ERRO] Erro ao criar tabela: {e}")
        import traceback
        traceback.print_exc()
        return False


def registrar_modelo_boleto():
    """Registra o modelo-boleto.pdf no banco de dados"""
    print("\n[INFO] Registrando modelo-boleto.pdf...")

    # Caminho do arquivo
    boleto_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'boletos',
        'modelo-boleto.pdf'
    )

    # Verificar se arquivo existe
    if not os.path.exists(boleto_path):
        print(f"[ERRO] Arquivo nao encontrado: {boleto_path}")
        return False

    # Obter tamanho do arquivo
    file_size = os.path.getsize(boleto_path)

    print(f"[INFO] Arquivo: {boleto_path}")
    print(f"[INFO] Tamanho: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

    # Verificar se já existe
    existing = db.execute_query(
        "SELECT id FROM boletos_modelo WHERE nome = %s",
        ('Modelo Banese',)
    )

    if existing:
        print("[AVISO] Modelo ja registrado no banco de dados!")
        print(f"[INFO] ID: {existing[0]['id']}")

        # Atualizar
        db.execute_update("""
            UPDATE boletos_modelo
            SET pdf_path = %s,
                pdf_size = %s,
                updated_at = %s
            WHERE nome = %s
        """, (boleto_path, file_size, datetime.now(), 'Modelo Banese'))

        print("[OK] Registro atualizado com sucesso!")
        return True

    # Inserir novo registro
    try:
        result = db.execute_query("""
            INSERT INTO boletos_modelo (
                nome, descricao, tipo, banco,
                pdf_filename, pdf_path, pdf_size,
                ativo, padrao, uploaded_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            'Modelo Banese',
            'Modelo de boleto do Banco Banese - Usado para envio em massa aos clientes do consorcio',
            'banco_especifico',
            'Banese',
            'modelo-boleto.pdf',
            boleto_path,
            file_size,
            True,  # ativo
            True,  # padrao
            'sistema'  # uploaded_by
        ))

        boleto_id = result[0]['id']
        print(f"[OK] Modelo registrado com sucesso!")
        print(f"[INFO] ID: {boleto_id}")
        return True

    except Exception as e:
        print(f"[ERRO] Erro ao registrar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False


def listar_modelos():
    """Lista todos os modelos cadastrados"""
    print("\n[INFO] Modelos cadastrados:")
    print("-" * 80)

    try:
        modelos = db.execute_query("""
            SELECT id, nome, banco, pdf_filename, pdf_size, ativo, padrao, total_envios, created_at
            FROM boletos_modelo
            ORDER BY padrao DESC, created_at DESC
        """, ())

        if not modelos:
            print("[AVISO] Nenhum modelo cadastrado")
            return

        for modelo in modelos:
            print(f"\n[ID] {modelo['id']}")
            print(f"[NOME] {modelo['nome']}")
            print(f"[BANCO] {modelo['banco']}")
            print(f"[ARQUIVO] {modelo['pdf_filename']}")
            print(f"[TAMANHO] {modelo['pdf_size']:,} bytes ({modelo['pdf_size'] / 1024:.2f} KB)")
            print(f"[ATIVO] {'Sim' if modelo['ativo'] else 'Nao'}")
            print(f"[PADRAO] {'Sim' if modelo['padrao'] else 'Nao'}")
            print(f"[ENVIOS] {modelo['total_envios']}")
            print(f"[CRIADO] {modelo['created_at']}")
            print("-" * 80)

    except Exception as e:
        print(f"[ERRO] Erro ao listar modelos: {e}")


def main():
    """Funcao principal"""
    print("=" * 80)
    print("SISTEMA DE REGISTRO DE BOLETOS MODELO")
    print("=" * 80)

    # 1. Criar tabela
    if not criar_tabela_boletos_modelo():
        print("\n[ERRO] Falha ao criar tabela. Abortando...")
        return

    # 2. Registrar modelo
    if not registrar_modelo_boleto():
        print("\n[ERRO] Falha ao registrar modelo. Abortando...")
        return

    # 3. Listar modelos
    listar_modelos()

    print("\n" + "=" * 80)
    print("[OK] PROCESSO CONCLUIDO COM SUCESSO!")
    print("=" * 80)


if __name__ == '__main__':
    main()
