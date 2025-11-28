"""
Teste da API HTTP FINAL
Usa credenciais do banco e testa o fluxo completo

Uso:
    python test_api_final.py --cpf 708.990.571-36
"""

import argparse
import sys
from datetime import datetime

from canopus_api_final import CanopusAPIFinal
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
    parser = argparse.ArgumentParser(description='Testar API HTTP Final')
    parser.add_argument('--cpf', required=True, help='CPF do cliente')
    args = parser.parse_args()

    print()
    print("=" * 80)
    print("TESTE - CANOPUS API HTTP (VERSÃO FINAL)")
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

    # Criar API
    inicio_total = datetime.now()
    api = CanopusAPIFinal(timeout=30)

    try:
        # LOGIN
        print("=" * 80)
        print("ETAPA 1: LOGIN")
        print("=" * 80)
        print()

        inicio = datetime.now()
        if not api.login(cred['usuario'], cred['senha']):
            print("[ERRO] Login falhou!")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Login realizado em {tempo:.1f}s")
        print()

        # BUSCAR
        print("=" * 80)
        print(f"ETAPA 2: BUSCAR CLIENTE - CPF {args.cpf}")
        print("=" * 80)
        print()

        inicio = datetime.now()
        cliente = api.buscar_cliente_por_cpf(args.cpf)

        if not cliente:
            print("[AVISO] Cliente não encontrado")
            print()
            print("💡 PRÓXIMO PASSO:")
            print("   Execute 'python capturar_requisicoes_v2.py --cpf XXX'")
            print("   Depois 'python mapear_fluxo.py'")
            print("   Para descobrir as URLs exatas do sistema")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Cliente encontrado em {tempo:.1f}s")
        print(f"    URL: {cliente['url']}")
        print()

        # EMITIR
        print("=" * 80)
        print("ETAPA 3: EMITIR BOLETO")
        print("=" * 80)
        print()

        inicio = datetime.now()
        pdf_bytes = api.emitir_boleto(cliente['url'])

        if not pdf_bytes:
            print("[ERRO] Falha ao emitir boleto")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        tamanho_kb = len(pdf_bytes) / 1024
        print(f"[OK] Boleto emitido em {tempo:.1f}s ({tamanho_kb:.1f} KB)")
        print()

        # SALVAR
        print("=" * 80)
        print("ETAPA 4: SALVAR PDF")
        print("=" * 80)
        print()

        arquivo = api.baixar_boleto(pdf_bytes, args.cpf)
        print(f"[OK] PDF salvo: {arquivo}")
        print()

        # RESUMO
        tempo_total = (datetime.now() - inicio_total).total_seconds()

        print("=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print()
        print(f"⏱️  Tempo total: {tempo_total:.1f}s")
        print(f"📄 Arquivo salvo")
        print(f"💾 Tamanho: {tamanho_kb:.1f} KB")
        print()
        print("🚀 API HTTP ~10x mais rápida que Playwright!")
        print()

        api.logout()

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
