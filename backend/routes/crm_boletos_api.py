"""
API de Boletos - Endpoints para gestão de boletos
"""
from flask import Blueprint, jsonify, request, session
from routes.auth import login_required
from models.database import DatabaseConnection
import logging

logger = logging.getLogger(__name__)
db = DatabaseConnection()

boletos_api_bp = Blueprint('boletos_api', __name__, url_prefix='/api/boletos')


@boletos_api_bp.route('/resumo', methods=['GET'])
@login_required
def resumo_boletos():
    """
    Retorna resumo geral de boletos
    - Total de clientes
    - Boletos baixados
    - Boletos com erro
    - Boletos enviados via WhatsApp
    """
    try:
        # Total de clientes finais ativos
        total_clientes = db.execute_query("""
            SELECT COUNT(DISTINCT cpf) as total
            FROM clientes_finais
            WHERE ativo = TRUE
        """)

        # Boletos baixados com sucesso (DISTINCT por CPF)
        baixados = db.execute_query("""
            SELECT COUNT(DISTINCT cpf) as total
            FROM downloads_canopus
            WHERE status = 'sucesso'
        """)

        # Boletos com erro (DISTINCT por CPF)
        erros = db.execute_query("""
            SELECT COUNT(DISTINCT cpf) as total
            FROM downloads_canopus
            WHERE status IN ('erro', 'sem_boleto')
        """)

        # Boletos enviados via WhatsApp
        enviados = db.execute_query("""
            SELECT COUNT(DISTINCT cliente_final_id) as total
            FROM boletos
            WHERE status_envio = 'enviado'
        """)

        # Pendentes de envio (baixados mas não enviados)
        pendentes_envio = db.execute_query("""
            SELECT COUNT(DISTINCT cliente_final_id) as total
            FROM boletos
            WHERE status_envio IN ('nao_enviado', 'pendente')
        """)

        return jsonify({
            'success': True,
            'total_clientes': total_clientes[0]['total'] if total_clientes else 0,
            'baixados': baixados[0]['total'] if baixados else 0,
            'erros': erros[0]['total'] if erros else 0,
            'enviados': enviados[0]['total'] if enviados else 0,
            'pendentes_envio': pendentes_envio[0]['total'] if pendentes_envio else 0
        })

    except Exception as e:
        logger.error(f"Erro ao buscar resumo de boletos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@boletos_api_bp.route('/baixados', methods=['GET'])
@login_required
def listar_boletos_baixados():
    """
    Lista boletos baixados com sucesso
    Query params:
    - page: número da página (default 1)
    - limit: itens por página (default 20)
    - status_envio: filtro por status de envio (todos, enviado, nao_enviado)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status_envio_filter = request.args.get('status_envio', 'todos')

        offset = (page - 1) * limit

        # Query base
        where_clause = "WHERE dc.status = 'sucesso'"

        # Aplicar filtro de status_envio se não for 'todos'
        if status_envio_filter != 'todos':
            if status_envio_filter == 'enviado':
                where_clause += " AND b.status_envio = 'enviado'"
            elif status_envio_filter == 'nao_enviado':
                where_clause += " AND (b.status_envio = 'nao_enviado' OR b.status_envio IS NULL OR b.status_envio = 'pendente')"

        # Buscar boletos baixados
        boletos = db.execute_query(f"""
            SELECT DISTINCT ON (dc.cpf, dc.nome_arquivo)
                dc.id,
                dc.cpf,
                dc.nome_arquivo,
                dc.caminho_arquivo,
                dc.tamanho_bytes,
                dc.status,
                dc.data_download,
                cf.nome_completo as cliente_nome,
                b.valor_original,
                b.data_vencimento,
                b.status_envio,
                b.pdf_filename
            FROM downloads_canopus dc
            LEFT JOIN clientes_finais cf ON dc.cpf = cf.cpf
            LEFT JOIN LATERAL (
                SELECT valor_original, data_vencimento, status_envio, pdf_filename
                FROM boletos
                WHERE boletos.cliente_final_id = cf.id
                ORDER BY created_at DESC
                LIMIT 1
            ) b ON true
            {where_clause}
            ORDER BY dc.cpf, dc.nome_arquivo, dc.data_download DESC
            LIMIT {limit} OFFSET {offset}
        """)

        # Contar total
        total = db.execute_query(f"""
            SELECT COUNT(DISTINCT dc.cpf) as total
            FROM downloads_canopus dc
            LEFT JOIN clientes_finais cf ON dc.cpf = cf.cpf
            LEFT JOIN LATERAL (
                SELECT status_envio
                FROM boletos
                WHERE boletos.cliente_final_id = cf.id
                ORDER BY created_at DESC
                LIMIT 1
            ) b ON true
            {where_clause}
        """)

        total_count = total[0]['total'] if total else 0
        total_pages = (total_count + limit - 1) // limit

        # Formatar boletos
        boletos_formatados = []
        for boleto in boletos:
            boletos_formatados.append({
                'id': boleto['id'],
                'cliente_nome': boleto['cliente_nome'],
                'cpf': boleto['cpf'],
                'valor': float(boleto['valor_original']) if boleto['valor_original'] else 0,
                'vencimento': boleto['data_vencimento'].strftime('%d/%m/%Y') if boleto['data_vencimento'] else 'N/A',
                'arquivo_nome': boleto['nome_arquivo'],
                'tamanho': boleto['tamanho_bytes'],
                'status_envio': boleto['status_envio'] or 'nao_enviado',
                'data_download': boleto['data_download'].isoformat() if boleto['data_download'] else None
            })

        return jsonify({
            'success': True,
            'boletos': boletos_formatados,
            'total': total_count,
            'pagina': page,
            'total_paginas': total_pages
        })

    except Exception as e:
        logger.error(f"Erro ao listar boletos baixados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@boletos_api_bp.route('/erros/sem-boleto', methods=['GET'])
@login_required
def listar_erros_sem_boleto():
    """
    Lista clientes que retornaram 'sem boleto' na automação
    """
    try:
        erros = db.execute_query("""
            SELECT DISTINCT ON (dc.cpf)
                dc.cpf,
                cf.nome_completo as nome,
                cf.grupo_cota,
                dc.data_download as data_verificacao,
                dc.mensagem_erro
            FROM downloads_canopus dc
            LEFT JOIN clientes_finais cf ON dc.cpf = cf.cpf
            WHERE dc.status = 'sem_boleto'
            ORDER BY dc.cpf, dc.data_download DESC
        """)

        clientes = []
        for erro in erros:
            clientes.append({
                'cpf': erro['cpf'],
                'nome': erro['nome'],
                'grupo_cota': erro['grupo_cota'],
                'data_verificacao': erro['data_verificacao'].isoformat() if erro['data_verificacao'] else None,
                'mensagem': erro['mensagem_erro']
            })

        return jsonify({
            'success': True,
            'clientes': clientes,
            'total': len(clientes)
        })

    except Exception as e:
        logger.error(f"Erro ao listar erros sem boleto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@boletos_api_bp.route('/erros/cpf-nao-encontrado', methods=['GET'])
@login_required
def listar_erros_cpf_nao_encontrado():
    """
    Lista clientes cujo CPF não foi encontrado no sistema Canopus
    """
    try:
        erros = db.execute_query("""
            SELECT DISTINCT ON (dc.cpf)
                dc.cpf,
                cf.nome_completo as nome_planilha,
                dc.data_download as data_verificacao,
                dc.mensagem_erro
            FROM downloads_canopus dc
            LEFT JOIN clientes_finais cf ON dc.cpf = cf.cpf
            WHERE dc.status = 'erro'
              AND (dc.mensagem_erro LIKE '%CPF não encontrado%'
                   OR dc.mensagem_erro LIKE '%Nenhum resultado%')
            ORDER BY dc.cpf, dc.data_download DESC
        """)

        clientes = []
        for erro in erros:
            clientes.append({
                'cpf': erro['cpf'],
                'nome_planilha': erro['nome_planilha'],
                'data_verificacao': erro['data_verificacao'].isoformat() if erro['data_verificacao'] else None,
                'mensagem': erro['mensagem_erro']
            })

        return jsonify({
            'success': True,
            'clientes': clientes,
            'total': len(clientes)
        })

    except Exception as e:
        logger.error(f"Erro ao listar erros de CPF não encontrado: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500


@boletos_api_bp.route('/historico', methods=['GET'])
@login_required
def listar_historico():
    """
    Lista histórico de execuções de automação
    """
    try:
        execucoes = db.execute_query("""
            SELECT
                id,
                tipo,
                total_clientes,
                total_downloads,
                total_erros,
                inicio,
                fim,
                EXTRACT(EPOCH FROM (fim - inicio)) as duracao_segundos
            FROM execucoes_automacao
            ORDER BY inicio DESC
            LIMIT 50
        """)

        historico = []
        for exec in execucoes:
            duracao_min = int(exec['duracao_segundos'] / 60) if exec['duracao_segundos'] else 0

            historico.append({
                'data': exec['inicio'].isoformat() if exec['inicio'] else None,
                'tipo': exec['tipo'],
                'total': exec['total_clientes'],
                'sucesso': exec['total_downloads'],
                'erros': exec['total_erros'],
                'duracao': f"{duracao_min}min"
            })

        return jsonify({
            'success': True,
            'execucoes': historico
        })

    except Exception as e:
        logger.error(f"Erro ao listar histórico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'erro': str(e)}), 500
