"""
Configura teste de disparo usando cliente e boleto REAIS
Apenas modifica o WhatsApp temporariamente para nao enviar pro cliente verdadeiro

Uso: python configurar_teste_real.py
"""

import sys
import os
import glob

# Adicionar path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db

# Pasta dos boletos reais
PASTA_BOLETOS = r'D:\Nexus\automation\canopus\downloads\Danner'


def listar_boletos_disponiveis():
    """Lista todos os PDFs de boletos disponiveis na pasta"""

    if not os.path.exists(PASTA_BOLETOS):
        print(f"[ERRO] Pasta nao encontrada: {PASTA_BOLETOS}")
        return []

    pdfs = glob.glob(os.path.join(PASTA_BOLETOS, '*.pdf'))

    print(f"\n[BOLETOS] Boletos disponiveis em {PASTA_BOLETOS}:")
    print("-" * 60)

    for i, pdf in enumerate(pdfs[:20]):  # Limitar a 20 para nao poluir
        nome_arquivo = os.path.basename(pdf)
        tamanho = os.path.getsize(pdf) / 1024  # KB
        print(f"  [{i+1}] {nome_arquivo[:50]:<50} ({tamanho:.1f} KB)")

    if len(pdfs) > 20:
        print(f"  ... e mais {len(pdfs) - 20} boletos")

    print("-" * 60)
    print(f"  Total: {len(pdfs)} boletos")

    return pdfs


def listar_clientes_reais():
    """Lista clientes reais do banco que podem ser usados para teste"""

    clientes = db.execute_query("""
        SELECT
            cf.id,
            cf.nome_completo,
            cf.cpf,
            cf.whatsapp,
            cf.cliente_nexus_id,
            COUNT(b.id) as total_boletos
        FROM clientes_finais cf
        LEFT JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE cf.ativo = true
        AND cf.whatsapp IS NOT NULL
        AND cf.whatsapp != ''
        GROUP BY cf.id, cf.nome_completo, cf.cpf, cf.whatsapp, cf.cliente_nexus_id
        ORDER BY cf.nome_completo
        LIMIT 20
    """)

    print(f"\n[CLIENTES] Clientes reais disponiveis para teste:")
    print("-" * 80)
    print(f"{'ID':<5} {'Nome':<35} {'WhatsApp':<15} {'Boletos':<8}")
    print("-" * 80)

    for c in clientes:
        nome = c['nome_completo'][:33] if c['nome_completo'] else 'N/A'
        whatsapp = c['whatsapp'] or 'N/A'
        print(f"{c['id']:<5} {nome:<35} {whatsapp:<15} {c['total_boletos']:<8}")

    print("-" * 80)

    return clientes


def buscar_cliente_por_boleto(nome_arquivo_pdf: str):
    """
    Tenta encontrar o cliente no banco baseado no nome do arquivo PDF.
    Formato esperado: NOME_CLIENTE_MM_AAAA.pdf
    """

    # Extrair nome do arquivo (sem extensao)
    nome_sem_ext = os.path.splitext(os.path.basename(nome_arquivo_pdf))[0]

    # Separar partes (NOME_CLIENTE_MM_AAAA)
    partes = nome_sem_ext.rsplit('_', 2)

    if len(partes) >= 3:
        nome_cliente = partes[0].replace('_', ' ')
    else:
        nome_cliente = nome_sem_ext.replace('_', ' ')

    print(f"\n[BUSCA] Procurando cliente: {nome_cliente}")

    # Buscar no banco por nome similar
    clientes = db.execute_query("""
        SELECT id, nome_completo, cpf, whatsapp, cliente_nexus_id
        FROM clientes_finais
        WHERE UPPER(nome_completo) LIKE UPPER(%s)
        AND ativo = true
        LIMIT 5
    """, (f'%{nome_cliente[:20]}%',))

    if clientes:
        print(f"   [OK] Encontrado: {clientes[0]['nome_completo']}")
        return clientes[0]
    else:
        print(f"   [AVISO] Cliente nao encontrado no banco")
        return None


def modificar_whatsapp_para_teste(cliente_id: int):
    """
    Adiciona '9' apos o DDD do WhatsApp do cliente para teste.
    Formato: 5567XXXXXXXX -> 55679XXXXXXXX (adiciona 9 apos DDD 67)
    Retorna o numero original para restaurar depois.
    """

    # Buscar numero original
    cliente = db.execute_query(
        "SELECT whatsapp FROM clientes_finais WHERE id = %s",
        (cliente_id,)
    )

    if not cliente:
        print(f"[ERRO] Cliente ID {cliente_id} nao encontrado!")
        return None

    whatsapp_original = str(cliente[0]['whatsapp']).strip()

    # Formato brasileiro: 55 (país) + 2 dígitos DDD + 8 ou 9 dígitos
    # Exemplo: 5567841266146 -> 55 67 841266146
    # Adiciona 9 após DDD: 55 67 9 841266146 = 556799841266146

    if len(whatsapp_original) >= 4:
        # 55 (país) + 67 (DDD) + resto
        codigo_pais = whatsapp_original[:2]   # "55"
        ddd = whatsapp_original[2:4]          # "67"
        numero = whatsapp_original[4:]        # "841266146"
        whatsapp_teste = f"{codigo_pais}{ddd}9{numero}"  # "556799841266146"
    else:
        # Fallback: adiciona 9 no início
        whatsapp_teste = f"9{whatsapp_original}"

    # Atualizar no banco
    db.execute_update(
        "UPDATE clientes_finais SET whatsapp = %s WHERE id = %s",
        (whatsapp_teste, cliente_id)
    )

    print(f"\n[WHATSAPP] WhatsApp modificado para teste:")
    print(f"   Original: {whatsapp_original}")
    print(f"   Teste:    {whatsapp_teste} (numero VALIDO mas diferente)")
    print(f"   Formato:  {codigo_pais} {ddd} 9{numero}")

    return whatsapp_original


def restaurar_whatsapp_original(cliente_id: int, whatsapp_original: str):
    """Restaura o WhatsApp original do cliente apos o teste"""

    db.execute_update(
        "UPDATE clientes_finais SET whatsapp = %s WHERE id = %s",
        (whatsapp_original, cliente_id)
    )

    print(f"\n[OK] WhatsApp restaurado: {whatsapp_original}")


def vincular_boleto_pdf_ao_cliente(cliente_id: int, caminho_pdf: str):
    """
    Cria ou atualiza registro de boleto no banco vinculado ao PDF real.
    """

    from datetime import datetime

    nome_arquivo = os.path.basename(caminho_pdf)

    # Extrair mes e ano do nome do arquivo (NOME_MM_AAAA.pdf)
    partes = os.path.splitext(nome_arquivo)[0].rsplit('_', 2)

    if len(partes) >= 3:
        try:
            mes = int(partes[-2])
            ano = int(partes[-1])
        except ValueError:
            mes = datetime.now().month
            ano = datetime.now().year
    else:
        mes = datetime.now().month
        ano = datetime.now().year

    # Buscar cliente_nexus_id
    cliente = db.execute_query(
        "SELECT cliente_nexus_id FROM clientes_finais WHERE id = %s",
        (cliente_id,)
    )

    if not cliente:
        print(f"[ERRO] Cliente {cliente_id} nao encontrado!")
        return None

    cliente_nexus_id = cliente[0]['cliente_nexus_id']

    # Verificar se ja existe boleto para este cliente/mes/ano
    boleto_existe = db.execute_query("""
        SELECT id FROM boletos
        WHERE cliente_final_id = %s
        AND mes_referencia = %s
        AND ano_referencia = %s
    """, (cliente_id, mes, ano))

    if boleto_existe:
        # Atualizar boleto existente
        boleto_id = boleto_existe[0]['id']
        db.execute_update("""
            UPDATE boletos SET
                pdf_filename = %s,
                pdf_path = %s,
                status_envio = 'nao_enviado'
            WHERE id = %s
        """, (nome_arquivo, caminho_pdf, boleto_id))

        print(f"\n[BOLETO] Boleto atualizado:")
    else:
        # Criar novo boleto
        result = db.execute_query("""
            INSERT INTO boletos (
                cliente_nexus_id,
                cliente_final_id,
                numero_boleto,
                valor_original,
                data_vencimento,
                data_emissao,
                mes_referencia,
                ano_referencia,
                numero_parcela,
                descricao,
                status,
                status_envio,
                pdf_filename,
                pdf_path,
                gerado_por
            ) VALUES (
                %s, %s, %s, 500.00,
                CURRENT_DATE + INTERVAL '7 days',
                CURRENT_DATE,
                %s, %s, 1,
                'Boleto de teste com PDF real',
                'pendente',
                'nao_enviado',
                %s, %s,
                'importacao'
            ) RETURNING id
        """, (
            cliente_nexus_id,
            cliente_id,
            f'TESTE-{cliente_id}-{mes}-{ano}',
            mes, ano,
            nome_arquivo, caminho_pdf
        ))

        boleto_id = result[0]['id']
        print(f"\n[BOLETO] Boleto criado:")

    print(f"   ID: {boleto_id}")
    print(f"   Cliente ID: {cliente_id}")
    print(f"   PDF: {nome_arquivo}")
    print(f"   Mes/Ano: {mes}/{ano}")
    print(f"   Status envio: nao_enviado")

    return boleto_id


def configurar_teste_completo():
    """
    Fluxo completo para configurar teste com dados reais.
    """

    print("=" * 60)
    print("CONFIGURAR TESTE COM CLIENTE E BOLETO REAIS")
    print("=" * 60)

    # 1. Listar boletos disponiveis
    pdfs = listar_boletos_disponiveis()

    if not pdfs:
        print("\n[ERRO] Nenhum PDF encontrado. Execute a automacao Canopus primeiro.")
        return

    # 2. Escolher boleto
    escolha = input("\nEscolha o numero do boleto (ou ENTER para o primeiro): ").strip()

    if escolha:
        try:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(pdfs):
                print(f"[ERRO] Numero invalido. Usando o primeiro.")
                idx = 0
        except ValueError:
            print(f"[ERRO] Entrada invalida. Usando o primeiro.")
            idx = 0
    else:
        idx = 0

    pdf_escolhido = pdfs[idx]
    print(f"\n[OK] Boleto selecionado: {os.path.basename(pdf_escolhido)}")

    # 3. Tentar encontrar cliente pelo nome do arquivo
    cliente = buscar_cliente_por_boleto(pdf_escolhido)

    if not cliente:
        # Se nao encontrou, listar clientes para escolher
        print("\n[AVISO] Nao foi possivel encontrar o cliente automaticamente.")
        clientes = listar_clientes_reais()

        if not clientes:
            print("[ERRO] Nenhum cliente encontrado no banco!")
            return

        cliente_id = input("\nDigite o ID do cliente para teste: ").strip()

        try:
            cliente = db.execute_query(
                "SELECT id, nome_completo, cpf, whatsapp, cliente_nexus_id FROM clientes_finais WHERE id = %s",
                (int(cliente_id),)
            )

            if cliente:
                cliente = cliente[0]
            else:
                print("[ERRO] Cliente nao encontrado!")
                return
        except ValueError:
            print("[ERRO] ID invalido!")
            return

    print(f"\n[CLIENTE] Cliente selecionado:")
    print(f"   ID: {cliente['id']}")
    print(f"   Nome: {cliente['nome_completo']}")
    print(f"   CPF: {cliente['cpf']}")
    print(f"   WhatsApp: {cliente['whatsapp']}")

    # 4. Confirmar antes de modificar
    print("\n" + "=" * 60)
    print("[ATENCAO] Vamos modificar o WhatsApp temporariamente!")
    print("          O numero original sera salvo para restaurar depois.")
    print("=" * 60)

    confirma = input("\nContinuar? (s/N): ").strip().lower()

    if confirma != 's':
        print("Cancelado.")
        return

    # 5. Modificar WhatsApp (adicionar 9 no final)
    whatsapp_original = modificar_whatsapp_para_teste(cliente['id'])

    if not whatsapp_original:
        return

    # 6. Vincular boleto PDF ao cliente
    boleto_id = vincular_boleto_pdf_ao_cliente(cliente['id'], pdf_escolhido)

    # 7. Resumo final
    print("\n" + "=" * 60)
    print("[SUCESSO] TESTE CONFIGURADO COM SUCESSO!")
    print("=" * 60)
    print(f"""
Cliente ID:     {cliente['id']}
Nome:           {cliente['nome_completo']}
WhatsApp teste: {cliente['whatsapp']}9 (invalido - nao envia)
Boleto ID:      {boleto_id}
PDF:            {os.path.basename(pdf_escolhido)}

PROXIMOS PASSOS:
1. Acesse http://127.0.0.1:5000/crm/dashboard
2. Execute o disparo de boletos
3. Verifique os logs no terminal
4. O envio vai FALHAR (numero invalido) - isso e esperado!
5. Apos teste, execute:
   python configurar_teste_real.py --restaurar-ultimo
""")

    # Salvar info para restaurar depois
    script_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_ultimo_teste = os.path.join(script_dir, 'ultimo_teste.txt')

    with open(arquivo_ultimo_teste, 'w') as f:
        f.write(f"{cliente['id']},{whatsapp_original}")

    print(f"[SALVO] Info salva em ultimo_teste.txt para restaurar depois")


def restaurar_ultimo_teste():
    """Restaura o WhatsApp do ultimo teste"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_ultimo_teste = os.path.join(script_dir, 'ultimo_teste.txt')

    if not os.path.exists(arquivo_ultimo_teste):
        print("[ERRO] Nenhum teste anterior encontrado (ultimo_teste.txt)")
        return

    with open(arquivo_ultimo_teste, 'r') as f:
        dados = f.read().strip().split(',')

    if len(dados) != 2:
        print("[ERRO] Arquivo ultimo_teste.txt corrompido!")
        return

    try:
        cliente_id = int(dados[0])
        whatsapp_original = dados[1]
    except ValueError:
        print("[ERRO] Dados invalidos no arquivo ultimo_teste.txt!")
        return

    restaurar_whatsapp_original(cliente_id, whatsapp_original)

    # Remover arquivo
    os.remove(arquivo_ultimo_teste)
    print("[OK] Arquivo ultimo_teste.txt removido")


def resetar_status_boleto(boleto_id: int = None):
    """Reseta o status_envio do boleto para testar novamente"""

    if boleto_id:
        db.execute_update(
            "UPDATE boletos SET status_envio = 'nao_enviado' WHERE id = %s",
            (boleto_id,)
        )
        print(f"[OK] Boleto {boleto_id} resetado para 'nao_enviado'")
    else:
        # Resetar ultimo boleto de teste
        result = db.execute_update("""
            UPDATE boletos SET status_envio = 'nao_enviado'
            WHERE numero_boleto LIKE 'TESTE-%'
        """)
        print("[OK] Todos os boletos de teste resetados")


def listar_testes_ativos():
    """Lista boletos de teste ativos no sistema"""

    boletos_teste = db.execute_query("""
        SELECT
            b.id,
            b.numero_boleto,
            b.status_envio,
            b.pdf_filename,
            cf.nome_completo,
            cf.whatsapp
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.numero_boleto LIKE 'TESTE-%'
        ORDER BY b.created_at DESC
        LIMIT 10
    """)

    if not boletos_teste:
        print("\n[INFO] Nenhum boleto de teste encontrado")
        return

    print(f"\n[TESTES] Boletos de teste ativos:")
    print("-" * 100)
    print(f"{'ID':<6} {'Numero Boleto':<20} {'Cliente':<30} {'WhatsApp':<15} {'Status':<15}")
    print("-" * 100)

    for b in boletos_teste:
        nome = b['nome_completo'][:28] if b['nome_completo'] else 'N/A'
        print(f"{b['id']:<6} {b['numero_boleto']:<20} {nome:<30} {b['whatsapp']:<15} {b['status_envio']:<15}")

    print("-" * 100)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Configurar teste com dados reais')
    parser.add_argument('--restaurar', nargs=2, metavar=('CLIENTE_ID', 'WHATSAPP'),
                        help='Restaurar WhatsApp original')
    parser.add_argument('--restaurar-ultimo', action='store_true',
                        help='Restaurar ultimo teste')
    parser.add_argument('--resetar-boleto', type=int, metavar='BOLETO_ID',
                        help='Resetar status do boleto')
    parser.add_argument('--listar-boletos', action='store_true',
                        help='Listar boletos PDFs disponiveis')
    parser.add_argument('--listar-clientes', action='store_true',
                        help='Listar clientes disponiveis')
    parser.add_argument('--listar-testes', action='store_true',
                        help='Listar testes ativos')

    args = parser.parse_args()

    if args.restaurar:
        cliente_id, whatsapp = args.restaurar
        restaurar_whatsapp_original(int(cliente_id), whatsapp)
    elif args.restaurar_ultimo:
        restaurar_ultimo_teste()
    elif args.resetar_boleto:
        resetar_status_boleto(args.resetar_boleto)
    elif args.listar_boletos:
        listar_boletos_disponiveis()
    elif args.listar_clientes:
        listar_clientes_reais()
    elif args.listar_testes:
        listar_testes_ativos()
    else:
        configurar_teste_completo()
