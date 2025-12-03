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
    def initialize_pool(cls, minconn: int = None, maxconn: int = None):
        """
        Inicializa o pool de conexões

        Args:
            minconn: Número mínimo de conexões no pool (default: 2 para economizar recursos)
            maxconn: Número máximo de conexões no pool (default: 20)

        IMPORTANTE:
        - Render free/starter tier limita a 25 conexões totais
        - Deixamos margem de 5 para conexões administrativas
        - Pool configurado para máximo de 20 conexões
        """
        import os

        try:
            if cls._connection_pool is None:
                # CRÍTICO: Detectar ambiente e ajustar limites
                # Render tem limite de 25 conexões, então configurar para 20 max
                is_render = (
                    os.getenv('RENDER') is not None or
                    os.getenv('IS_RENDER') == 'true' or
                    'render.com' in Config.DATABASE_URL
                )

                # Valores padrão ajustados para ambiente
                if minconn is None:
                    minconn = 2  # Economizar recursos, iniciar com poucas conexões
                if maxconn is None:
                    maxconn = 20 if is_render else 30  # 20 no Render, 30 local

                # Validar limites
                if maxconn > 25 and is_render:
                    logger.warning(f"⚠️ maxconn={maxconn} excede limite do Render (25), ajustando para 20")
                    maxconn = 20

                # Usa DATABASE_URL diretamente (compatível com Render.com)
                conninfo = Config.DATABASE_URL

                # OTIMIZAÇÃO: Configurações avançadas do pool para evitar vazamentos
                cls._connection_pool = ConnectionPool(
                    conninfo=conninfo,
                    min_size=minconn,
                    max_size=maxconn,
                    timeout=30.0,  # Timeout para obter conexão (30s)
                    max_waiting=100,  # Máximo de requisições esperando
                    max_lifetime=3600.0,  # Reciclar conexões após 1 hora
                    max_idle=600.0,  # Fechar conexões ociosas após 10 min
                    reconnect_timeout=300.0,  # Timeout para reconectar
                )

                # IMPORTANTE: Abrir o pool explicitamente
                cls._connection_pool.open()

                logger.info(f"✅ Pool de conexões PostgreSQL inicializado com sucesso")
                logger.info(f"   Ambiente: {'Render (produção)' if is_render else 'Local (desenvolvimento)'}")
                logger.info(f"   Pool: min={minconn}, max={maxconn} conexões")
                logger.info(f"   Timeout: 30s, Max waiting: 100, Max lifetime: 1h")
                logger.info(f"   Conectado a: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar pool de conexões: {e}")
            raise

    @classmethod
    def get_connection(cls, timeout: float = 10.0):
        """
        Obtém uma conexão do pool

        Args:
            timeout: Tempo máximo para aguardar uma conexão (segundos). Default: 10.0s
        """
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.getconn(timeout=timeout)

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
            cls._connection_pool = None
            logger.info("🔒 Pool de conexões fechado")

    @classmethod
    def get_pool_stats(cls) -> Dict[str, Any]:
        """
        Retorna estatísticas do pool de conexões

        Returns:
            Dict com estatísticas do pool
        """
        if not cls._connection_pool:
            return {
                'status': 'pool_not_initialized',
                'error': 'Pool de conexões não foi inicializado'
            }

        try:
            stats = cls._connection_pool.get_stats()
            return {
                'status': 'ok',
                'pool_min': cls._connection_pool.min_size,
                'pool_max': cls._connection_pool.max_size,
                'pool_size': stats.get('pool_size', 0),
                'pool_available': stats.get('pool_available', 0),
                'requests_waiting': stats.get('requests_waiting', 0),
                'requests_num': stats.get('requests_num', 0),
                'usage_percent': round((stats.get('pool_size', 0) / cls._connection_pool.max_size) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Erro ao obter stats do pool: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    @classmethod
    def reset_pool(cls, minconn: int = None, maxconn: int = None):
        """
        Reseta o pool de conexões (solução de emergência para PoolTimeout)

        Args:
            minconn: Novo mínimo de conexões
            maxconn: Novo máximo de conexões
        """
        logger.warning("⚠️  RESETANDO POOL DE CONEXÕES...")

        try:
            # Fechar pool atual
            cls.close_all_connections()

            # Reinicializar com novos parâmetros
            cls.initialize_pool(minconn=minconn, maxconn=maxconn)

            logger.info("✅ Pool de conexões resetado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao resetar pool: {e}")
            raise


from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Context manager que GARANTE que a conexão seja devolvida ao pool.

    SEMPRE use assim:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)

    NUNCA use assim (causa vazamento):
        conn = get_db_connection()  # ❌ ERRADO

    Returns:
        Conexão PostgreSQL
    """
    conn = None
    try:
        conn = Database.get_connection()
        yield conn
        conn.commit()  # Commit automático se não houver erro
    except Exception as e:
        if conn:
            conn.rollback()  # Rollback automático em caso de erro
        raise e
    finally:
        if conn:
            Database.return_connection(conn)  # SEMPRE devolver ao pool!


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
