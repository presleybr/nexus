"""
Serviço para enviar boleto modelo para clientes via WhatsApp
Sistema Nexus CRM - Portal Consórcio
Usa o modelo-boleto.pdf e envia para todos os clientes
"""

import os
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BoletoModeloService:
    """Serviço para enviar boleto modelo para clientes"""

    def __init__(self):
        self.boletos_dir = 'boletos'
        self.modelo_path = os.path.join(self.boletos_dir, 'modelo-boleto.pdf')
        os.makedirs(self.boletos_dir, exist_ok=True)

    def verificar_modelo_existe(self):
        """Verifica se o arquivo modelo existe"""
        if not os.path.exists(self.modelo_path):
            logger.error(f"[ERROR] Arquivo modelo não encontrado: {self.modelo_path}")
            return False
        return True

    def preparar_boleto_para_cliente(self, cliente_final):
        """
        Prepara uma cópia do boleto modelo para envio ao cliente

        Args:
            cliente_final: Dicionário com dados do cliente

        Returns:
            Dicionário com caminho do arquivo preparado
        """
        try:
            # Verificar se modelo existe
            if not self.verificar_modelo_existe():
                return {
                    'success': False,
                    'error': 'Arquivo modelo-boleto.pdf não encontrado na pasta boletos/'
                }

            # Nome do arquivo para o cliente
            cpf_limpo = cliente_final['cpf'].replace('.', '').replace('-', '')
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"boleto_modelo_{cpf_limpo}_{timestamp}.pdf"
            filepath = os.path.join(self.boletos_dir, filename)

            # Copiar modelo para novo arquivo
            shutil.copy(self.modelo_path, filepath)

            file_size = os.path.getsize(filepath)

            logger.info(f"[OK] Boleto modelo preparado para {cliente_final['nome_completo']}: {filename}")

            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'usando_modelo': True
            }

        except Exception as e:
            logger.error(f"[ERROR] Erro ao preparar boleto modelo: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def enviar_modelo_para_todos_clientes(self, cliente_nexus_id, mensagem_personalizada=None):
        """
        Envia o boleto modelo para todos os clientes ativos do consórcio

        Args:
            cliente_nexus_id: ID do cliente Nexus (empresa)
            mensagem_personalizada: Mensagem opcional para enviar junto com o boleto

        Returns:
            Dicionário com resultado dos envios
        """
        try:
            import requests
            import base64
            from backend.models.database import db
            from services.mensagens_personalizadas import mensagens_service

            # Verificar se modelo existe
            if not self.verificar_modelo_existe():
                return {
                    'success': False,
                    'error': 'Arquivo modelo-boleto.pdf não encontrado'
                }

            # Buscar todos os clientes finais ativos com WhatsApp
            clientes = db.execute_query("""
                SELECT id, nome_completo, cpf, whatsapp, numero_contrato
                FROM clientes_finais
                WHERE cliente_nexus_id = %s AND ativo = true AND whatsapp IS NOT NULL
                ORDER BY nome_completo
            """, (cliente_nexus_id,))

            if not clientes:
                return {
                    'success': False,
                    'error': 'Nenhum cliente ativo com WhatsApp encontrado'
                }

            # Buscar nome da empresa
            cliente_nexus_data = db.execute_query(
                "SELECT nome_empresa FROM clientes_nexus WHERE id = %s",
                (cliente_nexus_id,)
            )
            nome_empresa = cliente_nexus_data[0]['nome_empresa'] if cliente_nexus_data else 'Cred MS'

            resultados = []
            total_enviados = 0
            total_erros = 0

            # Ler o PDF modelo uma vez
            with open(self.modelo_path, 'rb') as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

            # Enviar para cada cliente
            for cliente in clientes:
                try:
                    # Preparar número WhatsApp
                    whatsapp_numero = cliente['whatsapp'].replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

                    # Gerar mensagem personalizada e aleatória
                    if mensagem_personalizada:
                        # Se tiver mensagem personalizada, usa ela com o nome do cliente
                        primeiro_nome = cliente['nome_completo'].split()[0]
                        mensagem = mensagem_personalizada.replace('{nome}', primeiro_nome)
                    else:
                        # Usa uma das 10 mensagens aleatórias
                        mensagem = mensagens_service.gerar_mensagem_boleto(
                            dados_cliente=cliente,
                            dados_boleto={'valor_original': 0, 'data_vencimento': 'Conforme boleto'},
                            nome_empresa=nome_empresa
                        )

                    # Enviar mensagem
                    payload_msg = {
                        'phone': whatsapp_numero,
                        'message': mensagem
                    }

                    response_msg = requests.post('http://localhost:3001/send-text', json=payload_msg, timeout=10)

                    if not response_msg.ok:
                        raise Exception(f"Erro ao enviar mensagem: {response_msg.text}")

                    # Pequeno delay antes de enviar o PDF
                    import time
                    time.sleep(2)

                    # Enviar PDF
                    payload_doc = {
                        'phone': whatsapp_numero,
                        'file': pdf_base64,
                        'filename': 'boleto.pdf',
                        'caption': '📄 *Boleto Cred MS*\n\n💚 Seu parceiro de confiança!'
                    }

                    response_doc = requests.post('http://localhost:3001/send-file', json=payload_doc, timeout=30)

                    if not response_doc.ok:
                        raise Exception(f"Erro ao enviar PDF: {response_doc.text}")

                    resultados.append({
                        'cliente_id': cliente['id'],
                        'nome': cliente['nome_completo'],
                        'whatsapp': cliente['whatsapp'],
                        'status': 'enviado',
                        'erro': None
                    })

                    total_enviados += 1
                    logger.info(f"[OK] Boleto modelo enviado para {cliente['nome_completo']} ({cliente['whatsapp']})")

                    # Delay entre envios para evitar bloqueio
                    time.sleep(5)

                except Exception as e:
                    resultados.append({
                        'cliente_id': cliente['id'],
                        'nome': cliente['nome_completo'],
                        'whatsapp': cliente['whatsapp'],
                        'status': 'erro',
                        'erro': str(e)
                    })
                    total_erros += 1
                    logger.error(f"[ERROR] Erro ao enviar para {cliente['nome_completo']}: {str(e)}")

            return {
                'success': True,
                'total_clientes': len(clientes),
                'total_enviados': total_enviados,
                'total_erros': total_erros,
                'resultados': resultados
            }

        except Exception as e:
            logger.error(f"[ERROR] Erro no envio em massa: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# Instância global
boleto_modelo_service = BoletoModeloService()
