import sys
sys.path.insert(0, r'D:\Nexus')

from pathlib import Path
from datetime import datetime
from backend.models.database import Database

Database.initialize_pool()
db = Database()
conn = db.get_connection()
cur = conn.cursor()

print("=" * 80)
print("TESTANDO IMPORTACAO DE BOLETOS")
print("=" * 80)

try:
    # Limpar boletos existentes
    cur.execute("DELETE FROM boletos")
    conn.commit()
    print(f"\nBoletos deletados: {cur.rowcount}")

    # Pasta de downloads
    downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")
    pdfs = list(downloads_dir.glob("*.pdf"))

    print(f"Total de PDFs encontrados: {len(pdfs)}")

    # Meses
    meses = {
        'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'MARCO': 3,
        'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6,
        'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9,
        'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
    }

    boletos_importados = 0
    boletos_sem_cliente = 0
    boletos_erros = 0

    print("\n" + "=" * 80)
    print("PROCESSANDO BOLETOS")
    print("=" * 80)

    for pdf_file in pdfs:
        try:
            # Extrair info do nome
            nome_arquivo = pdf_file.stem
            partes = nome_arquivo.split('_')

            if len(partes) < 2:
                print(f"[SKIP] Nome invalido: {pdf_file.name}")
                boletos_erros += 1
                continue

            mes_str = partes[-1].upper()
            nome_cliente = '_'.join(partes[:-1])
            nome_cliente_formatado = nome_cliente.replace('_', ' ').title()

            mes_num = meses.get(mes_str, datetime.now().month)
            ano = datetime.now().year

            # Buscar cliente no banco
            cur.execute("""
                SELECT id, cpf, nome_completo
                FROM clientes_finais
                WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
                LIMIT 1
            """, (nome_cliente_formatado,))

            cliente = cur.fetchone()

            if not cliente:
                print(f"[SEM CLIENTE] {nome_cliente_formatado}")
                boletos_sem_cliente += 1
                continue

            cliente_id = cliente[0]

            # Verificar se boleto ja existe
            cur.execute("""
                SELECT id FROM boletos
                WHERE cliente_final_id = %s AND mes_referencia = %s
                  AND ano_referencia = %s AND pdf_filename = %s
            """, (cliente_id, mes_num, ano, pdf_file.name))

            if cur.fetchone():
                print(f"[JA EXISTE] {pdf_file.name}")
                continue

            # Inserir boleto
            data_vencimento = datetime(ano, mes_num, 10).date()
            numero_boleto = f"BOL-{cliente_id}-{mes_num:02d}{ano}"

            cur.execute("""
                INSERT INTO boletos (
                    cliente_final_id, cliente_nexus_id, numero_boleto, valor_original,
                    data_vencimento, data_emissao, mes_referencia, ano_referencia,
                    numero_parcela, descricao, status, status_envio,
                    pdf_filename, pdf_path, pdf_size, gerado_por,
                    created_at, updated_at
                ) VALUES (
                    %s, NULL, %s, 0.0, %s, %s, %s, %s,
                    1, %s, 'pendente', 'nao_enviado',
                    %s, %s, %s, 'automacao_canopus',
                    NOW(), NOW()
                )
                RETURNING id
            """, (
                cliente_id, numero_boleto, data_vencimento, datetime.now().date(),
                mes_num, ano, f"Boleto {mes_str}/{ano}",
                pdf_file.name, str(pdf_file), pdf_file.stat().st_size
            ))

            boleto_id = cur.fetchone()[0]
            boletos_importados += 1

            if boletos_importados <= 5:
                print(f"[OK] ID {boleto_id:3d} | Cliente: {cliente[2]} | {pdf_file.name}")

        except Exception as e:
            print(f"[ERRO] {pdf_file.name}: {e}")
            boletos_erros += 1
            continue

    conn.commit()

    print("\n" + "=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)
    print(f"Boletos importados: {boletos_importados}")
    print(f"Boletos sem cliente: {boletos_sem_cliente}")
    print(f"Boletos com erro: {boletos_erros}")

    # Verificar no banco
    cur.execute("SELECT COUNT(*) FROM boletos")
    total_db = cur.fetchone()[0]
    print(f"\nTotal de boletos no banco: {total_db}")

except Exception as e:
    import traceback
    print(f"\nERRO FATAL: {e}")
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
