import sys
sys.path.insert(0, r'D:\Nexus')

import pandas as pd
from pathlib import Path
from backend.models.database import Database, execute_query

# Inicializar pool
Database.initialize_pool()

excel_path = Path(r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx")

print("=" * 80)
print("TESTANDO IMPORTACAO DE CLIENTES")
print("=" * 80)

# Ler Excel exatamente como o código faz
df = pd.read_excel(excel_path, sheet_name=0, header=11)

print(f"\n1. Total de linhas ANTES de pular: {len(df)}")
print(f"   Colunas: {df.columns.tolist()[:6]}")

# Pular primeira linha
df = df[1:].reset_index(drop=True)

print(f"\n2. Total de linhas DEPOIS de pular: {len(df)}")

# Filtrar linhas válidas
df = df[df['Unnamed: 0'].notna() & df['Unnamed: 5'].notna()]

print(f"\n3. Total de linhas COM CPF e Nome: {len(df)}")

# Testar primeiras 5 linhas
print("\n4. TESTANDO PRIMEIRAS 5 LINHAS:")
print("=" * 80)

import re

clientes_ok = 0
clientes_erro = 0

for index in range(min(5, len(df))):
    row = df.iloc[index]

    cpf_raw = str(row['Unnamed: 0']).strip()
    nome_raw = str(row['Unnamed: 5']).strip()

    print(f"\nLinha {index}:")
    print(f"  CPF raw: '{cpf_raw}'")
    print(f"  Nome raw: '{nome_raw}'")

    # Validações
    if cpf_raw.lower() in ['nan', 'none', '']:
        print("  [ERRO] CPF vazio/nan")
        clientes_erro += 1
        continue

    if nome_raw.lower() in ['nan', 'none', '']:
        print("  [ERRO] Nome vazio/nan")
        clientes_erro += 1
        continue

    # Limpar nome
    nome = re.sub(r'\s*-?\s*\d+%?', '', nome_raw).strip()

    # Limpar CPF
    cpf = ''.join(filter(str.isdigit, cpf_raw))

    print(f"  CPF limpo: '{cpf}' (len={len(cpf)})")
    print(f"  Nome limpo: '{nome}'")

    # Validar CPF
    if not cpf or len(cpf) != 11 or not cpf.isdigit():
        print(f"  [ERRO] CPF invalido (len={len(cpf)})")
        clientes_erro += 1
        continue

    # Formatar CPF
    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    print(f"  CPF formatado: '{cpf_formatado}'")
    print(f"  [OK] Cliente valido!")
    clientes_ok += 1

print("\n" + "=" * 80)
print(f"RESULTADO: {clientes_ok} OK, {clientes_erro} ERRO")
print("=" * 80)

# Contar no banco
total_db = execute_query('SELECT COUNT(*) as total FROM clientes_finais', fetch=True)
print(f"\nTotal de clientes JA NO BANCO: {total_db[0]['total'] if total_db else 0}")
