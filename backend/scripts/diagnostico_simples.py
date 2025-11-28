"""
Diagnóstico Simples - Por que não dispara
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

CLIENTE_NEXUS_ID = 2

print('='*80)
print('DIAGNOSTICO DE DISPAROS - CLIENTE_NEXUS_ID = {}'.format(CLIENTE_NEXUS_ID))
print('='*80)

# Boletos pendentes COM WhatsApp
com_whatsapp = db.execute_query('''
    SELECT
        b.id,
        cf.nome_completo,
        cf.whatsapp,
        b.pdf_path
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.cliente_nexus_id = %s
    AND b.status_envio = 'nao_enviado'
    AND cf.whatsapp IS NOT NULL
    AND cf.whatsapp != ''
    AND cf.ativo = true
''', (CLIENTE_NEXUS_ID,))

# Boletos pendentes SEM WhatsApp
sem_whatsapp = db.execute_query('''
    SELECT
        b.id,
        cf.nome_completo,
        cf.whatsapp,
        cf.telefone_celular
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.cliente_nexus_id = %s
    AND b.status_envio = 'nao_enviado'
    AND (cf.whatsapp IS NULL OR cf.whatsapp = '')
    AND cf.ativo = true
''', (CLIENTE_NEXUS_ID,))

print()
print('[OK] BOLETOS PRONTOS PARA DISPARO: {}'.format(len(com_whatsapp)))
print('[X] BOLETOS BLOQUEADOS (sem WhatsApp): {}'.format(len(sem_whatsapp)))
print()

if com_whatsapp:
    print('CLIENTES QUE RECEBERAO MENSAGENS:')
    for i, b in enumerate(com_whatsapp[:5], 1):
        print('  {}. {} - WhatsApp: {}'.format(i, b['nome_completo'], b['whatsapp']))
    if len(com_whatsapp) > 5:
        print('  ... e mais {} clientes'.format(len(com_whatsapp) - 5))
    print()

if sem_whatsapp:
    print('CLIENTES QUE NAO RECEBERAO (sem WhatsApp):')
    for i, b in enumerate(sem_whatsapp[:10], 1):
        tel = b.get('telefone_celular', 'N/A')
        print('  {}. {} - Tel: {}'.format(i, b['nome_completo'], tel))
    if len(sem_whatsapp) > 10:
        print('  ... e mais {} clientes'.format(len(sem_whatsapp) - 10))
    print()

total_boletos = len(com_whatsapp) + len(sem_whatsapp)
if total_boletos > 0:
    taxa = (len(com_whatsapp) / total_boletos) * 100
    print('TAXA DE COBERTURA: {:.1f}% ({}/{})'.format(taxa, len(com_whatsapp), total_boletos))

print()
print('SOLUCAO: Cadastre o WhatsApp dos clientes sem numero')
print('  1. Acesse: http://localhost:5000/clientes-finais')
print('  2. Clique no cliente')
print('  3. Adicione o WhatsApp no formato: 5567999999999')
print()
print('='*80)
