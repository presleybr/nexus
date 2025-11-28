import bcrypt

password_hash = '$2b$12$FWsGvab2yjCVklpWVzkLFO8UMxV4IBPTDL8WgFM7dcy3iekL5qK6q'

senhas_testar = ['senha123', 'admin123', '123456', 'nexus2025', 'nexus123', 'admin', 'password']

print("\nTestando senhas...")
for senha in senhas_testar:
    if bcrypt.checkpw(senha.encode(), password_hash.encode()):
        print(f"\n✅ SENHA: {senha}\n")
        print("CREDENCIAIS:")
        print(f"Admin: admin@nexus.com / {senha}")
        print(f"Cliente: empresa1@nexus.com / {senha}")
        break
