"""
Módulo de Models - Exporta todos os modelos do sistema
"""

from .database import (
    Database,
    get_db_connection,
    execute_query,
    fetch_one,
    insert_and_return_id,
    execute_many,
    check_database_exists,
    create_database,
    init_schema,
    log_sistema
)

from .usuario import Usuario, criar_usuario_admin_padrao

from .cliente import (
    ClienteNexus,
    ClienteFinal,
    validar_cpf,
    validar_cnpj,
    formatar_cpf,
    formatar_cnpj
)

from .boleto import (
    Boleto,
    Disparo,
    Configuracao
)

from .whatsapp_session import WhatsAppSession

__all__ = [
    # Database
    'Database',
    'get_db_connection',
    'execute_query',
    'fetch_one',
    'insert_and_return_id',
    'execute_many',
    'check_database_exists',
    'create_database',
    'init_schema',
    'log_sistema',

    # Usuario
    'Usuario',
    'criar_usuario_admin_padrao',

    # Cliente
    'ClienteNexus',
    'ClienteFinal',
    'validar_cpf',
    'validar_cnpj',
    'formatar_cpf',
    'formatar_cnpj',

    # Boleto
    'Boleto',
    'Disparo',
    'Configuracao',

    # WhatsApp
    'WhatsAppSession',
]
