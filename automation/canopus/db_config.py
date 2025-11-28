"""
Configuração de banco de dados para automação Canopus
Centralizador de credenciais do PostgreSQL
"""

# Configurações do PostgreSQL
DB_HOST = "localhost"
DB_PORT = 5434
DB_NAME = "nexus_crm"
DB_USER = "postgres"
DB_PASSWORD = "nexus2025"


def get_connection_string():
    """
    Retorna string de conexão para psycopg

    Returns:
        str: Connection string no formato host=... port=... dbname=... user=... password=...
    """
    return f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"


def get_connection_params():
    """
    Retorna dicionário com parâmetros de conexão

    Returns:
        dict: Parâmetros de conexão para psycopg.connect(**params)
    """
    return {
        'host': DB_HOST,
        'port': DB_PORT,
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }


def get_connection_info():
    """
    Retorna informações de conexão para exibição (sem senha)

    Returns:
        str: String formatada com info de conexão
    """
    return f"""
Host: {DB_HOST}
Porta: {DB_PORT}
Banco: {DB_NAME}
Usuario: {DB_USER}
Senha: {'*' * len(DB_PASSWORD)}
"""


# Exportar todas as funções e variáveis
__all__ = [
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'get_connection_string',
    'get_connection_params',
    'get_connection_info'
]
