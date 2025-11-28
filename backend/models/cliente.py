"""
Modelo de Cliente - Gerencia clientes Nexus e clientes finais
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from .database import execute_query, fetch_one, insert_and_return_id, log_sistema


class ClienteNexus:
    """Modelo para clientes da Nexus (empresários)"""

    @staticmethod
    def criar(nome_empresa: str, cnpj: str, usuario_id: int, whatsapp_numero: str = None) -> int:
        """
        Cria um novo cliente Nexus

        Args:
            nome_empresa: Nome da empresa
            cnpj: CNPJ da empresa
            usuario_id: ID do usuário associado
            whatsapp_numero: Número do WhatsApp

        Returns:
            ID do cliente criado
        """
        query = """
            INSERT INTO clientes_nexus (nome_empresa, cnpj, usuario_id, whatsapp_numero)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """

        cliente_id = insert_and_return_id(query, (nome_empresa, cnpj, usuario_id, whatsapp_numero))

        # Cria configurações padrão para o cliente
        config_query = """
            INSERT INTO configuracoes_cliente (cliente_nexus_id)
            VALUES (%s)
        """
        execute_query(config_query, (cliente_id,))

        log_sistema('success', f'Cliente Nexus criado: {nome_empresa}', 'cliente', {'cliente_id': cliente_id})

        return cliente_id

    @staticmethod
    def buscar_por_id(cliente_id: int) -> Optional[Dict]:
        """Busca cliente por ID"""
        query = """
            SELECT cn.*, u.email
            FROM clientes_nexus cn
            LEFT JOIN usuarios u ON cn.usuario_id = u.id
            WHERE cn.id = %s
        """
        return fetch_one(query, (cliente_id,))

    @staticmethod
    def buscar_por_usuario_id(usuario_id: int) -> Optional[Dict]:
        """Busca cliente pelo ID do usuário"""
        query = """
            SELECT * FROM clientes_nexus
            WHERE usuario_id = %s
        """
        return fetch_one(query, (usuario_id,))

    @staticmethod
    def listar_todos() -> List[Dict]:
        """Lista todos os clientes Nexus"""
        query = """
            SELECT cn.*, u.email,
                   COUNT(DISTINCT b.cliente_final_cpf) as total_clientes_unicos,
                   COUNT(DISTINCT b.id) as total_boletos
            FROM clientes_nexus cn
            LEFT JOIN usuarios u ON cn.usuario_id = u.id
            LEFT JOIN boletos b ON cn.id = b.cliente_nexus_id
            GROUP BY cn.id, u.email
            ORDER BY cn.data_cadastro DESC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def atualizar_whatsapp(cliente_id: int, whatsapp_numero: str, conectado: bool = True):
        """Atualiza informações do WhatsApp"""
        query = """
            UPDATE clientes_nexus
            SET whatsapp_numero = %s, whatsapp_conectado = %s
            WHERE id = %s
        """
        execute_query(query, (whatsapp_numero, conectado, cliente_id))

    @staticmethod
    def atualizar_mensagem_antibloqueio(cliente_id: int, mensagem: str):
        """Atualiza a mensagem anti-bloqueio do cliente"""
        query = """
            UPDATE clientes_nexus
            SET mensagem_antibloqueio = %s
            WHERE id = %s
        """
        execute_query(query, (mensagem, cliente_id))

    @staticmethod
    def get_dashboard_data(cliente_id: int) -> Dict:
        """Retorna dados para o dashboard do cliente"""
        # Query direta ao invés de view (view não existe)
        query = """
            SELECT
                %s as cliente_nexus_id,
                COUNT(*) FILTER (WHERE TRUE) as total_boletos,
                COUNT(*) FILTER (WHERE status_envio = 'enviado') as boletos_enviados,
                COUNT(*) FILTER (WHERE status_envio = 'pendente' OR status_envio = 'nao_enviado') as boletos_pendentes,
                COUNT(*) FILTER (WHERE status = 'vencido') as boletos_vencidos,
                COUNT(*) FILTER (WHERE status = 'pago') as boletos_pagos,
                (SELECT COUNT(*) FROM clientes_finais WHERE cliente_nexus_id = %s AND ativo = true) as total_clientes
            FROM boletos
            WHERE cliente_nexus_id = %s
        """
        data = fetch_one(query, (cliente_id, cliente_id, cliente_id))

        if not data:
            # Retorna estrutura vazia se não houver dados
            return {
                'cliente_nexus_id': cliente_id,
                'total_boletos': 0,
                'boletos_enviados': 0,
                'boletos_pendentes': 0,
                'boletos_vencidos': 0,
                'boletos_pagos': 0,
                'valor_total': 0,
                'valor_pago': 0,
                'valor_pendente': 0,
                'total_disparos': 0,
                'disparos_enviados': 0,
                'disparos_erro': 0,
                'disparos_pendentes': 0,
                'taxa_sucesso_disparos': 0,
                'total_clientes_unicos': 0,
                'ultimos_boletos': [],
                'boletos_proximos_vencimento': []
            }

        # Busca últimos boletos
        boletos_query = """
            SELECT b.*,
                   b.cliente_final_nome as cliente_nome
            FROM boletos b
            WHERE b.cliente_nexus_id = %s
            ORDER BY b.created_at DESC
            LIMIT 10
        """
        ultimos_boletos = execute_query(boletos_query, (cliente_id,), fetch=True)

        # Busca boletos próximos do vencimento (próximos 7 dias)
        proximos_vencimento_query = """
            SELECT b.*,
                   b.cliente_final_nome as cliente_nome
            FROM boletos b
            WHERE b.cliente_nexus_id = %s
            AND b.vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            AND b.status_envio != 'pago'
            ORDER BY b.vencimento ASC
            LIMIT 10
        """
        boletos_proximos = execute_query(proximos_vencimento_query, (cliente_id,), fetch=True)

        data['ultimos_boletos'] = ultimos_boletos or []
        data['boletos_proximos_vencimento'] = boletos_proximos or []

        return data


class ClienteFinal:
    """Modelo para clientes finais (clientes dos empresários)"""

    @staticmethod
    def criar(cliente_nexus_id: int, nome: str, cpf: str, **kwargs) -> int:
        """
        Cria um novo cliente final

        Args:
            cliente_nexus_id: ID do cliente Nexus dono deste cliente
            nome: Nome completo
            cpf: CPF
            **kwargs: telefone, whatsapp, email, endereco, observacoes, numero_contrato, etc.

        Returns:
            ID do cliente criado
        """
        # Gera número de contrato automático se não fornecido
        numero_contrato = kwargs.get('numero_contrato')
        if not numero_contrato:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            numero_contrato = f"CRM-{timestamp[-8:]}"

        query = """
            INSERT INTO clientes_finais
            (cliente_nexus_id, nome_completo, cpf, telefone_celular, whatsapp, email,
             observacoes, numero_contrato, grupo_consorcio, cota_consorcio,
             valor_credito, valor_parcela, prazo_meses, data_adesao,
             status_contrato, origem, cadastrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        params = (
            cliente_nexus_id,
            nome,  # nome_completo
            cpf,
            kwargs.get('telefone'),  # telefone_celular
            kwargs.get('whatsapp'),  # WhatsApp como recebido (mantém formatação)
            kwargs.get('email'),
            kwargs.get('observacoes'),
            numero_contrato,
            kwargs.get('grupo_consorcio', '0'),  # valor padrão
            kwargs.get('cota_consorcio', '0'),   # valor padrão
            kwargs.get('valor_credito', 0.0),    # valor padrão
            kwargs.get('valor_parcela', 0.0),    # valor padrão
            kwargs.get('prazo_meses', 12),       # valor padrão
            kwargs.get('data_adesao', datetime.now().date()),
            kwargs.get('status_contrato', 'ativo'),
            'CRM',  # origem
            'CRM Sistema'  # cadastrado_por
        )

        cliente_id = insert_and_return_id(query, params)

        log_sistema('success', f'Cliente final criado: {nome}', 'cliente_final',
                   {'cliente_id': cliente_id, 'cliente_nexus_id': cliente_nexus_id})

        return cliente_id

    @staticmethod
    def buscar_por_id(cliente_id: int) -> Optional[Dict]:
        """Busca cliente final por ID"""
        query = "SELECT *, nome_completo as nome FROM clientes_finais WHERE id = %s"
        return fetch_one(query, (cliente_id,))

    @staticmethod
    def buscar_por_cpf(cpf: str) -> Optional[Dict]:
        """Busca cliente final por CPF"""
        query = "SELECT *, nome_completo as nome FROM clientes_finais WHERE cpf = %s AND ativo = true"
        return fetch_one(query, (cpf,))

    @staticmethod
    def listar_por_cliente_nexus(cliente_nexus_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Lista clientes finais de um cliente Nexus específico"""
        # Se limit for None, busca todos os clientes
        if limit is None:
            query = """
                SELECT cf.*,
                       cf.nome_completo as nome,
                       COUNT(b.id) as total_boletos,
                       COUNT(CASE WHEN b.status_envio = 'enviado' THEN 1 END) as boletos_enviados
                FROM clientes_finais cf
                LEFT JOIN boletos b ON cf.id = b.cliente_final_id
                WHERE cf.cliente_nexus_id = %s AND cf.ativo = true
                GROUP BY cf.id
                ORDER BY cf.created_at DESC
            """
            return execute_query(query, (cliente_nexus_id,), fetch=True)
        else:
            query = """
                SELECT cf.*,
                       cf.nome_completo as nome,
                       COUNT(b.id) as total_boletos,
                       COUNT(CASE WHEN b.status_envio = 'enviado' THEN 1 END) as boletos_enviados
                FROM clientes_finais cf
                LEFT JOIN boletos b ON cf.id = b.cliente_final_id
                WHERE cf.cliente_nexus_id = %s AND cf.ativo = true
                GROUP BY cf.id
                ORDER BY cf.created_at DESC
                LIMIT %s OFFSET %s
            """
            return execute_query(query, (cliente_nexus_id, limit, offset), fetch=True)

    @staticmethod
    def atualizar(cliente_id: int, **kwargs) -> bool:
        """Atualiza dados do cliente final"""
        # Mapeia campos do CRM para campos da tabela
        mapeamento_campos = {
            'nome': 'nome_completo',
            'telefone': 'telefone_celular',
            'whatsapp': 'whatsapp',
            'email': 'email',
            'observacoes': 'observacoes'
        }

        campos_update = []
        valores = []

        for campo, valor in kwargs.items():
            campo_db = mapeamento_campos.get(campo, campo)
            if campo_db and valor is not None:
                campos_update.append(f"{campo_db} = %s")
                valores.append(valor)

        if not campos_update:
            return False

        valores.append(cliente_id)
        query = f"""
            UPDATE clientes_finais
            SET {', '.join(campos_update)}
            WHERE id = %s
        """

        execute_query(query, tuple(valores))
        return True

    @staticmethod
    def deletar(cliente_id: int) -> bool:
        """Deleta (desativa) um cliente final - soft delete"""
        query = "UPDATE clientes_finais SET ativo = false WHERE id = %s"
        rows_affected = execute_query(query, (cliente_id,))

        if rows_affected > 0:
            log_sistema('warning', f'Cliente final desativado: ID {cliente_id}', 'cliente_final')
            return True
        return False

    @staticmethod
    def buscar_com_filtro(cliente_nexus_id: int, filtro: str = "") -> List[Dict]:
        """
        Busca clientes com filtro por nome, CPF, email ou telefone

        Args:
            cliente_nexus_id: ID do cliente Nexus
            filtro: Termo de busca

        Returns:
            Lista de clientes que correspondem ao filtro
        """
        query = """
            SELECT *, nome_completo as nome FROM clientes_finais
            WHERE cliente_nexus_id = %s AND ativo = true
            AND (
                nome_completo ILIKE %s
                OR cpf LIKE %s
                OR email ILIKE %s
                OR telefone_celular LIKE %s
                OR whatsapp LIKE %s
            )
            ORDER BY nome_completo
        """
        filtro_like = f"%{filtro}%"
        return execute_query(query, (cliente_nexus_id, filtro_like, filtro_like, filtro_like, filtro_like, filtro_like), fetch=True)

    @staticmethod
    def contar_por_cliente_nexus(cliente_nexus_id: int) -> int:
        """Conta total de clientes finais de um cliente Nexus"""
        query = "SELECT COUNT(*) as total FROM clientes_finais WHERE cliente_nexus_id = %s AND ativo = true"
        result = fetch_one(query, (cliente_nexus_id,))
        return result['total'] if result else 0


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro

    Args:
        cpf: CPF com ou sem formatação

    Returns:
        True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)

    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False

    # Calcula o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10

    # Calcula o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10

    # Verifica se os dígitos calculados conferem
    return cpf[-2:] == f"{digito1}{digito2}"


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro

    Args:
        cnpj: CNPJ com ou sem formatação

    Returns:
        True se válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)

    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False

    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False

    # Calcula o primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    digito1 = 0 if soma % 11 < 2 else 11 - (soma % 11)

    # Calcula o segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    digito2 = 0 if soma % 11 < 2 else 11 - (soma % 11)

    # Verifica se os dígitos calculados conferem
    return cnpj[-2:] == f"{digito1}{digito2}"


def formatar_cpf(cpf: str) -> str:
    """Formata CPF para XXX.XXX.XXX-XX"""
    cpf = re.sub(r'\D', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ para XX.XXX.XXX/XXXX-XX"""
    cnpj = re.sub(r'\D', '', cnpj)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
