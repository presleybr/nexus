"""
Rotas Administrativas - APENAS STAGING
Endpoints perigosos que só devem funcionar em ambiente de desenvolvimento/staging.
"""

from flask import Blueprint, jsonify, request
import os
import logging

from models.database import db_connection, dict_row

logger = logging.getLogger(__name__)

admin_staging_bp = Blueprint('admin_staging', __name__)


def is_staging_environment():
    """Verifica se está em ambiente staging/desenvolvimento"""
    # Verificar variável de ambiente
    env = os.environ.get('FLASK_ENV', 'production')
    database_url = os.environ.get('DATABASE_URL', '')

    # É staging se:
    # - FLASK_ENV é development ou staging
    # - DATABASE_URL contém 'staging'
    # - Está rodando localmente
    return (
        env in ['development', 'staging'] or
        'staging' in database_url.lower() or
        'localhost' in os.environ.get('SERVER_NAME', '')
    )


@admin_staging_bp.route('/api/admin/reset-dados-boletos', methods=['POST'])
def reset_dados_boletos():
    """
    Reseta TODOS os dados de clientes, boletos e downloads.
    APENAS FUNCIONA EM STAGING!
    """
    # Verificar ambiente
    if not is_staging_environment():
        logger.warning("Tentativa de reset em ambiente de produção BLOQUEADA!")
        return jsonify({
            'success': False,
            'error': 'Esta operação só é permitida em ambiente staging'
        }), 403

    try:
        logger.info("=" * 60)
        logger.info("🗑️ INICIANDO RESET DE DADOS (STAGING)")
        logger.info("=" * 60)

        clientes_removidos = 0
        boletos_removidos = 0
        downloads_removidos = 0

        with db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # 1. Contar registros antes de deletar
                cur.execute("SELECT COUNT(*) as total FROM downloads_canopus")
                downloads_removidos = cur.fetchone()['total']

                cur.execute("SELECT COUNT(*) as total FROM boletos")
                boletos_removidos = cur.fetchone()['total']

                cur.execute("SELECT COUNT(*) as total FROM clientes_finais")
                clientes_removidos = cur.fetchone()['total']

                # 2. Deletar na ordem correta (devido a foreign keys)
                logger.info(f"Deletando {downloads_removidos} downloads...")
                cur.execute("DELETE FROM downloads_canopus")

                logger.info(f"Deletando {boletos_removidos} boletos...")
                cur.execute("DELETE FROM boletos")

                logger.info(f"Deletando {clientes_removidos} clientes...")
                cur.execute("DELETE FROM clientes_finais")

                conn.commit()

        logger.info("=" * 60)
        logger.info("✅ RESET CONCLUÍDO COM SUCESSO!")
        logger.info(f"   Clientes removidos: {clientes_removidos}")
        logger.info(f"   Boletos removidos: {boletos_removidos}")
        logger.info(f"   Downloads removidos: {downloads_removidos}")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'clientes_removidos': clientes_removidos,
            'boletos_removidos': boletos_removidos,
            'downloads_removidos': downloads_removidos
        })

    except Exception as e:
        logger.error(f"❌ Erro ao resetar dados: {e}")
        logger.exception("Traceback:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_staging_bp.route('/api/admin/reset-downloads', methods=['POST'])
def reset_downloads():
    """
    Reseta APENAS a tabela downloads_canopus.
    APENAS FUNCIONA EM STAGING!
    """
    # Verificar ambiente
    if not is_staging_environment():
        logger.warning("Tentativa de reset em ambiente de produção BLOQUEADA!")
        return jsonify({
            'success': False,
            'error': 'Esta operação só é permitida em ambiente staging'
        }), 403

    try:
        logger.info("=" * 60)
        logger.info("📥 INICIANDO RESET DE DOWNLOADS (STAGING)")
        logger.info("=" * 60)

        downloads_removidos = 0

        with db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Contar registros
                cur.execute("SELECT COUNT(*) as total FROM downloads_canopus")
                downloads_removidos = cur.fetchone()['total']

                # Deletar
                logger.info(f"Deletando {downloads_removidos} downloads...")
                cur.execute("DELETE FROM downloads_canopus")

                conn.commit()

        logger.info("=" * 60)
        logger.info("✅ RESET DE DOWNLOADS CONCLUÍDO!")
        logger.info(f"   Downloads removidos: {downloads_removidos}")
        logger.info("=" * 60)

        return jsonify({
            'success': True,
            'downloads_removidos': downloads_removidos
        })

    except Exception as e:
        logger.error(f"❌ Erro ao resetar downloads: {e}")
        logger.exception("Traceback:")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_staging_bp.route('/api/admin/ambiente', methods=['GET'])
def verificar_ambiente():
    """Retorna informações sobre o ambiente atual"""
    return jsonify({
        'is_staging': is_staging_environment(),
        'flask_env': os.environ.get('FLASK_ENV', 'not set'),
        'database': 'staging' if 'staging' in os.environ.get('DATABASE_URL', '').lower() else 'production'
    })
