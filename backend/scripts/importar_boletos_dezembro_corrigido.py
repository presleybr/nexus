"""
Importação corrigida de boletos de dezembro
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import db

print("\n" + "="*80)
print("IMPORTACAO DE BOLETOS DE DEZEMBRO (CORRIGIDA)")
print("="*80 + "\n")

# Pasta de PDFs
pasta_pdfs = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

if not pasta_pdfs.exists():
    print(f"[ERRO] Pasta nao encontrada: {pasta_pdfs}")
    exit(1)

# Listar PDFs
pdfs = list(pasta_pdfs.glob("*.pdf"))
print(f"[INFO] Encontrados {len(pdfs)} PDFs\n")

stats = {
    'total': len(pdfs),
    'importados': 0,
    'ja_existentes': 0,
    'sem_cliente': 0,
    'erros': 0
}

# Mapeamento de meses
MESES = {
    'JANEIRO': 1, 'FEVEREIRO': 2, 'MARCO': 3, 'MARÇO': 3,
    'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6,
    'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9,
    'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
}

def limpar_nome_busca(nome):
    """Remove underscores, espaços e normaliza"""
    nome = nome.upper()
    nome = nome.replace('_', ' ')
    # Remover numeros e porcentagens do final
    nome = re.sub(r'\s*\d+%?\s*$', '', nome)
    return nome.strip()

# Cliente Nexus padrao (Dener) - ID correto do banco
CLIENTE_NEXUS_ID = 2

for pdf_file in pdfs:
    try:
        print(f"[{stats['importados']+1}/{len(pdfs)}] {pdf_file.name}")

        # Extrair informacoes do nome
        nome_arquivo = pdf_file.stem
        partes = nome_arquivo.split('_')

        if len(partes) < 2:
            print(f"   [ERRO] Nome invalido")
            stats['erros'] += 1
            continue

        # Ultima parte e o mes
        mes_str = partes[-1].upper()
        ano = 2025  # Ano padrao

        # Se ultima parte e ano
        if mes_str.isdigit() and len(mes_str) == 4:
            ano = int(mes_str)
            mes_str = partes[-2].upper()
            nome_cliente = '_'.join(partes[:-2])
        else:
            nome_cliente = '_'.join(partes[:-1])

        # Converter mes para numero
        mes_num = MESES.get(mes_str, 12)  # Default dezembro

        # Limpar nome para busca
        nome_busca = limpar_nome_busca(nome_cliente)

        print(f"   Cliente: {nome_busca}")
        print(f"   Mes: {mes_str} ({mes_num}), Ano: {ano}")

        # Buscar cliente no banco (busca flexivel)
        # Divide nome em palavras e busca por cada uma
        palavras = [p for p in nome_busca.split() if len(p) > 2]

        if not palavras:
            print(f"   [ERRO] Nome muito curto")
            stats['erros'] += 1
            continue

        # Montar query de busca flexivel
        condicoes = " AND ".join([f"UPPER(nome_completo) LIKE %s" for _ in palavras])
        params = [f"%{palavra}%" for palavra in palavras]

        cliente = db.execute_query(f"""
            SELECT id, nome_completo, cpf
            FROM clientes_finais
            WHERE {condicoes}
            AND ativo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """, tuple(params))

        if not cliente:
            print(f"   [AVISO] Cliente NAO encontrado")
            stats['sem_cliente'] += 1
            continue

        cliente_id = cliente[0]['id']
        cliente_nome = cliente[0]['nome_completo']
        cliente_cpf = cliente[0]['cpf']

        print(f"   [OK] Cliente encontrado: {cliente_nome} (ID: {cliente_id})")

        # Verificar se boleto ja existe
        boleto_existe = db.execute_query("""
            SELECT id FROM boletos
            WHERE cliente_final_id = %s
            AND mes_referencia = %s
            AND ano_referencia = %s
        """, (cliente_id, mes_num, ano))

        if boleto_existe:
            print(f"   [INFO] Boleto ja existe")
            stats['ja_existentes'] += 1
            continue

        # Gerar numero boleto
        numero_boleto = f"CANOPUS-{cliente_cpf}-{mes_num:02d}{ano}"

        # Data de vencimento (dia 28 do mes)
        try:
            data_venc = datetime(ano, mes_num, 28).date()
        except:
            data_venc = datetime(ano, mes_num, 1).date()

        # Inserir boleto
        db.execute_update("""
            INSERT INTO boletos (
                cliente_nexus_id,
                cliente_final_id,
                numero_boleto,
                valor_original,
                data_vencimento,
                data_emissao,
                mes_referencia,
                ano_referencia,
                numero_parcela,
                descricao,
                status,
                status_envio,
                pdf_filename,
                pdf_path,
                pdf_size,
                gerado_por,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """, (
            CLIENTE_NEXUS_ID,
            cliente_id,
            numero_boleto,
            0.0,
            data_venc,
            datetime.now().date(),
            mes_num,
            ano,
            1,
            f"Boleto {mes_str}/{ano} - {cliente_nome}",
            'pendente',
            'nao_enviado',
            pdf_file.name,
            str(pdf_file),
            pdf_file.stat().st_size,
            'automacao_canopus'
        ))

        print(f"   [OK] Boleto IMPORTADO!")
        stats['importados'] += 1

    except Exception as e:
        print(f"   [ERRO] {e}")
        stats['erros'] += 1

print("\n" + "="*80)
print("RESUMO:")
print("="*80)
print(f"Total PDFs: {stats['total']}")
print(f"Importados: {stats['importados']}")
print(f"Ja existentes: {stats['ja_existentes']}")
print(f"Sem cliente: {stats['sem_cliente']}")
print(f"Erros: {stats['erros']}")
print("="*80 + "\n")
