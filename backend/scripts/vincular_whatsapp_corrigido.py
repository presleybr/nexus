"""
Script para vincular números de WhatsApp CORRIGIDOS aos clientes
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

# Lista corrigida de clientes com WhatsApp
LISTA_WHATSAPP = [
    ("Silvio Fernandes", "5544981060002"),
    ("Edmilson", "5567991162722"),
    ("Allan Da", "55678403598"),
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
    ("Jonatan De Souza Lima", "556788333014"),
    ("Antonio Dos Santos Junior", "556791682222"),
    ("Victor Wander Gomes", "5567928744447"),
    ("Diego Victor Lino", "5567962338363"),
    ("Raquel Regina Horing", "5567810620233"),
    ("Sebastião Corrêa De Paula", "556798752283"),
    ("Sergio Cândido De Araujo", "5567993770113"),
    ("Willian da Silva Freitas", "5567916622853"),
    ("Jhony Francis Da Silva", "5567926889641"),
    ("Joel Da Silva Alves", "5567915511108"),
    ("Marcelo Candido Araujo", "556796695041"),
    ("Marcos Além Lara Gomes", "55678122264"),
    ("Paulo Ferreira Malta Neto", "5567963911866"),
    ("Eduardo José Mendonça Junior", "5567997288714"),
    ("Gilberto Ferreira Da Silva", "5567841266146"),
    ("Izabela Martim Maciel", "5567922933587"),
    ("Kelly Cristina Gimenes", "5567922775555"),
    ("Emilly Thamires Alcantara Dias", "5567928211456"),
    ("Leocir Garay Coelho", "5567969177007"),
    ("Luis Eduardo Ferreira", "5567848311225"),
    ("Adilson Evangelista De Sá", "5567981211311"),
    ("Daniel Passareli Rocha", "5567964433485"),
    ("Vanderson Santana", "5518997988023"),
]


def limpar_nome(nome):
    """Remove caracteres especiais e normaliza o nome"""
    nome = nome.upper().strip()
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
    palavras = [p for p in nome_limpo.split() if len(p) > 2]

    if not palavras:
        return []

    # Buscar por cada palavra
    for palavra in palavras:
        resultado = db.execute_query("""
            SELECT id, nome_completo, cpf, whatsapp
            FROM clientes_finais
            WHERE UPPER(nome_completo) LIKE %s
            AND ativo = TRUE
            LIMIT 5
        """, (f"%{palavra}%",))

        if resultado:
            return resultado

    return []


print("\n" + "="*80)
print("VINCULANDO WHATSAPP (LISTA CORRIGIDA)")
print("="*80 + "\n")

stats = {
    'vinculados': 0,
    'nao_encontrados': [],
    'ja_tinham': 0,
    'multiplos': 0
}

for nome_busca, whatsapp in LISTA_WHATSAPP:
    print(f"\n[INFO] {nome_busca} -> {whatsapp}")

    clientes = buscar_cliente_por_nome(nome_busca)

    if not clientes:
        print(f"   [ERRO] Cliente NAO encontrado")
        stats['nao_encontrados'].append(nome_busca)
        continue

    if len(clientes) > 1:
        print(f"   [AVISO] {len(clientes)} clientes encontrados, usando primeiro")
        stats['multiplos'] += 1

    cliente = clientes[0]

    # Verificar se já tem WhatsApp
    if cliente['whatsapp'] and cliente['whatsapp'].strip() and cliente['whatsapp'] != '0000000000':
        if cliente['whatsapp'] == whatsapp:
            print(f"   [OK] WhatsApp ja esta correto")
            stats['ja_tinham'] += 1
            continue
        else:
            print(f"   [INFO] Atualizando de {cliente['whatsapp']} para {whatsapp}")

    # Atualizar WhatsApp
    try:
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (whatsapp, cliente['id']))

        print(f"   [OK] VINCULADO! ID: {cliente['id']}, Nome: {cliente['nome_completo'][:40]}")
        stats['vinculados'] += 1

    except Exception as e:
        print(f"   [ERRO] {e}")

print("\n" + "="*80)
print("RESUMO:")
print("="*80)
print(f"Total na lista: {len(LISTA_WHATSAPP)}")
print(f"Vinculados: {stats['vinculados']}")
print(f"Ja tinham: {stats['ja_tinham']}")
print(f"Multiplos: {stats['multiplos']}")
print(f"Nao encontrados: {len(stats['nao_encontrados'])}")

if stats['nao_encontrados']:
    print("\nNAO ENCONTRADOS:")
    for nome in stats['nao_encontrados']:
        print(f"  - {nome}")

print("="*80 + "\n")
