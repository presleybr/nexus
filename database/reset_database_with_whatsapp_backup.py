"""
Script para resetar o banco de dados mantendo as sessões WhatsApp

Este script:
1. Faz backup das sessões WhatsApp conectadas
2. Reseta completamente o banco de dados
3. Restaura as sessões WhatsApp

ATENÇÃO: Este script vai APAGAR TODOS OS DADOS do banco exceto as sessões WhatsApp!
"""

import psycopg
import json
from datetime import datetime
import os
import sys

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'dbname': 'nexus_crm',
    'user': 'postgres',
    'password': 'nexus2025'
}

BACKUP_FILE = 'whatsapp_sessions_backup.json'
SCHEMA_FILE = 'schema.sql'

def conectar_db():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)

def fazer_backup_whatsapp():
    """Faz backup de todas as sessões WhatsApp"""
    print("\n" + "="*60)
    print("📦 ETAPA 1: BACKUP DAS SESSÕES WHATSAPP")
    print("="*60)

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Busca todas as sessões WhatsApp
        cursor.execute("""
            SELECT
                id,
                cliente_nexus_id,
                instance_name,
                phone_number,
                status,
                qr_code,
                session_data,
                connected_at,
                disconnected_at,
                created_at,
                updated_at,
                provider,
                twilio_account_sid,
                twilio_phone
            FROM whatsapp_sessions
        """)

        sessoes = cursor.fetchall()

        if not sessoes:
            print("⚠️  Nenhuma sessão WhatsApp encontrada para backup")
            return []

        # Converte para dicionário
        backup_data = []
        for sessao in sessoes:
            backup_data.append({
                'id': sessao[0],
                'cliente_nexus_id': sessao[1],
                'instance_name': sessao[2],
                'phone_number': sessao[3],
                'status': sessao[4],
                'qr_code': sessao[5],
                'session_data': sessao[6],
                'connected_at': sessao[7].isoformat() if sessao[7] else None,
                'disconnected_at': sessao[8].isoformat() if sessao[8] else None,
                'created_at': sessao[9].isoformat() if sessao[9] else None,
                'updated_at': sessao[10].isoformat() if sessao[10] else None,
                'provider': sessao[11],
                'twilio_account_sid': sessao[12],
                'twilio_phone': sessao[13]
            })

        # Salva em arquivo JSON
        backup_path = os.path.join(os.path.dirname(__file__), BACKUP_FILE)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Backup concluído: {len(backup_data)} sessão(ões) salva(s)")
        print(f"📄 Arquivo: {backup_path}")

        # Mostra resumo
        print("\n📊 Resumo do backup:")
        for sessao in backup_data:
            status_emoji = "🟢" if sessao['status'] == 'connected' else "🔴"
            print(f"  {status_emoji} {sessao['instance_name']} - {sessao['phone_number']} ({sessao['status']})")

        return backup_data

    except Exception as e:
        print(f"❌ Erro ao fazer backup: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def resetar_banco():
    """Reseta o banco de dados executando o schema.sql"""
    print("\n" + "="*60)
    print("🔄 ETAPA 2: RESETANDO BANCO DE DADOS")
    print("="*60)

    schema_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)

    if not os.path.exists(schema_path):
        print(f"❌ Arquivo {SCHEMA_FILE} não encontrado!")
        sys.exit(1)

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        print("⚠️  Dropando todas as tabelas...")

        # Busca todas as tabelas
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
        """)

        tabelas = cursor.fetchall()

        # Dropa todas as tabelas em cascata
        for tabela in tabelas:
            print(f"  🗑️  Dropando {tabela[0]}...")
            cursor.execute(f"DROP TABLE IF EXISTS {tabela[0]} CASCADE")

        conn.commit()

        # Dropa todas as views
        cursor.execute("""
            SELECT viewname
            FROM pg_views
            WHERE schemaname = 'public'
        """)

        views = cursor.fetchall()
        for view in views:
            print(f"  🗑️  Dropando view {view[0]}...")
            cursor.execute(f"DROP VIEW IF EXISTS {view[0]} CASCADE")

        conn.commit()

        # Dropa todas as funções
        cursor.execute("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
        """)

        funcoes = cursor.fetchall()
        for funcao in funcoes:
            print(f"  🗑️  Dropando função {funcao[0]}...")
            cursor.execute(f"DROP FUNCTION IF EXISTS {funcao[0]} CASCADE")

        conn.commit()

        print("✅ Tabelas, views e funções dropadas com sucesso")

        # Executa o schema.sql
        print(f"\n📝 Executando {SCHEMA_FILE}...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)
        conn.commit()

        print("✅ Schema criado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao resetar banco: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def restaurar_whatsapp(backup_data):
    """Restaura as sessões WhatsApp do backup"""
    print("\n" + "="*60)
    print("♻️  ETAPA 3: RESTAURANDO SESSÕES WHATSAPP")
    print("="*60)

    if not backup_data:
        print("⚠️  Nenhuma sessão para restaurar")
        return

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        restaurados = 0
        erros = 0

        for sessao in backup_data:
            try:
                cursor.execute("""
                    INSERT INTO whatsapp_sessions (
                        cliente_nexus_id,
                        instance_name,
                        phone_number,
                        status,
                        qr_code,
                        session_data,
                        connected_at,
                        disconnected_at,
                        created_at,
                        updated_at,
                        provider,
                        twilio_account_sid,
                        twilio_phone
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    sessao['cliente_nexus_id'],
                    sessao['instance_name'],
                    sessao['phone_number'],
                    sessao['status'],
                    sessao['qr_code'],
                    json.dumps(sessao['session_data']) if sessao['session_data'] else None,
                    sessao['connected_at'],
                    sessao['disconnected_at'],
                    sessao['created_at'],
                    sessao['updated_at'],
                    sessao['provider'],
                    sessao['twilio_account_sid'],
                    sessao['twilio_phone']
                ))

                status_emoji = "🟢" if sessao['status'] == 'connected' else "🔴"
                print(f"  {status_emoji} Restaurado: {sessao['instance_name']} - {sessao['phone_number']}")
                restaurados += 1

            except Exception as e:
                print(f"  ❌ Erro ao restaurar {sessao['instance_name']}: {e}")
                erros += 1

        conn.commit()

        print(f"\n✅ Restauração concluída!")
        print(f"  📊 Total restaurado: {restaurados}")
        if erros > 0:
            print(f"  ⚠️  Erros: {erros}")

    except Exception as e:
        print(f"❌ Erro ao restaurar sessões: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🚨 RESET DO BANCO DE DADOS COM BACKUP WHATSAPP 🚨")
    print("="*60)
    print("\n⚠️  ATENÇÃO: Este script vai:")
    print("  1. Fazer backup das sessões WhatsApp")
    print("  2. APAGAR TODOS OS DADOS do banco de dados")
    print("  3. Recriar todas as tabelas do zero")
    print("  4. Restaurar apenas as sessões WhatsApp")
    print("\n❌ TODOS OS OUTROS DADOS SERÃO PERDIDOS:")
    print("  - Usuários")
    print("  - Clientes Nexus")
    print("  - Clientes Finais")
    print("  - Boletos")
    print("  - Disparos")
    print("  - Configurações")
    print("  - Logs")
    print("  - Histórico")
    print("  - Consultores")
    print("  - Pontos de venda")
    print("  - E TUDO MAIS!")

    resposta = input("\n⚠️  Tem certeza absoluta que deseja continuar? (digite 'SIM TENHO CERTEZA' para confirmar): ")

    if resposta != 'SIM TENHO CERTEZA':
        print("\n❌ Operação cancelada pelo usuário")
        sys.exit(0)

    # Executa as etapas
    backup_data = fazer_backup_whatsapp()
    resetar_banco()
    restaurar_whatsapp(backup_data)

    print("\n" + "="*60)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("="*60)
    print("\n📋 Próximos passos:")
    print("  1. O banco de dados foi resetado")
    print("  2. As sessões WhatsApp foram preservadas")
    print("  3. Você pode importar novos clientes e dados")
    print("  4. As sessões WhatsApp continuarão funcionando")
    print(f"\n💾 Backup salvo em: {BACKUP_FILE}")
    print("   (Guarde este arquivo caso precise restaurar no futuro)")
    print("\n✅ Sistema pronto para uso!")

if __name__ == '__main__':
    main()
