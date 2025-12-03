
"""
Automação Canopus TURBO - VERS��O COM PARALELIZAÇÃO DE ABAS
Estende CanopusAutomation para processar múltiplos clientes simultaneamente

ESTRATÉGIA:
- USA PLAYWRIGHT (não precisa reverse engineer HTTP)
- Processa 3-5 clientes AO MESMO TEMPO em abas diferentes
- Cada aba é independente e processa 1 cliente completo

PERFORMANCE ESPERADA:
- Playwright otimizado: 8-15s/boleto, 43 boletos em ~8min
- Turbo (3 abas): 8-15s/boleto, 43 boletos em ~3min (3x mais rápido)
- Turbo (5 abas): 8-15s/boleto, 43 boletos em ~2min (4x mais rápido)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from canopus_automation import CanopusAutomation
from canopus_config import CanopusConfig

logger = logging.getLogger(__name__)


class CanopusAutomationTurbo(CanopusAutomation):
    """
    Versão TURBO da automação Canopus
    Processa múltiplos clientes em paralelo usando múltiplas abas do Playwright
    """

    def __init__(self, config: CanopusConfig = None, headless: bool = None, max_abas_paralelas: int = 3):
        """
        Inicializa automação TURBO

        Args:
            config: Configuração (usa padrão se não fornecido)
            headless: Modo headless
            max_abas_paralelas: Número de abas processando simultaneamente (padrão: 3)
        """
        super().__init__(config, headless)
        self.max_abas_paralelas = max_abas_paralelas
        logger.info(f"🚀 MODO TURBO ativado - {max_abas_paralelas} abas paralelas")

    async def processar_cliente_em_aba(
        self,
        cpf: str,
        mes: str,
        ano: int,
        destino: Path,
        nome_arquivo: str = None
    ) -> Dict[str, Any]:
        """
        Processa UM cliente em UMA aba específica

        Este método cria uma NOVA aba, processa o cliente, e fecha a aba.
        Permite processamento paralelo de múltiplos clientes.

        Args:
            cpf: CPF do cliente
            mes: Mês do boleto
            ano: Ano do boleto
            destino: Diretório de destino
            nome_arquivo: Nome do arquivo (opcional)

        Returns:
            Dicionário com resultado do processamento
        """
        # Criar nova página/aba
        page_cliente = await self.context.new_page()

        # Configurações
        page_cliente.set_default_timeout(15000)
        page_cliente.set_default_navigation_timeout(15000)

        # Listeners
        def log_console(msg):
            logger.debug(f"[ABA {cpf[:6]}] {msg.text}")

        def log_error(exc):
            logger.error(f"[ABA {cpf[:6]}] ERRO: {exc}")

        page_cliente.on("console", log_console)
        page_cliente.on("pageerror", log_error)

        try:
            # Substituir página temporariamente
            page_original = self.page
            self.page = page_cliente

            # Processar cliente
            resultado = await self.processar_cliente_completo(
                cpf=cpf,
                mes=mes,
                ano=ano,
                destino=destino,
                nome_arquivo=nome_arquivo
            )

            # Restaurar página original
            self.page = page_original

            return resultado

        except Exception as e:
            logger.error(f"❌ Erro ao processar cliente {cpf} em aba: {e}")
            return {
                'cpf': cpf,
                'status': self.config.Status.ERRO,
                'mensagem': f'Erro: {str(e)}',
                'tempo_execucao_segundos': 0
            }

        finally:
            try:
                await page_cliente.close()
                logger.debug(f"🔒 Aba fechada - CPF {cpf[:6]}")
            except:
                pass

    async def processar_multiplos_clientes_turbo(
        self,
        lista_clientes: List[Dict[str, Any]],
        usuario: str,
        senha: str,
        destino: Path,
        mes: str = None,
        ano: int = None,
        callback_progresso=None
    ) -> List[Dict[str, Any]]:
        """
        Processa múltiplos clientes em MODO TURBO (múltiplas abas paralelas)

        Args:
            lista_clientes: Lista de dicts com {'cpf': '...', 'nome': '...'}
            usuario: Usuário para login
            senha: Senha para login
            destino: Diretório de destino dos PDFs
            mes: Mês do boleto (opcional)
            ano: Ano do boleto (opcional)
            callback_progresso: Função async para atualizar progresso

        Returns:
            Lista de resultados (um dict por cliente)
        """
        resultados = []
        inicio_total = datetime.now()

        logger.info("=" * 80)
        logger.info(f"🚀 MODO TURBO - {len(lista_clientes)} clientes")
        logger.info(f"⚡ {self.max_abas_paralelas} abas processando simultaneamente")
        logger.info("=" * 80)

        try:
            # 1. Iniciar browser
            await self.iniciar_navegador()

            # 2. Fazer login
            login_ok = await self.login(usuario, senha)
            if not login_ok:
                logger.error("❌ Falha no login")
                return []

            # 3. Semáforo para controlar paralelismo
            semaforo = asyncio.Semaphore(self.max_abas_paralelas)
            processados = 0

            async def processar_com_semaforo(cliente: Dict, idx: int) -> Dict[str, Any]:
                nonlocal processados

                async with semaforo:
                    cpf = cliente.get('cpf')
                    nome = cliente.get('nome', '')

                    logger.info(f"📋 [{idx}/{len(lista_clientes)}] {nome} - CPF {cpf}")

                    resultado = await self.processar_cliente_em_aba(
                        cpf=cpf,
                        mes=mes or 'DEZEMBRO',
                        ano=ano or datetime.now().year,
                        destino=destino
                    )

                    processados += 1

                    # Callback de progresso
                    if callback_progresso:
                        try:
                            await callback_progresso({
                                'processados': processados,
                                'total': len(lista_clientes),
                                'porcentagem': int((processados / len(lista_clientes)) * 100),
                                'resultado': resultado
                            })
                        except:
                            pass

                    # Atualizar stats
                    if resultado.get('status') == self.config.Status.SUCESSO:
                        self.stats['downloads_sucesso'] += 1
                    else:
                        self.stats['downloads_erro'] += 1

                    return resultado

            # 4. Processar em paralelo
            tasks = [
                processar_com_semaforo(cliente, idx + 1)
                for idx, cliente in enumerate(lista_clientes)
            ]

            resultados = await asyncio.gather(*tasks, return_exceptions=True)

            # Tratar exceções
            for i, r in enumerate(resultados):
                if isinstance(r, Exception):
                    logger.error(f"❌ Exceção no cliente {i+1}: {r}")
                    resultados[i] = {
                        'cpf': lista_clientes[i].get('cpf'),
                        'status': self.config.Status.ERRO,
                        'mensagem': f'Exceção: {str(r)}'
                    }

        except Exception as e:
            logger.error(f"❌ Erro no processamento TURBO: {e}")

        finally:
            await self.fechar_navegador()

        # Estatísticas finais
        fim_total = datetime.now()
        tempo_total = (fim_total - inicio_total).total_seconds()

        logger.info("")
        logger.info("=" * 80)
        logger.info("🚀 MODO TURBO CONCLUÍDO!")
        logger.info("=" * 80)
        logger.info(f"✅ Processados: {len(lista_clientes)}")
        logger.info(f"✅ Sucesso: {self.stats['downloads_sucesso']}")
        logger.info(f"❌ Erro: {self.stats['downloads_erro']}")
        logger.info(f"⏱️  Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} min)")

        if self.stats['downloads_sucesso'] > 0:
            tempo_medio = tempo_total / self.stats['downloads_sucesso']
            logger.info(f"📈 Tempo médio: {tempo_medio:.1f}s")

            tempo_sequencial = self.stats['downloads_sucesso'] * 12
            ganho = tempo_sequencial / tempo_total
            logger.info(f"🚀 Ganho: {ganho:.1f}x mais rápido")

        logger.info("=" * 80)

        return resultados


# Função de conveniência
async def baixar_boletos_turbo(
    clientes: List[Dict],
    usuario: str,
    senha: str,
    destino: Path,
    mes: str = None,
    ano: int = None,
    max_abas: int = 3,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    Download de boletos em MODO TURBO (múltiplas abas paralelas)

    Args:
        clientes: Lista com 'cpf' e 'nome'
        usuario: Usuário Canopus
        senha: Senha Canopus
        destino: Path do diretório
        mes: Mês (opcional)
        ano: Ano (opcional)
        max_abas: Número de abas simultâneas
        headless: Modo headless

    Returns:
        Lista de resultados
    """
    turbo = CanopusAutomationTurbo(headless=headless, max_abas_paralelas=max_abas)

    return await turbo.processar_multiplos_clientes_turbo(
        lista_clientes=clientes,
        usuario=usuario,
        senha=senha,
        destino=destino,
        mes=mes,
        ano=ano
    )
