import pandas as pd

# Ler Excel com header=11 (como o código está fazendo)
df = pd.read_excel(r'D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx', header=11)

print('Colunas:')
print(df.columns.tolist())

print('\nPrimeiras 5 linhas:')
for i, row in df.head(5).iterrows():
    print(f'\n=== Linha {i} ===')
    print(f"Unnamed: 0: {row.get('Unnamed: 0', 'N/A')}")
    print(f"Unnamed: 1: {row.get('Unnamed: 1', 'N/A')}")
    print(f"Unnamed: 5: {row.get('Unnamed: 5', 'N/A')}")

print('\n\nREAL COLUMN NAMES (first 10):')
for col in df.columns[:10]:
    print(f"  {col}")
