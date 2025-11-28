import sys
sys.path.insert(0, r'D:\Nexus')

from pathlib import Path
from backend.models.database import Database, execute_query

Database.initialize_pool()

# Pasta de downloads
downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

# Nomes que falharam nos logs anteriores
nomes_erro_logs = [
    "Luis Eduardo Ferreira Caceres",
    "Marcelo Candido De Araujo",
    "Marcos Alem Lara Gomes",
    "Paulo Ferreira Malta Neto",
    "Raquel Regina Horing",
    "Sebastiao Correa De Paula",
    "Sergio Candido De Araujo",
    "Silvio Fernandes",
    "Vanderson Santana",
    "Vanilza Souza Nunes Coelho",
    "Victor Augusto E Silva",
    "Victor Wander Gomes Dias",
    "Wesley Junior Diderot Cheriscar",
    "Willian Da Silva Freitas",
    "Zacarias Dos Santos Arcanjo Imovel"
]

print("=" * 80)
print("VERIFICANDO NOMES QUE FALHARAM NOS LOGS")
print("=" * 80)

encontrados = 0
nao_encontrados = 0

for nome_formatado in nomes_erro_logs:
    # Buscar no banco
    result = execute_query("""
        SELECT id, nome_completo, cpf
        FROM clientes_finais
        WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
        LIMIT 1
    """, (nome_formatado,), fetch=True)

    print(f"\nNome: '{nome_formatado}'")

    if result:
        print(f"  [OK] ENCONTRADO: '{result[0]['nome_completo']}' (CPF: {result[0]['cpf']})")
        encontrados += 1
    else:
        print(f"  [ERRO] NAO ENCONTRADO!")
        nao_encontrados += 1

        # Buscar PDF correspondente
        nome_pdf_pattern = nome_formatado.upper().replace(' ', '_')
        pdfs_match = list(downloads_dir.glob(f"{nome_pdf_pattern}*.pdf"))

        if pdfs_match:
            print(f"       PDF existe: {pdfs_match[0].name}")

        # Buscar similar no banco
        primeira_palavra = nome_formatado.split()[0]
        similar = execute_query("""
            SELECT nome_completo
            FROM clientes_finais
            WHERE nome_completo ILIKE %s
            LIMIT 3
        """, (f'%{primeira_palavra}%',), fetch=True)

        if similar:
            print(f"       Similares no banco:")
            for s in similar:
                print(f"         - {s['nome_completo']}")

print("\n" + "=" * 80)
print(f"RESULTADO: {encontrados} encontrados, {nao_encontrados} nao encontrados")
print("=" * 80)
