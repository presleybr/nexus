"""
Atualiza os números de WhatsApp dos clientes usando a planilha do Dener
"""

import sys
import os
import io
import pandas as pd
from pathlib import Path

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db


def atualizar_whatsapp():
    """Atualiza números de WhatsApp dos clientes usando a planilha"""

    print("=" * 70)
    print("ATUALIZAÇÃO DE NÚMEROS DE WHATSAPP")
    print("=" * 70)

    # Caminho da planilha
    planilha_path = Path(r"D:\Nexus\planilhas\DENER__PLANILHA_GERAL.xlsx")

    if not planilha_path.exists():
        print(f"\n❌ Planilha não encontrada: {planilha_path}")
        return

    print(f"\n📄 Lendo planilha: {planilha_path.name}")

    # Ler Excel - cabeçalho na linha 11
    df = pd.read_excel(planilha_path, sheet_name=0, header=11)

    # Pular primeira linha (cabeçalho duplicado)
    df = df[1:].reset_index(drop=True)

    # Filtrar apenas PV 24627
    df = df[df['Unnamed: 6'] == 24627]

    print(f"✅ {len(df)} registros encontrados no PV 24627\n")

    stats = {
        'total': 0,
        'atualizados': 0,
        'sem_whatsapp': 0,
        'nao_encontrado': 0,
        'erros': 0
    }

    for idx, row in df.iterrows():
        try:
            stats['total'] += 1

            # Extrair CPF e limpar
            cpf_raw = str(row['Unnamed: 0']).strip()
            cpf = ''.join(filter(str.isdigit, cpf_raw))

            if not cpf or len(cpf) != 11:
                stats['erros'] += 1
                continue

            # Extrair WhatsApp da coluna Unnamed: 11 (coluna L)
            whatsapp_raw = row.get('Unnamed: 11')

            if pd.isna(whatsapp_raw) or not whatsapp_raw:
                stats['sem_whatsapp'] += 1
                continue

            # Limpar WhatsApp
            whatsapp = ''.join(filter(str.isdigit, str(whatsapp_raw)))

            if not whatsapp or len(whatsapp) < 10:
                stats['sem_whatsapp'] += 1
                continue

            # Adicionar 55 se não tiver
            if not whatsapp.startswith('55'):
                whatsapp = '55' + whatsapp

            # Buscar cliente no banco por CPF
            cliente = db.execute_query("""
                SELECT id, nome_completo, whatsapp
                FROM clientes_finais
                WHERE cpf = %s AND cliente_nexus_id = 2
            """, (cpf,))

            if not cliente:
                stats['nao_encontrado'] += 1
                continue

            cliente_id = cliente[0]['id']
            nome = cliente[0]['nome_completo']
            whatsapp_atual = cliente[0]['whatsapp']

            # Atualizar se for placeholder
            if whatsapp_atual == '55679999999999' or whatsapp_atual == '0000000000':
                db.execute_update("""
                    UPDATE clientes_finais
                    SET whatsapp = %s, telefone_celular = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (whatsapp, whatsapp, cliente_id))

                print(f"✅ {nome[:40]:40} | {whatsapp}")
                stats['atualizados'] += 1

        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            stats['erros'] += 1

    print("\n" + "=" * 70)
    print("📊 RESUMO:")
    print("=" * 70)
    print(f"   Total processados: {stats['total']}")
    print(f"   ✅ Atualizados: {stats['atualizados']}")
    print(f"   ⚠️ Sem WhatsApp na planilha: {stats['sem_whatsapp']}")
    print(f"   ⚠️ Cliente não encontrado: {stats['nao_encontrado']}")
    print(f"   ❌ Erros: {stats['erros']}")
    print("=" * 70)


if __name__ == '__main__':
    atualizar_whatsapp()
