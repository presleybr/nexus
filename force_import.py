"""
Script para testar a importação de clientes MANUALMENTE
"""
import sys
sys.path.insert(0, r'D:\Nexus')

import pandas as pd
from pathlib import Path
from backend.models.database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar pool
Database.initialize_pool()
db = Database()
conn = db.get_connection()
cur = conn.cursor()

print("=" * 80)
print("IMPORTACAO MANUAL DE CLIENTES")
print("=" * 80)

try:
    # 1. LIMPAR DADOS ANTIGOS
    print("\n1. Limpando dados antigos...")
    cur.execute("DELETE FROM boletos")
    boletos_deletados = cur.rowcount
    print(f"   Deletados: {boletos_deletados} boletos")

    cur.execute("DELETE FROM clientes_finais")
    clientes_deletados = cur.rowcount
    print(f"   Deletados: {clientes_deletados} clientes")

    conn.commit()

    # 2. IMPORTAR CLIENTES
    print("\n2. Importando clientes do Excel...")
    excel_path = Path(r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx")

    df = pd.read_excel(excel_path, sheet_name=0, header=11)
    print(f"   Linhas lidas: {len(df)}")

    # Pular primeira linha
    df = df[1:].reset_index(drop=True)
    print(f"   Apos pular header: {len(df)}")

    # Filtrar validos
    df = df[df['Unnamed: 0'].notna() & df['Unnamed: 5'].notna()]
    print(f"   Com CPF e Nome: {len(df)}")

    # Buscar consultor Danner
    cur.execute("SELECT id FROM consultores WHERE nome = 'Danner' LIMIT 1")
    consultor = cur.fetchone()
    consultor_id = consultor[0] if consultor else None
    print(f"   Consultor ID: {consultor_id}")

    if not consultor_id:
        print("   ERRO: Consultor Danner nao encontrado!")
        sys.exit(1)

    clientes_importados = 0
    clientes_erros = 0

    import re

    for index, row in df.iterrows():
        try:
            cpf_raw = str(row['Unnamed: 0']).strip()
            nome_raw = str(row['Unnamed: 5']).strip()

            # Pular vazios
            if cpf_raw.lower() in ['nan', 'none', ''] or nome_raw.lower() in ['nan', 'none', '']:
                continue

            # Limpar nome
            nome = re.sub(r'\s*-?\s*\d+%?', '', nome_raw).strip()

            # Limpar CPF
            cpf = ''.join(filter(str.isdigit, cpf_raw))

            # Validar CPF
            if not cpf or len(cpf) != 11 or not cpf.isdigit():
                print(f"   [AVISO] CPF invalido: {cpf_raw} (linha {index + 13})")
                clientes_erros += 1
                continue

            # Formatar CPF
            cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

            # Gerar numero de contrato unico
            numero_contrato = f"CANOPUS-{cpf}"

            # Inserir cliente
            cur.execute("""
                INSERT INTO clientes_finais (
                    nome_completo, cpf, telefone_celular, whatsapp,
                    numero_contrato, grupo_consorcio, cota_consorcio,
                    valor_credito, valor_parcela, prazo_meses, data_adesao,
                    consultor_id, cliente_nexus_id, ativo,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, '', '',
                    %s, 'N/A', 'N/A',
                    0.0, 0.0, 0, NOW(),
                    %s, NULL, TRUE,
                    NOW(), NOW()
                )
                ON CONFLICT (cpf) DO UPDATE SET
                    nome_completo = EXCLUDED.nome_completo,
                    consultor_id = EXCLUDED.consultor_id,
                    updated_at = NOW()
                RETURNING id
            """, (nome, cpf_formatado, numero_contrato, consultor_id))

            cliente_id = cur.fetchone()[0]
            clientes_importados += 1

            if clientes_importados <= 5:
                print(f"   [OK] {cliente_id:3d} | {nome} | {cpf_formatado}")

        except Exception as e:
            print(f"   [ERRO] Linha {index + 12}: {e}")
            print(f"          Nome: {nome if 'nome' in locals() else 'N/A'}")
            print(f"          CPF: {cpf_formatado if 'cpf_formatado' in locals() else 'N/A'}")
            import traceback
            if clientes_erros < 3:  # Mostrar detalhes dos primeiros 3 erros
                traceback.print_exc()
            clientes_erros += 1
            continue

    conn.commit()
    print(f"\n3. RESULTADO:")
    print(f"   Importados: {clientes_importados}")
    print(f"   Erros: {clientes_erros}")

    # 4. VERIFICAR NO BANCO
    cur.execute("SELECT COUNT(*) FROM clientes_finais")
    total_db = cur.fetchone()[0]
    print(f"\n4. VERIFICACAO:")
    print(f"   Total no banco: {total_db}")

except Exception as e:
    import traceback
    print(f"\nERRO FATAL: {e}")
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
    print("\n" + "=" * 80)
