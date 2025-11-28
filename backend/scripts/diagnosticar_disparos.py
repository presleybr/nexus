"""
Script de Diagnóstico Completo de Disparos
Identifica por que mensagens não estão sendo enviadas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db
from pathlib import Path

def formatar_whatsapp(numero):
    """Formata número de WhatsApp para exibição"""
    if not numero:
        return "[X] NAO CADASTRADO"

    numero_limpo = ''.join(filter(str.isdigit, str(numero)))

    if len(numero_limpo) < 12:
        return f"[!] INCOMPLETO ({numero_limpo})"
    elif len(numero_limpo) == 12:
        return f"[OK] ({numero_limpo})"
    elif len(numero_limpo) == 13:
        return f"[OK] ({numero_limpo})"
    else:
        return f"[!] FORMATO ESTRANHO ({numero_limpo})"

def main():
    print("\n" + "="*100)
    print("DIAGNÓSTICO COMPLETO - POR QUE OS DISPAROS NÃO ESTÃO FUNCIONANDO")
    print("="*100 + "\n")

    # Escolher cliente_nexus_id
    print("Digite o cliente_nexus_id (ou Enter para 2):")
    cliente_id_input = input("> ").strip()
    CLIENTE_NEXUS_ID = int(cliente_id_input) if cliente_id_input else 2

    print(f"\nAnalisando cliente_nexus_id = {CLIENTE_NEXUS_ID}\n")

    # === ETAPA 1: Verificar boletos no banco ===
    print("="*100)
    print("ETAPA 1: VERIFICAR BOLETOS NO BANCO")
    print("="*100 + "\n")

    total_boletos = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos WHERE cliente_nexus_id = %s
    """, (CLIENTE_NEXUS_ID,))

    print(f"📊 Total de boletos cadastrados: {total_boletos[0]['total']}")

    pendentes = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos
        WHERE cliente_nexus_id = %s AND status_envio = 'nao_enviado'
    """, (CLIENTE_NEXUS_ID,))

    print(f"⏳ Boletos pendentes (não enviados): {pendentes[0]['total']}")

    enviados = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos
        WHERE cliente_nexus_id = %s AND status_envio = 'enviado'
    """, (CLIENTE_NEXUS_ID,))

    print(f"✅ Boletos já enviados: {enviados[0]['total']}\n")

    # === ETAPA 2: Verificar WhatsApp dos clientes ===
    print("="*100)
    print("ETAPA 2: VERIFICAR WHATSAPP DOS CLIENTES")
    print("="*100 + "\n")

    clientes_com_boleto = db.execute_query("""
        SELECT DISTINCT
            cf.id,
            cf.nome_completo,
            cf.cpf,
            cf.whatsapp,
            cf.telefone_celular,
            cf.ativo,
            COUNT(b.id) as qtd_boletos_pendentes
        FROM clientes_finais cf
        JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        GROUP BY cf.id, cf.nome_completo, cf.cpf, cf.whatsapp, cf.telefone_celular, cf.ativo
        ORDER BY cf.nome_completo
    """, (CLIENTE_NEXUS_ID,))

    print(f"👥 Total de clientes únicos com boletos pendentes: {len(clientes_com_boleto)}\n")

    sem_whatsapp = []
    whatsapp_invalido = []
    whatsapp_ok = []

    print("ANÁLISE DETALHADA DOS CLIENTES:\n")
    print(f"{'ID':<6} {'NOME':<40} {'WHATSAPP':<30} {'BOLETOS':<10}")
    print("-" * 90)

    for cliente in clientes_com_boleto:
        status_whatsapp = formatar_whatsapp(cliente['whatsapp'])

        print(f"{cliente['id']:<6} {cliente['nome_completo'][:38]:<40} {status_whatsapp:<30} {cliente['qtd_boletos_pendentes']:<10}")

        if not cliente['whatsapp']:
            sem_whatsapp.append(cliente)
        elif '[X]' in status_whatsapp or '[!]' in status_whatsapp:
            whatsapp_invalido.append(cliente)
        else:
            whatsapp_ok.append(cliente)

    print("\n" + "="*100)
    print("RESUMO DA ANÁLISE DE WHATSAPP")
    print("="*100)
    print(f"✅ Clientes com WhatsApp OK: {len(whatsapp_ok)}")
    print(f"⚠️ Clientes com WhatsApp inválido: {len(whatsapp_invalido)}")
    print(f"❌ Clientes SEM WhatsApp: {len(sem_whatsapp)}\n")

    # === ETAPA 3: Verificar boletos que SERIAM disparados ===
    print("="*100)
    print("ETAPA 3: BOLETOS QUE SERIAM DISPARADOS (QUERY REAL)")
    print("="*100 + "\n")

    boletos_query_real = db.execute_query("""
        SELECT
            b.id as boleto_id,
            b.pdf_path,
            b.numero_boleto,
            cf.nome_completo,
            cf.whatsapp
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        AND cf.whatsapp IS NOT NULL
        AND cf.whatsapp != ''
        AND cf.ativo = true
        ORDER BY b.data_vencimento ASC
    """, (CLIENTE_NEXUS_ID,))

    print(f"📤 Boletos que SERIAM disparados: {len(boletos_query_real)}\n")

    if boletos_query_real:
        print("Primeiros 5 boletos:\n")
        for i, boleto in enumerate(boletos_query_real[:5], 1):
            pdf_existe = "✅" if Path(boleto['pdf_path']).exists() else "❌"
            print(f"{i}. {boleto['nome_completo']}")
            print(f"   WhatsApp: {boleto['whatsapp']}")
            print(f"   PDF: {pdf_existe} {Path(boleto['pdf_path']).name}")
            print()
    else:
        print("⚠️ NENHUM BOLETO seria disparado com a query atual!\n")

    # === ETAPA 4: Identificar clientes BLOQUEADOS ===
    print("="*100)
    print("ETAPA 4: CLIENTES BLOQUEADOS (POR QUE NÃO RECEBEM)")
    print("="*100 + "\n")

    if sem_whatsapp:
        print(f"❌ {len(sem_whatsapp)} CLIENTES SEM WHATSAPP:\n")
        for cliente in sem_whatsapp[:10]:
            print(f"  • {cliente['nome_completo']} (ID: {cliente['id']})")
            if cliente['telefone_celular']:
                print(f"    ⚠️ Tem telefone cadastrado: {cliente['telefone_celular']}")
                print(f"    💡 Sugestão: Copiar telefone para WhatsApp")
            print()

    if whatsapp_invalido:
        print(f"\n⚠️ {len(whatsapp_invalido)} CLIENTES COM WHATSAPP INVÁLIDO:\n")
        for cliente in whatsapp_invalido[:10]:
            print(f"  • {cliente['nome_completo']} (ID: {cliente['id']})")
            print(f"    WhatsApp atual: {cliente['whatsapp']}")
            print(f"    💡 Sugestão: Corrigir número")
            print()

    # === ETAPA 5: Recomendações ===
    print("="*100)
    print("ETAPA 5: RECOMENDAÇÕES")
    print("="*100 + "\n")

    taxa_cobertura = (len(whatsapp_ok) / len(clientes_com_boleto) * 100) if clientes_com_boleto else 0

    print(f"📊 TAXA DE COBERTURA ATUAL: {taxa_cobertura:.1f}%")
    print(f"   ({len(whatsapp_ok)} de {len(clientes_com_boleto)} clientes podem receber mensagens)\n")

    print("🎯 AÇÕES RECOMENDADAS:\n")

    if sem_whatsapp:
        print("1️⃣ CADASTRAR WHATSAPP dos clientes sem número:")
        print("   • Acesse o CRM: http://localhost:5000/clientes-finais")
        print("   • Adicione o WhatsApp no formato: 5567999999999")
        print(f"   • Total a cadastrar: {len(sem_whatsapp)} clientes\n")

    if whatsapp_invalido:
        print("2️⃣ CORRIGIR NÚMEROS INVÁLIDOS:")
        print(f"   • {len(whatsapp_invalido)} números precisam de correção")
        print("   • Verifique se estão completos (13 dígitos: 5567999999999)\n")

    # Verificar se pode copiar telefone
    pode_copiar = db.execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais cf
        JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        AND (cf.whatsapp IS NULL OR cf.whatsapp = '')
        AND cf.telefone_celular IS NOT NULL
        AND cf.telefone_celular != ''
    """, (CLIENTE_NEXUS_ID,))

    if pode_copiar and pode_copiar[0]['total'] > 0:
        print("3️⃣ COPIAR TELEFONE PARA WHATSAPP:")
        print(f"   • {pode_copiar[0]['total']} clientes têm telefone mas não têm WhatsApp")
        print("   • Execute: python copiar_telefone_para_whatsapp.py\n")

    print("4️⃣ TESTAR DISPARO:")
    print("   • Após corrigir, execute: python verificar_boletos_para_disparo.py")
    print("   • Ou use o CRM: http://localhost:5000 → Disparo Automático\n")

    print("="*100)
    print(f"DIAGNÓSTICO CONCLUÍDO - {len(whatsapp_ok)} boletos prontos para envio")
    print("="*100 + "\n")

if __name__ == "__main__":
    main()
