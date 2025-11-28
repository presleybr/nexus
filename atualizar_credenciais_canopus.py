#!/usr/bin/env python3
"""
Atualizar credenciais Canopus no banco do Render
EDITE as variáveis abaixo com suas credenciais reais antes de executar!
"""
import psycopg

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

# ============================================================================
# ⚠️ EDITE AQUI COM SUAS CREDENCIAIS REAIS!
# ============================================================================

PONTO_VENDA = '24627'  # Ponto de venda a atualizar
USUARIO = 'dener'  # ← COLOQUE SEU USUÁRIO AQUI
SENHA = 'SUA_SENHA_AQUI'  # ← COLOQUE SUA SENHA AQUI
CODIGO_EMPRESA = '0101'  # ← AJUSTE SE NECESSÁRIO

# ============================================================================

print("=" * 80)
print("ATUALIZAR CREDENCIAIS CANOPUS NO RENDER")
print("=" * 80)

# Validar se editou
if SENHA == 'SUA_SENHA_AQUI':
    print("\n❌ ERRO: Você precisa editar este script e colocar sua senha real!")
    print("\nAbra o arquivo atualizar_credenciais_canopus.py e edite as linhas:")
    print("  - USUARIO = 'dener'  # ← seu usuário")
    print("  - SENHA = 'SUA_SENHA_AQUI'  # ← sua senha")
    print("  - CODIGO_EMPRESA = '0101'  # ← código da empresa")
    exit(1)

print(f"\n📋 Configuração:")
print(f"  Ponto de Venda: {PONTO_VENDA}")
print(f"  Usuário: {USUARIO}")
print(f"  Senha: {'*' * len(SENHA)}")
print(f"  Código Empresa: {CODIGO_EMPRESA}")

input("\n⚠️ Pressione ENTER para continuar ou CTRL+C para cancelar... ")

conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

# Verificar se credencial existe
cur.execute("""
    SELECT id FROM credenciais_canopus
    WHERE ponto_venda = %s
""", (PONTO_VENDA,))

existe = cur.fetchone()

if existe:
    print(f"\n✅ Credencial encontrada para PV {PONTO_VENDA}")
    print("📝 Atualizando...")

    cur.execute("""
        UPDATE credenciais_canopus
        SET
            usuario = %s,
            senha = %s,
            codigo_empresa = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE ponto_venda = %s
    """, (USUARIO, SENHA, CODIGO_EMPRESA, PONTO_VENDA))

    conn.commit()
    print(f"✅ Credenciais atualizadas com sucesso!")

else:
    print(f"\n⚠️ Nenhuma credencial encontrada para PV {PONTO_VENDA}")
    print("📝 Criando nova credencial...")

    cur.execute("""
        INSERT INTO credenciais_canopus (
            ponto_venda,
            usuario,
            senha,
            codigo_empresa,
            ativo,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """, (PONTO_VENDA, USUARIO, SENHA, CODIGO_EMPRESA))

    conn.commit()
    print(f"✅ Credencial criada com sucesso!")

# Verificar resultado
print("\n📊 Verificando resultado...")
cur.execute("""
    SELECT ponto_venda, usuario, codigo_empresa, ativo, updated_at
    FROM credenciais_canopus
    WHERE ponto_venda = %s
""", (PONTO_VENDA,))

resultado = cur.fetchone()

if resultado:
    print(f"\n✅ Credencial confirmada:")
    print(f"  PV: {resultado[0]}")
    print(f"  Usuário: {resultado[1]}")
    print(f"  Código Empresa: {resultado[2]}")
    print(f"  Status: {'ATIVO' if resultado[3] else 'INATIVO'}")
    print(f"  Atualizado em: {resultado[4]}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("✅ CONCLUÍDO!")
print("=" * 80)
print("\nPróximos passos:")
print("1. Aguarde o deploy do Render concluir")
print("2. Acesse a automação Canopus no frontend")
print("3. Clique em 'Iniciar Download' (ETAPA 3)")
print("4. Verifique os logs do Render para acompanhar o progresso")
print("\n" + "=" * 80)
