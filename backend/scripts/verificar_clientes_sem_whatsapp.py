"""
Verifica quais clientes dos 36 PDFs não têm WhatsApp
"""
import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("CLIENTES SEM WHATSAPP - PDFs DE DEZEMBRO")
print("="*80 + "\n")

PASTA_PDFS = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

# Pegar todos os PDFs
pdfs = list(PASTA_PDFS.glob("*.pdf"))
print(f"Total de PDFs: {len(pdfs)}\n")

sem_whatsapp = []
com_whatsapp = []

for pdf in sorted(pdfs):
    nome_arquivo = pdf.stem.replace("_DEZEMBRO", "").replace("_", " ")

    # Buscar cliente
    cliente = db.execute_query("""
        SELECT id, nome_completo, cpf, whatsapp
        FROM clientes_finais
        WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
        AND ativo = TRUE
        LIMIT 1
    """, (nome_arquivo,))

    if not cliente:
        print(f"[AVISO] Cliente não encontrado: {nome_arquivo}")
        continue

    cliente = cliente[0]
    whatsapp = cliente.get('whatsapp')

    if not whatsapp or whatsapp.strip() == '':
        sem_whatsapp.append({
            'nome': cliente['nome_completo'],
            'cpf': cliente['cpf'],
            'id': cliente['id']
        })
    else:
        com_whatsapp.append({
            'nome': cliente['nome_completo'],
            'whatsapp': whatsapp
        })

print("\n" + "="*80)
print("RESUMO")
print("="*80)
print(f"Total PDFs: {len(pdfs)}")
print(f"Com WhatsApp: {len(com_whatsapp)}")
print(f"SEM WhatsApp: {len(sem_whatsapp)}")
print("="*80 + "\n")

if sem_whatsapp:
    print("CLIENTES SEM WHATSAPP:\n")
    for cliente in sem_whatsapp:
        print(f"ID {cliente['id']:4} | {cliente['nome'][:50]:<50} | CPF: {cliente['cpf']}")
    print()

print("="*80 + "\n")
