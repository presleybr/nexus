"""
Modelo de WhatsApp Session - Gerencia sessões WhatsApp dos clientes
"""

from typing import Optional, Dict
from datetime import datetime
import json
from .database import execute_query, fetch_one, insert_and_return_id, log_sistema


class WhatsAppSession:
    """Modelo para gerenciamento de sessões WhatsApp"""

    @staticmethod
    def create(cliente_nexus_id: int, instance_name: str) -> int:
        """
        Cria uma nova sessão WhatsApp

        Args:
            cliente_nexus_id: ID do cliente Nexus
            instance_name: Nome da instância (ex: nexus_cliente_1)

        Returns:
            ID da sessão criada
        """
        # Verifica se já existe sessão ativa para este cliente
        sessao_existente = WhatsAppSession.get_by_cliente(cliente_nexus_id)

        if sessao_existente:
            # Atualiza a sessão existente
            query = """
                UPDATE whatsapp_sessions
                SET instance_name = %s,
                    status = 'disconnected',
                    qr_code = NULL,
                    session_data = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cliente_nexus_id = %s
                RETURNING id
            """
            result = execute_query(query, (instance_name, cliente_nexus_id), fetch=True)
            session_id = result[0]['id'] if result else None

            log_sistema('info', f'Sessão WhatsApp atualizada para cliente {cliente_nexus_id}',
                       'whatsapp', {'session_id': session_id})

            return session_id

        # Cria nova sessão
        query = """
            INSERT INTO whatsapp_sessions
            (cliente_nexus_id, instance_name, status)
            VALUES (%s, %s, 'disconnected')
            RETURNING id
        """

        session_id = insert_and_return_id(query, (cliente_nexus_id, instance_name))

        log_sistema('success', f'Sessão WhatsApp criada para cliente {cliente_nexus_id}',
                   'whatsapp', {'session_id': session_id, 'instance_name': instance_name})

        return session_id

    @staticmethod
    def update_qr_code(cliente_nexus_id: int, qr_base64: str) -> bool:
        """
        Atualiza o QR Code da sessão

        Args:
            cliente_nexus_id: ID do cliente
            qr_base64: QR Code em base64

        Returns:
            True se atualizado com sucesso
        """
        query = """
            UPDATE whatsapp_sessions
            SET qr_code = %s,
                status = 'qrcode',
                updated_at = CURRENT_TIMESTAMP
            WHERE cliente_nexus_id = %s
        """

        rows_affected = execute_query(query, (qr_base64, cliente_nexus_id))

        if rows_affected > 0:
            log_sistema('info', f'QR Code atualizado para cliente {cliente_nexus_id}', 'whatsapp')
            return True

        return False

    @staticmethod
    def update_status(cliente_nexus_id: int, status: str) -> bool:
        """
        Atualiza o status da conexão

        Args:
            cliente_nexus_id: ID do cliente
            status: Status (disconnected, qrcode, connecting, connected)

        Returns:
            True se atualizado com sucesso
        """
        # Se está conectando, limpa o QR code
        qr_code_update = ", qr_code = NULL" if status == 'connected' else ""

        # Se está conectando, salva timestamp
        if status == 'connected':
            query = f"""
                UPDATE whatsapp_sessions
                SET status = %s,
                    connected_at = CURRENT_TIMESTAMP,
                    qr_code = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cliente_nexus_id = %s
            """
        elif status == 'disconnected':
            query = f"""
                UPDATE whatsapp_sessions
                SET status = %s,
                    disconnected_at = CURRENT_TIMESTAMP,
                    qr_code = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cliente_nexus_id = %s
            """
        else:
            query = f"""
                UPDATE whatsapp_sessions
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE cliente_nexus_id = %s
            """

        rows_affected = execute_query(query, (status, cliente_nexus_id))

        if rows_affected > 0:
            log_sistema('info', f'Status WhatsApp atualizado para {status}',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return True

        return False

    @staticmethod
    def update_connection(cliente_nexus_id: int, phone_number: str,
                         session_data: Dict = None) -> bool:
        """
        Atualiza dados da conexão quando WhatsApp conecta

        Args:
            cliente_nexus_id: ID do cliente
            phone_number: Número do WhatsApp conectado
            session_data: Dados adicionais da sessão

        Returns:
            True se atualizado com sucesso
        """
        session_json = json.dumps(session_data) if session_data else None

        query = """
            UPDATE whatsapp_sessions
            SET phone_number = %s,
                session_data = %s,
                status = 'connected',
                connected_at = CURRENT_TIMESTAMP,
                qr_code = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE cliente_nexus_id = %s
        """

        rows_affected = execute_query(query, (phone_number, session_json, cliente_nexus_id))

        if rows_affected > 0:
            log_sistema('success', f'WhatsApp conectado: {phone_number}',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return True

        return False

    @staticmethod
    def get_by_cliente(cliente_nexus_id: int) -> Optional[Dict]:
        """
        Busca sessão por cliente

        Args:
            cliente_nexus_id: ID do cliente

        Returns:
            Dict com dados da sessão ou None
        """
        query = """
            SELECT * FROM whatsapp_sessions
            WHERE cliente_nexus_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """

        return fetch_one(query, (cliente_nexus_id,))

    @staticmethod
    def get_by_instance(instance_name: str) -> Optional[Dict]:
        """
        Busca sessão por nome da instância

        Args:
            instance_name: Nome da instância

        Returns:
            Dict com dados da sessão ou None
        """
        query = """
            SELECT * FROM whatsapp_sessions
            WHERE instance_name = %s
            ORDER BY created_at DESC
            LIMIT 1
        """

        return fetch_one(query, (instance_name,))

    @staticmethod
    def delete_session(cliente_nexus_id: int) -> bool:
        """
        Deleta sessão do cliente

        Args:
            cliente_nexus_id: ID do cliente

        Returns:
            True se deletado com sucesso
        """
        query = "DELETE FROM whatsapp_sessions WHERE cliente_nexus_id = %s"

        rows_affected = execute_query(query, (cliente_nexus_id,))

        if rows_affected > 0:
            log_sistema('warning', f'Sessão WhatsApp deletada',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return True

        return False

    @staticmethod
    def is_connected(cliente_nexus_id: int) -> bool:
        """
        Verifica se o cliente tem WhatsApp conectado

        Args:
            cliente_nexus_id: ID do cliente

        Returns:
            True se conectado
        """
        session = WhatsAppSession.get_by_cliente(cliente_nexus_id)

        if session and session.get('status') == 'connected':
            return True

        return False

    @staticmethod
    def get_instance_name(cliente_nexus_id: int) -> Optional[str]:
        """
        Retorna o nome da instância do cliente

        Args:
            cliente_nexus_id: ID do cliente

        Returns:
            Nome da instância ou None
        """
        session = WhatsAppSession.get_by_cliente(cliente_nexus_id)

        if session:
            return session.get('instance_name')

        return None
