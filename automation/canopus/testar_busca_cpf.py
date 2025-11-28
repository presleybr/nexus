"""
Testa o fluxo completo:
1. Login
2. Clicar em Atendimento
3. Clicar em Busca Avançada
4. Selecionar CPF
5. Preencher CPF
6. Buscar

Uso: python testar_busca_cpf.py --cpf 057.434.159-51
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Importar módulos
from canopus_automation import CanopusAutomation
from config import CanopusConfig
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


async def testar_busca(cpf: str):
    """Testa busca de CPF"""

    print()
    print("=" * 80)
    print("TESTE: BUSCA DE CPF NO CANOPUS")
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

    # Inicializar bot
    config = CanopusConfig()
    bot = CanopusAutomation(config, headless=False)

    try:
        # 1. Fazer login
        print("=" * 80)
        print("ETAPA 1: LOGIN")
        print("=" * 80)
        print()

        await bot.iniciar_navegador()

        login_ok = await bot.login(
            usuario=cred['usuario'],
            senha=cred['senha'],
            codigo_empresa=cred['codigo_empresa'],
            ponto_venda=cred['ponto_venda']
        )

        if not login_ok:
            print("[ERRO] Login falhou!")
            return 1

        print("[OK] Login realizado!")
        print()

        # 2. Buscar CPF
        print("=" * 80)
        print(f"ETAPA 2: BUSCAR CPF {cpf}")
        print("=" * 80)
        print()

        resultado = await bot.buscar_cliente_cpf(cpf)

        if not resultado:
            print("[AVISO] Cliente não encontrado ou erro na busca")
            await asyncio.sleep(10)
            return 1

        print("[OK] Cliente encontrado e acessado!")
        print()

        # 3. Navegar para Emissão de Cobrança
        print("=" * 80)
        print("ETAPA 3: EMISSÃO DE COBRANÇA")
        print("=" * 80)
        print()

        emissao_ok = await bot.navegar_emissao_cobranca()

        if not emissao_ok:
            print("[ERRO] Falha ao navegar para Emissão de Cobrança")
            await asyncio.sleep(10)
            return 1

        print("[OK] Navegado para Emissão de Cobrança!")
        print()

        # 4. Emitir e baixar boleto
        print("=" * 80)
        print("ETAPA 4: EMITIR E BAIXAR BOLETO")
        print("=" * 80)
        print()

        # Criar pasta de destino (Danner)
        from pathlib import Path
        pasta_destino = Path(r"D:\Nexus\automation\canopus\downloads\Danner")
        pasta_destino.mkdir(parents=True, exist_ok=True)

        print(f"[*] Pasta de destino: {pasta_destino}")
        print()

        # Não passar nome_arquivo para que seja gerado automaticamente
        # no formato: {nome_cliente}_{mes_boleto}.pdf
        # Passar CPF para buscar nome na planilha
        resultado_boleto = await bot.emitir_baixar_boleto(
            destino=pasta_destino,
            cpf=cpf
        )

        if resultado_boleto:
            print("[OK] Boleto emitido e baixado com sucesso!")
            print()
            print("Informações:")
            for key, value in resultado_boleto.items():
                print(f"  {key}: {value}")
        else:
            print("[ERRO] Falha ao emitir/baixar boleto")

        print()
        print("=" * 80)
        print("TESTE FINALIZADO!")
        print("=" * 80)
        print()
        print("O navegador permanecerá aberto.")
        print("Pressione ENTER para fechar ou feche o navegador manualmente...")
        print()

        # Aguardar usuário apertar ENTER
        import sys
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sys.stdin.readline)

    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await bot.fechar_navegador()

    return 0


def main():
    parser = argparse.ArgumentParser(description='Testar busca de CPF no Canopus')
    parser.add_argument('--cpf', required=True, help='CPF do cliente')

    args = parser.parse_args()

    return asyncio.run(testar_busca(args.cpf))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
