"""
Testa importação da planilha do Dener
Mostra estatísticas e primeiros clientes

Uso: python testar_dener.py
"""

import json
import sys
from pathlib import Path

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

from excel_importer_dener import ExcelImporterDener


def main():
    print()
    print("=" * 80)
    print("TESTE IMPORTACAO - PLANILHA DENER")
    print("=" * 80)
    print()

    # Verificar se planilha existe
    planilha = Path("D:/Nexus/planilhas/DENER__PLANILHA_GERAL.xlsx")
    if not planilha.exists():
        print(f"[ERRO] Planilha nao encontrada: {planilha}")
        print()
        print("Coloque a planilha em:")
        print(f"  {planilha}")
        print()
        return 1

    print(f"[OK] Planilha encontrada: {planilha.name}")
    print()

    # Criar importador
    importador = ExcelImporterDener(planilha)

    # Ler planilha
    try:
        print("[1/4] Lendo planilha...")
        clientes = importador.extrair_clientes()
        print(f"[OK] {len(clientes)} clientes extraidos (apenas 'Em dia')")
        print()
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Mostrar primeiros 10
    print("[2/4] Primeiros 10 clientes:")
    print("-" * 80)
    for i, cliente in enumerate(clientes[:10], 1):
        print(f"{i:2d}. {cliente['nome'][:40]:40s} | CPF: {cliente['cpf']} | PV: {cliente['ponto_venda']} | G/C: {cliente['grupo']}/{cliente['cota']}")
    print()

    # Estatísticas
    print("[3/4] Estatisticas:")
    print("-" * 80)
    stats = importador.estatisticas(clientes)

    print(f"Total de clientes 'Em dia': {stats['total']}")
    print()

    print("Por Ponto de Venda:")
    for pv, qtd in sorted(stats['por_ponto_venda'].items()):
        percentual = (qtd / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  Ponto {pv}: {qtd:3d} clientes ({percentual:5.1f}%)")
    print()

    print("Por Situacao:")
    for sit, qtd in sorted(stats['por_situacao'].items()):
        percentual = (qtd / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {sit}: {qtd:3d} clientes ({percentual:5.1f}%)")
    print()

    # Salvar JSON
    print("[4/4] Salvando JSON de teste...")
    json_path = Path(__file__).parent / "temp" / "dener_clientes.json"
    json_path.parent.mkdir(exist_ok=True)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'clientes': clientes,
                'estatisticas': stats,
                'data_extracao': str(Path(planilha).stat().st_mtime)
            }, f, indent=2, ensure_ascii=False)

        print(f"[OK] JSON salvo: {json_path}")
        print(f"     {stats['total']} clientes exportados")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar JSON: {e}")

    print()
    print("=" * 80)
    print("TESTE CONCLUIDO!")
    print("=" * 80)
    print()
    print("Resumo:")
    print(f"  - Total de clientes 'Em dia': {stats['total']}")
    print(f"  - Ponto 17308: {stats['por_ponto_venda'].get('17308', 0)} clientes")
    print(f"  - Ponto 24627: {stats['por_ponto_venda'].get('24627', 0)} clientes")
    print()
    print("Proximos passos:")
    print("  1. Verificar se os dados estao corretos")
    print("  2. Cadastrar credenciais: python cadastrar_credencial.py")
    print("  3. Processar Dener: python processar_dener.py --listar")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
