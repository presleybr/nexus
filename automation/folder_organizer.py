"""
Script de Organização de Pastas
Garante que a estrutura de pastas está correta e organizada
"""

import os
import shutil
from datetime import datetime
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from config import Config
from models import ClienteNexus, Database


def organizar_pastas():
    """Organiza e limpa a estrutura de pastas de boletos"""

    print("📁 Organizando estrutura de pastas...")

    Database.initialize_pool()

    try:
        # Diretório base de boletos
        base_dir = Config.BOLETO_PATH

        # Garante que existe
        os.makedirs(base_dir, exist_ok=True)

        # Busca todas as empresas
        empresas = ClienteNexus.listar_todos()

        for empresa in empresas:
            empresa_id = empresa['id']
            nome_empresa = empresa['nome_empresa'].replace(' ', '_').replace('/', '_')

            # Pasta da empresa
            empresa_dir = os.path.join(base_dir, f"empresa_{empresa_id}_{nome_empresa}")

            # Cria se não existir
            os.makedirs(empresa_dir, exist_ok=True)

            # Cria pastas por mês
            meses = [
                'janeiro_2024', 'fevereiro_2024', 'marco_2024', 'abril_2024',
                'maio_2024', 'junho_2024', 'julho_2024', 'agosto_2024',
                'setembro_2024', 'outubro_2024', 'novembro_2024', 'dezembro_2024'
            ]

            for mes in meses:
                mes_dir = os.path.join(empresa_dir, mes)
                os.makedirs(mes_dir, exist_ok=True)

            print(f"✅ {empresa['nome_empresa']}: Pastas criadas")

        print("\n✅ Organização concluída!")

        # Estatísticas
        total_pastas = 0
        total_arquivos = 0

        for root, dirs, files in os.walk(base_dir):
            total_pastas += len(dirs)
            total_arquivos += len(files)

        print(f"\n📊 Estatísticas:")
        print(f"   • Total de pastas: {total_pastas}")
        print(f"   • Total de arquivos: {total_arquivos}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    finally:
        Database.close_all_connections()


def limpar_pastas_antigas(dias=90):
    """Remove boletos mais antigos que X dias"""

    print(f"\n🧹 Limpando boletos com mais de {dias} dias...")

    base_dir = Config.BOLETO_PATH
    agora = datetime.now().timestamp()
    limite = dias * 24 * 60 * 60  # dias em segundos

    removidos = 0

    for root, dirs, files in os.walk(base_dir):
        for arquivo in files:
            if arquivo.endswith('.pdf'):
                caminho = os.path.join(root, arquivo)
                idade = agora - os.path.getmtime(caminho)

                if idade > limite:
                    try:
                        os.remove(caminho)
                        removidos += 1
                    except Exception as e:
                        print(f"⚠️  Erro ao remover {arquivo}: {e}")

    print(f"✅ {removidos} arquivos removidos")


if __name__ == '__main__':
    organizar_pastas()

    # Pergunta se quer limpar arquivos antigos
    resposta = input("\n❓ Deseja limpar boletos com mais de 90 dias? (s/n): ")

    if resposta.lower() == 's':
        limpar_pastas_antigas(90)
