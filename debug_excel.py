import pandas as pd

# Ler Excel exatamente como o código faz
excel_path = r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx"
df = pd.read_excel(excel_path, sheet_name=0, header=11)

print("="*80)
print("APÓS LER COM header=11")
print("="*80)
print(f"Total de linhas: {len(df)}")
print(f"\nColunas: {df.columns.tolist()[:6]}")

print("\n" + "="*80)
print("PRIMEIRAS 10 LINHAS (ANTES DE PULAR)")
print("="*80)
for i in range(min(10, len(df))):
    row = df.iloc[i]
    print(f"\nLinha {i}:")
    print(f"  Unnamed: 0: '{row['Unnamed: 0']}'")
    print(f"  Unnamed: 1: '{row.get('Unnamed: 1', 'N/A')}'")
    print(f"  Unnamed: 5: '{row.get('Unnamed: 5', 'N/A')}'")

# Agora pular primeira linha como o código faz
df = df[1:].reset_index(drop=True)

print("\n" + "="*80)
print("APÓS PULAR PRIMEIRA LINHA df[1:]")
print("="*80)
print(f"Total de linhas: {len(df)}")

print("\n" + "="*80)
print("PRIMEIRAS 10 LINHAS (APÓS PULAR)")
print("="*80)
for i in range(min(10, len(df))):
    row = df.iloc[i]
    cpf_raw = str(row['Unnamed: 0']).strip()
    nome_raw = str(row.get('Unnamed: 5', 'N/A')).strip()

    # Limpar CPF
    cpf = ''.join(filter(str.isdigit, cpf_raw))

    print(f"\nLinha {i}:")
    print(f"  CPF raw: '{cpf_raw}' -> limpo: '{cpf}' (len={len(cpf)})")
    print(f"  Nome: '{nome_raw}'")
    print(f"  É válido? {len(cpf) == 11}")
