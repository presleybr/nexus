"""
Script Principal da Automação Canopus
Orquestra todo o processo de download de boletos
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet

# Adicionar diretório backend ao path (para usar models/database)
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from config import CanopusConfig
from excel_importer import ExcelImporter
from canopus_bot import CanopusBot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format=CanopusConfig.LOG_FORMAT,
    datefmt=CanopusConfig.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(CanopusConfig.LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CanopusAutomacao:
    """Classe principal que orquestra a automação"""

    def __init__(self):
        """Inicializa a automação"""
        self.config = CanopusConfig
        self.db_conn = None
        self.importer = ExcelImporter(self.config)
        self.execucao_id = None

    def conectar_banco(self):
        """Conecta ao banco de dados PostgreSQL"""
        logger.info("🗄️ Conectando ao banco de dados...")

        try:
            self.db_conn = psycopg.connect(
                self.config.DB_CONNECTION_STRING,
                row_factory=dict_row
            )
            logger.info("✅ Conectado ao banco de dados")

        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise

    def desconectar_banco(self):
        """Desconecta do banco de dados"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("🔒 Desconectado do banco de dados")

    def criar_execucao(
        self,
        tipo_execucao: str,
        consultor_id: int = None,
        observacoes: str = None
    ) -> int:
        """
        Cria registro de execução no banco

        Args:
            tipo_execucao: Tipo da execução (MANUAL, AGENDADA, TESTE)
            consultor_id: ID do consultor (opcional)
            observacoes: Observações sobre a execução

        Returns:
            ID da execução criada
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO execucoes_automacao (
                        tipo_execucao,
                        consultor_id,
                        status,
                        observacoes,
                        usuario_execucao
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    tipo_execucao,
                    consultor_id,
                    self.config.StatusExecucao.INICIADA,
                    observacoes,
                    os.getenv("USERNAME", "sistema")
                ))

                execucao_id = cur.fetchone()["id"]
                self.db_conn.commit()

                logger.info(f"✅ Execução criada: ID {execucao_id}")
                return execucao_id

        except Exception as e:
            logger.error(f"❌ Erro ao criar execução: {e}")
            raise

    def atualizar_execucao(
        self,
        execucao_id: int,
        status: str,
        total_clientes: int = 0,
        total_sucessos: int = 0,
        total_erros: int = 0,
        total_nao_encontrados: int = 0,
        tempo_total: float = None
    ):
        """Atualiza registro de execução"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE execucoes_automacao SET
                        status = %s,
                        total_clientes = %s,
                        total_sucessos = %s,
                        total_erros = %s,
                        total_nao_encontrados = %s,
                        data_fim = CURRENT_TIMESTAMP,
                        tempo_total_segundos = %s
                    WHERE id = %s
                """, (
                    status,
                    total_clientes,
                    total_sucessos,
                    total_erros,
                    total_nao_encontrados,
                    tempo_total,
                    execucao_id
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar execução: {e}")

    def registrar_log_download(
        self,
        consultor_id: int,
        ponto_venda_id: int,
        resultado: Dict[str, Any]
    ):
        """
        Registra log de download no banco

        Args:
            consultor_id: ID do consultor
            ponto_venda_id: ID do ponto de venda
            resultado: Dicionário com resultado do processamento
        """
        try:
            dados_cliente = resultado.get("dados_cliente") or {}
            dados_boleto = resultado.get("dados_boleto") or {}

            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO log_downloads_boletos (
                        consultor_id,
                        ponto_venda_id,
                        cpf_cliente,
                        nome_cliente,
                        status,
                        mensagem_erro,
                        numero_boleto,
                        caminho_pdf,
                        tempo_execucao_segundos
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    consultor_id,
                    ponto_venda_id,
                    resultado.get("cpf"),
                    resultado.get("nome_cliente") or dados_cliente.get("nome"),
                    resultado.get("status"),
                    resultado.get("mensagem"),
                    dados_boleto.get("numero_boleto"),
                    dados_boleto.get("caminho_pdf"),
                    resultado.get("tempo_execucao")
                ))

                self.db_conn.commit()

        except Exception as e:
            logger.error(f"❌ Erro ao registrar log: {e}")

    def buscar_credenciais(self, ponto_venda_codigo: str) -> Optional[Dict[str, str]]:
        """
        Busca credenciais do ponto de venda no banco

        Args:
            ponto_venda_codigo: Código do ponto de venda

        Returns:
            Dicionário com usuário e senha ou None
        """
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.usuario, c.senha_encrypted
                    FROM credenciais_canopus c
                    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE pv.codigo = %s
                        AND c.ativo = TRUE
                        AND c.tipo_credencial = 'PRINCIPAL'
                    LIMIT 1
                """, (ponto_venda_codigo,))

                resultado = cur.fetchone()

                if resultado:
                    # Descriptografar senha
                    fernet = Fernet(self.config.ENCRYPTION_KEY.encode())
                    senha = fernet.decrypt(resultado["senha_encrypted"].encode()).decode()

                    return {
                        "usuario": resultado["usuario"],
                        "senha": senha
                    }

                return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar credenciais: {e}")
            return None

    def buscar_ponto_venda_id(self, codigo: str) -> Optional[int]:
        """Busca ID do ponto de venda pelo código"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM pontos_venda WHERE codigo = %s",
                    (codigo,)
                )
                resultado = cur.fetchone()
                return resultado["id"] if resultado else None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar ponto de venda: {e}")
            return None

    def executar_consultor(
        self,
        consultor_id: int,
        mes_referencia: str = None,
        headless: bool = None
    ) -> Dict[str, Any]:
        """
        Executa automação para um consultor específico

        Args:
            consultor_id: ID do consultor
            mes_referencia: Mês dos boletos
            headless: Executar em modo headless

        Returns:
            Dicionário com resultados
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"EXECUTANDO AUTOMAÇÃO PARA CONSULTOR ID: {consultor_id}")
        logger.info(f"{'=' * 80}\n")

        inicio = datetime.now()

        try:
            # Buscar dados do consultor
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT c.*, pv.codigo as ponto_venda_codigo
                    FROM consultores c
                    LEFT JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE c.id = %s AND c.ativo = TRUE
                """, (consultor_id,))

                consultor = cur.fetchone()

            if not consultor:
                logger.error(f"❌ Consultor {consultor_id} não encontrado ou inativo")
                return {"sucesso": False, "erro": "Consultor não encontrado"}

            logger.info(f"📋 Consultor: {consultor['nome']}")
            logger.info(f"📂 Pasta: {consultor['pasta_downloads']}")
            logger.info(f"📊 Planilha: {consultor['planilha_excel']}")

            # Verificar ponto de venda
            ponto_venda_codigo = consultor["ponto_venda_codigo"] or "CREDMS"
            ponto_venda_id = self.buscar_ponto_venda_id(ponto_venda_codigo)

            logger.info(f"🏢 Ponto de Venda: {ponto_venda_codigo}")

            # Buscar credenciais
            credenciais = self.buscar_credenciais(ponto_venda_codigo)
            if not credenciais:
                logger.error(f"❌ Credenciais não encontradas para {ponto_venda_codigo}")
                return {"sucesso": False, "erro": "Credenciais não encontradas"}

            # Importar planilha
            logger.info("\n📊 Importando planilha...")
            clientes = self.importer.ler_planilha_consultor(
                caminho_planilha=consultor["planilha_excel"],
                consultor_id=consultor_id
            )

            if not clientes:
                logger.warning("⚠️ Nenhum cliente encontrado na planilha")
                return {"sucesso": True, "clientes_processados": 0}

            # Criar execução
            self.execucao_id = self.criar_execucao(
                tipo_execucao=self.config.TipoExecucao.MANUAL,
                consultor_id=consultor_id,
                observacoes=f"Processando {len(clientes)} clientes"
            )

            # Iniciar bot
            logger.info("\n🤖 Iniciando bot Canopus...")

            with CanopusBot(
                headless=headless if headless is not None else self.config.HEADLESS,
                download_path=consultor["pasta_downloads"]
            ) as bot:

                # Fazer login
                logger.info(f"\n🔐 Fazendo login no ponto de venda: {ponto_venda_codigo}")
                login_ok = bot.fazer_login(
                    usuario=credenciais["usuario"],
                    senha=credenciais["senha"],
                    ponto_venda_codigo=ponto_venda_codigo
                )

                if not login_ok:
                    logger.error("❌ Falha no login")
                    self.atualizar_execucao(
                        self.execucao_id,
                        status=self.config.StatusExecucao.ERRO,
                        total_clientes=len(clientes)
                    )
                    return {"sucesso": False, "erro": "Falha no login"}

                # Processar clientes
                logger.info(f"\n📥 Processando {len(clientes)} clientes...\n")

                resultados = bot.processar_lote(
                    clientes=clientes,
                    pasta_destino=consultor["pasta_downloads"],
                    mes_referencia=mes_referencia or self.config.MES_PADRAO,
                    callback_progresso=lambda atual, total, res: self._callback_progresso(
                        atual, total, res, consultor_id, ponto_venda_id
                    )
                )

                # Calcular estatísticas
                stats = bot.stats
                tempo_total = (datetime.now() - inicio).total_seconds()

                # Atualizar execução
                self.atualizar_execucao(
                    self.execucao_id,
                    status=self.config.StatusExecucao.CONCLUIDA,
                    total_clientes=len(clientes),
                    total_sucessos=stats["sucessos"],
                    total_erros=stats["erros"],
                    total_nao_encontrados=stats["cpf_nao_encontrado"],
                    tempo_total=tempo_total
                )

                # Log final
                logger.info("\n" + "=" * 80)
                logger.info("AUTOMAÇÃO CONCLUÍDA!")
                logger.info("=" * 80)
                logger.info(f"✅ Total processado: {len(clientes)}")
                logger.info(f"✅ Sucessos: {stats['sucessos']}")
                logger.info(f"❌ Erros: {stats['erros']}")
                logger.info(f"⚠️ Não encontrados: {stats['cpf_nao_encontrado']}")
                logger.info(f"⏱️ Tempo total: {tempo_total:.2f}s")
                logger.info("=" * 80 + "\n")

                return {
                    "sucesso": True,
                    "clientes_processados": len(clientes),
                    "sucessos": stats["sucessos"],
                    "erros": stats["erros"],
                    "tempo_total": tempo_total,
                    "resultados": resultados
                }

        except Exception as e:
            logger.error(f"❌ Erro na execução: {e}", exc_info=True)

            if self.execucao_id:
                self.atualizar_execucao(
                    self.execucao_id,
                    status=self.config.StatusExecucao.ERRO
                )

            return {"sucesso": False, "erro": str(e)}

    def executar_todos_consultores(
        self,
        mes_referencia: str = None,
        headless: bool = None
    ):
        """
        Executa automação para todos os consultores ativos

        Args:
            mes_referencia: Mês dos boletos
            headless: Executar em modo headless
        """
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTANDO AUTOMAÇÃO PARA TODOS OS CONSULTORES")
        logger.info("=" * 80 + "\n")

        try:
            # Buscar consultores ativos
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT id, nome
                    FROM consultores
                    WHERE ativo = TRUE
                        AND planilha_excel IS NOT NULL
                    ORDER BY nome
                """)

                consultores = cur.fetchall()

            if not consultores:
                logger.warning("⚠️ Nenhum consultor ativo encontrado")
                return

            logger.info(f"📋 {len(consultores)} consultores encontrados\n")

            # Processar cada consultor
            for idx, consultor in enumerate(consultores, 1):
                logger.info(f"\n{'#' * 80}")
                logger.info(f"CONSULTOR {idx}/{len(consultores)}: {consultor['nome']}")
                logger.info(f"{'#' * 80}\n")

                resultado = self.executar_consultor(
                    consultor_id=consultor["id"],
                    mes_referencia=mes_referencia,
                    headless=headless
                )

                if resultado["sucesso"]:
                    logger.info(f"✅ {consultor['nome']}: Concluído com sucesso")
                else:
                    logger.error(f"❌ {consultor['nome']}: {resultado.get('erro')}")

                # Pausa entre consultores
                if idx < len(consultores):
                    logger.info("\n⏸️ Aguardando antes do próximo consultor...\n")
                    import time
                    time.sleep(5)

            logger.info("\n" + "=" * 80)
            logger.info("AUTOMAÇÃO DE TODOS OS CONSULTORES CONCLUÍDA!")
            logger.info("=" * 80 + "\n")

        except Exception as e:
            logger.error(f"❌ Erro ao executar todos consultores: {e}", exc_info=True)

    def _callback_progresso(
        self,
        atual: int,
        total: int,
        resultado: Dict[str, Any],
        consultor_id: int,
        ponto_venda_id: int
    ):
        """Callback chamado a cada cliente processado"""
        # Registrar log no banco
        self.registrar_log_download(consultor_id, ponto_venda_id, resultado)

        # Log de progresso
        percentual = (atual / total) * 100
        logger.info(f"📊 Progresso: {atual}/{total} ({percentual:.1f}%)")


# ============================================================================
# EXECUÇÃO VIA LINHA DE COMANDO
# ============================================================================

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Automação de Download de Boletos Canopus"
    )

    parser.add_argument(
        "--consultor",
        type=int,
        help="ID do consultor específico"
    )

    parser.add_argument(
        "--todos",
        action="store_true",
        help="Executar para todos os consultores"
    )

    parser.add_argument(
        "--mes",
        type=str,
        default="DEZEMBRO",
        help="Mês de referência dos boletos (padrão: DEZEMBRO)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executar navegador em modo headless"
    )

    parser.add_argument(
        "--visible",
        action="store_true",
        help="Executar navegador visível (força headless=False)"
    )

    args = parser.parse_args()

    # Validar argumentos
    if not args.consultor and not args.todos:
        parser.error("Especifique --consultor ID ou --todos")

    # Determinar modo headless
    headless = None
    if args.headless:
        headless = True
    elif args.visible:
        headless = False

    # Executar automação
    automacao = CanopusAutomacao()

    try:
        # Conectar ao banco
        automacao.conectar_banco()

        # Executar
        if args.todos:
            automacao.executar_todos_consultores(
                mes_referencia=args.mes,
                headless=headless
            )
        else:
            automacao.executar_consultor(
                consultor_id=args.consultor,
                mes_referencia=args.mes,
                headless=headless
            )

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execução interrompida pelo usuário")

    except Exception as e:
        logger.error(f"\n❌ Erro fatal: {e}", exc_info=True)
        return 1

    finally:
        # Desconectar do banco
        automacao.desconectar_banco()

    return 0


if __name__ == "__main__":
    sys.exit(main())
