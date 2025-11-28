import requests
import time
import random
import os
from typing import Optional, Dict, Any

class WhatsAppBaileys:
    """
    Serviço para integração com WhatsApp usando Baileys (servidor Node.js local)
    """

    def __init__(self):
        self.base_url = os.getenv('BAILEYS_URL', 'http://localhost:3000')
        self.timeout = 30

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Faz requisição HTTP para o servidor Baileys
        """
        try:
            url = f"{self.base_url}{endpoint}"

            if method == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Servidor Baileys não está respondendo. Certifique-se de que o servidor Node.js está rodando.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout ao conectar com servidor Baileys'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erro na requisição: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro inesperado: {str(e)}'
            }

    def conectar(self) -> Dict[str, Any]:
        """
        Inicia conexão com WhatsApp e gera QR Code

        Returns:
            dict: {'success': bool, 'message': str}
        """
        return self._make_request('POST', '/connect')

    def obter_qr(self) -> Dict[str, Any]:
        """
        Obtém QR Code em formato base64

        Returns:
            dict: {'success': bool, 'qr': str (base64), 'connected': bool}
        """
        return self._make_request('GET', '/qr')

    def verificar_status(self) -> Dict[str, Any]:
        """
        Verifica status da conexão com WhatsApp

        Returns:
            dict: {'connected': bool, 'status': str, 'phone': str}
        """
        return self._make_request('GET', '/status')

    def esta_conectado(self) -> bool:
        """
        Verifica se está conectado ao WhatsApp

        Returns:
            bool: True se conectado, False caso contrário
        """
        try:
            status = self.verificar_status()
            return status.get('connected', False)
        except Exception:
            return False

    def formatar_telefone(self, telefone: str) -> str:
        """
        Formata número de telefone removendo caracteres especiais

        Args:
            telefone: Telefone no formato +55 67 99988-7766 ou similar

        Returns:
            str: Telefone formatado (ex: 5567999887766)
        """
        # Remove todos os caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Se não começar com 55 (código do Brasil), adiciona
        if not telefone_limpo.startswith('55') and len(telefone_limpo) == 11:
            telefone_limpo = '55' + telefone_limpo

        return telefone_limpo

    def enviar_mensagem(self, telefone: str, mensagem: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto via WhatsApp

        Args:
            telefone: Número do telefone (com ou sem formatação)
            mensagem: Texto da mensagem

        Returns:
            dict: {'success': bool, 'message': str}
        """
        telefone_formatado = self.formatar_telefone(telefone)

        data = {
            "phone": telefone_formatado,
            "message": mensagem
        }

        return self._make_request('POST', '/send-text', data)

    def enviar_pdf(self, telefone: str, caminho_pdf: str, caption: str = "", filename: str = "boleto.pdf") -> Dict[str, Any]:
        """
        Envia arquivo PDF via WhatsApp

        Args:
            telefone: Número do telefone
            caminho_pdf: Caminho completo do arquivo PDF
            caption: Legenda/descrição do arquivo
            filename: Nome do arquivo a ser exibido

        Returns:
            dict: {'success': bool, 'message': str}
        """
        telefone_formatado = self.formatar_telefone(telefone)

        # Verifica se arquivo existe
        if not os.path.exists(caminho_pdf):
            return {
                'success': False,
                'error': f'Arquivo não encontrado: {caminho_pdf}'
            }

        data = {
            "phone": telefone_formatado,
            "filePath": caminho_pdf,
            "caption": caption,
            "filename": filename
        }

        return self._make_request('POST', '/send-file', data)

    def enviar_imagem(self, telefone: str, caminho_imagem: str, caption: str = "") -> Dict[str, Any]:
        """
        Envia imagem via WhatsApp

        Args:
            telefone: Número do telefone
            caminho_imagem: Caminho completo da imagem
            caption: Legenda da imagem

        Returns:
            dict: {'success': bool, 'message': str}
        """
        telefone_formatado = self.formatar_telefone(telefone)

        # Verifica se arquivo existe
        if not os.path.exists(caminho_imagem):
            return {
                'success': False,
                'error': f'Imagem não encontrada: {caminho_imagem}'
            }

        data = {
            "phone": telefone_formatado,
            "filePath": caminho_imagem,
            "caption": caption
        }

        return self._make_request('POST', '/send-image', data)

    def enviar_boleto_completo(self, telefone: str, pdf_path: str, mensagem_antibloqueio: str,
                              delay_min: int = 3, delay_max: int = 7) -> Dict[str, Any]:
        """
        Envia mensagem + PDF com delay anti-bloqueio

        Args:
            telefone: Número do telefone
            pdf_path: Caminho do PDF do boleto
            mensagem_antibloqueio: Mensagem personalizada antes do PDF
            delay_min: Delay mínimo em segundos (padrão: 3)
            delay_max: Delay máximo em segundos (padrão: 7)

        Returns:
            dict: {'success': bool, 'message': str, 'steps': dict}
        """
        resultados = {
            'mensagem': None,
            'delay': None,
            'pdf': None
        }

        # 1. Enviar mensagem de texto
        result_msg = self.enviar_mensagem(telefone, mensagem_antibloqueio)
        resultados['mensagem'] = result_msg

        if not result_msg.get('success'):
            return {
                'success': False,
                'error': 'Falha ao enviar mensagem de texto',
                'steps': resultados
            }

        # 2. Delay aleatório (anti-bloqueio)
        delay = random.randint(delay_min, delay_max)
        resultados['delay'] = delay
        time.sleep(delay)

        # 3. Enviar PDF
        result_pdf = self.enviar_pdf(telefone, pdf_path, "Segue anexo em PDF", "boleto.pdf")
        resultados['pdf'] = result_pdf

        if not result_pdf.get('success'):
            return {
                'success': False,
                'error': 'Falha ao enviar PDF',
                'steps': resultados
            }

        return {
            'success': True,
            'message': 'Mensagem e PDF enviados com sucesso',
            'steps': resultados
        }

    def desconectar(self) -> Dict[str, Any]:
        """
        Desconecta do WhatsApp e limpa sessão

        Returns:
            dict: {'success': bool, 'message': str}
        """
        return self._make_request('POST', '/logout')


# Instância global do serviço
whatsapp_service = WhatsAppBaileys()
