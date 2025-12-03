#!/usr/bin/env python3
"""
Atualizar credenciais Canopus no banco do Render (STAGING)
EDITE as variáveis abaixo com suas credenciais reais antes de executar!

NOTA: Este script usa a estrutura ATUAL do banco:
- ponto_venda_id (foreign key para pontos_venda)
- senha_encrypted (criptografada com Fernet)
"""
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

# Chave de criptografia (mesma do backend)
ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='

# ============================================================================
# ⚠️ EDITE AQUI COM SUAS CREDENCIAIS REAIS!
# ============================================================================

PONTO_VENDA_CODIGO = '24627'  # Código do ponto de venda
USUARIO = '24627'  # ← ATENÇÃO: O usuário é o código do PV!
SENHA = 'SUA_SENHA_AQUI'  # ← COLOQUE A SENHA REAL AQUI
CODIGO_EMPRESA = '0101'  # ← AJUSTE SE NECESSÁRIO

# ============================================================================

def criptografar_senha(senha: str) -> str:
    """Criptografa a senha usando Fernet"""
    cipher = Fernet(ENCRYPTION_KEY)
    return cipher.encrypt(senha.encode()).decode()

print("=" * 80)
print("ATUALIZAR CREDENCIAIS CANOPUS NO RENDER (STAGING)")
print("=" * 80)

# Validar se editou
if SENHA == 'SUA_SENHA_AQUI':
    print("\n❌ ERRO: Você precisa editar este script e colocar a senha real!")
    print("\nAbra o arquivo atualizar_credenciais_canopus.py e edite:")
    print(f"  - USUARIO = '{USUARIO}'  # ← usuário (código do PV)")
    print("  - SENHA = 'SUA_SENHA_AQUI'  # ← senha real")
    print(f"  - CODIGO_EMPRESA = '{CODIGO_EMPRESA}'  # ← código da empresa")
    exit(1)

print(f"\n📋 Configuração:")
print(f"  Ponto de Venda: {PONTO_VENDA_CODIGO}")
print(f"  Usuário: {USUARIO}")
print(f"  Senha: {'*' * len(SENHA)}")
print(f"  Código Empresa: {CODIGO_EMPRESA}")

input("\n⚠️ Pressione ENTER para continuar ou CTRL+C para cancelar... ")

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
cur = conn.cursor()

# 1. Buscar ID do ponto de venda
print("\n[1/3] Buscando ponto de venda...")
cur.execute("""
    SELECT id, codigo, nome
    FROM pontos_venda
    WHERE codigo = %s
""", (PONTO_VENDA_CODIGO,))

ponto_venda = cur.fetchone()

if not ponto_venda:
    print(f"❌ ERRO: Ponto de venda '{PONTO_VENDA_CODIGO}' não encontrado!")
    cur.close()
    conn.close()
    exit(1)

print(f"✅ Encontrado: {ponto_venda['codigo']} - {ponto_venda['nome']}")
ponto_venda_id = ponto_venda['id']

# 2. Verificar se credencial já existe
print("\n[2/3] Verificando credencial existente...")
cur.execute("""
    SELECT id, usuario
    FROM credenciais_canopus
    WHERE ponto_venda_id = %s
""", (ponto_venda_id,))

credencial_existente = cur.fetchone()

# 3. Criptografar senha
senha_encrypted = criptografar_senha(SENHA)

if credencial_existente:
    print(f"✅ Credencial encontrada (ID: {credencial_existente['id']})")
    print(f"   Usuário antigo: {credencial_existente['usuario']}")
    print(f"   Usuário novo: {USUARIO}")
    print("\n[3/3] Atualizando credencial...")

    cur.execute("""
        UPDATE credenciais_canopus
        SET
            usuario = %s,
            senha_encrypted = %s,
            codigo_empresa = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE ponto_venda_id = %s
    """, (USUARIO, senha_encrypted, CODIGO_EMPRESA, ponto_venda_id))

    conn.commit()
    print(f"✅ Credencial atualizada com sucesso!")

else:
    print(f"⚠️ Nenhuma credencial encontrada para PV {PONTO_VENDA_CODIGO}")
    print("\n[3/3] Criando nova credencial...")

    cur.execute("""
        INSERT INTO credenciais_canopus (
            ponto_venda_id,
            usuario,
            senha_encrypted,
            codigo_empresa,
            ativo,
            created_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """, (ponto_venda_id, USUARIO, senha_encrypted, CODIGO_EMPRESA))

    conn.commit()
    print(f"✅ Credencial criada com sucesso!")

# Verificar resultado final
print("\n📊 Verificando resultado final...")
cur.execute("""
    SELECT c.id, pv.codigo, pv.nome, c.usuario, c.codigo_empresa, c.ativo, c.updated_at
    FROM credenciais_canopus c
    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
    WHERE pv.codigo = %s
""", (PONTO_VENDA_CODIGO,))

resultado = cur.fetchone()

if resultado:
    print(f"\n✅ Credencial confirmada no banco:")
    print(f"  ID: {resultado['id']}")
    print(f"  PV: {resultado['codigo']} - {resultado['nome']}")
    print(f"  Usuário: {resultado['usuario']}")
    print(f"  Código Empresa: {resultado['codigo_empresa']}")
    print(f"  Status: {'ATIVO ✅' if resultado['ativo'] else 'INATIVO ❌'}")
    print(f"  Atualizado: {resultado['updated_at']}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("✅ CONCLUÍDO COM SUCESSO!")
print("=" * 80)
print("\nPróximos passos:")
print("1. Teste o login HTTP no staging:")
print("   https://nexus-staging-backend.onrender.com/crm/automacao-canopus")
print("2. Selecione o método '🌐 HTTP (Requisições Diretas)'")
print("3. Clique em 'Iniciar Download' (ETAPA 3)")
print("4. Verifique os logs do Render para ver se o login funcionou")
print("\n" + "=" * 80)
