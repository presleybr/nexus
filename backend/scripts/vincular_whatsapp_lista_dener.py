"""
Script para vincular números de WhatsApp reais da lista do Dener aos clientes
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

# Lista de clientes com WhatsApp fornecida pelo Dener
# Formato: (nome_aproximado, numero_whatsapp)
LISTA_WHATSAPP = [
    ("Silvio Fernandes", "5544981060002"),
    ("Edmilson", "5567991162722"),
    ("Allan Da", "556784035988"),
    ("Anderson Santana", "5518997988023"),
    ("Wesley Junior Diot", "5565841100040"),
    ("Willian da Silva Freitas", "556798497011"),
    ("Zacarias Dos Santos Arcanjo", "556793265"),
    ("Victor Augusto", "5567814166655"),
    ("Aline Silva", "5564960021588"),
    ("Aline Cristina Silva", "5564960021588"),
    ("Leda Silva", "5564960021588"),
    ("Bruna Rafaela De Souza Aragão", "5567963884340"),
    ("Soliane Valente França", "556798497011"),
    ("Gabriel Oliveira Borges", "5567930050233"),
    ("Vanilza Souza Nunes Coelho", "5567914311247"),
    ("Lucas Roberto Rodrigues", "5567984055601"),
    ("Jonatan De Souza Lima", "55678833014"),
    ("Antonio Dos Santos Junior", "556791682222"),
    ("Victor Wander Gomes", "5567928744447"),
    ("Diego Vir Lino", "5567962338363"),
    ("Raquel Regina Horing", "5567810620233"),
    ("Sebastião Corrêa De Paula", "556798752283"),
    ("Sergio Cândido De Araujo", "55679901133"),
    ("Willian da Silva Freitas", "5567916622853"),
    ("Francis Da Silva", "5567926889641"),
    ("Joel Da Silva Alves", "5567915511108"),
    ("Marcelo Candido Araujo", "5567966955041"),
    ("Marcos Além Lara Gomes", "55672644"),
    ("Paulo Ferreira Malta Neto", "5567963911866"),
    ("Ricardo José Mendonça Junior", "5567997288714"),
    ("Gilberto Ferreira Da Silva", "5567841266146"),
    ("Izabela Martim Maciel", "5567922933587"),
    ("Kelly Cristina Gimenes", "5567922775555"),
    ("Emilly Thamires Alcantara", "5567928211456"),
    ("Leocir Garay Coelho", "5567969177007"),
    ("Luis Eduardo Ferreira", "5567848311225"),
    ("Adilson Evangelista De Sá", "5567981211311"),
    ("Daniel Passareli Rocha", "5567964433485"),
]


def limpar_nome(nome):
    """Remove caracteres especiais e normaliza o nome"""
    # Converter para maiúsculas
    nome = nome.upper().strip()
    # Remover acentos
    replacements = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U',
        'Ç': 'C'
    }
    for old, new in replacements.items():
        nome = nome.replace(old, new)

    return nome


def buscar_cliente_por_nome(nome_busca):
    """Busca cliente no banco por nome (busca flexível)"""
    nome_limpo = limpar_nome(nome_busca)

    # Dividir nome em palavras
    palavras = nome_limpo.split()

    # Buscar por cada palavra do nome
    for palavra in palavras:
        if len(palavra) < 3:  # Pular palavras muito curtas (Da, De, Dos)
            continue

        resultado = db.execute_query("""
            SELECT id, nome_completo, cpf, whatsapp, ponto_venda
            FROM clientes_finais
            WHERE UPPER(nome_completo) LIKE %s
            AND ativo = TRUE
            LIMIT 5
        """, (f"%{palavra}%",))

        if resultado:
            return resultado

    return []


def verificar_boletos_cliente(cliente_id):
    """Verifica se o cliente possui boletos cadastrados"""
    boletos = db.execute_query("""
        SELECT COUNT(*) as total
        FROM boletos
        WHERE cliente_final_id = %s
    """, (cliente_id,))

    return boletos[0]['total'] if boletos else 0


def vincular_whatsapp_real():
    """Vincula números de WhatsApp reais da lista aos clientes"""

    print("\n" + "="*80)
    print("VINCULANDO NÚMEROS DE WHATSAPP REAIS AOS CLIENTES DO DENER")
    print("="*80 + "\n")

    relatorio = {
        'vinculados': 0,
        'nao_encontrados': [],
        'multiplos': [],
        'sem_boleto': [],
        'ja_vinculados': 0
    }

    for nome_busca, whatsapp in LISTA_WHATSAPP:
        print(f"\n{'='*80}")
        print(f"[INFO] Processando: {nome_busca}")
        print(f"[WHATSAPP] {whatsapp}")
        print(f"{'='*80}")

        # Buscar cliente
        clientes = buscar_cliente_por_nome(nome_busca)

        if not clientes:
            print(f"[ERRO] Cliente NAO encontrado: {nome_busca}")
            relatorio['nao_encontrados'].append(nome_busca)
            continue

        if len(clientes) > 1:
            print(f"[AVISO] Multiplos clientes encontrados ({len(clientes)}):")
            for cliente in clientes:
                boletos_count = verificar_boletos_cliente(cliente['id'])
                print(f"   - ID {cliente['id']}: {cliente['nome_completo'][:50]}")
                print(f"     CPF: {cliente['cpf']}, Boletos: {boletos_count}, PV: {cliente['ponto_venda']}")

            relatorio['multiplos'].append({
                'busca': nome_busca,
                'encontrados': [c['nome_completo'] for c in clientes]
            })

            # Usar o primeiro cliente encontrado com boletos
            clientes_com_boletos = [c for c in clientes if verificar_boletos_cliente(c['id']) > 0]
            if clientes_com_boletos:
                cliente = clientes_com_boletos[0]
                print(f"   [OK] Usando cliente com boletos: {cliente['nome_completo']}")
            else:
                cliente = clientes[0]
                print(f"   [AVISO] Nenhum tem boletos, usando primeiro: {cliente['nome_completo']}")
        else:
            cliente = clientes[0]

        # Verificar se já tem WhatsApp
        if cliente['whatsapp'] and cliente['whatsapp'].strip():
            print(f"[INFO] Cliente ja tem WhatsApp cadastrado: {cliente['whatsapp']}")
            print(f"   Atualizando para: {whatsapp}")
            relatorio['ja_vinculados'] += 1

        # Verificar boletos
        boletos_count = verificar_boletos_cliente(cliente['id'])
        print(f"[BOLETOS] Cadastrados: {boletos_count}")

        if boletos_count == 0:
            print(f"[AVISO] Cliente SEM BOLETOS cadastrados!")
            relatorio['sem_boleto'].append(cliente['nome_completo'])

        # Atualizar WhatsApp
        try:
            db.execute_update("""
                UPDATE clientes_finais
                SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (whatsapp, cliente['id']))

            print(f"[OK] WhatsApp VINCULADO com sucesso!")
            print(f"   Cliente: {cliente['nome_completo']}")
            print(f"   ID: {cliente['id']}")
            print(f"   CPF: {cliente['cpf']}")
            print(f"   WhatsApp: {whatsapp}")

            relatorio['vinculados'] += 1

        except Exception as e:
            print(f"[ERRO] ERRO ao vincular: {e}")

    # RELATÓRIO FINAL
    print("\n" + "="*80)
    print("[RELATORIO] RELATORIO FINAL")
    print("="*80)
    print(f"\n[OK] Vinculados com sucesso: {relatorio['vinculados']}/{len(LISTA_WHATSAPP)}")
    print(f"[INFO] Ja tinham WhatsApp: {relatorio['ja_vinculados']}")

    if relatorio['nao_encontrados']:
        print(f"\n[ERRO] NAO ENCONTRADOS ({len(relatorio['nao_encontrados'])}):")
        for nome in relatorio['nao_encontrados']:
            print(f"   - {nome}")

    if relatorio['multiplos']:
        print(f"\n[AVISO] MULTIPLOS ENCONTRADOS ({len(relatorio['multiplos'])}):")
        for item in relatorio['multiplos']:
            print(f"   - Busca: {item['busca']}")
            print(f"     Encontrados: {', '.join(item['encontrados'][:2])}...")

    if relatorio['sem_boleto']:
        print(f"\n[AVISO] SEM BOLETOS ({len(relatorio['sem_boleto'])}):")
        for nome in relatorio['sem_boleto']:
            print(f"   - {nome}")

    print("\n" + "="*80)
    print("[OK] PROCESSO CONCLUIDO!")
    print("="*80 + "\n")

    return relatorio


def listar_vinculacoes():
    """Lista todos os clientes com WhatsApp vinculado"""

    print("\n" + "="*80)
    print("[LISTA] CLIENTES COM WHATSAPP VINCULADO (PV 24627)")
    print("="*80 + "\n")

    clientes = db.execute_query("""
        SELECT id, nome_completo, cpf, whatsapp, ponto_venda,
               (SELECT COUNT(*) FROM boletos WHERE cliente_final_id = clientes_finais.id) as total_boletos
        FROM clientes_finais
        WHERE whatsapp IS NOT NULL
        AND whatsapp != ''
        AND ponto_venda = '24627'
        AND ativo = TRUE
        ORDER BY nome_completo
    """)

    if not clientes:
        print("[ERRO] Nenhum cliente com WhatsApp vinculado encontrado!")
        return

    print(f"Total: {len(clientes)} clientes\n")

    for cliente in clientes:
        print(f"[OK] {cliente['nome_completo'][:40]:<40} | WhatsApp: {cliente['whatsapp']:<15} | Boletos: {cliente['total_boletos']}")

    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Vincula WhatsApp reais aos clientes')
    parser.add_argument('--listar', action='store_true',
                       help='Lista vinculações atuais')

    args = parser.parse_args()

    if args.listar:
        listar_vinculacoes()
    else:
        relatorio = vincular_whatsapp_real()

        print("\n[INFO] Para ver todas as vinculações, execute:")
        print("   python vincular_whatsapp_lista_dener.py --listar\n")
