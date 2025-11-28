"""
Serviço de Integração com Evolution API
Gerencia instâncias WhatsApp, envio de mensagens e disparos em massa
"""

import requests
import base64
import time
import random
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class EvolutionAPIService:
    """Classe para integração com Evolution API"""

    def __init__(self):
        """Inicializa o serviço com configurações"""
        self.base_url = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
        self.api_key = os.getenv('EVOLUTION_API_KEY', 'nexus-evolution-key-2025')
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Tuple[bool, Dict]:
        """
        Faz requisição HTTP para a Evolution API

        Args:
            method: GET, POST, DELETE, etc
            endpoint: Endpoint da API (sem base_url)
            data: Dados JSON para enviar

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            else:
                return False, {'error': f'Método HTTP inválido: {method}'}

            # Verifica se foi sucesso (2xx)
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return True, response.json()
                except:
                    return True, {'message': 'Sucesso', 'status_code': response.status_code}
            else:
                logger.error(f"Erro na API Evolution: {response.status_code} - {response.text}")
                return False, {'error': response.text, 'status_code': response.status_code}

        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao chamar Evolution API: {endpoint}")
            return False, {'error': 'Timeout na requisição'}
        except requests.exceptions.ConnectionError:
            logger.error(f"Erro de conexão com Evolution API: {endpoint}")
            return False, {'error': 'Não foi possível conectar à Evolution API. Verifique se está rodando.'}
        except Exception as e:
            logger.error(f"Erro inesperado ao chamar Evolution API: {str(e)}")
            return False, {'error': str(e)}

    def formatar_telefone_brasileiro(self, telefone: str) -> str:
        """
        Formata telefone para padrão brasileiro aceito pela API

        Args:
            telefone: Telefone em qualquer formato

        Returns:
            Telefone formatado: 5567999887766
        """
        # Remove todos os caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Se já tem 55 no início, retorna
        if telefone_limpo.startswith('55') and len(telefone_limpo) >= 12:
            return telefone_limpo

        # Se tem 13 dígitos (55 + DDD + 9 dígitos), retorna
        if len(telefone_limpo) == 13:
            return telefone_limpo

        # Se tem 11 dígitos (DDD + 9 dígitos), adiciona 55
        if len(telefone_limpo) == 11:
            return f"55{telefone_limpo}"

        # Se tem 10 dígitos (DDD + 8 dígitos), adiciona 55 e 9
        if len(telefone_limpo) == 10:
            ddd = telefone_limpo[:2]
            numero = telefone_limpo[2:]
            return f"55{ddd}9{numero}"

        # Caso padrão: assume DDD 67 se não tiver DDD
        if len(telefone_limpo) == 9:
            return f"5567{telefone_limpo}"

        if len(telefone_limpo) == 8:
            return f"55679{telefone_limpo}"

        # Retorna como está se não conseguir formatar
        logger.warning(f"Não foi possível formatar telefone: {telefone}")
        return telefone_limpo

    def create_instance(self, instance_name: str) -> Tuple[bool, Dict]:
        """
        Cria uma nova instância WhatsApp

        Args:
            instance_name: Nome da instância (ex: nexus_cliente_1)

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        logger.info(f"📱 Criando instância WhatsApp: {instance_name}")

        data = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }

        sucesso, resposta = self._make_request('POST', 'instance/create', data)

        if sucesso:
            logger.info(f"✅ Instância criada: {instance_name}")
        else:
            logger.error(f"❌ Erro ao criar instância: {resposta.get('error')}")

        return sucesso, resposta

    def connect_instance(self, instance_name: str) -> Tuple[bool, Dict]:
        """
        Conecta instância e gera QR Code

        Args:
            instance_name: Nome da instância

        Returns:
            Tupla (sucesso: bool, resposta com qrcode: dict)
        """
        logger.info(f"🔗 Gerando QR Code para: {instance_name}")

        sucesso, resposta = self._make_request('GET', f'instance/connect/{instance_name}')

        if sucesso and 'qrcode' in resposta:
            logger.info(f"✅ QR Code gerado para: {instance_name}")
        else:
            logger.error(f"❌ Erro ao gerar QR Code: {resposta.get('error')}")

        return sucesso, resposta

    def get_instance_status(self, instance_name: str) -> Tuple[bool, str]:
        """
        Verifica status da conexão da instância

        Args:
            instance_name: Nome da instância

        Returns:
            Tupla (sucesso: bool, status: str)
            Status possíveis: 'open', 'close', 'connecting'
        """
        sucesso, resposta = self._make_request('GET', f'instance/connectionState/{instance_name}')

        if sucesso and 'instance' in resposta:
            status = resposta['instance'].get('state', 'close')
            logger.debug(f"Status de {instance_name}: {status}")
            return True, status
        else:
            logger.warning(f"⚠️ Não foi possível verificar status de {instance_name}")
            return False, 'close'

    def logout_instance(self, instance_name: str) -> Tuple[bool, Dict]:
        """
        Desconecta instância WhatsApp

        Args:
            instance_name: Nome da instância

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        logger.info(f"🔌 Desconectando instância: {instance_name}")

        sucesso, resposta = self._make_request('DELETE', f'instance/logout/{instance_name}')

        if sucesso:
            logger.info(f"✅ Instância desconectada: {instance_name}")
        else:
            logger.error(f"❌ Erro ao desconectar: {resposta.get('error')}")

        return sucesso, resposta

    def delete_instance(self, instance_name: str) -> Tuple[bool, Dict]:
        """
        Deleta instância WhatsApp permanentemente

        Args:
            instance_name: Nome da instância

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        logger.info(f"🗑️ Deletando instância: {instance_name}")

        sucesso, resposta = self._make_request('DELETE', f'instance/delete/{instance_name}')

        if sucesso:
            logger.info(f"✅ Instância deletada: {instance_name}")
        else:
            logger.error(f"❌ Erro ao deletar: {resposta.get('error')}")

        return sucesso, resposta

    def send_text(self, instance_name: str, phone: str, message: str) -> Tuple[bool, Dict]:
        """
        Envia mensagem de texto

        Args:
            instance_name: Nome da instância
            phone: Telefone de destino
            message: Mensagem de texto

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        phone_formatted = self.formatar_telefone_brasileiro(phone)

        logger.info(f"💬 Enviando texto para {phone_formatted} via {instance_name}")

        data = {
            "number": phone_formatted,
            "text": message
        }

        sucesso, resposta = self._make_request('POST', f'message/sendText/{instance_name}', data)

        if sucesso:
            logger.info(f"✅ Mensagem enviada para {phone_formatted}")
        else:
            logger.error(f"❌ Erro ao enviar mensagem: {resposta.get('error')}")

        return sucesso, resposta

    def send_pdf(self, instance_name: str, phone: str, pdf_path: str,
                 caption: str = "", filename: str = "documento.pdf") -> Tuple[bool, Dict]:
        """
        Envia arquivo PDF

        Args:
            instance_name: Nome da instância
            phone: Telefone de destino
            pdf_path: Caminho do arquivo PDF
            caption: Legenda do arquivo
            filename: Nome do arquivo a ser exibido

        Returns:
            Tupla (sucesso: bool, resposta: dict)
        """
        phone_formatted = self.formatar_telefone_brasileiro(phone)

        logger.info(f"📄 Enviando PDF para {phone_formatted} via {instance_name}")

        # Verifica se o arquivo existe
        if not os.path.exists(pdf_path):
            logger.error(f"❌ Arquivo PDF não encontrado: {pdf_path}")
            return False, {'error': 'Arquivo PDF não encontrado'}

        # Lê o arquivo e converte para base64
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                media_base64 = f"data:application/pdf;base64,{pdf_base64}"

        except Exception as e:
            logger.error(f"❌ Erro ao ler PDF: {str(e)}")
            return False, {'error': f'Erro ao ler PDF: {str(e)}'}

        data = {
            "number": phone_formatted,
            "mediatype": "document",
            "mimetype": "application/pdf",
            "caption": caption,
            "fileName": filename,
            "media": media_base64
        }

        sucesso, resposta = self._make_request('POST', f'message/sendMedia/{instance_name}', data)

        if sucesso:
            logger.info(f"✅ PDF enviado para {phone_formatted}")
        else:
            logger.error(f"❌ Erro ao enviar PDF: {resposta.get('error')}")

        return sucesso, resposta

    def send_with_antibloqueio(self, instance_name: str, phone: str, pdf_path: str,
                               mensagem_antibloqueio: str, filename: str = "boleto.pdf") -> Tuple[bool, Dict]:
        """
        Envia mensagem anti-bloqueio seguida de PDF com delay

        Args:
            instance_name: Nome da instância
            phone: Telefone de destino
            pdf_path: Caminho do PDF
            mensagem_antibloqueio: Mensagem enviada antes do PDF
            filename: Nome do arquivo

        Returns:
            Tupla (sucesso: bool, resultado: dict com detalhes)
        """
        phone_formatted = self.formatar_telefone_brasileiro(phone)

        logger.info(f"🛡️ Iniciando envio com anti-bloqueio para {phone_formatted}")

        resultado = {
            'phone': phone_formatted,
            'mensagem_enviada': False,
            'pdf_enviado': False,
            'erro': None
        }

        # 1. Envia mensagem anti-bloqueio
        sucesso_msg, resposta_msg = self.send_text(instance_name, phone, mensagem_antibloqueio)

        if not sucesso_msg:
            resultado['erro'] = f"Erro ao enviar mensagem: {resposta_msg.get('error')}"
            logger.error(resultado['erro'])
            return False, resultado

        resultado['mensagem_enviada'] = True
        logger.info("✅ Mensagem anti-bloqueio enviada")

        # 2. Delay aleatório (3-7 segundos) para parecer humano
        delay = random.uniform(3, 7)
        logger.info(f"⏳ Aguardando {delay:.1f}s antes de enviar PDF...")
        time.sleep(delay)

        # 3. Envia PDF
        sucesso_pdf, resposta_pdf = self.send_pdf(instance_name, phone, pdf_path,
                                                   "Segue anexo", filename)

        if not sucesso_pdf:
            resultado['erro'] = f"Erro ao enviar PDF: {resposta_pdf.get('error')}"
            logger.error(resultado['erro'])
            return False, resultado

        resultado['pdf_enviado'] = True
        logger.info("✅ PDF enviado com sucesso")

        return True, resultado

    def disparo_massa(self, instance_name: str, lista_envios: List[Dict],
                      mensagem_antibloqueio: str, intervalo_min: int = 5,
                      intervalo_max: int = 10) -> Dict:
        """
        Executa disparo em massa com controles anti-bloqueio

        Args:
            instance_name: Nome da instância
            lista_envios: Lista de dicts com {phone, pdf_path, filename}
            mensagem_antibloqueio: Mensagem anti-bloqueio
            intervalo_min: Intervalo mínimo entre disparos (segundos)
            intervalo_max: Intervalo máximo entre disparos (segundos)

        Returns:
            Dict com estatísticas: {
                'total': int,
                'enviados': int,
                'erros': int,
                'tempo_total': float,
                'detalhes': List[Dict]
            }
        """
        logger.info(f"🚀 Iniciando disparo em massa: {len(lista_envios)} envios")

        estatisticas = {
            'total': len(lista_envios),
            'enviados': 0,
            'erros': 0,
            'tempo_total': 0,
            'detalhes': []
        }

        inicio = time.time()
        contador = 0

        for envio in lista_envios:
            contador += 1

            phone = envio.get('phone')
            pdf_path = envio.get('pdf_path')
            filename = envio.get('filename', 'boleto.pdf')

            logger.info(f"📤 Disparo {contador}/{len(lista_envios)}: {phone}")

            # Envia com anti-bloqueio
            sucesso, resultado = self.send_with_antibloqueio(
                instance_name, phone, pdf_path, mensagem_antibloqueio, filename
            )

            if sucesso:
                estatisticas['enviados'] += 1
            else:
                estatisticas['erros'] += 1

            estatisticas['detalhes'].append(resultado)

            # Pausa a cada 20 mensagens (1 minuto)
            if contador % 20 == 0 and contador < len(lista_envios):
                logger.warning(f"⏸️ Pausando 60s após {contador} disparos (anti-bloqueio)")
                time.sleep(60)

            # Intervalo aleatório entre disparos (exceto no último)
            if contador < len(lista_envios):
                intervalo = random.uniform(intervalo_min, intervalo_max)
                logger.debug(f"⏳ Aguardando {intervalo:.1f}s até próximo disparo...")
                time.sleep(intervalo)

        fim = time.time()
        estatisticas['tempo_total'] = round(fim - inicio, 2)

        logger.info(f"""
        ✅ DISPARO EM MASSA CONCLUÍDO
        Total: {estatisticas['total']}
        Enviados: {estatisticas['enviados']}
        Erros: {estatisticas['erros']}
        Tempo: {estatisticas['tempo_total']}s
        """)

        return estatisticas


# Instância global do serviço
evolution_service = EvolutionAPIService()
