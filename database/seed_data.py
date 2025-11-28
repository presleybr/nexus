"""
Script de Seed Data - Popula o banco com dados fake para testes
Cria 3 empresas, 50 clientes cada e 200 boletos por empresa
"""

import sys
import os
from datetime import datetime, timedelta, date
import random

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from models.database import Database, execute_query, execute_many, fetch_one
import bcrypt

# Dados fake brasileiros
NOMES_BRASILEIROS = [
    "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa", "Carlos Souza",
    "Juliana Lima", "Fernando Alves", "Beatriz Rodrigues", "Rafael Pereira", "Camila Ferreira",
    "Lucas Martins", "Patricia Gomes", "Ricardo Ribeiro", "Fernanda Carvalho", "Gustavo Dias",
    "Amanda Barbosa", "Bruno Cardoso", "Leticia Monteiro", "Rodrigo Araujo", "Gabriela Ramos",
    "Thiago Correia", "Vanessa Castro", "Felipe Rocha", "Mariana Moura", "Daniel Pinto",
    "Larissa Teixeira", "Vinicius Mendes", "Carolina Vieira", "Marcelo Barros", "Renata Duarte",
    "Andre Nunes", "Bianca Freitas", "Fabio Cavalcante", "Tatiana Pires", "Leonardo Campos",
    "Priscila Moraes", "Henrique Farias", "Natalia Soares", "Eduardo Lopes", "Daniela Castro",
    "Marcos Cunha", "Aline Fernandes", "Caio Vasconcelos", "Simone Azevedo", "Renan Macedo",
    "Luciana Fonseca", "Guilherme Melo", "Raquel Batista", "Igor Nogueira", "Sabrina Antunes"
]

EMPRESAS = [
    {"nome": "Tech Solutions Ltda", "cnpj": "12.345.678/0001-90", "email": "empresa1@nexus.com"},
    {"nome": "Marketing Pro", "cnpj": "98.765.432/0001-10", "email": "empresa2@nexus.com"},
    {"nome": "Consultoria Empresarial", "cnpj": "11.222.333/0001-44", "email": "empresa3@nexus.com"}
]

def gerar_cpf_valido() -> str:
    """Gera um CPF válido aleatório"""
    def calcula_digito(cpf_parcial, peso_inicial):
        soma = sum(int(cpf_parcial[i]) * (peso_inicial - i) for i in range(len(cpf_parcial)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Gera os 9 primeiros dígitos
    cpf = [random.randint(0, 9) for _ in range(9)]

    # Calcula os dígitos verificadores
    cpf.append(calcula_digito(cpf, 10))
    cpf.append(calcula_digito(cpf, 11))

    # Formata o CPF
    cpf_str = ''.join(map(str, cpf))
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"

def gerar_telefone_brasileiro() -> str:
    """Gera um telefone brasileiro (67) 9XXXX-XXXX"""
    numero = random.randint(90000, 99999)
    numero2 = random.randint(1000, 9999)
    return f"(67) 9{numero}-{numero2}"

def popular_dados():
    """Popula o banco com dados fake"""

    print("=" * 60)
    print("🌱 POPULANDO BANCO DE DADOS COM DADOS FAKE")
    print("=" * 60)

    try:
        Database.initialize_pool()
        print("✅ Pool de conexões inicializado")

        # 1. Criar usuário admin
        print("\n📌 Passo 1/4: Criando usuário administrador...")
        admin_exists = fetch_one("SELECT id FROM usuarios WHERE email = 'admin@nexus.com'")

        if not admin_exists:
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            execute_query(
                "INSERT INTO usuarios (email, password_hash, tipo) VALUES (%s, %s, %s)",
                ('admin@nexus.com', password_hash, 'admin')
            )
            print("✅ Admin criado: admin@nexus.com / admin123")
        else:
            print("ℹ️  Admin já existe (ID: {})".format(admin_exists['id']))

        # 2. Criar empresas e usuários
        print("\n📌 Passo 2/4: Criando empresas clientes da Nexus...")
        print(f"   Total de empresas a criar: {len(EMPRESAS)}")

        clientes_nexus_ids = []

        for i, empresa in enumerate(EMPRESAS, 1):
            # Verifica se usuário já existe
            usuario_exists = fetch_one("SELECT id FROM usuarios WHERE email = %s", (empresa['email'],))

            if usuario_exists:
                # Usuário já existe, pega o ID
                print(f"ℹ️  Usuário já existe: {empresa['email']}")
                usuario_id = usuario_exists['id']
            else:
                # Cria usuário
                print(f"📝 Criando usuário: {empresa['email']}")
                password_hash = bcrypt.hashpw('empresa123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                resultado = execute_query(
                    "INSERT INTO usuarios (email, password_hash, tipo) VALUES (%s, %s, %s) RETURNING id",
                    (empresa['email'], password_hash, 'cliente'),
                    fetch=True
                )
                usuario_id = resultado[0]['id']
                print(f"✅ Usuário criado com ID: {usuario_id}")

            # Verifica se cliente_nexus já existe para este usuário
            cliente_nexus_exists = fetch_one(
                "SELECT id FROM clientes_nexus WHERE usuario_id = %s",
                (usuario_id,)
            )

            if cliente_nexus_exists:
                # Cliente Nexus já existe
                print(f"ℹ️  Empresa {i} já existe: {empresa['nome']}")
                clientes_nexus_ids.append(cliente_nexus_exists['id'])
            else:
                # Cria cliente Nexus
                print(f"📝 Criando cliente Nexus: {empresa['nome']}")
                telefone = gerar_telefone_brasileiro()
                whatsapp = gerar_telefone_brasileiro()

                try:
                    resultado = execute_query(
                        """INSERT INTO clientes_nexus
                           (usuario_id, nome_empresa, cnpj, telefone, whatsapp_numero, email_contato)
                           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                        (usuario_id, empresa['nome'], empresa['cnpj'], telefone, whatsapp, empresa['email']),
                        fetch=True
                    )
                    cliente_nexus_id = resultado[0]['id']
                    print(f"✅ Cliente Nexus criado com ID: {cliente_nexus_id}")
                except Exception as e:
                    print(f"❌ ERRO ao criar cliente_nexus para usuario_id={usuario_id}: {e}")
                    print(f"   Empresa: {empresa['nome']}")
                    print(f"   Email: {empresa['email']}")
                    raise

                # Cria configuração padrão
                execute_query(
                    "INSERT INTO configuracoes_cliente (cliente_nexus_id) VALUES (%s)",
                    (cliente_nexus_id,)
                )
                print(f"✅ Configuração criada para cliente {cliente_nexus_id}")

                clientes_nexus_ids.append(cliente_nexus_id)

                print(f"✅ Empresa {i}: {empresa['nome']}")
                print(f"   Login: {empresa['email']} / empresa123")

        # Verifica se temos clientes para criar boletos
        if not clientes_nexus_ids:
            print("\n⚠️  AVISO: Nenhum cliente Nexus foi criado/encontrado!")
            print("   Não será possível criar boletos.")
            return False

        print(f"\n✅ Total de clientes Nexus prontos: {len(clientes_nexus_ids)}")
        print(f"   IDs: {clientes_nexus_ids}")

        # 3. Criar boletos para cada empresa
        print(f"\n📌 Passo 3/4: Criando boletos (200 por empresa)...")

        total_boletos_criados = 0
        meses = [
            "Janeiro/2024", "Fevereiro/2024", "Março/2024", "Abril/2024",
            "Maio/2024", "Junho/2024", "Julho/2024", "Agosto/2024",
            "Setembro/2024", "Outubro/2024", "Novembro/2024", "Dezembro/2024",
            "Janeiro/2025", "Fevereiro/2025"
        ]

        status_opcoes = ['pago'] * 40 + ['pendente'] * 30 + ['vencido'] * 20 + ['enviado'] * 10

        for idx, cliente_nexus_id in enumerate(clientes_nexus_ids, 1):
            print(f"\n   📄 Criando boletos para cliente {idx}/{len(clientes_nexus_ids)} (ID: {cliente_nexus_id})...")
            boletos_para_criar = []
            cpfs_usados = set()

            for i in range(200):
                # Gera CPF único
                cpf = gerar_cpf_valido()
                while cpf in cpfs_usados:
                    cpf = gerar_cpf_valido()
                cpfs_usados.add(cpf)

                # Seleciona um nome
                nome = random.choice(NOMES_BRASILEIROS)

                # Dados do boleto
                mes_ref = random.choice(meses)
                valor = round(random.uniform(200, 2000), 2)

                # Vencimento aleatório
                dias = random.randint(-30, 60)
                vencimento = date.today() + timedelta(days=dias)

                # Status baseado no vencimento
                if dias < -7:
                    status = random.choice(['pago', 'enviado'])
                elif dias < 0:
                    status = random.choice(['vencido', 'pendente'])
                else:
                    status = random.choice(['pendente', 'enviado'])

                boletos_para_criar.append((
                    cliente_nexus_id,
                    cpf,
                    nome,
                    mes_ref,
                    valor,
                    vencimento,
                    None,  # pdf_path
                    status,
                    datetime.now() if status == 'enviado' else None
                ))

            # Insere em lote
            if boletos_para_criar:
                execute_many(
                    """INSERT INTO boletos
                       (cliente_nexus_id, cliente_final_cpf, cliente_final_nome, mes_referencia,
                        valor, vencimento, pdf_path, status_envio, data_envio)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    boletos_para_criar
                )
                total_boletos_criados += len(boletos_para_criar)
                print(f"      ✅ {len(boletos_para_criar)} boletos criados para este cliente")

        print(f"\n✅ Total de boletos criados: {total_boletos_criados}")

        # 4. Atualizar status do sistema
        print(f"\n📌 Passo 4/4: Atualizando status do sistema...")
        execute_query(
            "UPDATE status_sistema SET ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = 1"
        )
        print("✅ Status do sistema atualizado")

        print("\n" + "=" * 60)
        print("✅ DADOS FAKE CRIADOS COM SUCESSO!")
        print("=" * 60)
        print(f"\n📊 Resumo:")
        print(f"   • Empresas: {len(clientes_nexus_ids)}")
        print(f"   • Boletos: {total_boletos_criados}")
        print(f"\n🔐 Logins disponíveis:")
        print(f"   Admin: admin@nexus.com / admin123")
        for emp in EMPRESAS:
            print(f"   Cliente: {emp['email']} / empresa123")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERRO ao popular dados: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Database.close_all_connections()

if __name__ == '__main__':
    sucesso = popular_dados()
    sys.exit(0 if sucesso else 1)
