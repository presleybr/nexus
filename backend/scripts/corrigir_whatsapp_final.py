"""
Script para corrigir números de WhatsApp específicos
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def limpar_numero(numero):
    """Remove tudo exceto dígitos"""
    return re.sub(r'[^\d]', '', numero)

# Lista de correções
CORRECOES = [
    ("ZACARIAS DOS SANTOS", "+55 67 9309-3265"),
    ("VANILZA SOUZA", "+55 67 9143-1247"),
    ("ALLAN DA", "+55 67 8403-5987"),
    ("SEBASTIAO", "+55 67 9875-2283"),
    ("JOEL", "+55 67 9155-1108"),
    ("CARLA SOLIANE", "+55 67 9849-7011"),
]

print("\n" + "="*80)
print("CORRIGINDO NUMEROS DE WHATSAPP")
print("="*80 + "\n")

for nome_busca, numero_formatado in CORRECOES:
    # Limpar número (remover +, -, espaços)
    numero_limpo = limpar_numero(numero_formatado)

    print(f"[INFO] {nome_busca}")
    print(f"  Numero formatado: {numero_formatado}")
    print(f"  Numero limpo: {numero_limpo}")

    # Buscar cliente
    palavras = nome_busca.upper().split()
    condicoes = " AND ".join([f"UPPER(nome_completo) LIKE %s" for _ in palavras])
    params = [f"%{palavra}%" for palavra in palavras]

    clientes = db.execute_query(f"""
        SELECT id, nome_completo, whatsapp
        FROM clientes_finais
        WHERE {condicoes}
        AND ativo = TRUE
        LIMIT 5
    """, tuple(params))

    if not clientes:
        print(f"  [ERRO] Cliente NAO encontrado!\n")
        continue

    if len(clientes) > 1:
        print(f"  [AVISO] {len(clientes)} clientes encontrados:")
        for c in clientes:
            print(f"    - {c['nome_completo']}")

    cliente = clientes[0]

    print(f"  [OK] Cliente: {cliente['nome_completo']}")
    print(f"  [OK] ID: {cliente['id']}")

    if cliente['whatsapp'] == numero_limpo:
        print(f"  [INFO] Numero ja esta correto\n")
        continue

    if cliente['whatsapp']:
        print(f"  [INFO] WhatsApp antigo: {cliente['whatsapp']}")

    # Atualizar
    db.execute_update("""
        UPDATE clientes_finais
        SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (numero_limpo, cliente['id']))

    print(f"  [OK] WhatsApp atualizado: {numero_limpo}\n")

print("="*80)
print("[OK] CORRECOES CONCLUIDAS!")
print("="*80 + "\n")
