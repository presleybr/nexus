"""Testar retorno da API de clientes"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import db

# Buscar TODOS os clientes
clientes = db.execute_query("""
    SELECT cf.*,
           cf.nome_completo as nome,
           COUNT(b.id) as total_boletos,
           COUNT(CASE WHEN b.status_envio = 'enviado' THEN 1 END) as boletos_enviados
    FROM clientes_finais cf
    LEFT JOIN boletos b ON cf.id = b.cliente_final_id
    WHERE cf.cliente_nexus_id = 2 AND cf.ativo = true
    GROUP BY cf.id
    ORDER BY cf.created_at DESC
    LIMIT 100
""")

print(f'\nTotal de clientes: {len(clientes)}')

# Contar quantos têm WhatsApp
com_whatsapp = sum(1 for c in clientes if c.get('whatsapp') and c.get('whatsapp').strip() and c.get('whatsapp') != '0000000000')
sem_whatsapp = len(clientes) - com_whatsapp

print(f'Com WhatsApp: {com_whatsapp}')
print(f'Sem WhatsApp: {sem_whatsapp}')

print('\n10 clientes COM WhatsApp:\n')
count = 0
for c in clientes:
    if c.get('whatsapp') and c.get('whatsapp').strip() and c.get('whatsapp') != '0000000000':
        count += 1
        print(f'{count}. {c.get("nome_completo", "N/A")[:35]:<35} | WhatsApp: {c.get("whatsapp"):<20} | Boletos: {c.get("total_boletos", 0)}')
        if count >= 10:
            break
