"""
Serviço WPPConnect - Integração com WPPConnect Server
Substitui Baileys por uma solução mais estável e confiável
"""

import os
import requests
import time
from datetime import datetime
from typing import Dict, Optional, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import log_sistema


class WPPConnectService:
    """Serviço de integração com WPPConnect Server"""

    def __init__(self, base_url: str = None):
        """
        Inicializa o serviço WPPConnect

        Args:
            base_url: URL do servidor WPPConnect (padrão: Config.WPPCONNECT_URL)
        """
        self.base_url = base_url or Config.WPPCONNECT_URL
        self.timeout = 120  # 2 minutos para inicialização do navegador

    def _fazer_requisicao(self, method: str, endpoint: str, data: dict = None) -> Dict:
        """
        Faz requisição HTTP para o servidor WPPConnect

        Args:
            method: Método HTTP (GET, POST)
            endpoint: Endpoint da API
            data: Dados para enviar (opcional)

        Returns:
            Resposta da API
        """
        try:
            url = f"{self.base_url}{endpoint}"

            if method.upper() == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout ao conectar com WPPConnect Server'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'WPPConnect Server não está rodando. Execute: wppconnect-server/start.bat'
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

    def verificar_servidor(self) -> bool:
        """
        Verifica se o WPPConnect Server está rodando

        Returns:
            True se o servidor está rodando, False caso contrário
        """
        try:
            response = self._fazer_requisicao('GET', '/')
            return response.get('status') == 'running'
        except:
            return False

    def iniciar_conexao(self) -> Dict:
        """
        Inicia a conexão com WhatsApp

        Returns:
            Dicionário com resultado da operação
        """
        try:
            # Chamar /start do servidor Express
            resultado = self._fazer_requisicao('POST', '/start')

            if resultado.get('success'):
                log_sistema('info', 'Conexão WhatsApp iniciada via WPPConnect',
                           'whatsapp', {'servico': 'wppconnect'})

            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao iniciar conexão: {str(e)}',
                       'whatsapp', {'servico': 'wppconnect'})
            return {
                'success': False,
                'error': str(e)
            }

    def obter_qr_code(self) -> Dict:
        """
        Obtém o QR Code para conexão

        Returns:
            Dicionário com QR Code (base64) ou status de conexão
        """
        try:
            resultado = self._fazer_requisicao('GET', '/qr')

            if resultado.get('success') and resultado.get('connected'):
                log_sistema('success', f'WhatsApp já conectado: {resultado.get("phone")}',
                           'whatsapp', {'servico': 'wppconnect'})
            elif resultado.get('success') and resultado.get('qr'):
                log_sistema('info', 'QR Code gerado com sucesso',
                           'whatsapp', {'servico': 'wppconnect'})

            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao obter QR Code: {str(e)}',
                       'whatsapp', {'servico': 'wppconnect'})
            return {
                'success': False,
                'error': str(e)
            }

    def verificar_status(self) -> Dict:
        """
        Verifica o status da conexão WhatsApp

        Returns:
            Dicionário com status da conexão
        """
        try:
            resultado = self._fazer_requisicao('GET', '/status')
            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao verificar status: {str(e)}',
                       'whatsapp', {'servico': 'wppconnect'})
            return {
                'success': False,
                'connected': False,
                'error': str(e)
            }

    def enviar_mensagem(self, numero: str, mensagem: str,
                       cliente_nexus_id: int = None) -> Dict:
        """
        Envia mensagem de texto via WhatsApp

        Args:
            numero: Número do destinatário (ex: 5511999999999)
            mensagem: Texto da mensagem
            cliente_nexus_id: ID do cliente Nexus (opcional)

        Returns:
            Dicionário com resultado do envio
        """
        try:
            # Remove caracteres não numéricos
            numero_limpo = ''.join(filter(str.isdigit, numero))

            if len(numero_limpo) < 10:
                return {
                    'success': False,
                    'error': 'Número de telefone inválido'
                }

            # Faz a requisição para o servidor
            resultado = self._fazer_requisicao('POST', '/send-text', {
                'phone': numero_limpo,
                'message': mensagem
            })

            if resultado.get('success'):
                log_sistema('success', f'Mensagem enviada para {numero_limpo}',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id,
                               'numero': numero_limpo
                           })
            else:
                log_sistema('error', f'Falha ao enviar mensagem: {resultado.get("error")}',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id,
                               'numero': numero_limpo
                           })

            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao enviar mensagem: {str(e)}',
                       'whatsapp', {
                           'servico': 'wppconnect',
                           'cliente_nexus_id': cliente_nexus_id
                       })
            return {
                'success': False,
                'error': str(e)
            }

    def enviar_arquivo(self, numero: str, arquivo_path: str,
                      legenda: str = '', filename: str = None,
                      cliente_nexus_id: int = None) -> Dict:
        """
        Envia arquivo (PDF, imagem, etc) via WhatsApp

        Args:
            numero: Número do destinatário
            arquivo_path: Caminho completo do arquivo
            legenda: Legenda do arquivo (opcional)
            filename: Nome do arquivo (opcional)
            cliente_nexus_id: ID do cliente Nexus (opcional)

        Returns:
            Dicionário com resultado do envio
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(arquivo_path):
                return {
                    'success': False,
                    'error': f'Arquivo não encontrado: {arquivo_path}'
                }

            # Remove caracteres não numéricos do número
            numero_limpo = ''.join(filter(str.isdigit, numero))

            if len(numero_limpo) < 10:
                return {
                    'success': False,
                    'error': 'Número de telefone inválido'
                }

            # Prepara dados para envio
            data = {
                'phone': numero_limpo,
                'filePath': arquivo_path,
                'caption': legenda
            }

            if filename:
                data['filename'] = filename
            else:
                data['filename'] = os.path.basename(arquivo_path)

            # Faz a requisição
            resultado = self._fazer_requisicao('POST', '/send-file', data)

            if resultado.get('success'):
                log_sistema('success',
                           f'Arquivo enviado para {numero_limpo}: {os.path.basename(arquivo_path)}',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id,
                               'numero': numero_limpo,
                               'arquivo': os.path.basename(arquivo_path)
                           })
            else:
                log_sistema('error',
                           f'Falha ao enviar arquivo: {resultado.get("error")}',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id,
                               'numero': numero_limpo
                           })

            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao enviar arquivo: {str(e)}',
                       'whatsapp', {
                           'servico': 'wppconnect',
                           'cliente_nexus_id': cliente_nexus_id
                       })
            return {
                'success': False,
                'error': str(e)
            }

    def enviar_pdf(self, numero: str, pdf_path: str,
                   legenda: str = 'Segue seu boleto em anexo',
                   cliente_nexus_id: int = None) -> Dict:
        """
        Envia PDF via WhatsApp (atalho para enviar_arquivo)

        Args:
            numero: Número do destinatário
            pdf_path: Caminho do arquivo PDF
            legenda: Legenda do PDF
            cliente_nexus_id: ID do cliente Nexus

        Returns:
            Dicionário com resultado do envio
        """
        return self.enviar_arquivo(
            numero=numero,
            arquivo_path=pdf_path,
            legenda=legenda,
            cliente_nexus_id=cliente_nexus_id
        )

    def enviar_com_antibloqueio(self, numero: str, pdf_path: str,
                               mensagem_antibloqueio: str,
                               intervalo_segundos: int = 5,
                               cliente_nexus_id: int = None) -> Dict:
        """
        Envia mensagem anti-bloqueio seguida do PDF

        Args:
            numero: Número do destinatário
            pdf_path: Caminho do PDF
            mensagem_antibloqueio: Mensagem a enviar antes do PDF
            intervalo_segundos: Intervalo entre mensagem e PDF
            cliente_nexus_id: ID do cliente

        Returns:
            Dicionário com resultados
        """
        resultados = {
            'mensagem_antibloqueio': None,
            'pdf': None,
            'sucesso_total': False
        }

        try:
            # 1. Envia mensagem anti-bloqueio
            resultado_msg = self.enviar_mensagem(
                numero=numero,
                mensagem=mensagem_antibloqueio,
                cliente_nexus_id=cliente_nexus_id
            )
            resultados['mensagem_antibloqueio'] = resultado_msg

            if not resultado_msg.get('success'):
                log_sistema('error', 'Falha ao enviar mensagem anti-bloqueio',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id
                           })
                return resultados

            # 2. Aguarda intervalo
            log_sistema('info', f'Aguardando {intervalo_segundos}s antes de enviar PDF',
                       'whatsapp', {'servico': 'wppconnect'})
            time.sleep(intervalo_segundos)

            # 3. Envia PDF
            resultado_pdf = self.enviar_pdf(
                numero=numero,
                pdf_path=pdf_path,
                legenda="Segue seu boleto em anexo",
                cliente_nexus_id=cliente_nexus_id
            )
            resultados['pdf'] = resultado_pdf

            # 4. Verifica sucesso total
            resultados['sucesso_total'] = (
                resultado_msg.get('success') and resultado_pdf.get('success')
            )

            if resultados['sucesso_total']:
                log_sistema('success', 'Envio com anti-bloqueio concluído com sucesso',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id
                           })

            return resultados

        except Exception as e:
            log_sistema('error', f'Erro no envio com anti-bloqueio: {str(e)}',
                       'whatsapp', {
                           'servico': 'wppconnect',
                           'cliente_nexus_id': cliente_nexus_id
                       })
            resultados['erro'] = str(e)
            return resultados

    def enviar_em_massa(self, destinatarios: List[Dict],
                       cliente_nexus_id: int = None) -> Dict:
        """
        Envia mensagens em massa

        Args:
            destinatarios: Lista de dicts com 'numero', 'mensagem' ou 'pdf_path'
            cliente_nexus_id: ID do cliente

        Returns:
            Estatísticas do envio em massa
        """
        stats = {
            'total': len(destinatarios),
            'sucessos': 0,
            'erros': 0,
            'detalhes': []
        }

        log_sistema('info', f'Iniciando envio em massa para {len(destinatarios)} destinatários',
                   'whatsapp', {
                       'servico': 'wppconnect',
                       'cliente_nexus_id': cliente_nexus_id
                   })

        for idx, dest in enumerate(destinatarios, 1):
            try:
                numero = dest['numero']

                log_sistema('info', f'Processando envio {idx}/{len(destinatarios)}',
                           'whatsapp', {'numero': numero})

                if 'pdf_path' in dest:
                    # Envia PDF com anti-bloqueio
                    mensagem_anti = dest.get(
                        'mensagem_antibloqueio',
                        'Olá! Você receberá seu boleto em instantes.'
                    )

                    resultado = self.enviar_com_antibloqueio(
                        numero=numero,
                        pdf_path=dest['pdf_path'],
                        mensagem_antibloqueio=mensagem_anti,
                        intervalo_segundos=dest.get('intervalo', 5),
                        cliente_nexus_id=cliente_nexus_id
                    )

                    if resultado.get('sucesso_total'):
                        stats['sucessos'] += 1
                    else:
                        stats['erros'] += 1

                elif 'mensagem' in dest:
                    # Envia apenas mensagem
                    resultado = self.enviar_mensagem(
                        numero=numero,
                        mensagem=dest['mensagem'],
                        cliente_nexus_id=cliente_nexus_id
                    )

                    if resultado.get('success'):
                        stats['sucessos'] += 1
                    else:
                        stats['erros'] += 1

                stats['detalhes'].append({
                    'numero': numero,
                    'resultado': resultado
                })

                # Pequeno delay entre envios para evitar bloqueio
                if idx < len(destinatarios):  # Não aguarda no último
                    time.sleep(2)

            except Exception as e:
                stats['erros'] += 1
                stats['detalhes'].append({
                    'numero': dest.get('numero', 'N/A'),
                    'erro': str(e)
                })

                log_sistema('error', f'Erro ao processar destinatário: {str(e)}',
                           'whatsapp', {'numero': dest.get('numero', 'N/A')})

        log_sistema('info',
                   f'Envio em massa concluído: {stats["sucessos"]} sucessos, {stats["erros"]} erros',
                   'whatsapp', {
                       'servico': 'wppconnect',
                       'cliente_nexus_id': cliente_nexus_id,
                       'stats': stats
                   })

        return stats

    def desconectar(self, cliente_nexus_id: int = None) -> Dict:
        """
        Desconecta do WhatsApp

        Args:
            cliente_nexus_id: ID do cliente (opcional)

        Returns:
            Dicionário com resultado da operação
        """
        try:
            resultado = self._fazer_requisicao('POST', '/logout')

            if resultado.get('success'):
                log_sistema('info', 'WhatsApp desconectado via WPPConnect',
                           'whatsapp', {
                               'servico': 'wppconnect',
                               'cliente_nexus_id': cliente_nexus_id
                           })

            return resultado

        except Exception as e:
            log_sistema('error', f'Erro ao desconectar: {str(e)}',
                       'whatsapp', {
                           'servico': 'wppconnect',
                           'cliente_nexus_id': cliente_nexus_id
                       })
            return {
                'success': False,
                'error': str(e)
            }


# Instância global do serviço
wppconnect_service = WPPConnectService()
