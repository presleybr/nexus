"""
Teste do Cliente HTTP Real
Baseado no mapeamento de requisições

Uso:
    python test_http_client.py --cpf 708.990.571-36
"""

import argparse
import sys
from datetime import datetime

from canopus_http_client import CanopusHTTPClient
from db_config import get_connection_params
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet


ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='


def descriptografar_senha(senha_encrypted) -> str:
    """Descriptografa senha"""
    cipher = Fernet(ENCRYPTION_KEY)

    if isinstance(senha_encrypted, str):
        if senha_encrypted.startswith('\\x'):
            senha_encrypted = bytes.fromhex(senha_encrypted[2:])
        else:
            senha_encrypted = senha_encrypted.encode('utf-8')
    elif isinstance(senha_encrypted, memoryview):
        senha_encrypted = bytes(senha_encrypted)

    return cipher.decrypt(senha_encrypted).decode()


def buscar_credencial(ponto_venda_codigo: str):
    """Busca credencial no banco"""
    conn_params = get_connection_params()

    try:
        with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.usuario, c.senha_encrypted
                    FROM credenciais_canopus c
                    JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE pv.codigo = %s AND c.ativo = TRUE
                    LIMIT 1
                """, (ponto_venda_codigo,))

                resultado = cur.fetchone()
                if resultado:
                    return {
                        'usuario': resultado['usuario'],
                        'senha': descriptografar_senha(resultado['senha_encrypted'])
                    }
                return None
    except Exception as e:
        print(f"[ERRO] Falha ao buscar credencial: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Testar Cliente HTTP Real')
    parser.add_argument('--cpf', required=True, help='CPF do cliente')
    args = parser.parse_args()

    print()
    print("=" * 80)
    print("TESTE - CANOPUS HTTP CLIENT (REQUISIÇÕES REAIS)")
    print("=" * 80)
    print()

    # Buscar credencial
    print("[*] Buscando credenciais do PV 17.308...")
    cred = buscar_credencial('17.308')

    if not cred:
        print("[ERRO] Credencial não encontrada!")
        return 1

    print(f"[OK] Credencial encontrada - Usuario: {cred['usuario']}")
    print()

    # Criar cliente HTTP
    inicio_total = datetime.now()
    client = CanopusHTTPClient(timeout=30)

    try:
        # =================================================================
        # ETAPA 1: LOGIN
        # =================================================================

        print("=" * 80)
        print("ETAPA 1: LOGIN")
        print("=" * 80)
        print()

        inicio = datetime.now()
        if not client.login(cred['usuario'], cred['senha']):
            print("[ERRO] Login falhou!")
            print()
            print("Possíveis causas:")
            print("  - Credenciais incorretas")
            print("  - Servidor bloqueando requisições HTTP")
            print("  - Campos do formulário mudaram")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Login realizado em {tempo:.1f}s")
        print()

        # =================================================================
        # ETAPA 2: BUSCAR CPF
        # =================================================================

        print("=" * 80)
        print(f"ETAPA 2: BUSCAR CPF - {args.cpf}")
        print("=" * 80)
        print()

        inicio = datetime.now()
        cliente = client.buscar_cpf(args.cpf)

        if not cliente:
            print("[AVISO] Cliente não encontrado")
            print()
            print("Possíveis causas:")
            print("  - CPF não existe no sistema")
            print("  - Fluxo de navegação mudou")
            print("  - Campos da busca mudaram")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Cliente encontrado em {tempo:.1f}s")
        print(f"    Link: {cliente['link_elemento']}")
        print()

        # =================================================================
        # ETAPA 3: ACESSAR CLIENTE
        # =================================================================

        print("=" * 80)
        print("ETAPA 3: ACESSAR CLIENTE")
        print("=" * 80)
        print()

        inicio = datetime.now()
        if not client.acessar_cliente(cliente['link_elemento']):
            print("[ERRO] Falha ao acessar cliente")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Cliente acessado em {tempo:.1f}s")
        print()

        # =================================================================
        # ETAPA 4: EMITIR BOLETO
        # =================================================================

        print("=" * 80)
        print("ETAPA 4: EMITIR BOLETO")
        print("=" * 80)
        print()

        inicio = datetime.now()
        pdf_bytes = client.emitir_boleto()

        if not pdf_bytes:
            print("[ERRO] Falha ao emitir boleto")
            print()
            print("Possíveis causas:")
            print("  - Boleto não disponível")
            print("  - Fluxo de emissão mudou")
            print("  - PDF gerado de forma diferente")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        tamanho_kb = len(pdf_bytes) / 1024
        print(f"[OK] Boleto emitido em {tempo:.1f}s ({tamanho_kb:.1f} KB)")
        print()

        # =================================================================
        # ETAPA 5: SALVAR PDF
        # =================================================================

        print("=" * 80)
        print("ETAPA 5: SALVAR PDF")
        print("=" * 80)
        print()

        arquivo = client.salvar_pdf(pdf_bytes, args.cpf)
        print(f"[OK] PDF salvo: {arquivo}")
        print()

        # =================================================================
        # RESUMO
        # =================================================================

        tempo_total = (datetime.now() - inicio_total).total_seconds()

        print("=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print()
        print(f"⏱️  Tempo total: {tempo_total:.1f}s")
        print(f"📄 Arquivo: {arquivo}")
        print(f"💾 Tamanho: {tamanho_kb:.1f} KB")
        print()
        print("=" * 80)
        print("COMPARAÇÃO: HTTP vs Playwright")
        print("=" * 80)
        print()
        print(f"   HTTP Client:  {tempo_total:6.1f}s  ✅ (este teste)")
        print(f"   Playwright:   ~35-45s  ⚠️  (com navegador)")
        print()
        print(f"   🚀 HTTP é ~{35/tempo_total:.0f}x mais rápido!")
        print()

    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        return 0

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
