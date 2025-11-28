"""
Script de teste para Canopus API (requisições HTTP diretas)

Testa o fluxo completo:
1. Login
2. Busca de cliente por CPF
3. Emissão de boleto
4. Download do PDF

Uso:
    python test_api.py --cpf 057.434.159-51
    python test_api.py --cpf 708.990.571-36 --mes DEZEMBRO --ano 2024
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Importar módulos
from canopus_api import CanopusAPI
from db_config import get_connection_params
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet


# Chave de criptografia
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
                    SELECT
                        c.usuario,
                        c.senha_encrypted,
                        c.codigo_empresa,
                        pv.codigo as ponto_venda
                    FROM credenciais_canopus c
                    JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE pv.codigo = %s AND c.ativo = TRUE
                    LIMIT 1
                """, (ponto_venda_codigo,))

                resultado = cur.fetchone()

                if resultado:
                    senha = descriptografar_senha(resultado['senha_encrypted'])
                    return {
                        'usuario': resultado['usuario'],
                        'senha': senha,
                        'codigo_empresa': resultado['codigo_empresa'],
                        'ponto_venda': resultado['ponto_venda']
                    }
                return None

    except Exception as e:
        print(f"[ERRO] Falha ao buscar credencial: {e}")
        return None


def testar_api(cpf: str, mes: str = None, ano: int = None):
    """Testa API do Canopus"""

    print()
    print("=" * 80)
    print("TESTE - CANOPUS API (HTTP DIRETO - SEM NAVEGADOR)")
    print("=" * 80)
    print()

    # Buscar credencial
    print("[*] Buscando credenciais do PV 17.308...")
    cred = buscar_credencial('17.308')

    if not cred:
        print("[ERRO] Credencial não encontrada!")
        print("Execute: python cadastrar_credencial.py")
        return 1

    print(f"[OK] Credencial encontrada - Usuario: {cred['usuario']}")
    print()

    # Criar API
    inicio_total = datetime.now()
    api = CanopusAPI(timeout=30)

    try:
        # ====================================================================
        # ETAPA 1: LOGIN
        # ====================================================================

        print("=" * 80)
        print("ETAPA 1: LOGIN")
        print("=" * 80)
        print()

        inicio = datetime.now()

        login_ok = api.login(
            usuario=cred['usuario'],
            senha=cred['senha']
        )

        tempo = (datetime.now() - inicio).total_seconds()

        if not login_ok:
            print(f"[ERRO] Login falhou! ({tempo:.1f}s)")
            return 1

        print(f"[OK] Login realizado em {tempo:.1f}s")
        print()

        # ====================================================================
        # ETAPA 2: BUSCAR CLIENTE
        # ====================================================================

        print("=" * 80)
        print(f"ETAPA 2: BUSCAR CLIENTE - CPF {cpf}")
        print("=" * 80)
        print()

        inicio = datetime.now()

        cliente = api.buscar_cliente_por_cpf(cpf)

        tempo = (datetime.now() - inicio).total_seconds()

        if not cliente:
            print(f"[AVISO] Cliente não encontrado ({tempo:.1f}s)")
            return 1

        print(f"[OK] Cliente encontrado em {tempo:.1f}s")
        print()
        print("Dados do cliente:")
        for key, value in cliente.items():
            print(f"   {key}: {value}")
        print()

        # ====================================================================
        # ETAPA 3: EMITIR BOLETO
        # ====================================================================

        print("=" * 80)
        print("ETAPA 3: EMITIR BOLETO")
        print("=" * 80)
        print()

        inicio = datetime.now()

        pdf_bytes = api.emitir_boleto(
            cliente_url=cliente.get('url'),
            mes_referencia=mes
        )

        tempo = (datetime.now() - inicio).total_seconds()

        if not pdf_bytes:
            print(f"[ERRO] Falha ao emitir boleto ({tempo:.1f}s)")
            return 1

        tamanho_kb = len(pdf_bytes) / 1024
        print(f"[OK] Boleto emitido em {tempo:.1f}s ({tamanho_kb:.1f} KB)")
        print()

        # ====================================================================
        # ETAPA 4: SALVAR PDF
        # ====================================================================

        print("=" * 80)
        print("ETAPA 4: SALVAR PDF")
        print("=" * 80)
        print()

        arquivo = api.baixar_boleto(
            pdf_bytes=pdf_bytes,
            nome_cliente=cpf,
            mes=mes or 'DEZEMBRO',
            ano=ano or 2024,
            consultor='Danner'
        )

        print(f"[OK] PDF salvo: {arquivo}")
        print()

        # ====================================================================
        # RESUMO
        # ====================================================================

        tempo_total = (datetime.now() - inicio_total).total_seconds()

        print("=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print()
        print(f"⏱️  Tempo total: {tempo_total:.1f}s")
        print(f"📄 Arquivo: {Path(arquivo).name}")
        print(f"💾 Tamanho: {tamanho_kb:.1f} KB")
        print()

        # ====================================================================
        # COMPARAÇÃO COM PLAYWRIGHT
        # ====================================================================

        print("=" * 80)
        print("📊 COMPARAÇÃO: HTTP vs Playwright")
        print("=" * 80)
        print()
        print(f"   HTTP API:     {tempo_total:6.1f}s  ✅ (este teste)")
        print(f"   Playwright:   ~30-45s  ⚠️  (estimativa com navegador)")
        print()
        print(f"   🚀 API HTTP é ~{30/tempo_total:.0f}x mais rápida!")
        print()

        # Logout
        api.logout()

    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        return 0

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


def main():
    """Função principal"""

    parser = argparse.ArgumentParser(
        description='Testar Canopus API (HTTP direto)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python test_api.py --cpf 057.434.159-51
    python test_api.py --cpf 708.990.571-36 --mes DEZEMBRO --ano 2024

⚠️  NOTA IMPORTANTE:
    Este script usa a API HTTP direta (canopus_api.py).
    Antes de usar, você precisa mapear as requisições:

    1. python capturar_requisicoes.py
       (faça o fluxo completo manualmente no navegador)

    2. python mapear_fluxo.py
       (analise as requisições capturadas)

    3. Ajuste canopus_api.py com os campos corretos
       (IDs de formulários, URLs, etc)

    4. python test_api.py --cpf SEU_CPF
        """
    )

    parser.add_argument(
        '--cpf',
        required=True,
        help='CPF do cliente'
    )

    parser.add_argument(
        '--mes',
        default=None,
        help='Mês de referência (ex: DEZEMBRO)'
    )

    parser.add_argument(
        '--ano',
        type=int,
        default=None,
        help='Ano de referência (ex: 2024)'
    )

    args = parser.parse_args()

    return testar_api(args.cpf, args.mes, args.ano)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
