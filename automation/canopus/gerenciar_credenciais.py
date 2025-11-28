"""
Script Helper para Gerenciar Credenciais do Canopus
Permite adicionar, listar, atualizar e remover credenciais de forma segura
"""

import sys
import argparse
import getpass
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet

# Adicionar diretório backend ao path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from config import CanopusConfig


class GerenciadorCredenciais:
    """Gerencia credenciais do Canopus no banco de dados"""

    def __init__(self):
        """Inicializa gerenciador"""
        self.config = CanopusConfig
        self.db_conn = None
        self.fernet = Fernet(self.config.ENCRYPTION_KEY.encode())

    def conectar(self):
        """Conecta ao banco de dados"""
        try:
            self.db_conn = psycopg.connect(
                self.config.DB_CONNECTION_STRING,
                row_factory=dict_row
            )
            print("✅ Conectado ao banco de dados")
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            sys.exit(1)

    def desconectar(self):
        """Desconecta do banco"""
        if self.db_conn:
            self.db_conn.close()
            print("✅ Desconectado do banco de dados")

    def listar_pontos_venda(self):
        """Lista pontos de venda cadastrados"""
        print("\n" + "=" * 80)
        print("PONTOS DE VENDA CADASTRADOS")
        print("=" * 80)

        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT id, codigo, nome, ativo
                    FROM pontos_venda
                    ORDER BY codigo
                """)
                pontos = cur.fetchall()

            if not pontos:
                print("⚠️ Nenhum ponto de venda cadastrado")
                return

            for ponto in pontos:
                status = "✅" if ponto["ativo"] else "❌"
                print(f"{status} [{ponto['id']}] {ponto['codigo']} - {ponto['nome']}")

            print("=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Erro ao listar pontos de venda: {e}")

    def listar_credenciais(self, mostrar_senha=False):
        """Lista credenciais cadastradas"""
        print("\n" + "=" * 80)
        print("CREDENCIAIS CADASTRADAS")
        print("=" * 80)

        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, pv.codigo, pv.nome, c.usuario,
                           c.senha_encrypted, c.tipo_credencial, c.ativo
                    FROM credenciais_canopus c
                    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    ORDER BY pv.codigo, c.tipo_credencial
                """)
                credenciais = cur.fetchall()

            if not credenciais:
                print("⚠️ Nenhuma credencial cadastrada")
                print("\nUse: python gerenciar_credenciais.py --adicionar")
                print("=" * 80 + "\n")
                return

            for cred in credenciais:
                status = "✅" if cred["ativo"] else "❌"
                print(f"\n{status} ID: {cred['id']}")
                print(f"   Ponto de Venda: {cred['codigo']} - {cred['nome']}")
                print(f"   Usuário: {cred['usuario']}")
                print(f"   Tipo: {cred['tipo_credencial']}")

                if mostrar_senha:
                    try:
                        senha = self.fernet.decrypt(cred["senha_encrypted"].encode()).decode()
                        print(f"   Senha: {senha}")
                    except:
                        print(f"   Senha: [ERRO AO DESCRIPTOGRAFAR]")

            print("\n" + "=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Erro ao listar credenciais: {e}")

    def adicionar_credencial(
        self,
        ponto_venda_codigo: str,
        usuario: str,
        senha: str = None,
        tipo: str = "PRINCIPAL"
    ):
        """
        Adiciona nova credencial

        Args:
            ponto_venda_codigo: Código do ponto de venda (ex: CREDMS)
            usuario: Nome de usuário
            senha: Senha (será solicitada se não fornecida)
            tipo: Tipo da credencial (PRINCIPAL, BACKUP, etc.)
        """
        print("\n" + "=" * 80)
        print("ADICIONAR NOVA CREDENCIAL")
        print("=" * 80)

        try:
            # Buscar ponto de venda
            with self.db_conn.cursor() as cur:
                cur.execute(
                    "SELECT id, codigo, nome FROM pontos_venda WHERE codigo = %s",
                    (ponto_venda_codigo.upper(),)
                )
                ponto = cur.fetchone()

            if not ponto:
                print(f"❌ Ponto de venda '{ponto_venda_codigo}' não encontrado")
                print("\nPontos disponíveis:")
                self.listar_pontos_venda()
                return False

            print(f"\n📍 Ponto de Venda: {ponto['codigo']} - {ponto['nome']}")
            print(f"👤 Usuário: {usuario}")
            print(f"🔐 Tipo: {tipo}")

            # Solicitar senha se não fornecida
            if not senha:
                senha = getpass.getpass("Digite a senha: ")
                senha_confirm = getpass.getpass("Confirme a senha: ")

                if senha != senha_confirm:
                    print("❌ Senhas não conferem!")
                    return False

            # Criptografar senha
            senha_encrypted = self.fernet.encrypt(senha.encode()).decode()

            # Inserir no banco
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO credenciais_canopus (
                        ponto_venda_id,
                        usuario,
                        senha_encrypted,
                        tipo_credencial,
                        ativo
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    ponto["id"],
                    usuario,
                    senha_encrypted,
                    tipo,
                    True
                ))

                credencial_id = cur.fetchone()["id"]
                self.db_conn.commit()

            print(f"\n✅ Credencial adicionada com sucesso! ID: {credencial_id}")
            print("=" * 80 + "\n")
            return True

        except Exception as e:
            print(f"\n❌ Erro ao adicionar credencial: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    def atualizar_senha(self, credencial_id: int, nova_senha: str = None):
        """Atualiza senha de uma credencial"""
        print("\n" + "=" * 80)
        print("ATUALIZAR SENHA")
        print("=" * 80)

        try:
            # Buscar credencial
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, pv.codigo, pv.nome, c.usuario
                    FROM credenciais_canopus c
                    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE c.id = %s
                """, (credencial_id,))

                cred = cur.fetchone()

            if not cred:
                print(f"❌ Credencial ID {credencial_id} não encontrada")
                return False

            print(f"\n📍 Ponto: {cred['codigo']} - {cred['nome']}")
            print(f"👤 Usuário: {cred['usuario']}")

            # Solicitar nova senha
            if not nova_senha:
                nova_senha = getpass.getpass("Digite a NOVA senha: ")
                senha_confirm = getpass.getpass("Confirme a NOVA senha: ")

                if nova_senha != senha_confirm:
                    print("❌ Senhas não conferem!")
                    return False

            # Criptografar
            senha_encrypted = self.fernet.encrypt(nova_senha.encode()).decode()

            # Atualizar
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE credenciais_canopus
                    SET senha_encrypted = %s,
                        data_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (senha_encrypted, credencial_id))

                self.db_conn.commit()

            print(f"\n✅ Senha atualizada com sucesso!")
            print("=" * 80 + "\n")
            return True

        except Exception as e:
            print(f"\n❌ Erro ao atualizar senha: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return False

    def desativar_credencial(self, credencial_id: int):
        """Desativa uma credencial"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE credenciais_canopus
                    SET ativo = FALSE
                    WHERE id = %s
                """, (credencial_id,))

                self.db_conn.commit()

            print(f"✅ Credencial ID {credencial_id} desativada")
            return True

        except Exception as e:
            print(f"❌ Erro ao desativar: {e}")
            return False

    def testar_credencial(self, credencial_id: int):
        """Testa uma credencial (descriptografa e mostra)"""
        print("\n" + "=" * 80)
        print("TESTAR CREDENCIAL")
        print("=" * 80)

        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.*, pv.codigo, pv.nome as pv_nome
                    FROM credenciais_canopus c
                    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE c.id = %s
                """, (credencial_id,))

                cred = cur.fetchone()

            if not cred:
                print(f"❌ Credencial ID {credencial_id} não encontrada")
                return

            # Descriptografar
            senha = self.fernet.decrypt(cred["senha_encrypted"].encode()).decode()

            print(f"\n📍 Ponto: {cred['codigo']} - {cred['pv_nome']}")
            print(f"👤 Usuário: {cred['usuario']}")
            print(f"🔑 Senha: {senha}")
            print(f"📌 Tipo: {cred['tipo_credencial']}")
            print(f"✅ Status: {'Ativa' if cred['ativo'] else 'Inativa'}")
            print("\n" + "=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Erro ao testar credencial: {e}")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Gerenciar credenciais do sistema Canopus"
    )

    parser.add_argument("--listar", "-l", action="store_true",
                        help="Listar todas as credenciais")

    parser.add_argument("--pontos", "-p", action="store_true",
                        help="Listar pontos de venda")

    parser.add_argument("--adicionar", "-a", action="store_true",
                        help="Adicionar nova credencial")

    parser.add_argument("--atualizar", "-u", type=int, metavar="ID",
                        help="Atualizar senha da credencial ID")

    parser.add_argument("--desativar", "-d", type=int, metavar="ID",
                        help="Desativar credencial ID")

    parser.add_argument("--testar", "-t", type=int, metavar="ID",
                        help="Testar credencial ID (mostra senha)")

    parser.add_argument("--ponto", type=str,
                        help="Código do ponto de venda (para --adicionar)")

    parser.add_argument("--usuario", type=str,
                        help="Nome de usuário (para --adicionar)")

    parser.add_argument("--senha", type=str,
                        help="Senha (para --adicionar)")

    parser.add_argument("--tipo", type=str, default="PRINCIPAL",
                        help="Tipo da credencial (padrão: PRINCIPAL)")

    parser.add_argument("--mostrar-senhas", "-s", action="store_true",
                        help="Mostrar senhas ao listar (use com cuidado!)")

    args = parser.parse_args()

    # Criar gerenciador
    gerenciador = GerenciadorCredenciais()

    try:
        # Conectar ao banco
        gerenciador.conectar()

        # Executar ação
        if args.pontos:
            gerenciador.listar_pontos_venda()

        elif args.listar:
            gerenciador.listar_credenciais(mostrar_senha=args.mostrar_senhas)

        elif args.adicionar:
            if not args.ponto or not args.usuario:
                print("❌ Uso: --adicionar --ponto CODIGO --usuario USUARIO")
                sys.exit(1)

            gerenciador.adicionar_credencial(
                ponto_venda_codigo=args.ponto,
                usuario=args.usuario,
                senha=args.senha,
                tipo=args.tipo
            )

        elif args.atualizar:
            gerenciador.atualizar_senha(args.atualizar)

        elif args.desativar:
            gerenciador.desativar_credencial(args.desativar)

        elif args.testar:
            gerenciador.testar_credencial(args.testar)

        else:
            parser.print_help()

    finally:
        gerenciador.desconectar()


if __name__ == "__main__":
    main()
