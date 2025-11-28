"""
Script de Diagnóstico URGENTE - Disparo de Boletos
Verifica exatamente onde está o problema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def diagnosticar():
    print("="*60)
    print("DIAGNÓSTICO URGENTE - DISPARO DE BOLETOS")
    print("="*60)

    # 1. Verificar clientes finais
    print("\n1. CLIENTES FINAIS CADASTRADOS:")
    clientes = db.execute_query("""
        SELECT id, nome_completo, whatsapp, ativo
        FROM clientes_finais
        WHERE cliente_nexus_id = 2
        ORDER BY id
    """)

    if clientes:
        print(f"   Total de clientes: {len(clientes)}")
        for c in clientes[:5]:
            print(f"   - ID {c['id']}: {c['nome_completo']}")
            print(f"     WhatsApp: {c['whatsapp']}")
            print(f"     Ativo: {c['ativo']}")
    else:
        print("   ❌ NENHUM CLIENTE ENCONTRADO!")

    # 2. Verificar boletos no banco
    print("\n2. BOLETOS NO BANCO:")
    boletos = db.execute_query("""
        SELECT b.id, b.cliente_final_id, b.status_envio,
               b.created_at, cf.nome_completo
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = 2
        ORDER BY b.created_at DESC
        LIMIT 10
    """)

    if boletos:
        print(f"   Total de boletos (últimos 10): {len(boletos)}")
        for b in boletos:
            print(f"   - Boleto ID {b['id']}: {b['nome_completo']}")
            print(f"     Status: {b['status_envio']}")
            print(f"     Criado: {b['created_at']}")
    else:
        print("   ❌ NENHUM BOLETO ENCONTRADO!")

    # 3. Verificar boletos pendentes
    print("\n3. BOLETOS PENDENTES (não enviados):")
    pendentes = db.execute_query("""
        SELECT b.id, b.cliente_final_id, b.status_envio, cf.nome_completo, cf.whatsapp
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = 2
        AND b.status_envio = 'nao_enviado'
        AND cf.ativo = true
        ORDER BY b.created_at DESC
    """)

    if pendentes:
        print(f"   Total pendentes: {len(pendentes)}")
        for p in pendentes[:5]:
            print(f"   - Boleto ID {p['id']}: {p['nome_completo']}")
            print(f"     WhatsApp: {p['whatsapp']}")
            print(f"     Status: {p['status_envio']}")
    else:
        print("   ⚠️ NENHUM BOLETO PENDENTE!")
        print("   (Isso significa que todos já foram enviados ou não foram gerados)")

    # 4. Verificar disparos
    print("\n4. HISTÓRICO DE DISPAROS:")
    disparos = db.execute_query("""
        SELECT id, telefone_destino, status, data_disparo, erro
        FROM disparos
        WHERE cliente_nexus_id = 2
        ORDER BY created_at DESC
        LIMIT 10
    """)

    if disparos:
        print(f"   Total de disparos (últimos 10): {len(disparos)}")
        for d in disparos:
            print(f"   - Disparo ID {d['id']}")
            print(f"     Para: {d['telefone_destino']}")
            print(f"     Status: {d['status']}")
            if d.get('erro'):
                print(f"     Erro: {d['erro']}")
    else:
        print("   ⚠️ NENHUM DISPARO REGISTRADO!")

    # 5. Verificar logs recentes
    print("\n5. LOGS RECENTES DA AUTOMAÇÃO:")
    logs = db.execute_query("""
        SELECT tipo, mensagem, detalhes, created_at
        FROM logs_sistema
        WHERE categoria = 'automacao'
        ORDER BY created_at DESC
        LIMIT 10
    """)

    if logs:
        for log in logs:
            print(f"   [{log['tipo'].upper()}] {log['mensagem']}")
            print(f"   Horário: {log['created_at']}")
            if log.get('detalhes'):
                print(f"   Detalhes: {log['detalhes']}")
            print()
    else:
        print("   ⚠️ NENHUM LOG ENCONTRADO!")

    print("="*60)
    print("FIM DO DIAGNÓSTICO")
    print("="*60)

if __name__ == '__main__':
    diagnosticar()
