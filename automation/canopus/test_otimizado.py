"""
Teste da Automação OTIMIZADA
Com anti-detecção e melhorias de performance

Uso:
    python test_otimizado.py --cpf 708.990.571-36
    python test_otimizado.py --cpf 708.990.571-36 --headless
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

from canopus_automation_optimized import CanopusAutomationOptimized
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


async def testar_otimizado(cpf: str, headless: bool = False):
    """Testa automação otimizada"""

    print()
    print("=" * 80)
    print("TESTE - AUTOMAÇÃO OTIMIZADA (ANTI-DETECÇÃO + PERFORMANCE)")
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

    # Criar pasta de destino
    pasta_destino = Path(r"D:\Nexus\automation\canopus\downloads\Danner")
    pasta_destino.mkdir(parents=True, exist_ok=True)

    inicio_total = datetime.now()

    # Usar context manager
    async with CanopusAutomationOptimized(headless=headless) as bot:

        # LOGIN
        print("=" * 80)
        print("ETAPA 1: LOGIN (OTIMIZADO)")
        print("=" * 80)
        print()

        inicio = datetime.now()
        if not await bot.login(cred['usuario'], cred['senha']):
            print("[ERRO] Login falhou!")
            return 1

        tempo = (datetime.now() - inicio).total_seconds()
        print(f"[OK] Login em {tempo:.1f}s")
        print()

        # PROCESSAR CLIENTE COMPLETO
        print("=" * 80)
        print(f"ETAPA 2: PROCESSAR CLIENTE - {cpf}")
        print("=" * 80)
        print()

        # Não passar nome_arquivo para que seja gerado automaticamente
        # no formato: {nome_cliente}_{mes_boleto}.pdf
        resultado = await bot.processar_cliente_completo(
            cpf=cpf,
            destino=pasta_destino,
            nome_arquivo=None
        )

        tempo_total = (datetime.now() - inicio_total).total_seconds()

        # RESULTADO
        print()
        print("=" * 80)
        if resultado['status'] == 'SUCESSO':
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print(f"⚠️  TESTE FINALIZADO - Status: {resultado['status']}")
        print("=" * 80)
        print()
        print(f"Status: {resultado['status']}")
        print(f"Mensagem: {resultado['mensagem']}")
        if resultado['arquivo']:
            print(f"Arquivo: {resultado['arquivo']}")
        print(f"Tempo total: {tempo_total:.1f}s")
        print()

        # Comparação
        print("=" * 80)
        print("📊 COMPARAÇÃO: OTIMIZADO vs ORIGINAL")
        print("=" * 80)
        print()
        print(f"   Otimizado:  {tempo_total:6.1f}s  ✅ (este teste)")
        print(f"   Original:   ~35-40s  ⚠️  (versão anterior)")
        print()
        if tempo_total > 0:
            melhoria = ((40 - tempo_total) / 40) * 100
            print(f"   🚀 Melhoria: ~{melhoria:.0f}% mais rápido!")
        print()

    return 0


def main():
    parser = argparse.ArgumentParser(description='Testar Automação Otimizada')
    parser.add_argument('--cpf', required=True, help='CPF do cliente')
    parser.add_argument('--headless', action='store_true', help='Executar em modo headless')

    args = parser.parse_args()

    return asyncio.run(testar_otimizado(args.cpf, args.headless))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
