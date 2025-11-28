"""
Script de teste para integração com Google Drive
Testa todas as funcionalidades do sistema de planilhas
"""
import sys
import os
from pathlib import Path

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

import requests
import json
from config import Config


BASE_URL = f"http://127.0.0.1:{Config.FLASK_PORT}"
API_BASE = f"{BASE_URL}/api/automation"


def print_section(title):
    """Imprime um separador de seção"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_database_migration():
    """Testa se a migração foi aplicada corretamente"""
    print_section("1. TESTE DE MIGRAÇÃO DO BANCO DE DADOS")

    try:
        import psycopg
        from psycopg.rows import dict_row

        conninfo = f"host={Config.DB_HOST} port={Config.DB_PORT} dbname={Config.DB_NAME} user={Config.DB_USER} password={Config.DB_PASSWORD}"
        conn = psycopg.connect(conninfo, row_factory=dict_row)

        with conn.cursor() as cur:
            # Verificar estrutura da tabela consultores
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'consultores'
                AND column_name IN ('link_planilha_drive', 'ultima_atualizacao_planilha')
                ORDER BY column_name
            """)

            columns = cur.fetchall()

            if len(columns) == 2:
                print("[OK] Colunas da migração encontradas:")
                for col in columns:
                    print(f"  + {col['column_name']} ({col['data_type']}) - NULL: {col['is_nullable']}")

                # Verificar se existe algum consultor
                cur.execute("SELECT id, nome, link_planilha_drive FROM consultores LIMIT 5")
                consultores = cur.fetchall()

                if consultores:
                    print(f"\n[OK] {len(consultores)} consultor(es) encontrado(s):")
                    for c in consultores:
                        drive_status = "CONFIGURADO" if c['link_planilha_drive'] else "NAO CONFIGURADO"
                        print(f"  - ID {c['id']}: {c['nome']} - Drive: {drive_status}")
                else:
                    print("\n[AVISO] Nenhum consultor encontrado no banco")

                conn.close()
                return True
            else:
                print(f"[ERRO] Esperado 2 colunas, encontrado {len(columns)}")
                conn.close()
                return False

    except Exception as e:
        print(f"[ERRO] Falha ao verificar migração: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_listar_consultores():
    """Testa a rota de listagem de consultores"""
    print_section("2. TESTE DE API - LISTAR CONSULTORES")

    try:
        response = requests.get(f"{API_BASE}/consultores-planilhas", timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                consultores = data.get('data', {}).get('consultores', [])
                print(f"[OK] API retornou {len(consultores)} consultor(es)")

                for c in consultores[:3]:  # Mostrar apenas os 3 primeiros
                    print(f"\n  Consultor: {c.get('nome')}")
                    print(f"    - ID: {c.get('id')}")
                    print(f"    - Email: {c.get('email')}")
                    print(f"    - PV: {c.get('ponto_venda')}")
                    print(f"    - Link Drive: {c.get('link_planilha_drive') or 'NAO CONFIGURADO'}")

                return True
            else:
                print(f"[ERRO] API retornou success=False: {data.get('error')}")
                return False
        else:
            print(f"[ERRO] Status code inesperado: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"[ERRO] Falha ao testar API: {e}")
        return False


def test_drive_downloader_service():
    """Testa o serviço de download do Drive"""
    print_section("3. TESTE DO SERVIÇO DRIVE DOWNLOADER")

    try:
        # Adicionar services ao path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'backend' / 'services'))

        from drive_downloader import extrair_file_id_drive, gerar_url_download_drive

        # Testar extração de IDs
        test_cases = [
            ("https://drive.google.com/file/d/1ABC123xyz/view", "1ABC123xyz"),
            ("https://drive.google.com/open?id=2DEF456abc", "2DEF456abc"),
            ("1XYZ789def", "1XYZ789def"),
        ]

        print("Testando extração de File IDs:")
        all_passed = True

        for url, expected_id in test_cases:
            extracted = extrair_file_id_drive(url)
            status = "OK" if extracted == expected_id else "FALHOU"
            print(f"  [{status}] {url[:50]}... -> {extracted}")
            if extracted != expected_id:
                all_passed = False

        # Testar geração de URL
        file_id = "1ABC123xyz"
        download_url = gerar_url_download_drive(file_id)
        expected_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        if download_url == expected_url:
            print(f"\n[OK] Geracao de URL de download funcionando")
            print(f"  URL: {download_url}")
        else:
            print(f"\n[ERRO] URL gerada incorreta")
            all_passed = False

        # Verificar se o diretório de destino existe
        dest_dir = Path("D:/Nexus/automation/canopus/excel_files")
        if dest_dir.exists():
            print(f"\n[OK] Diretório de destino existe: {dest_dir}")

            # Listar arquivos .xlsx existentes
            xlsx_files = list(dest_dir.glob("*.xlsx"))
            if xlsx_files:
                print(f"[INFO] {len(xlsx_files)} arquivo(s) .xlsx encontrado(s):")
                for f in xlsx_files[:5]:
                    size_kb = f.stat().st_size / 1024
                    print(f"  - {f.name} ({size_kb:.2f} KB)")
            else:
                print("[INFO] Nenhum arquivo .xlsx encontrado (ainda)")
        else:
            print(f"\n[AVISO] Diretório de destino não existe: {dest_dir}")
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Diretório criado")

        return all_passed

    except Exception as e:
        print(f"[ERRO] Falha ao testar Drive Downloader: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_frontend_integration():
    """Testa se a página frontend carrega corretamente"""
    print_section("4. TESTE DE INTEGRAÇÃO FRONTEND")

    try:
        response = requests.get(f"{BASE_URL}/crm/automacao-canopus", timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            html = response.text

            # Verificar elementos-chave
            checks = [
                ('btnAtualizarPlanilhaDrive' in html, "Botão 'Atualizar Planilha do Drive'"),
                ('btnImportarPlanilha' in html, "Botão 'Importar Planilha'"),
                ('selectPontosVenda' in html, "Select de Pontos de Venda"),
                ('/api/automation/consultores-planilhas' in html, "Chamada à API de consultores"),
            ]

            all_passed = True
            for check_passed, check_name in checks:
                status = "OK" if check_passed else "FALHOU"
                print(f"  [{status}] {check_name}")
                if not check_passed:
                    all_passed = False

            return all_passed
        else:
            print(f"[ERRO] Status code inesperado: {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERRO] Falha ao testar frontend: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*70)
    print("  SUITE DE TESTES - INTEGRACAO GOOGLE DRIVE")
    print("="*70)

    results = {
        'Migracao Database': test_database_migration(),
        'API Listar Consultores': test_api_listar_consultores(),
        'Drive Downloader Service': test_drive_downloader_service(),
        'Frontend Integration': test_frontend_integration(),
    }

    # Resumo
    print_section("RESUMO DOS TESTES")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, result in results.items():
        status = "PASSOU" if result else "FALHOU"
        symbol = "[OK]" if result else "[ERRO]"
        print(f"  {symbol} {test_name}: {status}")

    print(f"\n{'='*70}")
    print(f"  Total: {total} | Passou: {passed} | Falhou: {failed}")
    print(f"{'='*70}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
