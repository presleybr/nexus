"""
Modelo de Boleto - Gerencia boletos e disparos
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from .database import execute_query, fetch_one, insert_and_return_id, execute_many, log_sistema


class Boleto:
    """Modelo para gerenciamento de boletos"""

    @staticmethod
    def criar(cliente_nexus_id: int, cliente_final_id: int, mes_referencia: str,
              valor: float, vencimento: date, pdf_path: str = None) -> int:
        """
        Cria um novo boleto

        Args:
            cliente_nexus_id: ID do cliente Nexus
            cliente_final_id: ID do cliente final
            mes_referencia: Mês de referência (ex: "Janeiro/2024")
            valor: Valor do boleto
            vencimento: Data de vencimento
            pdf_path: Caminho do PDF gerado

        Returns:
            ID do boleto criado
        """
        query = """
            INSERT INTO boletos
            (cliente_nexus_id, cliente_final_id, mes_referencia, valor, vencimento, pdf_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        boleto_id = insert_and_return_id(
            query,
            (cliente_nexus_id, cliente_final_id, mes_referencia, valor, vencimento, pdf_path)
        )

        log_sistema('info', f'Boleto criado: R$ {valor:.2f} - {mes_referencia}',
                   'boleto', {'boleto_id': boleto_id})

        return boleto_id

    @staticmethod
    def criar_em_lote(boletos_data: List[Dict]) -> int:
        """
        Cria múltiplos boletos de uma vez (Schema Portal Consórcio)

        Args:
            boletos_data: Lista de dicionários com dados dos boletos
                Campos obrigatórios:
                - cliente_nexus_id, cliente_final_id
                - numero_boleto, valor_original, data_vencimento, data_emissao
                - mes_referencia (int), ano_referencia (int), numero_parcela (int)

        Returns:
            Quantidade de boletos criados
        """
        query = """
            INSERT INTO boletos
            (cliente_nexus_id, cliente_final_id, numero_boleto,
             valor_original, data_vencimento, data_emissao,
             mes_referencia, ano_referencia, numero_parcela,
             pdf_path, status, status_envio, gerado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params_list = [
            (
                b['cliente_nexus_id'],
                b['cliente_final_id'],
                b['numero_boleto'],
                b['valor_original'],
                b['data_vencimento'],
                b.get('data_emissao', date.today()),
                b['mes_referencia'],  # int
                b['ano_referencia'],  # int
                b.get('numero_parcela', 1),
                b.get('pdf_path'),
                b.get('status', 'pendente'),
                b.get('status_envio', 'nao_enviado'),
                b.get('gerado_por', 'automatico')
            )
            for b in boletos_data
        ]

        total = execute_many(query, params_list)

        log_sistema('success', f'{total} boletos criados em lote', 'boleto')

        return total

    @staticmethod
    def buscar_por_id(boleto_id: int) -> Optional[Dict]:
        """Busca boleto por ID"""
        query = """
            SELECT b.*, cf.nome as cliente_nome, cf.whatsapp, cn.nome_empresa
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            LEFT JOIN clientes_nexus cn ON b.cliente_nexus_id = cn.id
            WHERE b.id = %s
        """
        return fetch_one(query, (boleto_id,))

    @staticmethod
    def listar_por_cliente_nexus(cliente_nexus_id: int, mes_referencia: str = None,
                                 status_envio: str = None, limit: int = 100) -> List[Dict]:
        """
        Lista boletos de um cliente Nexus com filtros opcionais

        Args:
            cliente_nexus_id: ID do cliente Nexus
            mes_referencia: Filtrar por mês (opcional)
            status_envio: Filtrar por status (opcional)
            limit: Limite de resultados

        Returns:
            Lista de boletos
        """
        conditions = ["b.cliente_nexus_id = %s"]
        params = [cliente_nexus_id]

        if mes_referencia:
            conditions.append("b.mes_referencia = %s")
            params.append(mes_referencia)

        if status_envio:
            conditions.append("b.status_envio = %s")
            params.append(status_envio)

        params.append(limit)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT b.*, cf.nome as cliente_nome, cf.whatsapp
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE {where_clause}
            ORDER BY b.created_at DESC
            LIMIT %s
        """

        return execute_query(query, tuple(params), fetch=True)

    @staticmethod
    def listar_pendentes(cliente_nexus_id: int) -> List[Dict]:
        """Lista boletos pendentes de envio"""
        query = """
            SELECT b.*, cf.nome as cliente_nome, cf.whatsapp
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_nexus_id = %s AND b.status_envio = 'pendente'
            ORDER BY b.vencimento ASC
        """
        return execute_query(query, (cliente_nexus_id,), fetch=True)

    @staticmethod
    def atualizar_status_envio(boleto_id: int, status: str, data_envio: datetime = None):
        """
        Atualiza status de envio do boleto

        Args:
            boleto_id: ID do boleto
            status: Novo status (pendente, enviado, erro)
            data_envio: Data/hora do envio
        """
        if data_envio is None:
            data_envio = datetime.now()

        query = """
            UPDATE boletos
            SET status_envio = %s, data_envio = %s
            WHERE id = %s
        """
        execute_query(query, (status, data_envio, boleto_id))

    @staticmethod
    def atualizar_pdf_path(boleto_id: int, pdf_path: str):
        """Atualiza o caminho do PDF do boleto"""
        query = "UPDATE boletos SET pdf_path = %s WHERE id = %s"
        execute_query(query, (pdf_path, boleto_id))

    @staticmethod
    def get_estatisticas(cliente_nexus_id: int, mes_referencia: str = None) -> Dict:
        """
        Retorna estatísticas de boletos

        Args:
            cliente_nexus_id: ID do cliente Nexus
            mes_referencia: Filtrar por mês (opcional)

        Returns:
            Dicionário com estatísticas
        """
        where_clause = "WHERE cliente_nexus_id = %s"
        params = [cliente_nexus_id]

        if mes_referencia:
            where_clause += " AND mes_referencia = %s"
            params.append(mes_referencia)

        query = f"""
            SELECT
                COUNT(*) as total_boletos,
                COUNT(CASE WHEN status_envio = 'enviado' THEN 1 END) as enviados,
                COUNT(CASE WHEN status_envio = 'pendente' THEN 1 END) as pendentes,
                COUNT(CASE WHEN status_envio = 'erro' THEN 1 END) as erros,
                COALESCE(SUM(valor), 0) as valor_total,
                COALESCE(SUM(CASE WHEN status_envio = 'enviado' THEN valor END), 0) as valor_enviado
            FROM boletos
            {where_clause}
        """

        return fetch_one(query, tuple(params)) or {}

    @staticmethod
    def deletar(boleto_id: int) -> bool:
        """Deleta um boleto"""
        query = "DELETE FROM boletos WHERE id = %s"
        rows_affected = execute_query(query, (boleto_id,))
        return rows_affected > 0


class Disparo:
    """Modelo para gerenciamento de disparos de WhatsApp"""

    @staticmethod
    def criar(boleto_id: int, cliente_final_id: int, cliente_nexus_id: int,
              mensagem_enviada: str = None) -> int:
        """Cria um novo registro de disparo"""
        query = """
            INSERT INTO disparos
            (boleto_id, cliente_final_id, cliente_nexus_id, mensagem_enviada)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """

        return insert_and_return_id(
            query,
            (boleto_id, cliente_final_id, cliente_nexus_id, mensagem_enviada)
        )

    @staticmethod
    def atualizar_status(disparo_id: int, status: str, erro_mensagem: str = None):
        """
        Atualiza o status de um disparo

        Args:
            disparo_id: ID do disparo
            status: Novo status (pendente, enviado, erro, cancelado)
            erro_mensagem: Mensagem de erro (se houver)
        """
        query = """
            UPDATE disparos
            SET status = %s, erro_mensagem = %s, data_disparo = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        execute_query(query, (status, erro_mensagem, disparo_id))

    @staticmethod
    def listar_por_cliente_nexus(cliente_nexus_id: int, status: str = None,
                                 limit: int = 100) -> List[Dict]:
        """Lista disparos de um cliente Nexus"""
        where_clause = "WHERE d.cliente_nexus_id = %s"
        params = [cliente_nexus_id]

        if status:
            where_clause += " AND d.status = %s"
            params.append(status)

        params.append(limit)

        query = f"""
            SELECT d.*, cf.nome as cliente_nome, b.mes_referencia, b.valor
            FROM disparos d
            LEFT JOIN clientes_finais cf ON d.cliente_final_id = cf.id
            LEFT JOIN boletos b ON d.boleto_id = b.id
            {where_clause}
            ORDER BY d.created_at DESC
            LIMIT %s
        """

        return execute_query(query, tuple(params), fetch=True)

    @staticmethod
    def contar_por_status(cliente_nexus_id: int) -> Dict:
        """Conta disparos por status"""
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'enviado' THEN 1 END) as enviados,
                COUNT(CASE WHEN status = 'pendente' THEN 1 END) as pendentes,
                COUNT(CASE WHEN status = 'erro' THEN 1 END) as erros
            FROM disparos
            WHERE cliente_nexus_id = %s
        """

        return fetch_one(query, (cliente_nexus_id,)) or {}

    @staticmethod
    def get_historico_disparos(cliente_nexus_id: int, dias: int = 30) -> List[Dict]:
        """
        Retorna histórico de disparos dos últimos N dias

        Args:
            cliente_nexus_id: ID do cliente Nexus
            dias: Número de dias para o histórico

        Returns:
            Lista com estatísticas diárias
        """
        query = """
            SELECT
                DATE(data_disparo) as data,
                COUNT(*) as total_disparos,
                COUNT(CASE WHEN status = 'enviado' THEN 1 END) as sucesso,
                COUNT(CASE WHEN status = 'erro' THEN 1 END) as erros
            FROM disparos
            WHERE cliente_nexus_id = %s
                AND data_disparo >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(data_disparo)
            ORDER BY data DESC
        """

        return execute_query(query, (cliente_nexus_id, dias), fetch=True)


class Configuracao:
    """Modelo para configurações do cliente"""

    @staticmethod
    def buscar(cliente_nexus_id: int) -> Optional[Dict]:
        """Busca configurações de um cliente"""
        query = "SELECT * FROM configuracoes_cliente WHERE cliente_nexus_id = %s"
        return fetch_one(query, (cliente_nexus_id,))

    @staticmethod
    def atualizar(cliente_nexus_id: int, **kwargs):
        """
        Atualiza configurações do cliente

        Campos disponíveis:
        - mensagem_antibloqueio
        - data_disparo_automatico
        - hora_disparo_automatico
        - intervalo_disparos
        - disparo_automatico_ativo
        """
        campos_validos = [
            'mensagem_antibloqueio',
            'data_disparo_automatico',
            'hora_disparo_automatico',
            'intervalo_disparos',
            'disparo_automatico_ativo'
        ]

        campos_update = []
        valores = []

        for campo, valor in kwargs.items():
            if campo in campos_validos:
                campos_update.append(f"{campo} = %s")
                valores.append(valor)

        if not campos_update:
            return False

        valores.append(cliente_nexus_id)

        query = f"""
            UPDATE configuracoes_cliente
            SET {', '.join(campos_update)}
            WHERE cliente_nexus_id = %s
        """

        execute_query(query, tuple(valores))
        return True
