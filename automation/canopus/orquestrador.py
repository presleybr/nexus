"""
Orquestrador da Automação Canopus
Gerencia o fluxo completo: importação, sincronização, download e registro
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row

# Adicionar paths necessários
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
canopus_path = Path(__file__).resolve().parent

# ESTRATÉGIA: Importar Database PRIMEIRO (com backend no path)
# Depois adicionar canopus para imports locais
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Importar Database do backend (antes de adicionar canopus_path)
from models.database import Database

# Agora adicionar canopus_path para imports locais
if str(canopus_path) not in sys.path:
    sys.path.insert(0, str(canopus_path))  # Canopus em PRIMEIRO para os próximos imports

# Importar módulos do canopus
from canopus_config import CanopusConfig
from excel_importer import ExcelImporter
from canopus_automation import CanopusAutomation
from db_config import get_connection_string, get_connection_params

logger = logging.getLogger(__name__)


# ============================================================================
# CLASSE DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Gerenciador de operações de banco de dados"""

    def __init__(self):
        """Inicializa o gerenciador"""
        self.config = CanopusConfig
        self.db = Database
        self.conn = None

    def conectar(self):
        """Estabelece conexão com o banco"""
        try:
            conn_params = get_connection_params()
            self.conn = psycopg.connect(**conn_params, row_factory=dict_row)
            logger.info("✅ Conectado ao banco de dados")
            return self.conn

        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise

    def desconectar(self):
        """Fecha conexão com o banco"""
        if self.conn:
            self.conn.close()
            logger.info("🔒 Desconectado do banco de dados")

    # ========================================================================
    # MÉTODOS DE EXECUÇÃO
    # ========================================================================

    def registrar_execucao(
        self,
        tipo: str,
        consultor_id: Optional[int] = None,
        parametros: Optional[Dict] = None
    ) -> str:
        """
        Registra uma nova execução da automação

        Args:
            tipo: Tipo da execução ('manual', 'agendada', 'teste')
            consultor_id: ID do consultor (None = todos)
            parametros: Parâmetros da execução

        Returns:
            UUID da execução
        """
        try:
            automacao_id = str(uuid4())

            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO execucoes_automacao (
                        automacao_id,
                        tipo,
                        consultor_id,
                        status,
                        parametros,
                        usuario_execucao
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    automacao_id,
                    tipo,
                    consultor_id,
                    'iniciada',
                    psycopg.types.json.Jsonb(parametros) if parametros else None,
                    'sistema'
                ))

                execucao_id = cur.fetchone()['id']
                self.conn.commit()

            logger.info(f"✅ Execução registrada: {automacao_id} (ID: {execucao_id})")
            return automacao_id

        except Exception as e:
            logger.error(f"❌ Erro ao registrar execução: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def atualizar_execucao(
        self,
        automacao_id: str,
        status: str = None,
        total_clientes: int = None,
        processados_sucesso: int = None,
        processados_erro: int = None,
        processados_nao_encontrado: int = None,
        processados_sem_boleto: int = None,
        progresso_percentual: float = None,
        mensagem_atual: str = None
    ):
        """
        Atualiza status da execução

        Args:
            automacao_id: UUID da execução
            status: Novo status
            total_clientes: Total de clientes
            processados_sucesso: Quantidade processada com sucesso
            processados_erro: Quantidade com erro
            processados_nao_encontrado: Quantidade não encontrada
            processados_sem_boleto: Quantidade sem boleto
            progresso_percentual: Progresso (0-100)
            mensagem_atual: Mensagem de status atual
        """
        try:
            updates = []
            params = []

            if status:
                updates.append("status = %s")
                params.append(status)

            if total_clientes is not None:
                updates.append("total_clientes = %s")
                params.append(total_clientes)

            if processados_sucesso is not None:
                updates.append("processados_sucesso = %s")
                params.append(processados_sucesso)

            if processados_erro is not None:
                updates.append("processados_erro = %s")
                params.append(processados_erro)

            if processados_nao_encontrado is not None:
                updates.append("processados_nao_encontrado = %s")
                params.append(processados_nao_encontrado)

            if processados_sem_boleto is not None:
                updates.append("processados_sem_boleto = %s")
                params.append(processados_sem_boleto)

            if progresso_percentual is not None:
                updates.append("progresso_percentual = %s")
                params.append(progresso_percentual)

            if mensagem_atual:
                updates.append("mensagem_atual = %s")
                params.append(mensagem_atual)

            if status in ['concluida', 'erro', 'cancelada']:
                updates.append("finalizado_em = CURRENT_TIMESTAMP")

                # Calcular tempo total
                with self.conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - iniciado_em))
                        FROM execucoes_automacao
                        WHERE automacao_id = %s
                    """, (automacao_id,))

                    tempo = cur.fetchone()
                    if tempo:
                        updates.append("tempo_total_segundos = %s")
                        params.append(int(tempo[0]))

            if not updates:
                return

            params.append(automacao_id)

            with self.conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE execucoes_automacao
                    SET {', '.join(updates)}
                    WHERE automacao_id = %s
                """, params)

                self.conn.commit()

            logger.debug(f"Execução {automacao_id} atualizada")

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar execução: {e}")
            if self.conn:
                self.conn.rollback()

    # ========================================================================
    # MÉTODOS DE STAGING
    # ========================================================================

    def salvar_cliente_staging(self, cliente: Dict[str, Any]) -> int:
        """
        Salva cliente na área de staging

        Args:
            cliente: Dicionário com dados do cliente

        Returns:
            ID do registro criado
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO clientes_planilha_staging (
                        cpf,
                        nome,
                        ponto_venda,
                        grupo,
                        cota,
                        contemplado,
                        consultor_nome,
                        arquivo_origem,
                        linha_planilha,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    cliente.get('cpf'),
                    cliente.get('nome'),
                    cliente.get('ponto_venda'),
                    cliente.get('grupo'),
                    cliente.get('cota'),
                    cliente.get('contemplado', False),
                    cliente.get('consultor_nome'),
                    cliente.get('arquivo_origem'),
                    cliente.get('linha_planilha'),
                    'pendente'
                ))

                staging_id = cur.fetchone()['id']
                self.conn.commit()

            return staging_id

        except Exception as e:
            logger.error(f"❌ Erro ao salvar cliente staging: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    def obter_clientes_pendentes(
        self,
        consultor_id: Optional[int] = None,
        limite: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém clientes pendentes de processamento

        Args:
            consultor_id: Filtrar por consultor (None = todos)
            limite: Limitar quantidade de resultados

        Returns:
            Lista de clientes pendentes
        """
        try:
            query = """
                SELECT s.*, c.id as consultor_id, c.ponto_venda as consultor_ponto_venda
                FROM clientes_planilha_staging s
                LEFT JOIN consultores c ON c.nome = s.consultor_nome
                WHERE s.status = 'pendente'
            """

            params = []

            if consultor_id:
                query += " AND c.id = %s"
                params.append(consultor_id)

            query += " ORDER BY s.importado_em"

            if limite:
                query += " LIMIT %s"
                params.append(limite)

            with self.conn.cursor() as cur:
                cur.execute(query, params)
                clientes = cur.fetchall()

            return clientes

        except Exception as e:
            logger.error(f"❌ Erro ao obter clientes pendentes: {e}")
            return []

    def marcar_staging_processado(self, staging_id: int, cliente_final_id: int = None):
        """Marca cliente staging como processado"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE clientes_planilha_staging
                    SET status = 'sincronizado',
                        cliente_final_id = %s,
                        sincronizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (cliente_final_id, staging_id))

                self.conn.commit()

        except Exception as e:
            logger.error(f"❌ Erro ao marcar staging processado: {e}")
            if self.conn:
                self.conn.rollback()

    # ========================================================================
    # MÉTODOS DE LOG DE DOWNLOADS
    # ========================================================================

    def registrar_download_boleto(
        self,
        automacao_id: str,
        consultor_id: int,
        cliente_final_id: Optional[int],
        resultado: Dict[str, Any]
    ) -> int:
        """
        Registra log de download de boleto

        Args:
            automacao_id: UUID da execução
            consultor_id: ID do consultor
            cliente_final_id: ID do cliente final
            resultado: Dicionário com resultado do processamento

        Returns:
            ID do log criado
        """
        try:
            dados_boleto = resultado.get('dados_boleto', {})

            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO log_downloads_boletos (
                        automacao_id,
                        consultor_id,
                        cliente_final_id,
                        cpf,
                        nome_cliente,
                        mes_referencia,
                        ano_referencia,
                        arquivo_nome,
                        arquivo_caminho,
                        arquivo_tamanho,
                        status,
                        mensagem_erro,
                        tempo_execucao_segundos
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    automacao_id,
                    consultor_id,
                    cliente_final_id,
                    resultado.get('cpf'),
                    resultado.get('dados_cliente', {}).get('nome'),
                    resultado.get('mes'),
                    resultado.get('ano'),
                    dados_boleto.get('arquivo_nome'),
                    dados_boleto.get('arquivo_caminho'),
                    dados_boleto.get('arquivo_tamanho'),
                    resultado.get('status'),
                    resultado.get('mensagem'),
                    resultado.get('tempo_execucao_segundos')
                ))

                log_id = cur.fetchone()['id']
                self.conn.commit()

            return log_id

        except Exception as e:
            logger.error(f"❌ Erro ao registrar download: {e}")
            if self.conn:
                self.conn.rollback()
            raise

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    def obter_consultor_id_por_nome(self, nome: str) -> Optional[int]:
        """Obtém ID do consultor pelo nome"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM consultores WHERE nome = %s AND ativo = TRUE",
                    (nome,)
                )
                resultado = cur.fetchone()
                return resultado['id'] if resultado else None

        except Exception as e:
            logger.error(f"❌ Erro ao obter consultor: {e}")
            return None

    def obter_credenciais(self, ponto_venda: str) -> Optional[Dict[str, str]]:
        """Obtém credenciais do ponto de venda"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT c.usuario, c.senha_encrypted, c.codigo_empresa
                    FROM credenciais_canopus c
                    INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE pv.codigo = %s AND c.ativo = TRUE
                    LIMIT 1
                """, (ponto_venda,))

                cred = cur.fetchone()

                if cred:
                    # Descriptografar senha
                    try:
                        from cryptography.fernet import Fernet
                        import base64

                        # Chave de criptografia (mesma usada em cadastrar_credencial.py)
                        ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='

                        cipher = Fernet(ENCRYPTION_KEY)

                        # Converter senha de bytes (se necessário)
                        senha_encrypted = cred['senha_encrypted']

                        logger.debug(f"Tipo da senha original: {type(senha_encrypted)}")
                        logger.debug(f"Tamanho: {len(senha_encrypted) if senha_encrypted else 0}")

                        # PostgreSQL pode retornar como memoryview, bytes ou string
                        if isinstance(senha_encrypted, memoryview):
                            senha_encrypted = bytes(senha_encrypted)
                            logger.debug("Convertido de memoryview para bytes")
                        elif isinstance(senha_encrypted, str):
                            # Se for string, pode estar em formato hex (PostgreSQL bytea)
                            if senha_encrypted.startswith('\\x'):
                                # Formato hex do PostgreSQL: remover \\x e converter
                                hex_string = senha_encrypted[2:]  # Remove \\x
                                senha_encrypted = bytes.fromhex(hex_string)
                                logger.debug(f"Convertido de hex string (\\x...) para bytes. Hex: {hex_string[:20]}...")
                            else:
                                # Tentar como base64
                                try:
                                    senha_encrypted = base64.b64decode(senha_encrypted)
                                    logger.debug("Convertido de base64 string para bytes")
                                except:
                                    senha_encrypted = senha_encrypted.encode()
                                    logger.debug("Convertido de string para bytes (encode)")

                        logger.debug(f"Tipo final: {type(senha_encrypted)}, Tamanho: {len(senha_encrypted)}")

                        senha_decrypted = cipher.decrypt(senha_encrypted).decode()

                        logger.info("✅ Senha descriptografada com sucesso")

                        return {
                            'usuario': cred['usuario'],
                            'senha': senha_decrypted,
                            'codigo_empresa': cred['codigo_empresa']
                        }
                    except Exception as e:
                        logger.error(f"❌ Erro ao descriptografar senha: {e}")
                        logger.exception("Detalhes do erro:")
                        return None

                return None

        except Exception as e:
            logger.error(f"❌ Erro ao obter credenciais: {e}")
            return None

    def __enter__(self):
        """Context manager - entrada"""
        self.conectar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.desconectar()


# ============================================================================
# CLASSE ORQUESTRADOR
# ============================================================================

class CanopusOrquestrador:
    """Orquestrador do fluxo completo de automação"""

    def __init__(self):
        """Inicializa o orquestrador"""
        self.config = CanopusConfig
        self.db_manager = DatabaseManager()
        self.excel_importer = ExcelImporter()
        self.automacao_id = None

    # ========================================================================
    # IMPORTAÇÃO DE PLANILHAS
    # ========================================================================

    def importar_planilhas(self, diretorio: Path = None) -> Dict[str, Any]:
        """
        Importa planilhas Excel para a área de staging

        Args:
            diretorio: Diretório das planilhas (padrão: EXCEL_DIR)

        Returns:
            Dicionário com estatísticas da importação
        """
        logger.info("=" * 80)
        logger.info("IMPORTAÇÃO DE PLANILHAS")
        logger.info("=" * 80)

        stats = {
            'total_planilhas': 0,
            'total_clientes': 0,
            'clientes_salvos': 0,
            'erros': 0,
            'planilhas_processadas': [],
        }

        try:
            with self.db_manager:
                # Registrar execução
                self.automacao_id = self.db_manager.registrar_execucao(
                    tipo='manual',
                    parametros={'operacao': 'importacao_planilhas'}
                )

                # Listar planilhas
                planilhas = self.excel_importer.listar_planilhas(diretorio)
                stats['total_planilhas'] = len(planilhas)

                if not planilhas:
                    logger.warning("⚠️ Nenhuma planilha encontrada")
                    self.db_manager.atualizar_execucao(
                        self.automacao_id,
                        status='concluida',
                        mensagem_atual='Nenhuma planilha encontrada'
                    )
                    return stats

                # Processar cada planilha
                for idx, planilha in enumerate(planilhas, 1):
                    logger.info(f"\n📊 [{idx}/{len(planilhas)}] Processando: {planilha.name}")

                    try:
                        # Extrair clientes
                        clientes = self.excel_importer.extrair_clientes(planilha)
                        stats['total_clientes'] += len(clientes)

                        # Salvar no staging
                        salvos = 0
                        for cliente in clientes:
                            try:
                                self.db_manager.salvar_cliente_staging(cliente)
                                salvos += 1
                            except Exception as e:
                                logger.error(f"Erro ao salvar cliente {cliente.get('cpf')}: {e}")
                                stats['erros'] += 1

                        stats['clientes_salvos'] += salvos

                        stats['planilhas_processadas'].append({
                            'arquivo': planilha.name,
                            'clientes': len(clientes),
                            'salvos': salvos
                        })

                        logger.info(f"✅ {salvos}/{len(clientes)} clientes salvos")

                    except Exception as e:
                        logger.error(f"❌ Erro ao processar {planilha.name}: {e}")
                        stats['erros'] += 1

                    # Atualizar progresso
                    progresso = (idx / len(planilhas)) * 100
                    self.db_manager.atualizar_execucao(
                        self.automacao_id,
                        status='em_andamento',
                        progresso_percentual=progresso,
                        mensagem_atual=f'Processando planilha {idx}/{len(planilhas)}'
                    )

                # Finalizar
                self.db_manager.atualizar_execucao(
                    self.automacao_id,
                    status='concluida',
                    total_clientes=stats['total_clientes'],
                    mensagem_atual=f"{stats['clientes_salvos']} clientes importados"
                )

                # Log final
                logger.info("\n" + "=" * 80)
                logger.info("RESUMO DA IMPORTAÇÃO")
                logger.info("=" * 80)
                logger.info(f"📊 Planilhas processadas: {stats['total_planilhas']}")
                logger.info(f"👥 Total de clientes: {stats['total_clientes']}")
                logger.info(f"✅ Clientes salvos: {stats['clientes_salvos']}")
                logger.info(f"❌ Erros: {stats['erros']}")
                logger.info("=" * 80 + "\n")

                return stats

        except Exception as e:
            logger.error(f"❌ Erro na importação: {e}")
            if self.automacao_id:
                self.db_manager.atualizar_execucao(
                    self.automacao_id,
                    status='erro',
                    mensagem_atual=str(e)
                )
            raise

    # ========================================================================
    # SINCRONIZAÇÃO COM CLIENTES_FINAIS
    # ========================================================================

    def sincronizar_clientes(self) -> Dict[str, Any]:
        """
        Sincroniza clientes do staging para clientes_finais

        Returns:
            Dicionário com estatísticas
        """
        logger.info("=" * 80)
        logger.info("SINCRONIZAÇÃO DE CLIENTES")
        logger.info("=" * 80)

        stats = {
            'total_pendentes': 0,
            'sincronizados': 0,
            'erros': 0,
        }

        try:
            with self.db_manager:
                # Obter clientes pendentes
                pendentes = self.db_manager.obter_clientes_pendentes()
                stats['total_pendentes'] = len(pendentes)

                logger.info(f"📋 {len(pendentes)} clientes pendentes de sincronização")

                for cliente in pendentes:
                    try:
                        # TODO: Verificar se já existe em clientes_finais
                        # TODO: Criar ou atualizar em clientes_finais
                        # TODO: Marcar como sincronizado

                        # Por enquanto, apenas marcar como processado
                        self.db_manager.marcar_staging_processado(cliente['id'])
                        stats['sincronizados'] += 1

                    except Exception as e:
                        logger.error(f"Erro ao sincronizar cliente {cliente['cpf']}: {e}")
                        stats['erros'] += 1

                logger.info(f"✅ {stats['sincronizados']} clientes sincronizados")
                return stats

        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
            raise

    # ========================================================================
    # PROCESSAMENTO DE DOWNLOADS
    # ========================================================================

    async def processar_downloads(
        self,
        consultor_nome: str,
        mes: str,
        ano: int = None,
        limite: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processa downloads de boletos

        Args:
            consultor_nome: Nome do consultor
            mes: Mês dos boletos
            ano: Ano dos boletos (padrão: ano atual)
            limite: Limitar quantidade de clientes

        Returns:
            Dicionário com estatísticas
        """
        if ano is None:
            ano = datetime.now().year

        logger.info("=" * 80)
        logger.info(f"DOWNLOAD DE BOLETOS - {consultor_nome} - {mes}/{ano}")
        logger.info("=" * 80)

        stats = {
            'total_clientes': 0,
            'sucessos': 0,
            'erros': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
        }

        try:
            with self.db_manager:
                # Obter ID do consultor
                consultor_id = self.db_manager.obter_consultor_id_por_nome(consultor_nome)

                if not consultor_id:
                    raise ValueError(f"Consultor '{consultor_nome}' não encontrado")

                # Registrar execução
                self.automacao_id = self.db_manager.registrar_execucao(
                    tipo='manual',
                    consultor_id=consultor_id,
                    parametros={
                        'operacao': 'download_boletos',
                        'mes': mes,
                        'ano': ano
                    }
                )

                # Obter clientes pendentes
                clientes = self.db_manager.obter_clientes_pendentes(
                    consultor_id=consultor_id,
                    limite=limite
                )

                stats['total_clientes'] = len(clientes)

                if not clientes:
                    logger.warning("⚠️ Nenhum cliente pendente")
                    self.db_manager.atualizar_execucao(
                        self.automacao_id,
                        status='concluida',
                        total_clientes=0
                    )
                    return stats

                logger.info(f"👥 {len(clientes)} clientes para processar")

                # Obter credenciais
                ponto_venda = clientes[0]['consultor_ponto_venda']
                credenciais = self.db_manager.obter_credenciais(ponto_venda)

                if not credenciais:
                    raise ValueError(f"Credenciais não encontradas para ponto {ponto_venda}")

                # Iniciar automação
                async with CanopusAutomation(headless=False) as bot:
                    # Fazer login
                    logger.info(f"🔐 Fazendo login no ponto {ponto_venda}...")

                    login_ok = await bot.login(
                        codigo_empresa=credenciais['codigo_empresa'],
                        ponto_venda=ponto_venda,
                        usuario=credenciais['usuario'],
                        senha=credenciais['senha']
                    )

                    if not login_ok:
                        raise Exception("Falha no login")

                    # Processar cada cliente
                    for idx, cliente in enumerate(clientes, 1):
                        logger.info(f"\n{'=' * 80}")
                        logger.info(f"[{idx}/{len(clientes)}] CPF: {cliente['cpf']}")
                        logger.info(f"{'=' * 80}")

                        try:
                            # Preparar destino
                            destino = self.config.get_consultor_dir(consultor_nome)
                            nome_arquivo = self.config.gerar_nome_boleto(
                                cliente['cpf'],
                                mes,
                                ano
                            )

                            # Processar cliente
                            resultado = await bot.processar_cliente_completo(
                                cpf=cliente['cpf'],
                                mes=mes,
                                ano=ano,
                                destino=destino,
                                nome_arquivo=nome_arquivo
                            )

                            # Registrar log
                            self.db_manager.registrar_download_boleto(
                                automacao_id=self.automacao_id,
                                consultor_id=consultor_id,
                                cliente_final_id=cliente.get('cliente_final_id'),
                                resultado=resultado
                            )

                            # Atualizar estatísticas
                            if resultado['status'] == self.config.Status.SUCESSO:
                                stats['sucessos'] += 1
                            elif resultado['status'] == self.config.Status.CPF_NAO_ENCONTRADO:
                                stats['cpf_nao_encontrado'] += 1
                            elif resultado['status'] == self.config.Status.SEM_BOLETO:
                                stats['sem_boleto'] += 1
                            else:
                                stats['erros'] += 1

                            # Atualizar progresso
                            progresso = (idx / len(clientes)) * 100
                            self.db_manager.atualizar_execucao(
                                self.automacao_id,
                                status='em_andamento',
                                total_clientes=stats['total_clientes'],
                                processados_sucesso=stats['sucessos'],
                                processados_erro=stats['erros'],
                                processados_nao_encontrado=stats['cpf_nao_encontrado'],
                                processados_sem_boleto=stats['sem_boleto'],
                                progresso_percentual=progresso,
                                mensagem_atual=f'Processando cliente {idx}/{len(clientes)}'
                            )

                            # Delay entre downloads
                            if idx < len(clientes):
                                await asyncio.sleep(self.config.DELAYS['entre_downloads'])

                        except Exception as e:
                            logger.error(f"❌ Erro ao processar cliente: {e}")
                            stats['erros'] += 1

                # Finalizar execução
                self.db_manager.atualizar_execucao(
                    self.automacao_id,
                    status='concluida',
                    total_clientes=stats['total_clientes'],
                    processados_sucesso=stats['sucessos'],
                    processados_erro=stats['erros'],
                    processados_nao_encontrado=stats['cpf_nao_encontrado'],
                    processados_sem_boleto=stats['sem_boleto'],
                    progresso_percentual=100.0
                )

                # Log final
                logger.info("\n" + "=" * 80)
                logger.info("RESUMO DOS DOWNLOADS")
                logger.info("=" * 80)
                logger.info(f"👥 Total de clientes: {stats['total_clientes']}")
                logger.info(f"✅ Sucessos: {stats['sucessos']}")
                logger.info(f"❌ Erros: {stats['erros']}")
                logger.info(f"⚠️ CPF não encontrado: {stats['cpf_nao_encontrado']}")
                logger.info(f"📄 Sem boleto: {stats['sem_boleto']}")
                logger.info("=" * 80 + "\n")

                return stats

        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            if self.automacao_id:
                self.db_manager.atualizar_execucao(
                    self.automacao_id,
                    status='erro',
                    mensagem_atual=str(e)
                )
            raise

    # ========================================================================
    # DOWNLOAD DE BOLETO INDIVIDUAL
    # ========================================================================

    async def baixar_boleto_cpf(
        self,
        cpf: str,
        mes: str,
        ano: int = None,
        pasta_destino: str = None,
        usuario: str = None,
        senha: str = None,
        codigo_empresa: str = '0101'
    ) -> Dict[str, Any]:
        """
        Baixa boleto de um CPF específico

        Args:
            cpf: CPF do cliente
            mes: Mês do boleto
            ano: Ano do boleto (padrão: ano atual)
            pasta_destino: Pasta de destino (padrão: downloads/Danner)
            usuario: Usuário do Canopus (opcional, busca do banco se não fornecido)
            senha: Senha do Canopus (opcional, busca do banco se não fornecido)
            codigo_empresa: Código da empresa (padrão: 0101)

        Returns:
            Dicionário com resultado do processamento
        """
        if ano is None:
            ano = datetime.now().year

        if pasta_destino is None:
            pasta_destino = Path(__file__).parent / "downloads" / "Danner"
        else:
            pasta_destino = Path(pasta_destino)

        # Garantir que a pasta existe
        pasta_destino.mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 Baixando boleto: CPF {cpf}, Mês {mes}, Ano {ano}")

        resultado = {
            'cpf': cpf,
            'mes': mes,
            'ano': ano,
            'sucesso': False,
            'status': None,
            'mensagem': None,
            'arquivo': None
        }

        try:
            # Se credenciais não foram fornecidas, buscar do banco
            if not usuario or not senha:
                with self.db_manager:
                    credenciais = self.db_manager.obter_credenciais('24627')

                    if not credenciais:
                        raise ValueError(
                            "Credenciais não encontradas no banco. "
                            "Execute: python automation/canopus/cadastrar_credencial.py"
                        )

                    usuario = credenciais['usuario']
                    senha = credenciais['senha']
                    codigo_empresa = credenciais.get('codigo_empresa', '0101')

            # Iniciar automação
            async with CanopusAutomation(headless=False) as bot:
                # Fazer login
                logger.info("🔐 Fazendo login no ponto 24627...")

                login_ok = await bot.login(
                    usuario=usuario,
                    senha=senha,
                    codigo_empresa=codigo_empresa,
                    ponto_venda='24627'
                )

                if not login_ok:
                    resultado['status'] = 'erro_login'
                    resultado['mensagem'] = 'Falha no login'
                    return resultado

                # Gerar nome do arquivo
                nome_arquivo = self.config.gerar_nome_boleto(cpf, mes, ano)

                # Processar cliente
                resultado_processamento = await bot.processar_cliente_completo(
                    cpf=cpf,
                    mes=mes,
                    ano=ano,
                    destino=pasta_destino,
                    nome_arquivo=nome_arquivo
                )

                # Mapear resultado
                resultado['status'] = resultado_processamento.get('status')
                resultado['mensagem'] = resultado_processamento.get('mensagem')

                if resultado_processamento.get('status') == self.config.Status.SUCESSO:
                    resultado['sucesso'] = True
                    resultado['arquivo'] = resultado_processamento.get('dados_boleto', {}).get('arquivo_caminho')

                return resultado

        except Exception as e:
            logger.error(f"❌ Erro ao baixar boleto: {e}")
            resultado['status'] = 'erro'
            resultado['mensagem'] = str(e)
            return resultado

    # ========================================================================
    # IMPORTAÇÃO DE BOLETOS PARA CRM
    # ========================================================================

    def importar_boletos_para_crm(self) -> Dict[str, Any]:
        """
        Importa boletos baixados (PDFs) da pasta para tabela de boletos do CRM

        Returns:
            Dicionário com estatísticas
        """
        logger.info("=" * 80)
        logger.info("IMPORTAÇÃO DE BOLETOS PARA CRM")
        logger.info("=" * 80)

        stats = {
            'total_pdfs': 0,
            'importados': 0,
            'ja_existentes': 0,
            'erros': 0,
            'sem_cliente': 0
        }

        try:
            # Pasta de downloads
            from pathlib import Path
            from datetime import datetime

            downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

            if not downloads_dir.exists():
                logger.error(f"Pasta de downloads não encontrada: {downloads_dir}")
                return stats

            # Listar todos os PDFs
            pdfs = list(downloads_dir.glob("*.pdf"))
            stats['total_pdfs'] = len(pdfs)

            logger.info(f"📁 Encontrados {len(pdfs)} PDFs na pasta")

            # Mapeamento de meses
            meses = {
                'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'MARCO': 3,
                'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6,
                'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9,
                'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
            }

            with self.db_manager:
                for pdf_file in pdfs:
                    try:
                        # Extrair informações do nome do arquivo
                        # Formato esperado: NOME_CLIENTE_MES.pdf ou NOME_CLIENTE_MES_ANO.pdf
                        nome_arquivo = pdf_file.stem
                        partes = nome_arquivo.split('_')

                        if len(partes) < 2:
                            logger.warning(f"⚠️ Nome de arquivo inválido: {pdf_file.name}")
                            stats['erros'] += 1
                            continue

                        # Última parte é mês (ou ano se tiver 4 dígitos)
                        mes_str = partes[-1].upper()
                        ano = datetime.now().year

                        # Verificar se última parte é ano (4 dígitos)
                        if mes_str.isdigit() and len(mes_str) == 4:
                            ano = int(mes_str)
                            mes_str = partes[-2].upper() if len(partes) > 2 else 'NOVEMBRO'

                        # Nome do cliente (tudo antes do mês)
                        if len(partes) > 2 and partes[-1].isdigit() and len(partes[-1]) == 4:
                            nome_cliente = '_'.join(partes[:-2])
                        else:
                            nome_cliente = '_'.join(partes[:-1])

                        nome_cliente_formatado = nome_cliente.replace('_', ' ').title()

                        # Converter mês para número
                        mes_num = meses.get(mes_str, datetime.now().month)

                        logger.info(f"📄 Processando: {nome_cliente_formatado} - {mes_str}/{ano}")

                        # Buscar cliente no banco
                        with self.db_manager.conn.cursor() as cur:
                            # Tentar buscar por nome (case-insensitive)
                            cur.execute("""
                                SELECT id, cpf, nome_completo
                                FROM clientes_finais
                                WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
                                LIMIT 1
                            """, (nome_cliente_formatado,))

                            cliente = cur.fetchone()

                            if not cliente:
                                logger.warning(f"⚠️ Cliente não encontrado: {nome_cliente_formatado}")
                                stats['sem_cliente'] += 1
                                continue

                            cliente_id = cliente[0]
                            cliente_cpf = cliente[1]
                            logger.info(f"✅ Cliente encontrado: {cliente[2]} (ID: {cliente_id})")

                            # Verificar se boleto já existe
                            cur.execute("""
                                SELECT id FROM boletos
                                WHERE cliente_final_id = %s
                                  AND mes_referencia = %s
                                  AND ano_referencia = %s
                                  AND pdf_filename = %s
                            """, (cliente_id, mes_num, ano, pdf_file.name))

                            boleto_existente = cur.fetchone()

                            if boleto_existente:
                                logger.info(f"⏭️ Boleto já existe no banco")
                                stats['ja_existentes'] += 1
                                continue

                            # Gerar número único do boleto
                            numero_boleto = f"CANOPUS-{cliente_cpf}-{mes_num:02d}{ano}"

                            # Inserir boleto
                            cur.execute("""
                                INSERT INTO boletos (
                                    cliente_final_id,
                                    numero_boleto,
                                    valor_original,
                                    data_vencimento,
                                    data_emissao,
                                    mes_referencia,
                                    ano_referencia,
                                    numero_parcela,
                                    descricao,
                                    status,
                                    status_envio,
                                    pdf_filename,
                                    pdf_path,
                                    pdf_size,
                                    gerado_por,
                                    created_at,
                                    updated_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                                )
                                RETURNING id
                            """, (
                                cliente_id,
                                numero_boleto,
                                0.0,  # Valor será atualizado depois
                                datetime(ano, mes_num, 28),  # Data de vencimento aproximada
                                datetime.now().date(),
                                mes_num,
                                ano,
                                1,  # Parcela 1 por padrão
                                f"Boleto {mes_str}/{ano} - {nome_cliente_formatado}",
                                'pendente',
                                'nao_enviado',
                                pdf_file.name,
                                str(pdf_file),
                                pdf_file.stat().st_size,
                                'automacao_canopus'
                            ))

                            boleto_id = cur.fetchone()[0]
                            self.db_manager.conn.commit()

                            logger.info(f"✅ Boleto importado! ID: {boleto_id}")
                            stats['importados'] += 1

                    except Exception as e:
                        logger.error(f"❌ Erro ao importar {pdf_file.name}: {e}")
                        stats['erros'] += 1
                        continue

            logger.info("=" * 80)
            logger.info("📊 RESUMO DA IMPORTAÇÃO")
            logger.info("=" * 80)
            logger.info(f"📁 Total de PDFs: {stats['total_pdfs']}")
            logger.info(f"✅ Importados: {stats['importados']}")
            logger.info(f"⏭️ Já existentes: {stats['ja_existentes']}")
            logger.info(f"⚠️ Sem cliente: {stats['sem_cliente']}")
            logger.info(f"❌ Erros: {stats['erros']}")
            logger.info("=" * 80)

            return stats

        except Exception as e:
            logger.error(f"❌ Erro na importação: {e}")
            import traceback
            traceback.print_exc()
            raise


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA PARA CLI
# ============================================================================

def executar_importacao_planilhas(diretorio: str = None):
    """
    Executa importação de planilhas via CLI

    Args:
        diretorio: Diretório das planilhas (opcional)
    """
    try:
        orquestrador = CanopusOrquestrador()

        dir_path = Path(diretorio) if diretorio else None
        stats = orquestrador.importar_planilhas(dir_path)

        print("\n✅ Importação concluída!")
        print(f"   Planilhas: {stats['total_planilhas']}")
        print(f"   Clientes salvos: {stats['clientes_salvos']}")

        return 0

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return 1


def executar_download_boletos(
    consultor: str,
    mes: str,
    ano: int = None,
    limite: int = None
):
    """
    Executa download de boletos via CLI

    Args:
        consultor: Nome do consultor
        mes: Mês dos boletos
        ano: Ano dos boletos
        limite: Limitar quantidade
    """
    try:
        orquestrador = CanopusOrquestrador()

        stats = asyncio.run(
            orquestrador.processar_downloads(
                consultor_nome=consultor,
                mes=mes,
                ano=ano,
                limite=limite
            )
        )

        print("\n✅ Downloads concluídos!")
        print(f"   Sucessos: {stats['sucessos']}")
        print(f"   Erros: {stats['erros']}")

        return 0

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        return 1


def executar_fluxo_completo(
    consultor: str,
    mes: str,
    ano: int = None
):
    """
    Executa fluxo completo: importação + sincronização + download

    Args:
        consultor: Nome do consultor
        mes: Mês dos boletos
        ano: Ano dos boletos
    """
    try:
        orquestrador = CanopusOrquestrador()

        # 1. Importar planilhas
        logger.info("\n🔄 ETAPA 1: Importando planilhas...")
        orquestrador.importar_planilhas()

        # 2. Sincronizar clientes
        logger.info("\n🔄 ETAPA 2: Sincronizando clientes...")
        orquestrador.sincronizar_clientes()

        # 3. Baixar boletos
        logger.info("\n🔄 ETAPA 3: Baixando boletos...")
        asyncio.run(
            orquestrador.processar_downloads(
                consultor_nome=consultor,
                mes=mes,
                ano=ano
            )
        )

        # 4. Importar para CRM
        logger.info("\n🔄 ETAPA 4: Importando boletos para CRM...")
        orquestrador.importar_boletos_para_crm()

        print("\n✅ Fluxo completo concluído com sucesso!")
        return 0

    except Exception as e:
        logger.error(f"❌ Erro no fluxo: {e}")
        return 1


# ============================================================================
# EXECUÇÃO VIA CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Orquestrador de Automação Canopus - Nexus CRM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Importar planilhas Excel
  python orquestrador.py importar --diretorio ..\\..\\planilhas

  # Sincronizar staging para clientes_finais
  python orquestrador.py sincronizar

  # Baixar boletos de um consultor
  python orquestrador.py download --consultor Dayler --mes DEZEMBRO --ano 2024

  # Importar boletos para CRM
  python orquestrador.py importar-crm

  # Fluxo completo (1+2+3+4)
  python orquestrador.py completo --consultor Dayler --mes DEZEMBRO

  # Ver status das execuções
  python orquestrador.py status
        """
    )

    subparsers = parser.add_subparsers(dest='comando', help='Comando a executar')

    # Comando: importar
    parser_importar = subparsers.add_parser(
        'importar',
        help='Importar planilhas Excel para staging'
    )
    parser_importar.add_argument(
        '--diretorio',
        help='Diretório das planilhas (padrão: D:\\Nexus\\planilhas)'
    )

    # Comando: sincronizar
    parser_sincronizar = subparsers.add_parser(
        'sincronizar',
        help='Sincronizar clientes do staging para clientes_finais'
    )

    # Comando: download
    parser_download = subparsers.add_parser(
        'download',
        help='Baixar boletos do Canopus'
    )
    parser_download.add_argument(
        '--consultor',
        required=True,
        help='Nome do consultor (Dayler, Neto, Mirelli, Danner)'
    )
    parser_download.add_argument(
        '--mes',
        required=True,
        help='Mês dos boletos (DEZEMBRO, JANEIRO, etc.)'
    )
    parser_download.add_argument(
        '--ano',
        type=int,
        help='Ano dos boletos (padrão: ano atual)'
    )
    parser_download.add_argument(
        '--limite',
        type=int,
        help='Limitar quantidade de clientes a processar'
    )

    # Comando: importar-crm
    parser_importar_crm = subparsers.add_parser(
        'importar-crm',
        help='Importar boletos baixados para tabela boletos do CRM'
    )

    # Comando: completo
    parser_completo = subparsers.add_parser(
        'completo',
        help='Executar fluxo completo: importar + sincronizar + download + importar-crm'
    )
    parser_completo.add_argument(
        '--consultor',
        help='Nome do consultor (deixe vazio para todos)'
    )
    parser_completo.add_argument(
        '--mes',
        required=True,
        help='Mês dos boletos (DEZEMBRO, JANEIRO, etc.)'
    )
    parser_completo.add_argument(
        '--ano',
        type=int,
        help='Ano dos boletos (padrão: ano atual)'
    )

    # Comando: status
    parser_status = subparsers.add_parser(
        'status',
        help='Exibir status das últimas execuções'
    )
    parser_status.add_argument(
        '--limite',
        type=int,
        default=10,
        help='Quantidade de execuções a exibir (padrão: 10)'
    )

    args = parser.parse_args()

    # Executar comando
    if args.comando == 'importar':
        sys.exit(executar_importacao_planilhas(args.diretorio))

    elif args.comando == 'sincronizar':
        try:
            orquestrador = CanopusOrquestrador()
            stats = orquestrador.sincronizar_clientes()
            print(f"\n✅ Sincronização concluída!")
            print(f"   Sincronizados: {stats['sincronizados']}")
            print(f"   Erros: {stats['erros']}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            sys.exit(1)

    elif args.comando == 'download':
        sys.exit(executar_download_boletos(
            consultor=args.consultor,
            mes=args.mes,
            ano=args.ano,
            limite=args.limite
        ))

    elif args.comando == 'importar-crm':
        try:
            orquestrador = CanopusOrquestrador()
            stats = orquestrador.importar_boletos_para_crm()
            print(f"\n✅ Importação para CRM concluída!")
            print(f"   Boletos importados: {stats['importados']}")
            print(f"   Erros: {stats['erros']}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            sys.exit(1)

    elif args.comando == 'completo':
        # Se consultor não especificado, processar todos
        if args.consultor:
            sys.exit(executar_fluxo_completo(
                consultor=args.consultor,
                mes=args.mes,
                ano=args.ano
            ))
        else:
            # Processar todos os consultores
            try:
                orquestrador = CanopusOrquestrador()

                # 1. Importar planilhas
                logger.info("\n🔄 ETAPA 1/4: Importando planilhas...")
                orquestrador.importar_planilhas()

                # 2. Sincronizar clientes
                logger.info("\n🔄 ETAPA 2/4: Sincronizando clientes...")
                orquestrador.sincronizar_clientes()

                # 3. Baixar boletos de todos os consultores
                logger.info("\n🔄 ETAPA 3/4: Baixando boletos de todos os consultores...")
                consultores = ['Dayler', 'Neto', 'Mirelli', 'Danner']

                for consultor in consultores:
                    logger.info(f"\n>>> Processando {consultor}...")
                    try:
                        asyncio.run(
                            orquestrador.processar_downloads(
                                consultor_nome=consultor,
                                mes=args.mes,
                                ano=args.ano
                            )
                        )
                    except Exception as e:
                        logger.error(f"Erro ao processar {consultor}: {e}")

                # 4. Importar para CRM
                logger.info("\n🔄 ETAPA 4/4: Importando boletos para CRM...")
                orquestrador.importar_boletos_para_crm()

                print("\n✅ Fluxo completo concluído para todos os consultores!")
                sys.exit(0)

            except Exception as e:
                logger.error(f"❌ Erro no fluxo: {e}")
                sys.exit(1)

    elif args.comando == 'status':
        try:
            with DatabaseManager() as db:
                with db.conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT
                            e.id,
                            e.automacao_id,
                            e.tipo,
                            c.nome as consultor,
                            e.status,
                            e.iniciado_em,
                            e.finalizado_em,
                            e.tempo_total_segundos,
                            e.total_clientes,
                            e.processados_sucesso,
                            e.processados_erro,
                            e.processados_nao_encontrado,
                            e.processados_sem_boleto,
                            e.progresso_percentual,
                            e.mensagem_atual
                        FROM execucoes_automacao e
                        LEFT JOIN consultores c ON e.consultor_id = c.id
                        ORDER BY e.iniciado_em DESC
                        LIMIT {args.limite}
                    """)

                    execucoes = cur.fetchall()

                    if not execucoes:
                        print("\n⚠️ Nenhuma execução encontrada")
                        sys.exit(0)

                    print("\n" + "=" * 100)
                    print("STATUS DAS EXECUÇÕES - AUTOMAÇÃO CANOPUS")
                    print("=" * 100)

                    for exec in execucoes:
                        print(f"\nID: {exec['id']} | UUID: {exec['automacao_id'][:8]}...")
                        print(f"Tipo: {exec['tipo']} | Consultor: {exec['consultor'] or 'Todos'}")
                        print(f"Status: {exec['status']} | Progresso: {exec['progresso_percentual'] or 0:.1f}%")
                        print(f"Iniciado: {exec['iniciado_em']}")

                        if exec['finalizado_em']:
                            print(f"Finalizado: {exec['finalizado_em']} ({exec['tempo_total_segundos']}s)")

                        if exec['total_clientes']:
                            print(f"Clientes: {exec['total_clientes']} | "
                                  f"✅ {exec['processados_sucesso'] or 0} | "
                                  f"❌ {exec['processados_erro'] or 0} | "
                                  f"⚠️ {exec['processados_nao_encontrado'] or 0} | "
                                  f"📄 {exec['processados_sem_boleto'] or 0}")

                        if exec['mensagem_atual']:
                            print(f"Mensagem: {exec['mensagem_atual']}")

                        print("-" * 100)

                    print()
                    sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Erro ao exibir status: {e}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)
