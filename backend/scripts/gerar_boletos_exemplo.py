"""
Script para gerar boletos de exemplo para os clientes cadastrados
"""

import os
import sys
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.models.database import db, get_db_connection, Database
from backend.services.boleto_generator import boleto_generator


def gerar_boletos_para_clientes():
    """Gera boletos de exemplo para todos os clientes finais ativos"""
    print("=" * 80)
    print("GERACAO DE BOLETOS DE EXEMPLO")
    print("=" * 80)

    conn = None
    try:
        # Buscar clientes finais ativos
        clientes = db.execute_query("""
            SELECT *
            FROM clientes_finais
            WHERE ativo = true
            ORDER BY id
        """, ())

        if not clientes:
            print("\n[AVISO] Nenhum cliente ativo encontrado!")
            return

        print(f"\n[INFO] Encontrados {len(clientes)} clientes ativos")
        print(f"[INFO] Gerando 3 parcelas para cada cliente...\n")

        total_gerados = 0
        total_erros = 0

        # Obter conexão única para todas as inserções
        conn = get_db_connection()

        for cliente in clientes:
            print(f"[INFO] Cliente: {cliente['nome_completo']}")

            # Gerar 3 parcelas para cada cliente
            for parcela in range(1, 4):
                try:
                    # Data de vencimento: hoje + (parcela * 30 dias)
                    data_vencimento = date.today() + timedelta(days=parcela * 30)

                    # Valor da parcela
                    valor = float(cliente['valor_parcela'])

                    # Gerar PDF do boleto
                    resultado_pdf = boleto_generator.gerar_boleto_pdf(
                        cliente_final=cliente,
                        valor=valor,
                        data_vencimento=data_vencimento,
                        numero_parcela=parcela
                    )

                    if not resultado_pdf['success']:
                        print(f"  [ERRO] Falha ao gerar PDF da parcela {parcela}")
                        total_erros += 1
                        continue

                    # Calcular mês/ano de referência
                    mes_ref = data_vencimento.month
                    ano_ref = data_vencimento.year

                    # Inserir boleto no banco usando conexão dedicada
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO boletos (
                                cliente_nexus_id, cliente_final_id, numero_boleto,
                                linha_digitavel, codigo_barras, nosso_numero,
                                valor_original, valor_atualizado, data_vencimento, data_emissao,
                                mes_referencia, ano_referencia, numero_parcela,
                                descricao, status, status_envio,
                                pdf_filename, pdf_path, pdf_size, gerado_por
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) RETURNING id
                        """, (
                            cliente['cliente_nexus_id'], cliente['id'],
                            resultado_pdf['nosso_numero'],
                            resultado_pdf['linha_digitavel'], resultado_pdf['codigo_barras'],
                            resultado_pdf['nosso_numero'],
                            valor, valor, data_vencimento, date.today(),
                            mes_ref, ano_ref, parcela,
                            f"Parcela {parcela}/{cliente['prazo_meses']}",
                            'pendente', 'nao_enviado',
                            resultado_pdf['filename'], resultado_pdf['filepath'],
                            resultado_pdf['file_size'], 'script_exemplo'
                        ))
                        boleto_id = cursor.fetchone()[0]
                        conn.commit()  # Commit imediato após cada insert

                    print(f"  [OK] Parcela {parcela} - ID {boleto_id} - Vencimento: {data_vencimento}")
                    total_gerados += 1

                except Exception as e:
                    print(f"  [ERRO] Parcela {parcela}: {str(e)}")
                    if conn:
                        conn.rollback()
                    total_erros += 1

            print()  # Linha em branco entre clientes

        print("=" * 80)
        print(f"[INFO] Total de boletos gerados: {total_gerados}")
        print(f"[INFO] Total de erros: {total_erros}")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERRO] Erro ao gerar boletos: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            Database.return_connection(conn)


if __name__ == '__main__':
    gerar_boletos_para_clientes()
