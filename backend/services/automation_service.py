"""
Serviço de Automação - Orquestra todo o processo automático
Etapas 21-33 do manual
"""

import os
import time
from datetime import datetime, date, timedelta
from typing import Dict, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import (
    ClienteNexus, ClienteFinal, Boleto, Disparo, Configuracao,
    log_sistema, execute_query
)
from services.pdf_generator import BoletoGenerator
from services.whatsapp_service import whatsapp_service
from services.webscraping import campus_scraper
from services.pdf_extractor import extrair_dados_boleto
from services.mensagens_personalizadas import gerar_mensagem_boleto


class AutomationService:
    """Serviço principal de automação do sistema"""

    def __init__(self):
        self.pdf_generator = BoletoGenerator()

    def executar_automacao_completa(self, cliente_nexus_id: int) -> Dict:
        """
        Executa a automação completa para um cliente
        Etapas 21-33 do manual

        Args:
            cliente_nexus_id: ID do cliente Nexus

        Returns:
            Estatísticas da execução
        """
        inicio = time.time()

        log_sistema('info', 'Iniciando automação completa', 'automacao',
                   {'cliente_nexus_id': cliente_nexus_id})

        stats = {
            'cliente_nexus_id': cliente_nexus_id,
            'inicio': datetime.now().isoformat(),
            'clientes_processados': 0,
            'boletos_gerados': 0,
            'boletos_enviados': 0,
            'erros': 0,
            'tempo_total_segundos': 0
        }

        try:
            # FILTRO CRÍTICO: Buscar apenas clientes com boletos pendentes na tabela 'boletos'
            # Evita disparos para quem não tem boleto!
            from models.database import db

            clientes_com_boletos = db.execute_query("""
                SELECT DISTINCT
                    cf.id,
                    cf.nome_completo as nome,
                    cf.whatsapp,
                    cf.cpf,
                    COUNT(b.id) as total_boletos_pendentes
                FROM clientes_finais cf
                INNER JOIN boletos b ON b.cliente_final_id = cf.id
                WHERE cf.cliente_nexus_id = %s
                    AND b.status_envio IN ('nao_enviado', 'pendente')
                    AND cf.whatsapp IS NOT NULL
                    AND LENGTH(cf.whatsapp) >= 10
                GROUP BY cf.id, cf.nome_completo, cf.whatsapp, cf.cpf
                ORDER BY cf.nome_completo
            """, (cliente_nexus_id,))

            log_sistema('info', f'Clientes com boletos pendentes: {len(clientes_com_boletos) if clientes_com_boletos else 0}', 'automacao',
                       {'cliente_nexus_id': cliente_nexus_id,
                        'total_clientes_filtrados': len(clientes_com_boletos) if clientes_com_boletos else 0})

            if not clientes_com_boletos:
                stats['mensagem'] = 'Nenhum cliente com boletos pendentes encontrado'
                log_sistema('warning', stats['mensagem'], 'automacao',
                           {'cliente_nexus_id': cliente_nexus_id})
                return stats

            clientes = clientes_com_boletos

            log_sistema('info', f'Total de clientes a processar: {len(clientes)}',
                       'automacao', {
                           'total_clientes': len(clientes),
                           'criterio': 'apenas_com_boletos_pendentes'
                       })

            # Busca configurações do cliente
            config = Configuracao.buscar(cliente_nexus_id)
            mensagem_antibloqueio = config.get('mensagem_antibloqueio',
                                              'Olá! Você receberá seu boleto em instantes.')
            intervalo = config.get('intervalo_disparos', 5)

            # Buscar cliente Nexus
            cliente_nexus = ClienteNexus.buscar_por_id(cliente_nexus_id)

            # Etapa 28: Notificação inicial
            self._enviar_notificacao_inicial(cliente_nexus, len(clientes))

            # BUSCAR BOLETOS PENDENTES EXISTENTES (não gera novos!)
            boletos_para_enviar = db.execute_query("""
                SELECT
                    b.id as boleto_id,
                    b.numero_boleto,
                    b.valor_original as valor,
                    b.data_vencimento as vencimento,
                    b.pdf_path,
                    b.pdf_filename,
                    b.mes_referencia,
                    cf.id as cliente_final_id,
                    cf.nome_completo as cliente_final_nome,
                    cf.whatsapp
                FROM boletos b
                INNER JOIN clientes_finais cf ON b.cliente_final_id = cf.id
                WHERE b.cliente_nexus_id = %s
                    AND b.status_envio IN ('nao_enviado', 'pendente')
                    AND cf.whatsapp IS NOT NULL
                    AND LENGTH(cf.whatsapp) >= 10
                ORDER BY b.data_vencimento, cf.nome_completo
            """, (cliente_nexus_id,))

            stats['clientes_processados'] = len(clientes)
            stats['boletos_gerados'] = len(boletos_para_enviar)

            log_sistema('info', f'Boletos pendentes encontrados: {len(boletos_para_enviar)}',
                       'automacao', {
                           'total_boletos': len(boletos_para_enviar),
                           'clientes_distintos': len(clientes)
                       })

            # Etapa 29-30: Disparos automáticos
            stats_disparos = self._executar_disparos_automaticos(
                cliente_nexus_id,
                boletos_para_enviar,
                mensagem_antibloqueio,
                intervalo
            )

            stats['boletos_enviados'] = stats_disparos['sucessos']
            stats['erros'] += stats_disparos['erros']

            # Etapa 31: Mensagem final
            tempo_total = time.time() - inicio
            stats['tempo_total_segundos'] = round(tempo_total, 2)

            self._enviar_mensagem_final(cliente_nexus, stats)

            # Registra histórico
            self._registrar_historico_automacao(cliente_nexus_id, stats)

            log_sistema('success', 'Automação completa finalizada', 'automacao', stats)

            return stats

        except Exception as e:
            log_sistema('error', f'Erro na automação: {str(e)}', 'automacao',
                       {'cliente_nexus_id': cliente_nexus_id})
            stats['erro_geral'] = str(e)
            return stats

    def _criar_pasta_organizada(self, cliente_nexus_id: int, nome_empresa: str) -> str:
        """
        Etapa 23: Cria estrutura de pastas organizada

        boletos/
          ├── empresa_X/
          │   ├── janeiro_2024/
          │   ├── fevereiro_2024/
        """
        # Sanitiza nome da empresa
        nome_pasta = nome_empresa.replace(' ', '_').replace('/', '_')

        mes_atual = datetime.now().strftime("%B_%Y").lower()

        pasta = os.path.join(
            Config.BOLETO_PATH,
            f"empresa_{cliente_nexus_id}_{nome_pasta}",
            mes_atual
        )

        os.makedirs(pasta, exist_ok=True)

        log_sistema('info', f'Pasta criada: {pasta}', 'automacao',
                   {'cliente_nexus_id': cliente_nexus_id})

        return pasta

    def _gerar_boleto_para_cliente(self, cliente_nexus_id: int,
                                   cliente_final: Dict, pasta_destino: str) -> Dict:
        """Gera boleto PDF para um cliente"""

        # Busca dados do cliente Nexus
        cliente_nexus = ClienteNexus.buscar_por_id(cliente_nexus_id)

        # Dados do boleto
        mes_referencia = datetime.now().strftime("%B/%Y")

        # Simula consulta ao Campus Consórcio
        dados_consulta = campus_scraper.simular_consulta(cliente_final['cpf'])

        # Monta dados para o PDF
        dados_boleto = {
            'beneficiario': cliente_nexus.get('nome_empresa', 'Empresa'),
            'cnpj_beneficiario': cliente_nexus.get('cnpj', '00.000.000/0000-00'),
            'pagador': cliente_final['nome'],
            'cpf_pagador': cliente_final['cpf'],
            'endereco_pagador': cliente_final.get('endereco', ''),
            'valor': dados_consulta['valor_parcela'],
            'vencimento': dados_consulta['proxima_parcela'],
            'mes_referencia': mes_referencia,
            'numero_documento': f"{cliente_final['id']:06d}"
        }

        # Nome do arquivo
        nome_arquivo = f"boleto_{cliente_final['nome'].replace(' ', '_')}_{cliente_final['id']}.pdf"
        caminho_pdf = os.path.join(pasta_destino, nome_arquivo)

        # Gera o PDF
        self.pdf_generator.gerar_boleto(dados_boleto, caminho_pdf)

        return {
            'cliente_final_id': cliente_final['id'],
            'cliente_final_nome': cliente_final['nome'],
            'whatsapp': cliente_final.get('whatsapp'),
            'pdf_path': caminho_pdf,
            'valor': dados_boleto['valor'],
            'vencimento': dados_boleto['vencimento'],
            'mes_referencia': mes_referencia,
            'numero_documento': dados_boleto['numero_documento']
        }

    def _registrar_boletos_no_banco(self, cliente_nexus_id: int, boletos: List[Dict]):
        """Etapa 26: Registra boletos gerados no banco de dados"""

        boletos_para_inserir = []

        # Obter data/hora atual
        agora = datetime.now()
        mes_atual = agora.month
        ano_atual = agora.year

        for idx, boleto in enumerate(boletos):
            # Gerar número único do boleto (timestamp + índice)
            # Adiciona um pequeno delay para garantir unicidade do timestamp
            if idx > 0:
                time.sleep(0.001)  # 1ms de delay
            timestamp = int(datetime.now().timestamp() * 1000)  # milissegundos
            numero_boleto = f"BOL{cliente_nexus_id:04d}{timestamp}{idx:04d}"

            boletos_para_inserir.append({
                'cliente_nexus_id': cliente_nexus_id,
                'cliente_final_id': boleto['cliente_final_id'],
                'numero_boleto': numero_boleto,
                'valor_original': boleto['valor'],
                'data_vencimento': boleto['vencimento'],
                'data_emissao': agora.date(),
                'mes_referencia': mes_atual,
                'ano_referencia': ano_atual,
                'numero_parcela': 1,  # Pode ser ajustado conforme necessidade
                'pdf_path': boleto['pdf_path'],
                'status': 'pendente',
                'status_envio': 'nao_enviado',
                'gerado_por': 'automatico'
            })

        if boletos_para_inserir:
            total = Boleto.criar_em_lote(boletos_para_inserir)
            log_sistema('success', f'{total} boletos registrados no banco', 'automacao',
                       {'cliente_nexus_id': cliente_nexus_id})

    def _executar_disparos_automaticos(self, cliente_nexus_id: int, boletos: List[Dict],
                                       mensagem_antibloqueio: str, intervalo: int) -> Dict:
        """Etapas 29-30: Disparo automático com anti-bloqueio"""

        stats = {
            'total': len(boletos),
            'sucessos': 0,
            'erros': 0
        }

        from models.database import db

        log_sistema('info', f'🚀 Iniciando disparos para {len(boletos)} clientes COM WhatsApp', 'automacao',
                   {'cliente_nexus_id': cliente_nexus_id, 'total_boletos': len(boletos)})

        for idx, boleto in enumerate(boletos, 1):
            try:
                whatsapp = boleto.get('whatsapp')

                log_sistema('info', f'📱 [{idx}/{len(boletos)}] Processando: {boleto["cliente_final_nome"]} → {whatsapp}',
                           'automacao', {
                               'boleto_id': boleto.get('cliente_final_id'),
                               'cliente': boleto['cliente_final_nome'],
                               'whatsapp': whatsapp,
                               'pdf_path': boleto.get('pdf_path')
                           })

                # Validação adicional (segurança)
                if not whatsapp or len(str(whatsapp).strip()) < 10:
                    log_sistema('error', f"❌ WhatsApp inválido para {boleto['cliente_final_nome']}: '{whatsapp}'",
                               'automacao', {'cliente_final_id': boleto['cliente_final_id']})
                    stats['erros'] += 1
                    continue

                # Usar boleto_id que já vem da query
                boleto_id = boleto.get('boleto_id')

                # Registra o disparo como pendente
                if boleto_id:
                    disparo_id = db.execute_query("""
                        INSERT INTO disparos
                        (boleto_id, cliente_nexus_id, telefone_destino, status, mensagem_enviada)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (boleto_id, cliente_nexus_id, whatsapp, 'pendente', mensagem_antibloqueio))

                    disparo_id = disparo_id[0]['id'] if disparo_id else None
                else:
                    disparo_id = None

                # Etapa 30: Extração de dados do PDF e envio com anti-bloqueio
                pdf_path = boleto.get('pdf_path')

                # Extrair dados do PDF para mensagem personalizada
                dados_pdf = {}
                if pdf_path and os.path.exists(pdf_path):
                    log_sistema('info', f'📄 Extraindo dados do PDF: {os.path.basename(pdf_path)}',
                               'automacao', {'pdf_path': pdf_path})
                    dados_pdf = extrair_dados_boleto(pdf_path)

                    if dados_pdf.get('sucesso'):
                        log_sistema('success', f'✅ Dados extraídos do PDF: venc={dados_pdf.get("vencimento_str")}, valor=R$ {dados_pdf.get("valor", 0):.2f}',
                                   'automacao', {'dados_pdf': dados_pdf})
                    else:
                        log_sistema('warning', f'⚠️ Não foi possível extrair todos os dados do PDF',
                                   'automacao', {'pdf_path': pdf_path})

                # Gerar mensagem personalizada com dados do PDF
                mensagem_personalizada = gerar_mensagem_boleto(
                    nome_cliente=boleto['cliente_final_nome'],
                    vencimento=boleto.get('vencimento'),  # Fallback do banco
                    valor=boleto.get('valor'),            # Fallback do banco
                    contrato=None,
                    empresa="Cred MS Consorcios",
                    dados_pdf=dados_pdf  # Dados do PDF têm prioridade
                )

                log_sistema('info', f'📤 [{idx}/{len(boletos)}] Enviando boleto para {boleto["cliente_final_nome"]} ({whatsapp})',
                           'automacao', {
                               'boleto_id': boleto_id,
                               'disparo_id': disparo_id,
                               'pdf_path': pdf_path,
                               'whatsapp': whatsapp,
                               'mensagem_preview': mensagem_personalizada[:80] + '...',
                               'intervalo': intervalo,
                               'dados_extraidos': {
                                   'vencimento': dados_pdf.get('vencimento_str'),
                                   'valor': dados_pdf.get('valor')
                               }
                           })

                resultado = whatsapp_service.enviar_com_antibloqueio(
                    whatsapp,
                    pdf_path,
                    mensagem_personalizada,  # Usa mensagem personalizada com dados do PDF
                    intervalo,
                    cliente_nexus_id
                )

                log_sistema('info', f'📊 Resultado do envio para {boleto["cliente_final_nome"]}: {resultado.get("sucesso_total")}',
                           'automacao', {
                               'cliente': boleto['cliente_final_nome'],
                               'whatsapp': whatsapp,
                               'sucesso': resultado.get('sucesso_total'),
                               'erro': resultado.get('erro'),
                               'resultado_completo': resultado
                           })

                if resultado['sucesso_total']:
                    stats['sucessos'] += 1

                    # Atualiza status do disparo para enviado
                    if disparo_id:
                        db.execute_update("""
                            UPDATE disparos
                            SET status = 'enviado', data_disparo = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (disparo_id,))

                    # Atualiza status do boleto
                    if boleto_id:
                        db.execute_update("""
                            UPDATE boletos
                            SET status_envio = 'enviado', data_envio = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (boleto_id,))

                    log_sistema('success', f'✅ [{idx}/{len(boletos)}] Boleto enviado com sucesso para {boleto["cliente_final_nome"]}!',
                               'automacao', {
                                   'boleto_id': boleto_id,
                                   'disparo_id': disparo_id,
                                   'whatsapp': whatsapp,
                                   'cliente': boleto["cliente_final_nome"]
                               })
                else:
                    stats['erros'] += 1

                    # Marca disparo como erro
                    erro_msg = resultado.get('erro', 'Erro desconhecido')
                    if disparo_id:
                        db.execute_update("""
                            UPDATE disparos
                            SET status = 'erro', erro = %s, data_disparo = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (erro_msg, disparo_id))

                    log_sistema('error', f'❌ [{idx}/{len(boletos)}] ERRO ao enviar boleto para {boleto["cliente_final_nome"]}: {erro_msg}',
                               'automacao', {
                                   'boleto_id': boleto_id,
                                   'disparo_id': disparo_id,
                                   'whatsapp': whatsapp,
                                   'erro': erro_msg,
                                   'resultado_completo': resultado
                               })

            except Exception as e:
                log_sistema('error', f'❌ Exceção no disparo para {boleto.get("cliente_final_nome", "cliente")}: {str(e)}',
                           'automacao', {
                               'cliente': boleto.get('cliente_final_nome'),
                               'whatsapp': boleto.get('whatsapp'),
                               'exception': str(e)
                           })
                stats['erros'] += 1

        # Log de resumo final
        log_sistema('info', f'🏁 Disparos finalizados: {stats["sucessos"]} sucessos, {stats["erros"]} erros de {stats["total"]} total',
                   'automacao', {
                       'total': stats['total'],
                       'sucessos': stats['sucessos'],
                       'erros': stats['erros'],
                       'taxa_sucesso': f'{(stats["sucessos"]/stats["total"]*100):.1f}%' if stats['total'] > 0 else '0%'
                   })

        return stats

    def _enviar_notificacao_inicial(self, cliente_nexus: Dict, total_clientes: int):
        """Etapa 28: Notificação inicial ao empresário"""

        mensagem = f"""
Olá! Seus boletos foram gerados com sucesso.

📊 Total de boletos: {total_clientes}
⏰ Iniciando disparo automático...

Sistema Nexus - Aqui seu tempo vale ouro
        """.strip()

        # Envia para o número da Nexus (administrador)
        try:
            whatsapp_service.enviar_mensagem(
                '556796600884',  # Número fixo da Nexus
                mensagem,
                cliente_nexus['id']
            )
        except Exception as e:
            log_sistema('warning', f'Erro ao enviar notificação inicial para Nexus: {str(e)}', 'automacao')

        # Envia para o cliente também (se tiver WhatsApp)
        if cliente_nexus.get('whatsapp_numero'):
            try:
                whatsapp_service.enviar_mensagem(
                    cliente_nexus['whatsapp_numero'],
                    mensagem,
                    cliente_nexus['id']
                )
            except Exception as e:
                log_sistema('warning', f'Erro ao enviar notificação inicial para cliente: {str(e)}', 'automacao')

    def _enviar_mensagem_final(self, cliente_nexus: Dict, stats: Dict):
        """Etapa 31: Mensagem final ao empresário"""

        # Calcula informações de tempo
        tempo_minutos = stats['tempo_total_segundos'] / 60

        # Calcula taxa de sucesso
        total_processado = stats.get('clientes_processados', 0)
        total_enviado = stats.get('boletos_enviados', 0)
        total_erros = stats.get('erros', 0)

        taxa_sucesso = 0
        if total_processado > 0:
            taxa_sucesso = (total_enviado / total_processado) * 100

        # Monta mensagem base
        mensagem = f"""
✅ *DISPAROS FINALIZADOS COM SUCESSO!*

⏱️ *Tempo total:* {tempo_minutos:.1f} minutos

📊 *Estatísticas do Disparo:*
• Total processado: {total_processado} clientes
• Boletos enviados: {total_enviado}
• Taxa de sucesso: {taxa_sucesso:.1f}%"""

        # Adiciona informações sobre erros se houver
        if total_erros > 0:
            mensagem += f"\n• ⚠️ Erros encontrados: {total_erros}"

        # Adiciona informações sobre próximo disparo
        mensagem += f"""

📅 *Próximo disparo automático:*
• Os boletos serão gerados e enviados automaticamente

✨ *Nexus - Aqui seu tempo vale ouro!*
Obrigado por confiar em nossos serviços.
        """.strip()

        # Envia para o número da Nexus (administrador)
        try:
            whatsapp_service.enviar_mensagem(
                '556796600884',  # Número fixo da Nexus
                mensagem,
                cliente_nexus['id']
            )
        except Exception as e:
            log_sistema('warning', f'Erro ao enviar mensagem final para Nexus: {str(e)}', 'automacao')

        # Envia para o cliente também (se tiver WhatsApp)
        if cliente_nexus.get('whatsapp_numero'):
            try:
                whatsapp_service.enviar_mensagem(
                    cliente_nexus['whatsapp_numero'],
                    mensagem,
                    cliente_nexus['id']
                )
            except Exception as e:
                log_sistema('warning', f'Erro ao enviar mensagem final para cliente: {str(e)}', 'automacao')

    def _registrar_historico_automacao(self, cliente_nexus_id: int, stats: Dict):
        """Registra no histórico de disparos"""

        query = """
            INSERT INTO historico_disparos
            (cliente_nexus_id, tipo_disparo, total_envios, envios_sucesso,
             envios_erro, executado_por, status, detalhes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        import json

        execute_query(query, (
            cliente_nexus_id,
            'disparo_boletos_completo',
            stats.get('clientes_processados', 0),
            stats.get('boletos_enviados', 0),
            stats.get('erros', 0),
            'automation_service',
            'concluido',
            json.dumps(stats)
        ))

    def gerar_boletos_sem_enviar(self, cliente_nexus_id: int) -> Dict:
        """
        Gera apenas os boletos sem enviar
        Útil para testes e geração manual
        """
        clientes = ClienteFinal.listar_por_cliente_nexus(cliente_nexus_id, limit=1000)

        cliente_nexus = ClienteNexus.buscar_por_id(cliente_nexus_id)
        pasta = self._criar_pasta_organizada(cliente_nexus_id,
                                            cliente_nexus.get('nome_empresa', 'Cliente'))

        boletos = []

        for cliente in clientes:
            try:
                boleto_data = self._gerar_boleto_para_cliente(
                    cliente_nexus_id,
                    cliente,
                    pasta
                )
                boletos.append(boleto_data)
            except Exception as e:
                print(f"Erro ao gerar boleto: {e}")

        # Registra no banco
        self._registrar_boletos_no_banco(cliente_nexus_id, boletos)

        return {
            'total_gerados': len(boletos),
            'pasta': pasta,
            'boletos': boletos
        }


# Instância global
automation_service = AutomationService()


# ============================================================================
# DISPARO INDIVIDUAL PARA TESTE
# ============================================================================

def enviar_boletos_apenas_disparo(cliente_nexus_id: int, cliente_final_id: int) -> Dict:
    """
    Envia boletos pendentes apenas para um cliente específico
    Usado para testes individuais

    Args:
        cliente_nexus_id: ID do cliente Nexus (empresário)
        cliente_final_id: ID do cliente final específico

    Returns:
        Dict com estatísticas do envio
    """
    from models.database import db
    from services.whatsapp_service import whatsapp_service
    from models import log_sistema

    stats = {
        'enviados': 0,
        'erros': 0,
        'mensagem': ''
    }

    try:
        # Buscar boletos pendentes do cliente
        boletos = db.execute_query("""
            SELECT
                b.id as boleto_id,
                b.numero_boleto,
                b.valor_original,
                b.data_vencimento,
                b.pdf_path,
                b.pdf_filename,
                cf.id as cliente_final_id,
                cf.nome_completo as cliente_final_nome,
                cf.whatsapp
            FROM boletos b
            INNER JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_final_id = %s
                AND b.cliente_nexus_id = %s
                AND b.status_envio = 'nao_enviado'
                AND cf.whatsapp IS NOT NULL
                AND LENGTH(cf.whatsapp) >= 10
            ORDER BY b.data_vencimento
        """, (cliente_final_id, cliente_nexus_id))

        if not boletos:
            stats['mensagem'] = 'Nenhum boleto pendente encontrado'
            return stats

        # Mensagem padrão para o envio
        mensagem = "Olá! Segue seu boleto em anexo. Qualquer dúvida, estou à disposição!"

        log_sistema(
            'info',
            f'Iniciando disparo individual - {len(boletos)} boleto(s)',
            'disparo_individual',
            {'cliente_final_id': cliente_final_id, 'total_boletos': len(boletos)}
        )

        # Enviar cada boleto
        for idx, boleto in enumerate(boletos, 1):
            try:
                whatsapp = boleto['whatsapp']
                pdf_path = boleto['pdf_path']
                boleto_id = boleto['boleto_id']

                # Extrair dados do PDF para mensagem personalizada
                dados_pdf = {}
                if pdf_path and os.path.exists(pdf_path):
                    log_sistema(
                        'info',
                        f'📄 Extraindo dados do PDF: {os.path.basename(pdf_path)}',
                        'disparo_individual',
                        {'pdf_path': pdf_path}
                    )
                    dados_pdf = extrair_dados_boleto(pdf_path)

                    if dados_pdf.get('sucesso'):
                        log_sistema(
                            'success',
                            f'✅ Dados extraídos: venc={dados_pdf.get("vencimento_str")}, valor=R$ {dados_pdf.get("valor", 0):.2f}',
                            'disparo_individual',
                            {'dados_pdf': dados_pdf}
                        )

                # Gerar mensagem personalizada com dados do PDF
                mensagem_personalizada = gerar_mensagem_boleto(
                    nome_cliente=boleto['cliente_final_nome'],
                    vencimento=str(boleto.get('data_vencimento', '')),  # Fallback do banco
                    valor=boleto.get('valor_original'),                 # Fallback do banco
                    contrato=boleto.get('numero_boleto'),
                    empresa="Cred MS Consorcios",
                    dados_pdf=dados_pdf  # Dados do PDF têm prioridade
                )

                log_sistema(
                    'info',
                    f'[{idx}/{len(boletos)}] Enviando para {boleto["cliente_final_nome"]} ({whatsapp})',
                    'disparo_individual',
                    {
                        'boleto_id': boleto_id,
                        'whatsapp': whatsapp,
                        'dados_extraidos': {
                            'vencimento': dados_pdf.get('vencimento_str'),
                            'valor': dados_pdf.get('valor')
                        }
                    }
                )

                # Registra disparo como pendente
                disparo_id = db.execute_query("""
                    INSERT INTO disparos
                    (boleto_id, cliente_nexus_id, telefone_destino, status, mensagem_enviada)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (boleto_id, cliente_nexus_id, whatsapp, 'pendente', mensagem_personalizada))

                disparo_id = disparo_id[0]['id'] if disparo_id else None

                # Enviar via WhatsApp
                resultado = whatsapp_service.enviar_com_antibloqueio(
                    whatsapp,
                    pdf_path,
                    mensagem_personalizada,  # Usa mensagem personalizada com dados do PDF
                    intervalo=2,  # 2 segundos entre mensagens
                    cliente_nexus_id=cliente_nexus_id
                )

                if resultado.get('sucesso_total'):
                    stats['enviados'] += 1

                    # Atualiza disparo
                    if disparo_id:
                        db.execute_update("""
                            UPDATE disparos
                            SET status = 'enviado', data_disparo = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (disparo_id,))

                    # Atualiza boleto
                    db.execute_update("""
                        UPDATE boletos
                        SET status_envio = 'enviado', data_envio = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (boleto_id,))

                    log_sistema(
                        'success',
                        f'✅ Boleto {boleto_id} enviado com sucesso',
                        'disparo_individual',
                        {'boleto_id': boleto_id}
                    )
                else:
                    stats['erros'] += 1
                    erro_msg = resultado.get('erro', 'Erro desconhecido')

                    if disparo_id:
                        db.execute_update("""
                            UPDATE disparos
                            SET status = 'erro', erro = %s
                            WHERE id = %s
                        """, (erro_msg, disparo_id))

                    log_sistema(
                        'error',
                        f'❌ Erro ao enviar boleto {boleto_id}: {erro_msg}',
                        'disparo_individual',
                        {'boleto_id': boleto_id, 'erro': erro_msg}
                    )

            except Exception as e:
                stats['erros'] += 1
                log_sistema(
                    'error',
                    f'❌ Exceção ao processar boleto {boleto.get("boleto_id")}: {str(e)}',
                    'disparo_individual',
                    {'erro': str(e)}
                )

        # Mensagem final
        if stats['enviados'] > 0:
            stats['mensagem'] = f'{stats["enviados"]} boleto(s) enviado(s) com sucesso!'
        else:
            stats['mensagem'] = 'Nenhum boleto foi enviado. Verifique os logs.'

        return stats

    except Exception as e:
        import traceback
        traceback.print_exc()
        log_sistema('error', f'Erro no disparo individual: {str(e)}', 'disparo_individual')
        stats['mensagem'] = f'Erro: {str(e)}'
        return stats
