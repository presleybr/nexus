"""
Módulo de conexão e gerenciamento do banco de dados PostgreSQL
Fornece funções para conectar, executar queries e gerenciar transações
Usa psycopg (versão 3)
"""

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import sys
import os
import json

# Adiciona o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Classe para gerenciar conexões com PostgreSQL usando connection pooling"""

    _connection_pool = None

    @classmethod
    def initialize_pool(cls, minconn: int = 1, maxconn: int = 10):
        """
        Inicializa o pool de conexões

        Args:
            minconn: Número mínimo de conexões no pool
            maxconn: Número máximo de conexões no pool
        """
        try:
            if cls._connection_pool is None:
                # Usa DATABASE_URL diretamente (compatível com Render.com)
                conninfo = Config.DATABASE_URL
                cls._connection_pool = ConnectionPool(conninfo, min_size=minconn, max_size=maxconn)
                logger.info(f"✅ Pool de conexões PostgreSQL inicializado com sucesso")
                logger.info(f"   Conectado a: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar pool de conexões: {e}")
            raise

    @classmethod
    def get_connection(cls):
        """Obtém uma conexão do pool"""
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        """Retorna uma conexão ao pool"""
        if cls._connection_pool:
            cls._connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        """Fecha todas as conexões do pool"""
        if cls._connection_pool:
            cls._connection_pool.close()
            logger.info("🔒 Pool de conexões fechado")


def get_db_connection():
    """
    Função auxiliar para obter uma conexão do banco

    Returns:
        Conexão PostgreSQL
    """
    return Database.get_connection()


def execute_query(query: str, params: Optional[Tuple] = None, fetch: bool = False) -> Any:
    """
    Executa uma query SQL

    Args:
        query: Query SQL a ser executada
        params: Parâmetros para a query (prevenção de SQL injection)
        fetch: Se True, retorna os resultados; se False, apenas executa

    Returns:
        Resultados da query se fetch=True, None caso contrário
    """
    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor(row_factory=dict_row) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                results = cursor.fetchall()
                conn.commit()  # Commit para fechar a transação mesmo em SELECTs
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.rowcount

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Erro ao executar query: {e}")
        logger.error(f"Query: {query}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def execute_many(query: str, params_list: List[Tuple]) -> int:
    """
    Executa múltiplas queries de uma vez (bulk insert/update)

    Args:
        query: Query SQL a ser executada
        params_list: Lista de tuplas com parâmetros

    Returns:
        Número de linhas afetadas
    """
    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Erro ao executar batch query: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def fetch_one(query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
    """
    Executa query e retorna apenas um resultado

    Args:
        query: Query SQL
        params: Parâmetros da query

    Returns:
        Dict com resultado ou None se não encontrado
    """
    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor(row_factory=dict_row) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result = cursor.fetchone()
            return dict(result) if result else None

    except Exception as e:
        logger.error(f"❌ Erro ao buscar registro: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def insert_and_return_id(query: str, params: Tuple) -> int:
    """
    Executa INSERT e retorna o ID do registro criado

    Args:
        query: Query INSERT (deve incluir RETURNING id)
        params: Parâmetros da query

    Returns:
        ID do registro inserido
    """
    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            inserted_id = cursor.fetchone()[0]
            return inserted_id

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Erro ao inserir registro: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def check_database_exists() -> bool:
    """
    Verifica se o banco de dados existe

    Returns:
        True se existe, False caso contrário
    """
    try:
        # Conecta ao banco postgres para verificar se nexus_crm existe
        # Substitui o nome do banco na URL por 'postgres'
        import re
        postgres_url = re.sub(r'/[^/]+$', '/postgres', Config.DATABASE_URL)

        with psycopg.connect(postgres_url, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (Config.DB_NAME,)
                )
                exists = cursor.fetchone() is not None
                return exists

    except Exception as e:
        logger.error(f"❌ Erro ao verificar banco de dados: {e}")
        return False


def create_database():
    """Cria o banco de dados se não existir"""
    try:
        # Conecta ao banco postgres para criar nexus_crm
        # Substitui o nome do banco na URL por 'postgres'
        import re
        postgres_url = re.sub(r'/[^/]+$', '/postgres', Config.DATABASE_URL)

        with psycopg.connect(postgres_url, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {Config.DB_NAME}")
                logger.info(f"✅ Banco de dados '{Config.DB_NAME}' criado com sucesso")

    except psycopg.errors.DuplicateDatabase:
        logger.info(f"ℹ️  Banco de dados '{Config.DB_NAME}' já existe")
    except Exception as e:
        logger.error(f"❌ Erro ao criar banco de dados: {e}")
        raise


def check_tables_exist() -> bool:
    """
    Verifica se as tabelas principais existem no banco

    Returns:
        True se as tabelas existem, False caso contrário
    """
    try:
        query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('usuarios', 'clientes_nexus', 'boletos', 'logs_sistema')
        """

        result = fetch_one(query)
        # Se todas as 4 tabelas principais existirem
        return result and result['count'] == 4

    except Exception as e:
        logger.error(f"❌ Erro ao verificar tabelas: {e}")
        return False


def init_schema():
    """Inicializa o schema do banco de dados executando o arquivo SQL"""
    try:
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'database',
            'schema.sql'
        )

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()

            logger.info("✅ Schema do banco de dados inicializado com sucesso")
        finally:
            Database.return_connection(conn)

    except Exception as e:
        logger.error(f"❌ Erro ao inicializar schema: {e}")
        raise


def log_sistema(tipo: str, mensagem: str, categoria: str = None, detalhes: Dict = None, usuario_id: int = None):
    """
    Registra log no sistema

    Args:
        tipo: Tipo do log (info, warning, error, success)
        mensagem: Mensagem do log
        categoria: Categoria do log
        detalhes: Detalhes adicionais em formato JSON
        usuario_id: ID do usuário relacionado ao log
    """
    try:
        query = """
            INSERT INTO logs_sistema (tipo, categoria, mensagem, detalhes, usuario_id)
            VALUES (%s, %s, %s, %s, %s)
        """

        detalhes_json = json.dumps(detalhes) if detalhes else None
        execute_query(query, (tipo, categoria, mensagem, detalhes_json, usuario_id))

    except Exception as e:
        logger.error(f"❌ Erro ao registrar log: {e}")


# Inicializa o pool de conexões ao importar o módulo
try:
    Database.initialize_pool()
except Exception as e:
    logger.warning(f"⚠️  Pool não inicializado: {e}")


# Store reference to module-level functions before class definition
_module_execute_query = execute_query

# Criar instância compatível para novos módulos
class DatabaseWrapper:
    """Wrapper para manter compatibilidade com código novo"""

    @staticmethod
    def execute_query(query: str, params: tuple = None):
        """Executa query e retorna resultados"""
        return _module_execute_query(query, params, fetch=True)

    @staticmethod
    def execute_update(query: str, params: tuple = None):
        """Executa query de atualização/inserção"""
        return _module_execute_query(query, params, fetch=False)


# Instância global para importação
db = DatabaseWrapper()
