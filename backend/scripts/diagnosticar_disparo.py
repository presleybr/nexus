"""
Script de diagnóstico para testar disparo de boletos
Testa envio para um único cliente com logs detalhados
"""

import sys
import os
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db
from services.whatsapp_service import whatsapp_service
from services.pdf_extractor import extrair_dados_boleto
from services.mensagens_personalizadas import mensagens_service
import json


def diagnosticar_disparo():
    """Diagnóstico completo do sistema de disparo"""

    print("=" * 80)
    print("DIAGNÓSTICO DO SISTEMA DE DISPARO")
    print("=" * 80)

    cliente_nexus_id = 2  # Cred MS Consorcios

    # 1. Verificar status do WhatsApp
    print("\n[1] Verificando conexão WhatsApp...")
    from services.wppconnect_service import wppconnect_service

    status = wppconnect_service.verificar_status()
    print(f"   Status: {json.dumps(status, indent=2)}")

    if not status.get('connected'):
        print("   ❌ WhatsApp NÃO está conectado!")
        print("   Execute o WPPConnect Server e conecte o WhatsApp primeiro.")
        return

    print(f"   ✅ WhatsApp conectado: {status.get('phone')}")

    # 2. Buscar um boleto para teste
    print("\n[2] Buscando boleto para teste...")

    boletos = db.execute_query("""
        SELECT
            b.id as boleto_id,
            b.pdf_path,
            b.numero_boleto,
            b.data_vencimento,
            b.valor_original,
            cf.nome_completo,
            cf.whatsapp,
            cf.cpf
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        AND cf.whatsapp != '55679999999999'
        AND cf.whatsapp != '0000000000'
        AND cf.whatsapp IS NOT NULL
        LIMIT 1
    """, (cliente_nexus_id,))

    if not boletos:
        print("   ❌ Nenhum boleto disponível para teste!")
        return

    boleto = boletos[0]

    print(f"   ✅ Boleto encontrado:")
    print(f"      Cliente: {boleto['nome_completo']}")
    print(f"      WhatsApp: {boleto['whatsapp']}")
    print(f"      PDF: {boleto['pdf_path']}")
    print(f"      Vencimento: {boleto['data_vencimento']}")
    print(f"      Valor: R$ {boleto['valor_original']:.2f}")

    # 3. Verificar se PDF existe
    print("\n[3] Verificando arquivo PDF...")

    if not os.path.exists(boleto['pdf_path']):
        print(f"   ❌ Arquivo PDF NÃO encontrado: {boleto['pdf_path']}")
        return

    tamanho_kb = os.path.getsize(boleto['pdf_path']) / 1024
    print(f"   ✅ PDF encontrado ({tamanho_kb:.1f} KB)")

    # 4. Extrair dados do PDF
    print("\n[4] Extraindo dados do PDF...")

    dados_pdf = extrair_dados_boleto(boleto['pdf_path'])

    if dados_pdf.get('sucesso'):
        print(f"   ✅ Dados extraídos com sucesso:")
        print(f"      Vencimento: {dados_pdf.get('vencimento_str')}")
        print(f"      Valor: R$ {dados_pdf.get('valor', 0):.2f}")
        print(f"      Nome: {dados_pdf.get('nome_pagador')}")
        print(f"      CPF: {dados_pdf.get('cpf')}")
    else:
        print(f"   ⚠️ Não foi possível extrair dados do PDF")
        dados_pdf = {}

    # 5. Gerar mensagem personalizada
    print("\n[5] Gerando mensagem personalizada...")

    mensagem = mensagens_service.gerar_mensagem_boleto(
        dados_cliente={
            'nome_completo': boleto['nome_completo'],
            'numero_contrato': boleto.get('numero_boleto', 'N/A')
        },
        dados_boleto={
            'valor_original': dados_pdf.get('valor') if dados_pdf.get('sucesso') else boleto['valor_original'],
            'data_vencimento': dados_pdf.get('vencimento_str') if dados_pdf.get('sucesso') else boleto['data_vencimento'].strftime('%d/%m/%Y')
        },
        nome_empresa='Cred MS Consorcios'
    )

    print(f"   Mensagem gerada ({len(mensagem)} caracteres):")
    print(f"   ---")
    print(f"   {mensagem[:200]}...")
    print(f"   ---")

    # 6. Testar envio de mensagem
    print("\n[6] Testando envio de mensagem de texto...")

    resultado_msg = whatsapp_service.enviar_mensagem(
        boleto['whatsapp'],
        mensagem,
        cliente_nexus_id
    )

    print(f"   Resultado completo:")
    print(f"   {json.dumps(resultado_msg, indent=2, default=str)}")

    if not resultado_msg.get('sucesso'):
        print(f"   ❌ ERRO ao enviar mensagem!")
        print(f"   Erro: {resultado_msg.get('erro')}")
        return

    print(f"   ✅ Mensagem enviada com sucesso!")

    # 7. Aguardar e testar envio de PDF
    print("\n[7] Aguardando 3 segundos antes de enviar PDF...")
    import time
    time.sleep(3)

    print("\n[8] Testando envio de PDF...")

    vencimento_str = dados_pdf.get('vencimento_str') if dados_pdf.get('sucesso') else boleto['data_vencimento'].strftime('%d/%m/%Y')
    valor_str = f"R$ {dados_pdf.get('valor', 0):.2f}" if dados_pdf.get('sucesso') else f"R$ {boleto['valor_original']:.2f}"

    legenda = f"📄 *Boleto Cred MS*\nVencimento: {vencimento_str}\nValor: {valor_str}\n\n💚 Cred MS - Seu parceiro de confiança!"

    resultado_pdf = whatsapp_service.enviar_pdf(
        boleto['whatsapp'],
        boleto['pdf_path'],
        legenda,
        cliente_nexus_id
    )

    print(f"   Resultado completo:")
    print(f"   {json.dumps(resultado_pdf, indent=2, default=str)}")

    if not resultado_pdf.get('sucesso'):
        print(f"   ❌ ERRO ao enviar PDF!")
        print(f"   Erro: {resultado_pdf.get('erro')}")
        return

    print(f"   ✅ PDF enviado com sucesso!")

    # 8. Atualizar status do boleto (opcional - comentado para não marcar como enviado)
    print("\n[9] Teste concluído com SUCESSO!")
    print("\n" + "=" * 80)
    print("RESUMO:")
    print("=" * 80)
    print(f"✅ WhatsApp: Conectado")
    print(f"✅ Boleto: Encontrado")
    print(f"✅ PDF: Válido ({tamanho_kb:.1f} KB)")
    print(f"✅ Extração: {'Sucesso' if dados_pdf.get('sucesso') else 'Falhou (usando dados do banco)'}")
    print(f"✅ Mensagem: Enviada")
    print(f"✅ PDF: Enviado")
    print("\n🎉 O sistema está funcionando corretamente!")
    print("\nNOTA: O boleto NÃO foi marcado como enviado (teste apenas).")
    print("=" * 80)


if __name__ == '__main__':
    try:
        diagnosticar_disparo()
    except Exception as e:
        print(f"\n❌ ERRO FATAL:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
