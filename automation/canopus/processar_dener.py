"""
Processa apenas o consultor Dener
Fluxo simplificado para testar e depois executar a automação

Uso:
  python processar_dener.py --listar          # Lista clientes
  python processar_dener.py --exportar        # Exporta JSON
  python processar_dener.py --simular         # Simula o fluxo
  python processar_dener.py --processar       # Processa clientes (futuro)
"""

import sys
import json
import argparse
from pathlib import Path

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

from excel_importer_dener import ExcelImporterDener

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    print("[ERRO] psycopg nao instalado!")
    sys.exit(1)

# Importar configurações do banco
from db_config import get_connection_params


def conectar_banco():
    """Conecta ao banco de dados"""
    conn_params = get_connection_params()

    try:
        conn = psycopg.connect(**conn_params, row_factory=dict_row)
        return conn
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao banco: {e}")
        return None


def listar_clientes():
    """Lista todos os clientes do Dener"""

    print()
    print("=" * 80)
    print("LISTAR CLIENTES - DENER")
    print("=" * 80)
    print()

    # Importar clientes
    importador = ExcelImporterDener()

    try:
        clientes = importador.extrair_clientes()
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha: {e}")
        return 1

    # Estatísticas
    stats = importador.estatisticas(clientes)

    print(f"Total de clientes 'Em dia': {stats['total']}")
    print()

    # Agrupar por ponto de venda
    for pv in sorted(stats['por_ponto_venda'].keys()):
        clientes_pv = [c for c in clientes if c['ponto_venda'] == pv]
        print(f"\n[Ponto {pv}] - {len(clientes_pv)} clientes")
        print("-" * 80)

        for i, cliente in enumerate(clientes_pv, 1):
            print(f"{i:3d}. {cliente['nome'][:45]:45s} | CPF: {cliente['cpf']} | G/C: {cliente['grupo']}/{cliente['cota']}")

    print()
    print("=" * 80)
    print(f"Total: {stats['total']} clientes")
    print("=" * 80)
    print()

    return 0


def exportar_json():
    """Exporta clientes para JSON"""

    print()
    print("=" * 80)
    print("EXPORTAR CLIENTES - JSON")
    print("=" * 80)
    print()

    # Importar clientes
    importador = ExcelImporterDener()

    try:
        clientes = importador.extrair_clientes()
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha: {e}")
        return 1

    # Salvar JSON
    json_path = Path(__file__).parent / "temp" / "dener_clientes.json"
    json_path.parent.mkdir(exist_ok=True)

    try:
        stats = importador.estatisticas(clientes)

        data = {
            'consultor': 'Dener',
            'total_clientes': len(clientes),
            'estatisticas': stats,
            'clientes': clientes
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] JSON exportado: {json_path}")
        print(f"     {len(clientes)} clientes")
        print()

        return 0

    except Exception as e:
        print(f"[ERRO] Falha ao exportar JSON: {e}")
        return 1


def simular_processamento():
    """Simula o processamento dos clientes"""

    print()
    print("=" * 80)
    print("SIMULAR PROCESSAMENTO - DENER")
    print("=" * 80)
    print()

    # Importar clientes
    importador = ExcelImporterDener()

    try:
        clientes = importador.extrair_clientes()
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha: {e}")
        return 1

    print(f"Total de clientes para processar: {len(clientes)}")
    print()

    # Perguntar quantos processar
    while True:
        try:
            qtd = input("Quantos clientes deseja simular? (0 para todos): ").strip()
            qtd_int = int(qtd)

            if qtd_int == 0:
                clientes_processar = clientes
                break
            elif qtd_int > 0 and qtd_int <= len(clientes):
                clientes_processar = clientes[:qtd_int]
                break
            else:
                print(f"[ERRO] Digite um numero entre 0 e {len(clientes)}")
        except ValueError:
            print("[ERRO] Digite um numero valido!")
        except KeyboardInterrupt:
            print("\n[CANCELADO]")
            return 0

    print()
    print(f"[*] Simulando processamento de {len(clientes_processar)} clientes...")
    print()

    # Simular processamento
    for i, cliente in enumerate(clientes_processar, 1):
        print(f"[{i}/{len(clientes_processar)}] Processando: {cliente['nome']}")
        print(f"     CPF: {cliente['cpf']}")
        print(f"     Ponto: {cliente['ponto_venda']}")
        print(f"     Grupo/Cota: {cliente['grupo']}/{cliente['cota']}")
        print(f"     -> [SIMULADO] Buscaria no Canopus...")
        print(f"     -> [SIMULADO] Baixaria boleto de DEZEMBRO/2024...")
        print(f"     -> [SIMULADO] Salvaria em: automation/canopus/downloads/Dener/{cliente['cpf']}_DEZ_2024.pdf")
        print()

    print("=" * 80)
    print("SIMULACAO CONCLUIDA!")
    print("=" * 80)
    print()
    print(f"Clientes simulados: {len(clientes_processar)}")
    print()
    print("IMPORTANTE:")
    print("  Esta foi apenas uma SIMULACAO!")
    print("  Nenhum boleto foi realmente baixado.")
    print()
    print("Proximos passos:")
    print("  1. Mapear seletores CSS do Canopus")
    print("  2. Testar login: python teste_automacao.py --teste login")
    print("  3. Implementar download real")
    print()

    return 0


def processar_real():
    """Processamento real (futuro)"""

    print()
    print("=" * 80)
    print("PROCESSAMENTO REAL - NAO IMPLEMENTADO")
    print("=" * 80)
    print()
    print("Esta funcionalidade ainda nao foi implementada.")
    print()
    print("Necessario:")
    print("  1. Mapear seletores CSS do Canopus")
    print("  2. Testar login e navegacao")
    print("  3. Implementar logica de download")
    print()
    print("Use --simular para testar o fluxo sem executar de verdade.")
    print()

    return 1


def main():
    parser = argparse.ArgumentParser(
        description='Processar clientes do consultor Dener',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python processar_dener.py --listar          # Lista todos os clientes
  python processar_dener.py --exportar        # Exporta para JSON
  python processar_dener.py --simular         # Simula processamento
  python processar_dener.py --processar       # Processa de verdade (futuro)
        """
    )

    parser.add_argument('--listar', action='store_true', help='Listar clientes')
    parser.add_argument('--exportar', action='store_true', help='Exportar para JSON')
    parser.add_argument('--simular', action='store_true', help='Simular processamento')
    parser.add_argument('--processar', action='store_true', help='Processar de verdade (futuro)')

    args = parser.parse_args()

    # Verificar se alguma ação foi especificada
    if not any([args.listar, args.exportar, args.simular, args.processar]):
        parser.print_help()
        return 1

    # Executar ação
    if args.listar:
        return listar_clientes()

    if args.exportar:
        return exportar_json()

    if args.simular:
        return simular_processamento()

    if args.processar:
        return processar_real()

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO pelo usuario]")
        sys.exit(0)
