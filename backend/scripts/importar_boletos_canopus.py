"""
Importa boletos da Canopus para o banco de dados

Lê os PDFs, extrai dados e cria:
- Clientes finais (se não existirem)
- Boletos com dados extraídos do PDF
"""

import sys
import os
import io
from datetime import datetime

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db
from services.pdf_extractor import extrair_dados_boleto


# Mapeamento de nomes para WhatsApp (você pode ajustar conforme necessário)
# Este é um exemplo - você pode ter uma planilha com esses dados
CLIENTES_WHATSAPP = {
    'ZACARIAS DOS SANTOS ARCANJO': '5567999999999',  # Exemplo
    # Adicione mais conforme necessário
}


def importar_boletos_canopus():
    """Importa todos os boletos da pasta Canopus para o banco"""

    print("=" * 70)
    print("IMPORTAÇÃO DE BOLETOS DA CANOPUS PARA O BANCO")
    print("=" * 70)

    pasta_canopus = r'D:\Nexus\automation\canopus\downloads\Danner'
    cliente_nexus_id = 2  # ID da empresa Cred MS Consorcios (verificado no banco)

    if not os.path.exists(pasta_canopus):
        print(f"❌ Pasta não existe: {pasta_canopus}")
        return

    # Buscar todos os PDFs
    pdfs = [f for f in os.listdir(pasta_canopus) if f.endswith('.pdf')]

    if not pdfs:
        print(f"❌ Nenhum PDF encontrado em: {pasta_canopus}")
        return

    print(f"\n📄 Encontrados {len(pdfs)} PDFs para processar\n")

    stats = {
        'total_pdfs': len(pdfs),
        'clientes_criados': 0,
        'clientes_existentes': 0,
        'boletos_criados': 0,
        'erros': 0,
        'pdfs_sem_dados': 0
    }

    # Processar cada PDF
    for idx, pdf_filename in enumerate(pdfs, 1):
        pdf_path = os.path.join(pasta_canopus, pdf_filename)

        print(f"[{idx}/{len(pdfs)}] Processando: {pdf_filename[:50]}")

        try:
            # Extrair dados do PDF
            print(f"   📄 Extraindo dados...")
            dados_pdf = extrair_dados_boleto(pdf_path)

            if not dados_pdf.get('sucesso'):
                print(f"   ⚠️  Não foi possível extrair dados completos do PDF")
                stats['pdfs_sem_dados'] += 1
                continue

            # Dados extraídos
            nome = dados_pdf.get('nome_pagador')
            cpf = dados_pdf.get('cpf', '').replace('.', '').replace('-', '')
            vencimento = dados_pdf.get('vencimento')
            valor = dados_pdf.get('valor', 0)
            contrato = dados_pdf.get('contrato')

            print(f"   ✅ Nome: {nome}")
            print(f"   ✅ CPF: {cpf}")
            print(f"   ✅ Vencimento: {dados_pdf.get('vencimento_str')}")
            print(f"   ✅ Valor: R$ {valor:.2f}")

            # Verificar se cliente já existe (por CPF)
            cliente_existente = db.execute_query("""
                SELECT id, nome_completo, whatsapp
                FROM clientes_finais
                WHERE cpf = %s AND cliente_nexus_id = %s
            """, (cpf, cliente_nexus_id))

            if cliente_existente:
                cliente_id = cliente_existente[0]['id']
                print(f"   ℹ️  Cliente já existe no banco (ID: {cliente_id})")
                stats['clientes_existentes'] += 1
            else:
                # Criar novo cliente
                print(f"   ➕ Criando novo cliente...")

                # Tentar obter WhatsApp do mapeamento ou usar placeholder
                whatsapp = CLIENTES_WHATSAPP.get(nome, '55679999999999')  # Placeholder
                telefone_celular = whatsapp
                numero_contrato = f"TEMP-{cpf}"  # Número de contrato temporário baseado no CPF

                # Separar grupo e cota do PDF (formato: 008310-1627-00)
                grupo_cota_completo = dados_pdf.get('grupo_cota', '')
                if grupo_cota_completo and '-' in grupo_cota_completo:
                    partes = grupo_cota_completo.split('-')
                    grupo_consorcio = partes[0] if len(partes) > 0 else 'N/A'
                    cota_consorcio = partes[1] if len(partes) > 1 else 'N/A'
                else:
                    grupo_consorcio = 'N/A'
                    cota_consorcio = 'N/A'

                # Preencher TODOS os campos NOT NULL comuns com valores padrão ou do PDF
                valor_parcela = valor  # Valor da parcela é o valor do boleto
                prazo_meses = 60  # Prazo padrão de 60 meses (5 anos) - comum em consórcios
                data_adesao = datetime.now().date()  # Data de hoje como data de adesão

                novo_cliente = db.execute_query("""
                    INSERT INTO clientes_finais
                    (cliente_nexus_id, nome_completo, cpf, whatsapp, telefone_celular, numero_contrato,
                     grupo_consorcio, cota_consorcio, valor_credito, valor_parcela, prazo_meses,
                     data_adesao, ativo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (cliente_nexus_id, nome, cpf, whatsapp, telefone_celular, numero_contrato,
                      grupo_consorcio, cota_consorcio, 0.0, valor_parcela, prazo_meses,
                      data_adesao, True))

                cliente_id = novo_cliente[0]['id']
                print(f"   ✅ Cliente criado (ID: {cliente_id})")
                stats['clientes_criados'] += 1

            # Verificar se boleto já existe para este cliente e mês
            mes_ref = vencimento.month if vencimento else datetime.now().month
            ano_ref = vencimento.year if vencimento else datetime.now().year

            boleto_existente = db.execute_query("""
                SELECT id FROM boletos
                WHERE cliente_final_id = %s
                AND mes_referencia = %s
                AND ano_referencia = %s
            """, (cliente_id, mes_ref, ano_ref))

            if boleto_existente:
                print(f"   ℹ️  Boleto já existe para este cliente/mês")
                continue

            # Criar boleto
            print(f"   ➕ Criando boleto...")

            numero_boleto = contrato or f"CANOPUS-{cpf}-{mes_ref:02d}{ano_ref}"

            novo_boleto = db.execute_query("""
                INSERT INTO boletos
                (cliente_nexus_id, cliente_final_id, numero_boleto, valor_original,
                 data_vencimento, data_emissao, mes_referencia, ano_referencia,
                 numero_parcela, pdf_path, pdf_filename, status, status_envio, gerado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                cliente_nexus_id,
                cliente_id,
                numero_boleto,
                valor,
                vencimento,
                datetime.now().date(),
                mes_ref,
                ano_ref,
                1,  # número da parcela
                pdf_path,
                pdf_filename,
                'pendente',
                'nao_enviado',
                'importacao_canopus'
            ))

            boleto_id = novo_boleto[0]['id']
            print(f"   ✅ Boleto criado (ID: {boleto_id})")
            stats['boletos_criados'] += 1

            print()  # Linha em branco

        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
            stats['erros'] += 1
            print()
            continue

    # Resumo final
    print("=" * 70)
    print("📊 RESUMO DA IMPORTAÇÃO:")
    print("=" * 70)
    print(f"   📄 PDFs processados: {stats['total_pdfs']}")
    print(f"   👥 Clientes criados: {stats['clientes_criados']}")
    print(f"   👥 Clientes já existentes: {stats['clientes_existentes']}")
    print(f"   📄 Boletos criados: {stats['boletos_criados']}")
    print(f"   ⚠️  PDFs sem dados completos: {stats['pdfs_sem_dados']}")
    print(f"   ❌ Erros: {stats['erros']}")

    if stats['boletos_criados'] > 0:
        print("\n✅ Importação concluída com sucesso!")
        print(f"   Agora você pode disparar {stats['boletos_criados']} boleto(s)")
    else:
        print("\n⚠️  Nenhum boleto foi criado")

    print("=" * 70)


if __name__ == '__main__':
    importar_boletos_canopus()
