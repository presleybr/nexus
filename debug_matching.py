import sys
sys.path.insert(0, r'D:\Nexus')

from pathlib import Path
from backend.models.database import Database, execute_query

Database.initialize_pool()

# Pasta de downloads
downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

# Pegar alguns PDFs
pdfs = list(downloads_dir.glob("*.pdf"))[:10]

print("=" * 80)
print("TESTANDO MATCHING DE NOMES")
print("=" * 80)

for pdf_file in pdfs:
    # Extrair nome do PDF (mesma logica do codigo)
    nome_arquivo = pdf_file.stem
    partes = nome_arquivo.split('_')

    mes_str = partes[-1].upper()
    nome_cliente = '_'.join(partes[:-1])
    nome_cliente_formatado = nome_cliente.replace('_', ' ').title()

    print(f"\n{'='*80}")
    print(f"PDF: {pdf_file.name}")
    print(f"Nome extraido: '{nome_cliente_formatado}'")

    # Buscar no banco (mesma query do codigo)
    result = execute_query("""
        SELECT id, cpf, nome_completo
        FROM clientes_finais
        WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
        LIMIT 1
    """, (nome_cliente_formatado,), fetch=True)

    if result:
        print(f"[OK] ENCONTRADO no banco:")
        print(f"     ID: {result[0]['id']}")
        print(f"     Nome DB: '{result[0]['nome_completo']}'")
        print(f"     CPF: {result[0]['cpf']}")
    else:
        print(f"[ERRO] NAO ENCONTRADO no banco!")

        # Tentar busca parcial
        primeira_palavra = nome_cliente_formatado.split()[0]
        similar = execute_query("""
            SELECT id, nome_completo, cpf
            FROM clientes_finais
            WHERE nome_completo ILIKE %s
            ORDER BY nome_completo
            LIMIT 5
        """, (f'%{primeira_palavra}%',), fetch=True)

        if similar:
            print(f"\n     Clientes similares com '{primeira_palavra}':")
            for s in similar:
                print(f"       - {s['nome_completo']} (CPF: {s['cpf']})")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

# Contar total
total_pdfs = len(list(downloads_dir.glob("*.pdf")))
print(f"Total de PDFs: {total_pdfs}")

total_clientes = execute_query("SELECT COUNT(*) as total FROM clientes_finais", fetch=True)
print(f"Total de clientes no banco: {total_clientes[0]['total']}")
