"""
Rotas de Automação - Geração e disparo automático de boletos
"""

from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import automation_service
from routes.auth import login_required

automation_bp = Blueprint('automation', __name__, url_prefix='/api/automation')


@automation_bp.route('/executar-completa', methods=['POST'])
@login_required
def executar_automacao_completa():
    """
    Executa a automação completa (Etapas 21-33)
    Gera boletos, organiza em pastas e dispara via WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Executa a automação
        resultado = automation_service.executar_automacao_completa(cliente_nexus_id)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@automation_bp.route('/gerar-boletos', methods=['POST'])
@login_required
def gerar_boletos():
    """Gera boletos sem enviar"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        resultado = automation_service.gerar_boletos_sem_enviar(cliente_nexus_id)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@automation_bp.route('/historico', methods=['GET'])
@login_required
def get_historico():
    """Retorna histórico de disparos/automações com dados REAIS de boletos processados"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        from models import execute_query

        # Query melhorada para mostrar dados REAIS de boletos
        query = """
            SELECT
                hd.id,
                hd.tipo_disparo as tipo_automacao,
                hd.total_envios as total_processados,
                hd.envios_sucesso as total_sucessos,
                hd.envios_erro as total_erros,
                hd.horario_execucao as data_execucao,
                EXTRACT(EPOCH FROM (
                    SELECT MAX(horario_execucao) - MIN(horario_execucao)
                    FROM historico_disparos
                    WHERE id = hd.id
                ))::INTEGER as tempo_execucao_segundos,
                hd.detalhes,
                -- Dados REAIS de boletos processados
                (
                    SELECT COUNT(DISTINCT b.id)
                    FROM boletos b
                    WHERE b.id = ANY(hd.boletos_ids)
                ) as total_boletos_processados,
                (
                    SELECT COUNT(DISTINCT b.id)
                    FROM boletos b
                    WHERE b.id = ANY(hd.boletos_ids)
                      AND b.status_envio = 'enviado'
                ) as boletos_enviados,
                (
                    SELECT SUM(b.valor_original)::DECIMAL(10,2)
                    FROM boletos b
                    WHERE b.id = ANY(hd.boletos_ids)
                ) as valor_total_boletos,
                (
                    SELECT json_agg(
                        json_build_object(
                            'cliente_nome', cf.nome_completo,
                            'valor', b.valor_original,
                            'vencimento', b.data_vencimento,
                            'status_envio', b.status_envio
                        )
                    )
                    FROM boletos b
                    LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
                    WHERE b.id = ANY(hd.boletos_ids)
                    LIMIT 5
                ) as ultimos_boletos
            FROM historico_disparos hd
            WHERE hd.cliente_nexus_id = %s
            ORDER BY hd.horario_execucao DESC
            LIMIT 20
        """

        historico = execute_query(query, (cliente_nexus_id,), fetch=True)

        # Processa os resultados para formato JSON adequado
        historico_formatado = []
        for item in historico:
            historico_formatado.append({
                'id': item[0],
                'tipo_automacao': item[1],
                'total_processados': item[2],
                'total_sucessos': item[3],
                'total_erros': item[4],
                'data_execucao': item[5],
                'tempo_execucao_segundos': item[6] if item[6] else 0,
                'detalhes': item[7],
                'total_boletos_processados': item[8] or 0,
                'boletos_enviados': item[9] or 0,
                'valor_total_boletos': float(item[10]) if item[10] else 0.0,
                'ultimos_boletos': item[11] or []
            })

        return jsonify({'historico': historico_formatado}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500
