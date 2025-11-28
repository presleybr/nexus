"""
Cliente HTTP direto para sistema Canopus
Faz requisições sem navegador

Baseado na engenharia reversa do sistema ASP.NET do Canopus
"""

import re
import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import CanopusConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CanopusAPI')


class CanopusAPI:
    """
    Cliente HTTP para sistema Canopus.
    Faz login e requisições diretas sem navegador.

    Vantagens:
    - 10x mais rápido que automação com navegador
    - Não precisa de interface gráfica
    - Pode rodar em servidor
    - Mais confiável e menos recursos
    - Processa múltiplos clientes em paralelo
    """

    BASE_URL = 'https://cnp3.consorciocanopus.com.br'

    def __init__(self, timeout: int = 30):
        """
        Inicializa cliente HTTP

        Args:
            timeout: Timeout padrão em segundos
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = timeout
        self._logged_in = False
        self._usuario_atual = None

        # Cache de campos ASP.NET
        self._viewstate_cache = {}

    def _extract_asp_fields(self, html: str) -> Dict[str, str]:
        """
        Extrai campos ocultos do ASP.NET (ViewState, EventValidation, etc)

        Args:
            html: HTML da página

        Returns:
            Dicionário com campos ocultos
        """
        soup = BeautifulSoup(html, 'html.parser')

        fields = {}

        # Campos ocultos comuns do ASP.NET
        hidden_fields = [
            '__VIEWSTATE',
            '__VIEWSTATEGENERATOR',
            '__EVENTVALIDATION',
            '__EVENTTARGET',
            '__EVENTARGUMENT',
            '__LASTFOCUS',
            '__SCROLLPOSITIONX',
            '__SCROLLPOSITIONY',
        ]

        for field_name in hidden_fields:
            field = soup.find('input', {'name': field_name})
            if field:
                fields[field_name] = field.get('value', '')

        return fields

    def _extract_form_fields(self, html: str, form_id: str = None) -> Dict[str, str]:
        """
        Extrai todos os campos de um formulário

        Args:
            html: HTML da página
            form_id: ID do formulário (opcional)

        Returns:
            Dicionário com campos do formulário
        """
        soup = BeautifulSoup(html, 'html.parser')

        if form_id:
            form = soup.find('form', {'id': form_id})
        else:
            form = soup.find('form')

        if not form:
            return {}

        fields = {}

        # Inputs
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                fields[name] = value

        # Selects
        for select_tag in form.find_all('select'):
            name = select_tag.get('name')
            if name:
                selected = select_tag.find('option', {'selected': True})
                if selected:
                    fields[name] = selected.get('value', '')

        # Textareas
        for textarea_tag in form.find_all('textarea'):
            name = textarea_tag.get('name')
            if name:
                fields[name] = textarea_tag.get_text(strip=True)

        return fields

    def login(self, usuario: str, senha: str) -> bool:
        """
        Faz login no sistema Canopus.

        Args:
            usuario: Usuário de acesso
            senha: Senha

        Returns:
            True se login bem-sucedido
        """
        try:
            logger.info(f"🔐 Fazendo login: {usuario}")

            # 1. Acessar página de login para pegar ViewState e cookies
            logger.debug("Carregando página de login...")
            response = self.session.get(
                f'{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx',
                timeout=self.timeout
            )
            response.raise_for_status()

            # Extrair campos ASP.NET
            asp_fields = self._extract_asp_fields(response.text)
            logger.debug(f"Campos ASP.NET: {list(asp_fields.keys())}")

            # 2. Montar dados do POST de login
            # NOTA: Os nomes dos campos precisam ser ajustados conforme o mapeamento
            login_data = {
                **asp_fields,
                'ctl00$Conteudo$txtUsuario': usuario,
                'ctl00$Conteudo$txtSenha': senha,
                'ctl00$Conteudo$btnEntrar': 'Entrar',
            }

            # 3. Fazer POST de login
            logger.debug("Enviando credenciais...")
            response = self.session.post(
                f'{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx',
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 4. Verificar se login foi bem-sucedido
            # Critérios de sucesso:
            # - Redirecionou para frmMain.aspx
            # - Não tem mensagem de erro
            # - Tem elementos do menu logado

            if 'frmMain.aspx' in response.url:
                self._logged_in = True
                self._usuario_atual = usuario
                logger.info("✅ Login bem-sucedido!")
                return True

            # Verificar mensagens de erro comuns
            error_patterns = [
                'senha inválida',
                'usuário inválido',
                'acesso negado',
                'credenciais incorretas',
            ]

            response_lower = response.text.lower()
            for pattern in error_patterns:
                if pattern in response_lower:
                    logger.error(f"❌ Erro no login: {pattern}")
                    return False

            # Se ainda está na página de login
            if 'frmCorCCCnsLogin.aspx' in response.url:
                logger.error("❌ Login falhou - ainda na página de login")
                return False

            logger.warning("⚠️ Status do login incerto - verificar manualmente")
            return False

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede no login: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no login: {e}")
            return False

    def buscar_cliente_por_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente por CPF.

        Args:
            cpf: CPF do cliente (com ou sem formatação)

        Returns:
            Dados do cliente ou None se não encontrado
        """
        if not self._logged_in:
            logger.error("❌ Não está logado!")
            return None

        try:
            # Limpar e formatar CPF
            cpf_limpo = re.sub(r'[^\d]', '', cpf)
            cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

            logger.info(f"🔍 Buscando cliente: {cpf_formatado}")

            # NOTA: Esta URL e campos precisam ser ajustados
            # conforme capturado no mapeamento de requisições

            # 1. Navegar para busca avançada
            # (baseado no fluxo: Atendimento -> Busca Avançada)
            logger.debug("Navegando para busca avançada...")

            # URL pode ser algo como:
            # /WWW/CONCO/frmConCoConsulta.aspx
            # Ajustar conforme mapeamento

            response = self.session.get(
                f'{self.BASE_URL}/WWW/CONCO/frmConCoConsulta.aspx',
                timeout=self.timeout
            )
            response.raise_for_status()

            # 2. Extrair campos e fazer busca
            asp_fields = self._extract_asp_fields(response.text)

            search_data = {
                **asp_fields,
                # Ajustar nomes conforme mapeamento:
                'ctl00$Conteudo$ddlTipoBusca': 'F',  # F = CPF
                'ctl00$Conteudo$txtBusca': cpf_formatado,
                'ctl00$Conteudo$btnBuscar': 'Buscar',
            }

            logger.debug("Executando busca...")
            response = self.session.post(
                f'{self.BASE_URL}/WWW/CONCO/frmConCoConsulta.aspx',
                data=search_data,
                timeout=self.timeout
            )

            # 3. Parsear resultado
            soup = BeautifulSoup(response.text, 'html.parser')

            # Verificar se encontrou resultados
            # Ajustar seletores conforme HTML real
            resultado_table = soup.find('table', {'id': re.compile('grd.*Resultado')})

            if not resultado_table:
                logger.warning(f"⚠️ Cliente não encontrado: {cpf_formatado}")
                return None

            # Extrair dados do cliente
            # Ajustar conforme estrutura da tabela
            linhas = resultado_table.find_all('tr')[1:]  # Pular header

            if not linhas:
                logger.warning(f"⚠️ Nenhum resultado para: {cpf_formatado}")
                return None

            # Pegar primeira linha
            primeira_linha = linhas[0]
            colunas = primeira_linha.find_all('td')

            # Extrair link do cliente
            link = primeira_linha.find('a')
            if link:
                cliente_url = link.get('href')
            else:
                cliente_url = None

            logger.info(f"✅ Cliente encontrado: {cpf_formatado}")

            return {
                'cpf': cpf_limpo,
                'cpf_formatado': cpf_formatado,
                'encontrado': True,
                'url': cliente_url,
                # Adicionar outros campos conforme necessário
            }

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede na busca: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado na busca: {e}")
            import traceback
            traceback.print_exc()
            return None

    def emitir_boleto(
        self,
        cliente_url: str,
        mes_referencia: str = None
    ) -> Optional[bytes]:
        """
        Emite boleto e retorna bytes do PDF.

        Args:
            cliente_url: URL do cliente (obtida na busca)
            mes_referencia: Mês de referência (opcional)

        Returns:
            Bytes do PDF ou None se falhar
        """
        if not self._logged_in:
            logger.error("❌ Não está logado!")
            return None

        try:
            logger.info(f"📄 Emitindo boleto...")

            # NOTA: O fluxo exato precisa ser mapeado
            # a partir das requisições capturadas

            # Fluxo aproximado:
            # 1. Acessar página do cliente
            # 2. Navegar para Emissão de Cobrança
            # 3. Selecionar boleto/parcela
            # 4. Clicar em Emitir
            # 5. Capturar PDF gerado

            # 1. Acessar cliente
            if cliente_url:
                logger.debug(f"Acessando cliente: {cliente_url}")
                response = self.session.get(
                    f'{self.BASE_URL}{cliente_url}',
                    timeout=self.timeout
                )
                response.raise_for_status()

            # 2. Navegar para emissão
            # URL pode ser /WWW/CONCM/frmConCmEmissao.aspx
            logger.debug("Navegando para emissão...")
            response = self.session.get(
                f'{self.BASE_URL}/WWW/CONCM/frmConCmEmissao.aspx',
                timeout=self.timeout
            )

            asp_fields = self._extract_asp_fields(response.text)

            # 3. Selecionar boleto e emitir
            # Ajustar conforme mapeamento
            emitir_data = {
                **asp_fields,
                # Checkbox do boleto - ajustar ID
                'ctl00$Conteudo$grdBoleto$ctl02$chkEmite': 'on',
                # Botão emitir
                'ctl00$Conteudo$btnEmitir': 'Emitir Cobrança',
            }

            logger.debug("Emitindo boleto...")
            response = self.session.post(
                f'{self.BASE_URL}/WWW/CONCM/frmConCmEmissao.aspx',
                data=emitir_data,
                timeout=self.timeout
            )

            # 4. Parsear resposta para encontrar URL do PDF
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar por link/iframe do PDF
            # Pode ser algo como: frmConCmImpressao.aspx?applicationKey=XXXXX
            pdf_link = soup.find('iframe', {'src': re.compile('frmConCmImpressao')})

            if pdf_link:
                pdf_url = pdf_link.get('src')
                logger.debug(f"URL do PDF: {pdf_url}")

                # Baixar PDF
                response = self.session.get(
                    f'{self.BASE_URL}{pdf_url}',
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    pdf_bytes = response.content

                    if len(pdf_bytes) > 1000:
                        logger.info(f"✅ PDF baixado: {len(pdf_bytes)} bytes")
                        return pdf_bytes
                    else:
                        logger.error("❌ PDF muito pequeno (provavelmente erro)")
                        return None
                else:
                    logger.error(f"❌ Erro ao baixar PDF: HTTP {response.status_code}")
                    return None
            else:
                logger.error("❌ Link do PDF não encontrado na resposta")
                return None

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede ao emitir: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao emitir: {e}")
            import traceback
            traceback.print_exc()
            return None

    def baixar_boleto(
        self,
        pdf_bytes: bytes,
        nome_cliente: str,
        mes: str,
        ano: int,
        consultor: str = "Danner"
    ) -> str:
        """
        Salva bytes do PDF em arquivo

        Args:
            pdf_bytes: Bytes do PDF
            nome_cliente: Nome do cliente
            mes: Mês
            ano: Ano
            consultor: Nome do consultor (para pasta)

        Returns:
            Caminho do arquivo salvo
        """

        # Sanitizar nome
        nome_limpo = nome_cliente.upper().replace(' ', '_')
        nome_limpo = re.sub(r'[^A-Z0-9_]', '', nome_limpo)[:50]

        # Pasta destino
        pasta = Path(r'D:\Nexus\automation\canopus\downloads') / consultor
        pasta.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = pasta / f"{nome_limpo}_{mes}_{ano}_{timestamp}.pdf"

        # Salvar
        with open(arquivo, 'wb') as f:
            f.write(pdf_bytes)

        tamanho_kb = len(pdf_bytes) / 1024
        logger.info(f"✅ Salvo: {arquivo.name} ({tamanho_kb:.1f} KB)")

        return str(arquivo)

    def processar_cliente_completo(
        self,
        cpf: str,
        mes: str,
        ano: int,
        consultor: str = "Danner"
    ) -> Dict[str, Any]:
        """
        Processa cliente completo: busca + emite + baixa PDF

        Args:
            cpf: CPF do cliente
            mes: Mês
            ano: Ano
            consultor: Nome do consultor

        Returns:
            Dicionário com resultado
        """
        inicio = datetime.now()

        resultado = {
            'cpf': cpf,
            'mes': mes,
            'ano': ano,
            'sucesso': False,
            'mensagem': None,
            'arquivo': None,
            'tempo_segundos': 0,
        }

        try:
            # 1. Buscar cliente
            cliente = self.buscar_cliente_por_cpf(cpf)

            if not cliente:
                resultado['mensagem'] = 'Cliente não encontrado'
                return resultado

            # 2. Emitir boleto
            pdf_bytes = self.emitir_boleto(
                cliente_url=cliente.get('url'),
                mes_referencia=mes
            )

            if not pdf_bytes:
                resultado['mensagem'] = 'Erro ao emitir boleto'
                return resultado

            # 3. Salvar PDF
            arquivo = self.baixar_boleto(
                pdf_bytes=pdf_bytes,
                nome_cliente=cpf,
                mes=mes,
                ano=ano,
                consultor=consultor
            )

            resultado['sucesso'] = True
            resultado['mensagem'] = 'Boleto baixado com sucesso'
            resultado['arquivo'] = arquivo

        except Exception as e:
            resultado['mensagem'] = f'Erro: {e}'
            logger.error(f"❌ Erro ao processar cliente: {e}")

        finally:
            fim = datetime.now()
            resultado['tempo_segundos'] = (fim - inicio).total_seconds()

        return resultado

    def logout(self):
        """Faz logout do sistema"""
        if self._logged_in:
            try:
                # Ajustar URL de logout conforme mapeamento
                self.session.get(f'{self.BASE_URL}/WWW/Logout.aspx', timeout=5)
            except:
                pass
            finally:
                self._logged_in = False
                self._usuario_atual = None
                logger.info("🔒 Logout realizado")


# ============================================================================
# TESTE RÁPIDO
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("TESTE - CANOPUS API (HTTP DIRETO)")
    print("=" * 80)
    print("\n⚠️  NOTA: Este código precisa ser ajustado conforme mapeamento")
    print("   Execute primeiro: python capturar_requisicoes.py")
    print("   Depois: python mapear_fluxo.py")
    print("\n" + "=" * 80)

    usuario = input("\nUsuário: ").strip()
    senha = input("Senha: ").strip()

    if not usuario or not senha:
        print("❌ Usuário e senha são obrigatórios")
        exit(1)

    # Criar API
    api = CanopusAPI()

    # Login
    if api.login(usuario, senha):
        print("\n✅ Login OK!")

        # Testar busca
        cpf_teste = input("\nCPF para testar busca (ou ENTER para pular): ").strip()

        if cpf_teste:
            cliente = api.buscar_cliente_por_cpf(cpf_teste)

            if cliente:
                print(f"\n✅ Cliente encontrado:")
                for key, value in cliente.items():
                    print(f"   {key}: {value}")
            else:
                print("\n❌ Cliente não encontrado")

        # Logout
        api.logout()
    else:
        print("\n❌ Falha no login")
        print("   Verifique as credenciais e os campos do formulário")
