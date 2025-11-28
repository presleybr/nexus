"""
Script para fazer APENAS backup das sessões WhatsApp

Este script salva todas as sessões WhatsApp em um arquivo JSON
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
    print("📦 BACKUP DAS SESSÕES WHATSAPP")
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
            print("⚠️  Nenhuma sessão WhatsApp encontrada")
            return

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

        # Gera nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'whatsapp_backup_{timestamp}.json'
        backup_path = os.path.join(os.path.dirname(__file__), backup_filename)

        # Salva em arquivo JSON
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Backup concluído: {len(backup_data)} sessão(ões) salva(s)")
        print(f"📄 Arquivo: {backup_path}")

        # Mostra resumo
        print("\n📊 Sessões incluídas no backup:")
        for sessao in backup_data:
            status_emoji = "🟢" if sessao['status'] == 'connected' else "🔴"
            print(f"  {status_emoji} {sessao['instance_name']} - {sessao['phone_number']} ({sessao['status']})")

        print("\n✅ Backup salvo com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao fazer backup: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    fazer_backup_whatsapp()
