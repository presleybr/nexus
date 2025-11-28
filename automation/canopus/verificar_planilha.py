import pandas as pd
from pathlib import Path

planilha = Path('D:/Nexus/planilhas/DENER__PLANILHA_GERAL.xlsx')
df = pd.read_excel(planilha, sheet_name=0, header=11)

# Remover primeira linha (cabeçalho duplicado)
df = df[1:]

# Pegar apenas as colunas que importamos
df_filtrado = df.iloc[:, [0, 5, 6]]  # CPF, Nome, PV
df_filtrado.columns = ['cpf', 'nome', 'pv']

# Remover vazios
df_filtrado = df_filtrado[df_filtrado['cpf'].notna()]

# Filtrar PV 17308 e 24627
df_filtrado = df_filtrado[df_filtrado['pv'].isin([17308, 24627])]

print('=' * 80)
print('CLIENTES NA PLANILHA POR PONTO DE VENDA')
print('=' * 80)

print('\nPV 17308:')
pv17 = df_filtrado[df_filtrado['pv'] == 17308]
print(f'Total: {len(pv17)}')
if len(pv17) > 0:
    print('\nPrimeiros 5:')
    for idx, row in pv17.head(5).iterrows():
        cpf = str(row['cpf']).replace('.', '').replace('-', '').strip()
        print(f'  CPF: {cpf} - {row["nome"]}')

print('\n' + '-' * 80)
print('\nPV 24627:')
pv24 = df_filtrado[df_filtrado['pv'] == 24627]
print(f'Total: {len(pv24)}')
if len(pv24) > 0:
    print('\nPrimeiros 5:')
    for idx, row in pv24.head(5).iterrows():
        cpf = str(row['cpf']).replace('.', '').replace('-', '').strip()
        print(f'  CPF: {cpf} - {row["nome"]}')

print('\n' + '=' * 80)
print(f'TOTAIS: PV 17308 = {len(pv17)}, PV 24627 = {len(pv24)}')
print('=' * 80)
