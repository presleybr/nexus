"""
Modelo de Usuário - Gerencia autenticação e usuários do sistema
"""

from typing import Optional, Dict, List
import bcrypt
from .database import execute_query, fetch_one, insert_and_return_id, log_sistema


class Usuario:
    """Modelo para gerenciamento de usuários"""

    @staticmethod
    def criar(email: str, password: str, tipo: str = 'cliente') -> int:
        """
        Cria um novo usuário

        Args:
            email: Email único
            password: Senha (será hasheada)
            tipo: Tipo de usuário ('cliente' ou 'admin')

        Returns:
            ID do usuário criado
        """
        # Hash da senha com bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = """
            INSERT INTO usuarios (email, password_hash, tipo)
            VALUES (%s, %s, %s)
            RETURNING id
        """

        usuario_id = insert_and_return_id(query, (email, password_hash, tipo))

        log_sistema('success', f'Usuário criado: {email} ({tipo})', 'usuario',
                   {'usuario_id': usuario_id})

        return usuario_id

    @staticmethod
    def autenticar(email: str, password: str) -> Optional[Dict]:
        """
        Autentica um usuário

        Args:
            email: Email do usuário
            password: Senha

        Returns:
            Dados do usuário se autenticado, None caso contrário
        """
        print(f"\n[AUTENTICAR] Tentando autenticar: {email}")

        query = """
            SELECT * FROM usuarios
            WHERE email = %s AND ativo = true
        """

        usuario = fetch_one(query, (email,))
        print(f"[AUTENTICAR] Usuário encontrado: {usuario is not None}")

        if not usuario:
            print(f"[AUTENTICAR] ❌ Usuário não encontrado ou inativo: {email}")
            return None

        try:
            # Garante que password_hash seja string
            password_hash = usuario['password_hash']
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')

            print(f"[AUTENTICAR] Hash armazenado: {password_hash[:20]}...")
            print(f"[AUTENTICAR] Verificando senha...")

            # Verifica a senha
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                print(f"[AUTENTICAR] ✅ Senha correta!")

                # Remove o hash da senha antes de retornar
                del usuario['password_hash']

                try:
                    log_sistema('info', f'Login realizado: {email}', 'autenticacao',
                               {'usuario_id': usuario['id']})
                except Exception as log_err:
                    print(f"[AUTENTICAR] ⚠️ Erro ao registrar log (continuando): {log_err}")

                return usuario
            else:
                print(f"[AUTENTICAR] ❌ Senha incorreta!")
        except Exception as e:
            print(f"[AUTENTICAR] ❌ Erro ao verificar senha: {e}")
            import traceback
            print(traceback.format_exc())

        try:
            log_sistema('warning', f'Tentativa de login falhou: {email}', 'autenticacao')
        except Exception as log_err:
            print(f"[AUTENTICAR] ⚠️ Erro ao registrar log de falha (ignorando): {log_err}")

        return None

    @staticmethod
    def buscar_por_id(usuario_id: int) -> Optional[Dict]:
        """Busca usuário por ID (sem retornar password_hash)"""
        query = """
            SELECT id, email, tipo, ativo, created_at, updated_at
            FROM usuarios
            WHERE id = %s
        """
        return fetch_one(query, (usuario_id,))

    @staticmethod
    def buscar_por_email(email: str) -> Optional[Dict]:
        """Busca usuário por email"""
        query = """
            SELECT id, email, tipo, ativo, created_at, updated_at
            FROM usuarios
            WHERE email = %s
        """
        return fetch_one(query, (email,))

    @staticmethod
    def listar_todos(tipo: str = None) -> List[Dict]:
        """
        Lista todos os usuários

        Args:
            tipo: Filtrar por tipo (opcional)

        Returns:
            Lista de usuários
        """
        if tipo:
            query = """
                SELECT id, email, tipo, ativo, created_at, updated_at
                FROM usuarios
                WHERE tipo = %s
                ORDER BY created_at DESC
            """
            return execute_query(query, (tipo,), fetch=True)
        else:
            query = """
                SELECT id, email, tipo, ativo, created_at, updated_at
                FROM usuarios
                ORDER BY created_at DESC
            """
            return execute_query(query, fetch=True)

    @staticmethod
    def atualizar_senha(usuario_id: int, nova_senha: str) -> bool:
        """Atualiza a senha de um usuário"""
        password_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        query = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
        rows_affected = execute_query(query, (password_hash, usuario_id))

        if rows_affected > 0:
            log_sistema('info', f'Senha alterada para usuário ID {usuario_id}', 'usuario')
            return True
        return False

    @staticmethod
    def atualizar_email(usuario_id: int, novo_email: str) -> bool:
        """Atualiza o email de um usuário"""
        query = "UPDATE usuarios SET email = %s WHERE id = %s"
        rows_affected = execute_query(query, (novo_email, usuario_id))
        return rows_affected > 0

    @staticmethod
    def ativar_desativar(usuario_id: int, ativo: bool) -> bool:
        """Ativa ou desativa um usuário"""
        query = "UPDATE usuarios SET ativo = %s WHERE id = %s"
        rows_affected = execute_query(query, (ativo, usuario_id))

        status_texto = "ativado" if ativo else "desativado"
        if rows_affected > 0:
            log_sistema('warning', f'Usuário {status_texto}: ID {usuario_id}', 'usuario')
            return True
        return False

    @staticmethod
    def deletar(usuario_id: int) -> bool:
        """Deleta um usuário (cascata deleta cliente_nexus associado)"""
        query = "DELETE FROM usuarios WHERE id = %s"
        rows_affected = execute_query(query, (usuario_id,))

        if rows_affected > 0:
            log_sistema('warning', f'Usuário deletado: ID {usuario_id}', 'usuario')
            return True
        return False

    @staticmethod
    def verificar_email_existe(email: str) -> bool:
        """Verifica se um email já existe"""
        query = "SELECT 1 FROM usuarios WHERE email = %s"
        result = fetch_one(query, (email,))
        return result is not None

    @staticmethod
    def contar_por_tipo() -> Dict:
        """Conta usuários por tipo"""
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN tipo = 'admin' THEN 1 END) as admins,
                COUNT(CASE WHEN tipo = 'cliente' THEN 1 END) as clientes,
                COUNT(CASE WHEN ativo = true THEN 1 END) as ativos,
                COUNT(CASE WHEN ativo = false THEN 1 END) as inativos
            FROM usuarios
        """
        return fetch_one(query) or {}


def criar_usuario_admin_padrao():
    """Cria o usuário admin padrão se não existir"""
    if not Usuario.verificar_email_existe('admin@nexus.com'):
        Usuario.criar(
            email='admin@nexus.com',
            password='admin123',
            tipo='admin'
        )
        print("✅ Usuário admin padrão criado: admin@nexus.com / admin123")
        return True
    return False
