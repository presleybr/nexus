"""
Rotas CRM - Disparo Individual para Teste e Gerenciamento de Números
"""

from flask import Blueprint, request, jsonify, session

from models.database import db
from models import log_sistema
from routes.auth import login_required

disparo_individual_bp = Blueprint('disparo_individual', __name__, url_prefix='/api/crm')


# ============================================================================
# FUNÇÃO HELPER
# ============================================================================

def buscar_numeros_notificacao(cliente_nexus_id: int) -> list:
    """
    Busca todos os números de notificação ativos de um cliente nexus
    Retorna lista de números WhatsApp (strings)
    """
    try:
        numeros = db.execute_query("""
            SELECT whatsapp
            FROM numeros_notificacao
            WHERE cliente_nexus_id = %s AND ativo = true
            ORDER BY id
        """, (cliente_nexus_id,))

        return [n['whatsapp'] for n in numeros] if numeros else []
    except Exception as e:
        print(f"Erro ao buscar números de notificação: {e}")
        # Fallback para números hardcoded se houver erro
        return ['556796600884', '556798905585']


# ============================================================================
# GERENCIAMENTO DE NÚMEROS DE NOTIFICAÇÃO
# ============================================================================

@disparo_individual_bp.route('/numeros-notificacao', methods=['GET'])
@login_required
def listar_numeros_notificacao():
    """Lista todos os números de notificação do cliente nexus logado"""
    try:
        cliente_nexus_id = session.get('usuario_id')

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        numeros = db.execute_query("""
            SELECT id, nome, whatsapp, ativo, created_at
            FROM numeros_notificacao
            WHERE cliente_nexus_id = %s
            ORDER BY id
        """, (cliente_nexus_id,))

        return jsonify({
            'success': True,
            'numeros': numeros or [],
            'total': len(numeros) if numeros else 0
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@disparo_individual_bp.route('/numeros-notificacao', methods=['POST'])
@login_required
def adicionar_numero_notificacao():
    """Adiciona um novo número de notificação"""
    try:
        cliente_nexus_id = session.get('usuario_id')
        data = request.get_json()

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        nome = data.get('nome', '').strip()
        whatsapp = data.get('whatsapp', '').strip()

        if not nome or not whatsapp:
            return jsonify({'success': False, 'erro': 'Nome e WhatsApp são obrigatórios'}), 400

        # Validação do WhatsApp
        if len(whatsapp) < 12 or len(whatsapp) > 15:
            return jsonify({'success': False, 'erro': 'Número de WhatsApp inválido'}), 400

        if not whatsapp.startswith('55'):
            return jsonify({'success': False, 'erro': 'Número deve começar com 55 (código do Brasil)'}), 400

        # Verificar se já existe
        existe = db.execute_query("""
            SELECT id FROM numeros_notificacao
            WHERE cliente_nexus_id = %s AND whatsapp = %s
        """, (cliente_nexus_id, whatsapp))

        if existe:
            return jsonify({'success': False, 'erro': 'Este número já está cadastrado'}), 400

        # Inserir
        resultado = db.execute_query("""
            INSERT INTO numeros_notificacao (cliente_nexus_id, nome, whatsapp)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (cliente_nexus_id, nome, whatsapp))

        log_sistema('success', f'Número de notificação adicionado: {nome} - {whatsapp}', 'numeros_notificacao',
                   {'id': resultado[0]['id']})

        return jsonify({
            'success': True,
            'mensagem': 'Número adicionado com sucesso',
            'id': resultado[0]['id']
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@disparo_individual_bp.route('/numeros-notificacao/<int:numero_id>', methods=['PUT'])
@login_required
def atualizar_numero_notificacao(numero_id):
    """Atualiza um número de notificação"""
    try:
        cliente_nexus_id = session.get('usuario_id')
        data = request.get_json()

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        # Verificar se pertence ao cliente
        numero = db.execute_query("""
            SELECT id FROM numeros_notificacao
            WHERE id = %s AND cliente_nexus_id = %s
        """, (numero_id, cliente_nexus_id))

        if not numero:
            return jsonify({'success': False, 'erro': 'Número não encontrado'}), 404

        nome = data.get('nome', '').strip()
        whatsapp = data.get('whatsapp', '').strip()

        if not nome or not whatsapp:
            return jsonify({'success': False, 'erro': 'Nome e WhatsApp são obrigatórios'}), 400

        # Atualizar
        db.execute_update("""
            UPDATE numeros_notificacao
            SET nome = %s, whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (nome, whatsapp, numero_id))

        log_sistema('success', f'Número de notificação atualizado: {nome} - {whatsapp}', 'numeros_notificacao',
                   {'id': numero_id})

        return jsonify({
            'success': True,
            'mensagem': 'Número atualizado com sucesso'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@disparo_individual_bp.route('/numeros-notificacao/<int:numero_id>', methods=['DELETE'])
@login_required
def deletar_numero_notificacao(numero_id):
    """Deleta um número de notificação"""
    try:
        cliente_nexus_id = session.get('usuario_id')

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        # Verificar se pertence ao cliente
        numero = db.execute_query("""
            SELECT id, nome, whatsapp FROM numeros_notificacao
            WHERE id = %s AND cliente_nexus_id = %s
        """, (numero_id, cliente_nexus_id))

        if not numero:
            return jsonify({'success': False, 'erro': 'Número não encontrado'}), 404

        # Deletar
        db.execute_update("""
            DELETE FROM numeros_notificacao
            WHERE id = %s
        """, (numero_id,))

        log_sistema('success', f'Número de notificação deletado: {numero[0]["nome"]} - {numero[0]["whatsapp"]}',
                   'numeros_notificacao', {'id': numero_id})

        return jsonify({
            'success': True,
            'mensagem': 'Número deletado com sucesso'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@disparo_individual_bp.route('/clientes-com-boletos-pendentes', methods=['GET'])
@login_required
def listar_clientes_com_boletos_pendentes():
    """
    Lista todos os clientes que têm boletos com status_envio = 'nao_enviado'
    Retorna dados para popular o select de disparo individual
    """
    try:
        cliente_nexus_id = session.get('usuario_id')

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        # Buscar clientes com boletos pendentes
        query = """
            SELECT
                cf.id,
                cf.nome_completo,
                cf.whatsapp,
                COUNT(b.id) as total_boletos,
                MAX(b.mes_referencia) as mes_referencia,
                MAX(b.ano_referencia) as ano_referencia
            FROM clientes_finais cf
            INNER JOIN boletos b ON b.cliente_final_id = cf.id
            WHERE cf.cliente_nexus_id = %s
                AND cf.ativo = true
                AND b.status_envio = 'nao_enviado'
            GROUP BY cf.id, cf.nome_completo, cf.whatsapp
            ORDER BY cf.nome_completo
        """

        clientes = db.execute_query(query, (cliente_nexus_id,))

        # Formatar dados
        clientes_formatados = []
        for cliente in clientes:
            clientes_formatados.append({
                'id': cliente['id'],
                'nome_completo': cliente['nome_completo'],
                'whatsapp': cliente['whatsapp'],
                'total_boletos': cliente['total_boletos'],
                'mes_referencia': cliente['mes_referencia'],
                'ano_referencia': cliente['ano_referencia']
            })

        return jsonify({
            'success': True,
            'clientes': clientes_formatados,
            'total': len(clientes_formatados)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@disparo_individual_bp.route('/disparar-cliente-especifico', methods=['POST'])
@login_required
def disparar_cliente_especifico():
    """
    Dispara boletos apenas para um cliente específico
    Usado para testes individuais
    """
    try:
        from services.automation_service import enviar_boletos_apenas_disparo

        cliente_nexus_id = session.get('usuario_id')
        data = request.get_json()
        cliente_final_id = data.get('cliente_id')

        if not cliente_nexus_id:
            return jsonify({'success': False, 'erro': 'Cliente não identificado'}), 401

        if not cliente_final_id:
            return jsonify({'success': False, 'erro': 'ID do cliente não fornecido'}), 400

        # Verificar se o cliente pertence ao cliente_nexus logado
        cliente = db.execute_query(
            "SELECT id, nome_completo, whatsapp FROM clientes_finais WHERE id = %s AND cliente_nexus_id = %s",
            (cliente_final_id, cliente_nexus_id)
        )

        if not cliente:
            return jsonify({'success': False, 'erro': 'Cliente não encontrado ou sem permissão'}), 404

        cliente_info = cliente[0]

        if not cliente_info['whatsapp']:
            return jsonify({'success': False, 'erro': 'Cliente não possui WhatsApp cadastrado'}), 400

        # Buscar boletos pendentes do cliente
        boletos = db.execute_query("""
            SELECT
                b.id,
                b.numero_boleto,
                b.valor_original,
                b.data_vencimento,
                b.pdf_path,
                b.pdf_filename,
                cf.nome_completo,
                cf.whatsapp
            FROM boletos b
            INNER JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_final_id = %s
                AND b.cliente_nexus_id = %s
                AND b.status_envio = 'nao_enviado'
            ORDER BY b.data_vencimento
        """, (cliente_final_id, cliente_nexus_id))

        if not boletos:
            return jsonify({
                'success': False,
                'erro': 'Nenhum boleto pendente encontrado para este cliente'
            }), 404

        log_sistema(
            'info',
            f'Iniciando disparo individual para cliente: {cliente_info["nome_completo"]}',
            'disparo_individual',
            {
                'cliente_id': cliente_final_id,
                'cliente_nome': cliente_info['nome_completo'],
                'whatsapp': cliente_info['whatsapp'],
                'total_boletos': len(boletos)
            }
        )

        # Executar disparo apenas para este cliente
        resultado = enviar_boletos_apenas_disparo(
            cliente_nexus_id=cliente_nexus_id,
            cliente_final_id=cliente_final_id
        )

        if resultado.get('enviados', 0) > 0:
            log_sistema(
                'success',
                f'Disparo individual concluído: {resultado.get("enviados")} boleto(s) enviado(s)',
                'disparo_individual',
                {
                    'cliente_id': cliente_final_id,
                    'boletos_enviados': resultado.get('enviados'),
                    'erros': resultado.get('erros')
                }
            )

            return jsonify({
                'success': True,
                'mensagem': f'Boletos enviados com sucesso para {cliente_info["nome_completo"]}',
                'detalhes': {
                    'cliente': cliente_info['nome_completo'],
                    'whatsapp': cliente_info['whatsapp'],
                    'boletos_enviados': resultado.get('enviados', 0),
                    'erros': resultado.get('erros', 0),
                    'mensagem': resultado.get('mensagem', '')
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'erro': resultado.get('mensagem', 'Erro ao enviar boletos'),
                'detalhes': resultado
            }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        log_sistema('error', f'Erro no disparo individual: {str(e)}', 'disparo_individual')
        return jsonify({'success': False, 'erro': str(e)}), 500
