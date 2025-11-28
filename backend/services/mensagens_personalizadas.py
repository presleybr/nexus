"""
Serviço de Mensagens Personalizadas
Gerencia mensagens variadas e humanizadas para envio aos clientes
Agora com suporte a dados extraídos do PDF
"""

import random
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MensagensPersonalizadas:
    """Gerencia mensagens personalizadas para envio de documentos/boletos"""

    def __init__(self):
        # Lista com 10 mensagens personalizadas e calorosas
        self.mensagens_base = [
            # 1. Tom acolhedor e próximo
            """Olá, {nome}! Tudo bem com você? 😊
Espero que esteja tudo certo por aí! Estou enviando o documento que você precisa.
Se surgir qualquer dúvida, pode me chamar que estarei à disposição!""",

            # 2. Tom amigável e prestativo
            """Oi, {nome}! Como você está?
Segue em anexo o documento solicitado. Dei uma conferida aqui e está tudo certo!
Qualquer coisa, é só me chamar, tá bom? Estou aqui para ajudar!""",

            # 3. Tom carinhoso e atencioso
            """Olá, {nome}! Espero que esteja tendo um ótimo dia! ☀️
Envio em anexo o seu documento. Confere lá pra mim quando puder?
Se precisar de qualquer ajuda, pode contar comigo! Estou sempre à disposição.""",

            # 4. Tom profissional mas caloroso
            """Bom dia, {nome}! Tudo bem por aí?
Estou enviando o documento que você solicitou. Está tudo em ordem!
Se tiver alguma dúvida ou precisar de algo mais, é só me avisar. Estou aqui para te ajudar!""",

            # 5. Tom descontraído e próximo
            """E aí, {nome}! Tudo certo? 😄
Segue o documento que você pediu. Já está tudo certinho pra você!
Qualquer coisa que precisar, pode me chamar sem compromisso, combinado?""",

            # 6. Tom empático e cuidadoso
            """Olá, {nome}! Espero que você e sua família estejam bem! 💙
Envio aqui o seu documento conforme solicitado.
Se tiver qualquer dúvida ou precisar de esclarecimentos, fico à total disposição, viu?""",

            # 7. Tom positivo e motivador
            """Oi, {nome}! Espero que seu dia esteja sendo incrível! ✨
Aqui está o documento que você precisa. Tudo certo e organizado!
Se pintar qualquer dúvida, pode me chamar a hora que for. Estou aqui pra isso!""",

            # 8. Tom cordial e atencioso
            """Olá, {nome}! Como tem passado?
Segue em anexo o documento solicitado. Revisei tudo com cuidado!
Fico à disposição para qualquer esclarecimento que você precisar. Pode contar comigo!""",

            # 9. Tom gentil e paciente
            """Oi, {nome}! Tudo bem com você e os seus? 🤗
Estou enviando o seu documento. Dá uma conferida quando puder!
Se tiver alguma dúvida, por menor que seja, pode me procurar sem receio, ok?""",

            # 10. Tom afetuoso e parceiro
            """Olá, {nome}! Que bom falar com você! 😊
Aqui está o documento que você estava aguardando. Está tudo nos conformes!
Lembre-se: qualquer dúvida ou necessidade, estou sempre aqui ao seu dispor!"""
        ]

        # Mensagens específicas para boletos
        self.mensagens_boleto = [
            # 1. Tom acolhedor
            """Olá, {nome}! Tudo bem com você? 😊
Espero que esteja tudo certo por aí! Estou enviando o boleto do seu consórcio da *{empresa}*.

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Por favor, fique atento ao prazo de vencimento para evitar juros e multas! 📅
Qualquer dúvida, pode me chamar que estarei à disposição!

Att,
*{empresa}* 🏆""",

            # 2. Tom amigável
            """Oi, {nome}! Como você está?
Segue em anexo o boleto do seu consórcio da *{empresa}*. Dei uma conferida e está tudo certo!

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Não esquece de pagar dentro do prazo, hein? Assim você evita juros! 😉
Qualquer coisa, é só me chamar, tá bom? Estou aqui para ajudar!

Abraço,
*{empresa}* 💚""",

            # 3. Tom carinhoso
            """Olá, {nome}! Espero que esteja tendo um ótimo dia! ☀️
Envio em anexo o boleto do seu consórcio da *{empresa}*.

📋 *Detalhes importantes:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Confere lá pra mim quando puder? E se precisar de qualquer ajuda, pode contar comigo!

Com carinho,
*{empresa}* 💙""",

            # 4. Tom profissional caloroso
            """Bom dia, {nome}! Tudo bem por aí?
Estou enviando o boleto do seu consórcio da *{empresa}*. Está tudo em ordem!

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Por favor, fique atento à data de vencimento para evitar encargos adicionais. 📅
Se tiver alguma dúvida, é só me avisar. Estou aqui para te ajudar!

Atenciosamente,
*{empresa}* 🏆""",

            # 5. Tom descontraído
            """E aí, {nome}! Tudo certo? 😄
Segue o boleto do seu consórcio da *{empresa}*. Já está tudo certinho pra você!

📋 *Confira os dados:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Paga em dia pra não ter dor de cabeça com juros, ok? 😊
Qualquer coisa que precisar, pode me chamar sem compromisso!

Abraço,
*{empresa}* ✨""",

            # 6. Tom empático
            """Olá, {nome}! Espero que você e sua família estejam bem! 💙
Envio aqui o boleto do seu consórcio da *{empresa}*.

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Por favor, fique atento ao prazo de vencimento para evitar juros e multas! 📅
Se tiver qualquer dúvida, fico à total disposição, viu?

Com atenção,
*{empresa}* 🤗""",

            # 7. Tom motivador
            """Oi, {nome}! Espero que seu dia esteja sendo incrível! ✨
Aqui está o boleto do seu consórcio da *{empresa}*. Tudo certo e organizado!

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Mais um passo rumo à conquista do seu sonho! 🎯 Pague em dia e fique tranquilo.
Se pintar qualquer dúvida, pode me chamar a hora que for!

Sucesso,
*{empresa}* 🚀""",

            # 8. Tom cordial
            """Olá, {nome}! Como tem passado?
Segue em anexo o boleto do seu consórcio da *{empresa}*. Revisei tudo com cuidado!

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Por favor, fique atento ao prazo de vencimento para evitar encargos! 📅
Fico à disposição para qualquer esclarecimento. Pode contar comigo!

Cordialmente,
*{empresa}* 💼""",

            # 9. Tom gentil
            """Oi, {nome}! Tudo bem com você e os seus? 🤗
Estou enviando o boleto do seu consórcio da *{empresa}*.

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Dá uma conferida quando puder! E não esquece do prazo, viu? 😊
Se tiver alguma dúvida, por menor que seja, pode me procurar sem receio!

Com carinho,
*{empresa}* 💚""",

            # 10. Tom parceiro
            """Olá, {nome}! Que bom falar com você! 😊
Aqui está o boleto do seu consórcio da *{empresa}* que você estava aguardando.

📋 *Informações do Boleto:*
• *Contrato:* {contrato}
• *Vencimento:* {vencimento}

Fique atento ao prazo de vencimento para evitar juros e multas! 📅
Lembre-se: qualquer dúvida ou necessidade, estou sempre aqui ao seu dispor!

Parceria sempre,
*{empresa}* 🤝"""
        ]

    def obter_mensagem_aleatoria(self, tipo: str = 'documento') -> str:
        """
        Retorna uma mensagem aleatória da lista

        Args:
            tipo: Tipo de mensagem ('documento' ou 'boleto')

        Returns:
            Mensagem aleatória (string)
        """
        if tipo == 'boleto':
            return random.choice(self.mensagens_boleto)
        else:
            return random.choice(self.mensagens_base)

    def personalizar_mensagem(self, mensagem: str, dados: Dict) -> str:
        """
        Personaliza a mensagem com os dados do cliente

        Args:
            mensagem: Template da mensagem
            dados: Dicionário com dados do cliente
                   {nome, empresa, contrato, valor, vencimento}

        Returns:
            Mensagem personalizada
        """
        # Pega apenas o primeiro nome do cliente
        nome_completo = dados.get('nome', 'Cliente')
        primeiro_nome = nome_completo.split()[0] if nome_completo else 'Cliente'

        # Substitui as variáveis
        mensagem_final = mensagem.replace('{nome}', primeiro_nome)

        # Substitui dados do boleto se existirem
        if 'empresa' in dados:
            mensagem_final = mensagem_final.replace('{empresa}', dados['empresa'])
        if 'contrato' in dados:
            mensagem_final = mensagem_final.replace('{contrato}', str(dados['contrato']))
        if 'valor' in dados:
            mensagem_final = mensagem_final.replace('{valor}', f"{float(dados['valor']):.2f}")
        if 'vencimento' in dados:
            mensagem_final = mensagem_final.replace('{vencimento}', dados['vencimento'])

        return mensagem_final

    def gerar_mensagem_boleto(self, dados_cliente: Dict, dados_boleto: Dict,
                             nome_empresa: str = 'Cred MS') -> str:
        """
        Gera uma mensagem completa de boleto personalizada e aleatória

        Args:
            dados_cliente: {nome, contrato, ...}
            dados_boleto: {valor, vencimento, ...}
            nome_empresa: Nome da empresa

        Returns:
            Mensagem personalizada e pronta para envio
        """
        # Seleciona mensagem aleatória
        template = self.obter_mensagem_aleatoria('boleto')

        # Monta dicionário completo
        dados_completos = {
            'nome': dados_cliente.get('nome_completo', dados_cliente.get('nome', 'Cliente')),
            'empresa': nome_empresa,
            'contrato': dados_cliente.get('numero_contrato', 'N/A'),
            'valor': dados_boleto.get('valor_original', 0),
            'vencimento': dados_boleto.get('data_vencimento', '').strftime('%d/%m/%Y')
                         if hasattr(dados_boleto.get('data_vencimento'), 'strftime')
                         else str(dados_boleto.get('data_vencimento', 'N/A'))
        }

        # Personaliza e retorna
        return self.personalizar_mensagem(template, dados_completos)

    def gerar_mensagem_com_pdf(
        self,
        nome_cliente: str,
        vencimento: str = None,
        valor: float = None,
        contrato: str = None,
        empresa: str = "Cred MS Consorcios",
        dados_pdf: Dict = None
    ) -> str:
        """
        Gera mensagem personalizada para envio de boleto.
        Dados do PDF têm prioridade sobre os parâmetros diretos.

        Args:
            nome_cliente: Nome do cliente (pode ser completo)
            vencimento: Data de vencimento (DD/MM/YYYY) - opcional se dados_pdf fornecido
            valor: Valor do boleto - opcional
            contrato: Número do contrato - opcional se dados_pdf fornecido
            empresa: Nome da empresa
            dados_pdf: Dict com dados extraídos do PDF (sobrescreve outros parâmetros)

        Returns:
            Mensagem formatada pronta para envio
        """

        # Se passou dados do PDF, usar eles (mais confiáveis)
        if dados_pdf and dados_pdf.get('sucesso'):
            if dados_pdf.get('vencimento_str'):
                vencimento = dados_pdf['vencimento_str']
                logger.info(f"📅 Usando vencimento do PDF: {vencimento}")

            if dados_pdf.get('contrato'):
                contrato = dados_pdf['contrato']
                logger.info(f"📋 Usando contrato do PDF: {contrato}")

            if dados_pdf.get('valor') and dados_pdf['valor'] > 0:
                valor = dados_pdf['valor']
                logger.info(f"💰 Usando valor do PDF: R$ {valor:.2f}")

            if dados_pdf.get('nome_pagador'):
                nome_cliente = dados_pdf['nome_pagador']
                logger.info(f"👤 Usando nome do PDF: {nome_cliente}")

        # Extrair primeiro nome
        primeiro_nome = nome_cliente.split()[0].capitalize() if nome_cliente else "Cliente"

        # Seleciona template aleatório de boleto
        template = self.obter_mensagem_aleatoria('boleto')

        # Monta dados completos
        dados_completos = {
            'nome': primeiro_nome,
            'empresa': empresa,
            'contrato': contrato or 'N/A',
            'vencimento': vencimento or 'N/A'
        }

        # Adiciona valor se disponível (formata com vírgula)
        if valor and valor > 0:
            valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            # Modifica o template para incluir valor
            if '• *Vencimento:*' in template:
                template = template.replace(
                    '• *Vencimento:* {vencimento}',
                    f'• *Vencimento:* {{vencimento}}\n• *Valor:* {valor_formatado}'
                )

        # Personaliza e retorna
        mensagem = self.personalizar_mensagem(template, dados_completos)

        logger.info(f"✅ Mensagem gerada com sucesso para {primeiro_nome}")

        return mensagem


# Instância global
mensagens_service = MensagensPersonalizadas()


# Funções auxiliares para compatibilidade
def gerar_mensagem_boleto(
    nome_cliente: str,
    vencimento: str = None,
    valor: float = None,
    contrato: str = None,
    empresa: str = "Cred MS Consorcios",
    dados_pdf: Dict = None
) -> str:
    """
    Função auxiliar para gerar mensagem de boleto.
    Wrapper para a instância global.

    Args:
        nome_cliente: Nome do cliente
        vencimento: Data de vencimento (DD/MM/YYYY)
        valor: Valor do boleto
        contrato: Número do contrato
        empresa: Nome da empresa
        dados_pdf: Dict com dados extraídos do PDF (prioridade)

    Returns:
        Mensagem personalizada
    """
    return mensagens_service.gerar_mensagem_com_pdf(
        nome_cliente=nome_cliente,
        vencimento=vencimento,
        valor=valor,
        contrato=contrato,
        empresa=empresa,
        dados_pdf=dados_pdf
    )


def gerar_mensagem_antibloqueio(nome_cliente: str, vencimento: str = None) -> str:
    """
    Função de compatibilidade - chama gerar_mensagem_boleto.
    Mantida para não quebrar código existente.
    """
    return gerar_mensagem_boleto(
        nome_cliente=nome_cliente,
        vencimento=vencimento
    )
