"""
Adiciona número de WhatsApp de TESTE a um cliente específico
"""

import sys
import os
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db


def adicionar_numero_teste(nome_cliente, whatsapp):
    """
    Adiciona número de WhatsApp de teste a um cliente específico

    Args:
        nome_cliente: Nome do cliente (pode ser parte do nome)
        whatsapp: Número de WhatsApp (ex: 5567999887766)
    """

    print("=" * 70)
    print("ADICIONAR NÚMERO DE TESTE")
    print("=" * 70)

    # Buscar cliente por nome (match parcial)
    clientes = db.execute_query("""
        SELECT id, nome_completo, whatsapp, cpf
        FROM clientes_finais
        WHERE UPPER(nome_completo) LIKE UPPER(%s)
        AND cliente_nexus_id = 2
    """, (f'%{nome_cliente}%',))

    if not clientes:
        print(f"\n❌ Nenhum cliente encontrado com nome: {nome_cliente}")
        return

    if len(clientes) > 1:
        print(f"\n⚠️  Encontrados {len(clientes)} clientes:")
        for idx, c in enumerate(clientes, 1):
            print(f"   {idx}. {c['nome_completo']}")
        print(f"\nUsando o primeiro: {clientes[0]['nome_completo']}")

    cliente = clientes[0]

    # Limpar WhatsApp (remover caracteres não numéricos)
    whatsapp_limpo = ''.join(filter(str.isdigit, whatsapp))

    # Adicionar 55 se não tiver
    if not whatsapp_limpo.startswith('55'):
        whatsapp_limpo = '55' + whatsapp_limpo

    # Atualizar
    db.execute_update("""
        UPDATE clientes_finais
        SET whatsapp = %s, telefone_celular = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (whatsapp_limpo, whatsapp_limpo, cliente['id']))

    print(f"\n✅ Número atualizado com sucesso!")
    print(f"   Cliente: {cliente['nome_completo']}")
    print(f"   WhatsApp: {whatsapp_limpo}")
    print(f"   CPF: {cliente['cpf']}")

    # Verificar boletos pendentes
    boletos = db.execute_query("""
        SELECT id, numero_boleto, data_vencimento, valor_original, status_envio
        FROM boletos
        WHERE cliente_final_id = %s
        AND status_envio = 'nao_enviado'
    """, (cliente['id'],))

    if boletos:
        print(f"\n📄 Boletos pendentes para este cliente: {len(boletos)}")
        for b in boletos:
            print(f"   • {b['numero_boleto']} - Venc: {b['data_vencimento']} - R$ {b['valor_original']:.2f}")
        print(f"\n✅ Cliente PRONTO para receber disparo!")
    else:
        print(f"\n⚠️  Nenhum boleto pendente para este cliente")

    print("=" * 70)


if __name__ == '__main__':
    # Verificar argumentos
    if len(sys.argv) < 3:
        print("=" * 70)
        print("USO:")
        print("=" * 70)
        print(f"   python {os.path.basename(__file__)} \"NOME_CLIENTE\" \"WHATSAPP\"")
        print()
        print("EXEMPLOS:")
        print('   python adicionar_numero_teste.py "ZACARIAS" "67999887766"')
        print('   python adicionar_numero_teste.py "ADILSON" "5567991234567"')
        print()
        print("CLIENTES DISPONÍVEIS:")
        print("-" * 70)

        # Listar alguns clientes
        clientes = db.execute_query("""
            SELECT nome_completo, cpf
            FROM clientes_finais
            WHERE cliente_nexus_id = 2
            AND whatsapp = '55679999999999'
            ORDER BY nome_completo
            LIMIT 10
        """)

        for idx, c in enumerate(clientes, 1):
            print(f"   {idx}. {c['nome_completo']}")

        print(f"\n   ... e mais clientes")
        print("=" * 70)
        sys.exit(1)

    nome_cliente = sys.argv[1]
    whatsapp = sys.argv[2]

    adicionar_numero_teste(nome_cliente, whatsapp)
