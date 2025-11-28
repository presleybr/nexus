"""
Script para restaurar APENAS as sessões WhatsApp de um backup

Use este script se você já tem um backup e quer restaurar apenas as sessões WhatsApp
"""

import psycopg
import json
import os
import sys
from glob import glob

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

def listar_backups():
    """Lista todos os arquivos de backup disponíveis"""
    backup_dir = os.path.dirname(__file__)
    backups = glob(os.path.join(backup_dir, 'whatsapp_backup_*.json'))
    backups.extend(glob(os.path.join(backup_dir, 'whatsapp_sessions_backup.json')))
    return sorted(backups, reverse=True)

def restaurar_whatsapp(backup_file):
    """Restaura as sessões WhatsApp do backup"""
    print("\n" + "="*60)
    print("♻️  RESTAURANDO SESSÕES WHATSAPP")
    print("="*60)

    # Carrega o backup
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de backup: {e}")
        sys.exit(1)

    if not backup_data:
        print("⚠️  Nenhuma sessão no backup")
        return

    print(f"📦 Encontradas {len(backup_data)} sessão(ões) no backup")

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        restaurados = 0
        ignorados = 0
        erros = 0

        for sessao in backup_data:
            try:
                # Verifica se já existe
                cursor.execute("""
                    SELECT id FROM whatsapp_sessions
                    WHERE instance_name = %s
                """, (sessao['instance_name'],))

                existe = cursor.fetchone()

                if existe:
                    print(f"  ⏭️  Ignorado (já existe): {sessao['instance_name']}")
                    ignorados += 1
                    continue

                # Insere a sessão
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
        if ignorados > 0:
            print(f"  ⏭️  Ignorados (já existiam): {ignorados}")
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
    print("♻️  RESTAURAR SESSÕES WHATSAPP DO BACKUP")
    print("="*60)

    # Lista backups disponíveis
    backups = listar_backups()

    if not backups:
        print("\n❌ Nenhum arquivo de backup encontrado!")
        print("   Procurado por: whatsapp_backup_*.json ou whatsapp_sessions_backup.json")
        sys.exit(1)

    print("\n📁 Backups disponíveis:")
    for i, backup in enumerate(backups, 1):
        filename = os.path.basename(backup)
        size = os.path.getsize(backup)
        print(f"  {i}. {filename} ({size} bytes)")

    if len(backups) == 1:
        escolha = 1
        print(f"\n✅ Usando único backup disponível: {os.path.basename(backups[0])}")
    else:
        try:
            escolha = int(input(f"\nEscolha o backup (1-{len(backups)}): "))
            if escolha < 1 or escolha > len(backups):
                print("❌ Escolha inválida!")
                sys.exit(1)
        except ValueError:
            print("❌ Escolha inválida!")
            sys.exit(1)

    backup_file = backups[escolha - 1]

    print(f"\n⚠️  Vai restaurar sessões WhatsApp de:")
    print(f"   {os.path.basename(backup_file)}")

    resposta = input("\n✅ Confirma? (s/n): ")

    if resposta.lower() != 's':
        print("\n❌ Operação cancelada")
        sys.exit(0)

    restaurar_whatsapp(backup_file)

    print("\n✅ Processo concluído!")

if __name__ == '__main__':
    main()
