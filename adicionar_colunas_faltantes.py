#!/usr/bin/env python3
"""
Script para adicionar colunas faltantes no banco do Render
"""
import psycopg

# Conectar ao banco do Render
DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("Conectando ao banco do Render...")
conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

# Lista de alterações necessárias
alteracoes = [
    {
        'nome': 'Adicionar link_planilha_drive em consultores',
        'sql': """
            ALTER TABLE consultores
            ADD COLUMN IF NOT EXISTS link_planilha_drive TEXT,
            ADD COLUMN IF NOT EXISTS ultima_atualizacao_planilha TIMESTAMP
        """
    },
    {
        'nome': 'Adicionar colunas em configuracoes_automacao',
        'sql': """
            ALTER TABLE configuracoes_automacao
            ADD COLUMN IF NOT EXISTS dia_do_mes INTEGER DEFAULT 1,
            ADD COLUMN IF NOT EXISTS dias_antes_vencimento INTEGER DEFAULT 3,
            ADD COLUMN IF NOT EXISTS horario_disparo TIME DEFAULT '09:00:00',
            ADD COLUMN IF NOT EXISTS mensagem_antibloqueio TEXT DEFAULT 'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!',
            ADD COLUMN IF NOT EXISTS intervalo_min_segundos INTEGER DEFAULT 3,
            ADD COLUMN IF NOT EXISTS intervalo_max_segundos INTEGER DEFAULT 7,
            ADD COLUMN IF NOT EXISTS pausa_apos_disparos INTEGER DEFAULT 20,
            ADD COLUMN IF NOT EXISTS tempo_pausa_segundos INTEGER DEFAULT 60
        """
    }
]

print("\nAplicando alteracoes no banco...")
print("="*60)

for i, alteracao in enumerate(alteracoes, 1):
    print(f"\n[{i}/{len(alteracoes)}] {alteracao['nome']}")
    try:
        cur.execute(alteracao['sql'])
        conn.commit()
        print("    OK - Aplicado com sucesso!")
    except Exception as e:
        print(f"    ERRO: {e}")
        conn.rollback()

print("\n" + "="*60)
print("Verificando estrutura das tabelas...")
print("="*60)

# Verificar consultores
print("\nColunas da tabela 'consultores':")
cur.execute("""
    SELECT column_name, data_type, column_default
    FROM information_schema.columns
    WHERE table_name = 'consultores'
    AND column_name IN ('link_planilha_drive', 'ultima_atualizacao_planilha')
    ORDER BY column_name
""")
for col in cur.fetchall():
    print(f"  - {col[0]}: {col[1]}")

# Verificar configuracoes_automacao
print("\nColunas da tabela 'configuracoes_automacao':")
cur.execute("""
    SELECT column_name, data_type, column_default
    FROM information_schema.columns
    WHERE table_name = 'configuracoes_automacao'
    AND column_name IN ('dia_do_mes', 'dias_antes_vencimento', 'horario_disparo',
                        'mensagem_antibloqueio', 'intervalo_min_segundos',
                        'intervalo_max_segundos', 'pausa_apos_disparos',
                        'tempo_pausa_segundos')
    ORDER BY column_name
""")
for col in cur.fetchall():
    print(f"  - {col[0]}: {col[1]} (default: {col[2]})")

cur.close()
conn.close()
print("\nConexao fechada.")
print("\nCONCLUIDO! As colunas foram adicionadas ao banco do Render.")
