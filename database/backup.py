"""
Script de Backup do Banco de Dados
Cria backup completo do PostgreSQL
"""

import os
import subprocess
from datetime import datetime
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from config import Config


def criar_backup():
    """Cria backup do banco de dados PostgreSQL"""

    print("💾 Criando backup do banco de dados...")

    # Diretório de backups
    backup_dir = os.path.join(Config.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # Nome do arquivo de backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"nexus_backup_{timestamp}.sql")

    # Comando pg_dump
    comando = [
        'pg_dump',
        '-h', Config.DB_HOST,
        '-p', str(Config.DB_PORT),
        '-U', Config.DB_USER,
        '-d', Config.DB_NAME,
        '-f', backup_file
    ]

    try:
        # Define senha como variável de ambiente
        env = os.environ.copy()
        env['PGPASSWORD'] = Config.DB_PASSWORD

        # Executa pg_dump
        resultado = subprocess.run(
            comando,
            env=env,
            capture_output=True,
            text=True
        )

        if resultado.returncode == 0:
            tamanho = os.path.getsize(backup_file) / 1024  # KB

            print(f"✅ Backup criado com sucesso!")
            print(f"📁 Arquivo: {backup_file}")
            print(f"💾 Tamanho: {tamanho:.2f} KB")

            # Lista backups existentes
            listar_backups()

        else:
            print(f"❌ Erro ao criar backup:")
            print(resultado.stderr)

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def restaurar_backup(backup_file):
    """Restaura backup do banco de dados"""

    print(f"♻️  Restaurando backup: {backup_file}")

    if not os.path.exists(backup_file):
        print(f"❌ Arquivo não encontrado: {backup_file}")
        return

    confirmacao = input("⚠️  ATENÇÃO: Isso irá SOBRESCREVER o banco atual. Continuar? (s/n): ")

    if confirmacao.lower() != 's':
        print("❌ Operação cancelada")
        return

    # Comando psql
    comando = [
        'psql',
        '-h', Config.DB_HOST,
        '-p', str(Config.DB_PORT),
        '-U', Config.DB_USER,
        '-d', Config.DB_NAME,
        '-f', backup_file
    ]

    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = Config.DB_PASSWORD

        resultado = subprocess.run(
            comando,
            env=env,
            capture_output=True,
            text=True
        )

        if resultado.returncode == 0:
            print("✅ Backup restaurado com sucesso!")
        else:
            print(f"❌ Erro ao restaurar backup:")
            print(resultado.stderr)

    except Exception as e:
        print(f"❌ Erro: {e}")


def listar_backups():
    """Lista todos os backups disponíveis"""

    backup_dir = os.path.join(Config.BASE_DIR, 'backups')

    if not os.path.exists(backup_dir):
        print("\nℹ️  Nenhum backup encontrado")
        return

    backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]

    if not backups:
        print("\nℹ️  Nenhum backup encontrado")
        return

    print(f"\n📋 Backups disponíveis ({len(backups)}):")
    print("-" * 60)

    for backup in sorted(backups, reverse=True):
        caminho = os.path.join(backup_dir, backup)
        tamanho = os.path.getsize(caminho) / 1024
        data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))

        print(f"  • {backup}")
        print(f"    Tamanho: {tamanho:.2f} KB")
        print(f"    Data: {data_mod.strftime('%d/%m/%Y %H:%M:%S')}")
        print()


def limpar_backups_antigos(dias=30):
    """Remove backups mais antigos que X dias"""

    print(f"\n🧹 Limpando backups com mais de {dias} dias...")

    backup_dir = os.path.join(Config.BASE_DIR, 'backups')

    if not os.path.exists(backup_dir):
        return

    agora = datetime.now().timestamp()
    limite = dias * 24 * 60 * 60

    removidos = 0

    for arquivo in os.listdir(backup_dir):
        if arquivo.endswith('.sql'):
            caminho = os.path.join(backup_dir, arquivo)
            idade = agora - os.path.getmtime(caminho)

            if idade > limite:
                os.remove(caminho)
                removidos += 1
                print(f"  ❌ Removido: {arquivo}")

    print(f"\n✅ {removidos} backups removidos")


if __name__ == '__main__':
    print("=" * 60)
    print("💾 SISTEMA DE BACKUP - NEXUS CRM")
    print("=" * 60)

    print("\nOpções:")
    print("1. Criar novo backup")
    print("2. Listar backups")
    print("3. Restaurar backup")
    print("4. Limpar backups antigos (30+ dias)")
    print("5. Sair")

    opcao = input("\nEscolha uma opção: ")

    if opcao == '1':
        criar_backup()

    elif opcao == '2':
        listar_backups()

    elif opcao == '3':
        listar_backups()
        arquivo = input("\nDigite o nome do arquivo de backup: ")
        backup_dir = os.path.join(Config.BASE_DIR, 'backups')
        caminho_completo = os.path.join(backup_dir, arquivo)
        restaurar_backup(caminho_completo)

    elif opcao == '4':
        limpar_backups_antigos(30)

    elif opcao == '5':
        print("👋 Até logo!")

    else:
        print("❌ Opção inválida")
