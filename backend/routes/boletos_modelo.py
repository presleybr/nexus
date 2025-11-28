"""
Rotas para gerenciar Boletos Modelo
Sistema Nexus CRM - Portal Consórcio
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import logging
import os

from models.database import db
from routes.portal_consorcio import login_required_portal

logger = logging.getLogger(__name__)

# Blueprint
boletos_modelo_bp = Blueprint('boletos_modelo', __name__, url_prefix='/portal-consorcio/api/boletos-modelo')


@boletos_modelo_bp.route('', methods=['GET'])
@login_required_portal
def listar_boletos_modelo():
    """Lista todos os boletos modelo cadastrados"""
    try:
        modelos = db.execute_query("""
            SELECT id, nome, descricao, tipo, banco,
                   pdf_filename, pdf_size, ativo, padrao,
                   total_envios, ultimo_envio, created_at
            FROM boletos_modelo
            WHERE ativo = true
            ORDER BY padrao DESC, created_at DESC
        """, ())

        return jsonify({
            'success': True,
            'modelos': modelos
        })

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao listar modelos: {str(e)}")
        return jsonify({'error': 'Erro ao listar modelos'}), 500


@boletos_modelo_bp.route('/<int:modelo_id>', methods=['GET'])
@login_required_portal
def obter_boleto_modelo(modelo_id):
    """Obtém detalhes de um boleto modelo específico"""
    try:
        modelo = db.execute_query("""
            SELECT *
            FROM boletos_modelo
            WHERE id = %s
        """, (modelo_id,))

        if not modelo:
            return jsonify({'error': 'Modelo não encontrado'}), 404

        return jsonify({
            'success': True,
            'modelo': modelo[0]
        })

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao obter modelo: {str(e)}")
        return jsonify({'error': 'Erro ao obter modelo'}), 500


@boletos_modelo_bp.route('/<int:modelo_id>/download', methods=['GET'])
@login_required_portal
def download_boleto_modelo(modelo_id):
    """Download do PDF do boleto modelo"""
    try:
        # Buscar modelo
        modelo = db.execute_query(
            "SELECT * FROM boletos_modelo WHERE id = %s",
            (modelo_id,)
        )

        if not modelo:
            return jsonify({'error': 'Modelo não encontrado'}), 404

        modelo = modelo[0]

        if not modelo['pdf_path'] or not os.path.exists(modelo['pdf_path']):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        return send_file(
            modelo['pdf_path'],
            mimetype='application/pdf',
            as_attachment=True,
            download_name=modelo['pdf_filename']
        )

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao fazer download: {str(e)}")
        return jsonify({'error': 'Erro ao fazer download'}), 500


@boletos_modelo_bp.route('/<int:modelo_id>/visualizar', methods=['GET'])
@login_required_portal
def visualizar_boleto_modelo(modelo_id):
    """Visualizar PDF do boleto modelo inline"""
    try:
        # Buscar modelo
        modelo = db.execute_query(
            "SELECT * FROM boletos_modelo WHERE id = %s",
            (modelo_id,)
        )

        if not modelo:
            return jsonify({'error': 'Modelo não encontrado'}), 404

        modelo = modelo[0]

        if not modelo['pdf_path'] or not os.path.exists(modelo['pdf_path']):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        return send_file(
            modelo['pdf_path'],
            mimetype='application/pdf',
            as_attachment=False  # Inline
        )

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao visualizar PDF: {str(e)}")
        return jsonify({'error': 'Erro ao visualizar PDF'}), 500


@boletos_modelo_bp.route('/padrao', methods=['GET'])
@login_required_portal
def obter_modelo_padrao():
    """Obtém o boleto modelo padrão do sistema"""
    try:
        modelo = db.execute_query("""
            SELECT *
            FROM boletos_modelo
            WHERE padrao = true AND ativo = true
            LIMIT 1
        """, ())

        if not modelo:
            return jsonify({'error': 'Nenhum modelo padrão configurado'}), 404

        return jsonify({
            'success': True,
            'modelo': modelo[0]
        })

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao obter modelo padrão: {str(e)}")
        return jsonify({'error': 'Erro ao obter modelo padrão'}), 500


@boletos_modelo_bp.route('/<int:modelo_id>/estatisticas', methods=['GET'])
@login_required_portal
def estatisticas_modelo(modelo_id):
    """Obtém estatísticas de uso de um modelo"""
    try:
        modelo = db.execute_query("""
            SELECT id, nome, total_envios, ultimo_envio, created_at
            FROM boletos_modelo
            WHERE id = %s
        """, (modelo_id,))

        if not modelo:
            return jsonify({'error': 'Modelo não encontrado'}), 404

        modelo = modelo[0]

        # Calcular estatísticas adicionais se necessário
        stats = {
            'modelo_id': modelo['id'],
            'nome': modelo['nome'],
            'total_envios': modelo['total_envios'],
            'ultimo_envio': modelo['ultimo_envio'],
            'criado_em': modelo['created_at'],
        }

        return jsonify({
            'success': True,
            'estatisticas': stats
        })

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao obter estatísticas: {str(e)}")
        return jsonify({'error': 'Erro ao obter estatísticas'}), 500


@boletos_modelo_bp.route('/<int:modelo_id>/incrementar-envio', methods=['POST'])
@login_required_portal
def incrementar_contador_envio(modelo_id):
    """Incrementa o contador de envios do modelo"""
    try:
        db.execute_update("""
            UPDATE boletos_modelo
            SET total_envios = total_envios + 1,
                ultimo_envio = %s
            WHERE id = %s
        """, (datetime.now(), modelo_id))

        return jsonify({
            'success': True,
            'message': 'Contador incrementado'
        })

    except Exception as e:
        logger.error(f"[BOLETOS_MODELO] Erro ao incrementar contador: {str(e)}")
        return jsonify({'error': 'Erro ao incrementar contador'}), 500


def register_boletos_modelo_routes(app):
    """Registrar blueprint de boletos modelo"""
    app.register_blueprint(boletos_modelo_bp)
    logger.info("[BOLETOS_MODELO] Rotas de boletos modelo registradas")
