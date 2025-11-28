#!/usr/bin/env python3
"""
Script para atualizar a senha do usuário credms@nexusbrasi.ai no Render
"""
import psycopg
import bcrypt

# Conectar ao banco do Render
DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("Conectando ao banco do Render...")
conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

# Gerar hash correto para a senha 'credms123'
senha = 'credms123'
print(f"\nGerando hash para senha: {senha}")
hash_correto = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Hash gerado: {hash_correto}")
print(f"Tamanho: {len(hash_correto)}")

# Verificar que o hash funciona
print("\nTestando hash antes de atualizar...")
if bcrypt.checkpw(senha.encode('utf-8'), hash_correto.encode('utf-8')):
    print("OK - Hash valido!")
else:
    print("ERRO - Hash invalido! Abortando.")
    exit(1)

# Atualizar no banco
email = 'credms@nexusbrasi.ai'
print(f"\nAtualizando senha para: {email}")
cur.execute('UPDATE usuarios SET password_hash = %s WHERE email = %s', (hash_correto, email))
conn.commit()
print(f"Linhas atualizadas: {cur.rowcount}")

# Verificar atualização
print("\nVerificando atualização...")
cur.execute('SELECT id, email, password_hash, tipo, ativo FROM usuarios WHERE email = %s', (email,))
usuario = cur.fetchone()

if usuario:
    print(f"\nUsuário encontrado:")
    print(f"  ID: {usuario[0]}")
    print(f"  Email: {usuario[1]}")
    print(f"  Hash: {usuario[2][:30]}...")
    print(f"  Tamanho hash: {len(usuario[2])}")
    print(f"  Tipo: {usuario[3]}")
    print(f"  Ativo: {usuario[4]}")

    # Testar autenticação
    print("\nTestando autenticacao...")
    if bcrypt.checkpw(senha.encode('utf-8'), usuario[2].encode('utf-8')):
        print(">>> AUTENTICACAO BEM-SUCEDIDA! <<<")
        print(f"\nCredenciais para login:")
        print(f"  Email: {email}")
        print(f"  Senha: {senha}")
    else:
        print("ERRO - Autenticacao falhou!")
else:
    print("ERRO - Usuario nao encontrado!")

cur.close()
conn.close()
print("\nConexao fechada.")
