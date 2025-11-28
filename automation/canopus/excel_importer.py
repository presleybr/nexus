"""
Importador e Monitor de Planilhas Excel
Lê planilhas dos consultores e detecta alterações automaticamente
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
import hashlib
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from canopus_config import CanopusConfig, Consultor

logger = logging.getLogger(__name__)


# ============================================================================
# CLASSE IMPORTADOR DE EXCEL
# ============================================================================

class ExcelImporter:
    """Importa dados de planilhas Excel dos consultores"""

    def __init__(self, config: CanopusConfig = None):
        """
        Inicializa o importador

        Args:
            config: Configuração (usa padrão se não fornecido)
        """
        self.config = config or CanopusConfig

    def listar_planilhas(self, diretorio: Path = None) -> List[Path]:
        """
        Lista todas as planilhas Excel no diretório

        Args:
            diretorio: Diretório para buscar (padrão: EXCEL_DIR)

        Returns:
            Lista de caminhos para arquivos Excel
        """
        dir_busca = diretorio or self.config.EXCEL_DIR

        planilhas = []
        for extensao in ['*.xlsx', '*.xls', '*.xlsm']:
            planilhas.extend(dir_busca.glob(extensao))

        # Filtrar arquivos temporários do Excel
        planilhas = [p for p in planilhas if not p.name.startswith('~$')]

        logger.info(f"📊 Encontradas {len(planilhas)} planilhas em {dir_busca}")
        return sorted(planilhas)

    def identificar_consultor(self, caminho_planilha: Path) -> Optional[Consultor]:
        """
        Identifica consultor pelo nome do arquivo

        Args:
            caminho_planilha: Caminho da planilha

        Returns:
            Objeto Consultor ou None
        """
        consultor = self.config.get_consultor_by_filename(caminho_planilha.name)

        if consultor:
            logger.info(f"✅ Consultor identificado: {consultor.nome}")
        else:
            logger.warning(f"⚠️ Consultor não identificado para: {caminho_planilha.name}")

        return consultor

    def encontrar_coluna(
        self,
        df: pd.DataFrame,
        variacoes: List[str]
    ) -> Optional[str]:
        """
        Busca flexível de coluna por múltiplas variações de nome

        Args:
            df: DataFrame
            variacoes: Lista de possíveis nomes da coluna

        Returns:
            Nome da coluna encontrada ou None
        """
        # Normalizar colunas do DataFrame
        colunas_normalizadas = {
            col: col.strip().upper().replace(' ', '_')
            for col in df.columns
        }

        # Buscar correspondência
        for variacao in variacoes:
            variacao_norm = variacao.strip().upper().replace(' ', '_')

            # Busca exata
            for col_original, col_norm in colunas_normalizadas.items():
                if col_norm == variacao_norm:
                    return col_original

            # Busca parcial (contém)
            for col_original, col_norm in colunas_normalizadas.items():
                if variacao_norm in col_norm or col_norm in variacao_norm:
                    return col_original

        return None

    def mapear_colunas(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Mapeia automaticamente as colunas da planilha

        Args:
            df: DataFrame

        Returns:
            Dicionário {campo: nome_coluna}
        """
        mapeamento = {}
        excel_cols = self.config.EXCEL_COLUMNS

        # Mapear cada campo
        campos = {
            'cpf': excel_cols.cpf_variations,
            'nome': excel_cols.nome_variations,
            'grupo': excel_cols.grupo_variations,
            'cota': excel_cols.cota_variations,
            'ponto_venda': excel_cols.ponto_venda_variations,
            'whatsapp': excel_cols.whatsapp_variations,
            'contemplado': excel_cols.contemplado_variations,
        }

        for campo, variacoes in campos.items():
            coluna = self.encontrar_coluna(df, variacoes)
            if coluna:
                mapeamento[campo] = coluna
                logger.debug(f"  ✓ {campo}: {coluna}")

        logger.info(f"📋 Colunas mapeadas: {list(mapeamento.keys())}")
        return mapeamento

    def extrair_clientes(
        self,
        caminho_planilha: Path,
        sheet_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extrai dados dos clientes da planilha

        Args:
            caminho_planilha: Caminho do arquivo Excel
            sheet_name: Nome da aba (None = primeira aba)

        Returns:
            Lista de dicionários com dados dos clientes
        """
        logger.info(f"📖 Lendo planilha: {caminho_planilha.name}")

        try:
            # Ler Excel
            df = pd.read_excel(
                caminho_planilha,
                sheet_name=sheet_name or 0,
                dtype=str  # Ler tudo como string
            )

            # Remover linhas vazias
            df = df.dropna(how='all')

            if df.empty:
                logger.warning(f"⚠️ Planilha vazia: {caminho_planilha.name}")
                return []

            logger.info(f"📊 Linhas encontradas: {len(df)}")

            # Identificar consultor
            consultor = self.identificar_consultor(caminho_planilha)

            # Mapear colunas
            mapeamento = self.mapear_colunas(df)

            if 'cpf' not in mapeamento:
                raise ValueError("Coluna CPF não encontrada na planilha!")

            # Extrair clientes
            clientes = []

            for idx, row in df.iterrows():
                try:
                    cliente = self._processar_linha(
                        row=row,
                        mapeamento=mapeamento,
                        consultor=consultor,
                        arquivo_origem=str(caminho_planilha),
                        linha=idx + 2  # +2 porque Excel começa em 1 e tem cabeçalho
                    )

                    if cliente:
                        clientes.append(cliente)

                except Exception as e:
                    logger.warning(f"Erro na linha {idx + 2}: {e}")
                    continue

            logger.info(f"✅ {len(clientes)} clientes extraídos de {caminho_planilha.name}")
            return clientes

        except Exception as e:
            logger.error(f"❌ Erro ao ler planilha {caminho_planilha.name}: {e}")
            raise

    def _processar_linha(
        self,
        row: pd.Series,
        mapeamento: Dict[str, str],
        consultor: Optional[Consultor],
        arquivo_origem: str,
        linha: int
    ) -> Optional[Dict[str, Any]]:
        """
        Processa uma linha da planilha

        Args:
            row: Linha do DataFrame
            mapeamento: Mapeamento de colunas
            consultor: Dados do consultor
            arquivo_origem: Caminho do arquivo
            linha: Número da linha

        Returns:
            Dicionário com dados do cliente ou None
        """
        # Extrair CPF
        cpf_raw = row.get(mapeamento['cpf'], '')
        cpf_limpo = self.config.limpar_cpf(cpf_raw)

        # Validar CPF
        if not self.config.validar_cpf(cpf_limpo):
            logger.debug(f"Linha {linha}: CPF inválido: {cpf_raw}")
            return None

        # Montar dados do cliente
        cliente = {
            'cpf': cpf_limpo,
            'cpf_formatado': self.config.formatar_cpf(cpf_limpo),
            'arquivo_origem': arquivo_origem,
            'linha_planilha': linha,
        }

        # Adicionar consultor se identificado
        if consultor:
            cliente['consultor_nome'] = consultor.nome
            cliente['consultor_empresa'] = consultor.empresa
            cliente['consultor_ponto_venda'] = consultor.ponto_venda
            cliente['consultor_pasta'] = consultor.pasta_boletos

        # Adicionar campos opcionais
        if 'nome' in mapeamento and pd.notna(row.get(mapeamento['nome'])):
            cliente['nome'] = str(row[mapeamento['nome']]).strip()

        if 'grupo' in mapeamento and pd.notna(row.get(mapeamento['grupo'])):
            cliente['grupo'] = str(row[mapeamento['grupo']]).strip()

        if 'cota' in mapeamento and pd.notna(row.get(mapeamento['cota'])):
            cliente['cota'] = str(row[mapeamento['cota']]).strip()

        if 'ponto_venda' in mapeamento and pd.notna(row.get(mapeamento['ponto_venda'])):
            cliente['ponto_venda'] = str(row[mapeamento['ponto_venda']]).strip()
        elif consultor:
            cliente['ponto_venda'] = consultor.ponto_venda

        if 'whatsapp' in mapeamento and pd.notna(row.get(mapeamento['whatsapp'])):
            whatsapp_raw = row[mapeamento['whatsapp']]
            whatsapp_limpo = self.config.limpar_telefone(whatsapp_raw)
            if whatsapp_limpo:
                cliente['whatsapp'] = self.config.formatar_telefone(whatsapp_limpo)

        if 'contemplado' in mapeamento and pd.notna(row.get(mapeamento['contemplado'])):
            contemplado_val = str(row[mapeamento['contemplado']]).strip().upper()
            cliente['contemplado'] = contemplado_val in ['SIM', 'S', 'TRUE', '1', 'CONTEMPLADO']

        return cliente

    def importar_todas_planilhas(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Importa todas as planilhas do diretório

        Returns:
            Dicionário {nome_arquivo: [clientes]}
        """
        logger.info("🔄 Importando todas as planilhas...")

        planilhas = self.listar_planilhas()
        resultado = {}

        for planilha in planilhas:
            try:
                clientes = self.extrair_clientes(planilha)
                resultado[planilha.name] = clientes

            except Exception as e:
                logger.error(f"❌ Erro ao importar {planilha.name}: {e}")
                resultado[planilha.name] = []

        total_clientes = sum(len(c) for c in resultado.values())
        logger.info(f"✅ Importação concluída: {total_clientes} clientes de {len(planilhas)} planilhas")

        return resultado

    def gerar_hash_planilha(self, caminho: Path) -> str:
        """
        Gera hash MD5 do arquivo para detectar alterações

        Args:
            caminho: Caminho do arquivo

        Returns:
            Hash MD5 do arquivo
        """
        hash_md5 = hashlib.md5()

        with open(caminho, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()


# ============================================================================
# CLASSE MONITOR DE PLANILHAS
# ============================================================================

class ExcelFileHandler(FileSystemEventHandler):
    """Handler para eventos do sistema de arquivos"""

    def __init__(self, callback):
        """
        Inicializa o handler

        Args:
            callback: Função a chamar quando planilha for modificada
        """
        super().__init__()
        self.callback = callback
        self.last_modified = {}
        self.debounce_seconds = 2  # Aguardar 2s antes de processar

    def on_modified(self, event):
        """Callback quando arquivo é modificado"""
        if event.is_directory:
            return

        # Verificar se é arquivo Excel
        if not event.src_path.endswith(('.xlsx', '.xls', '.xlsm')):
            return

        # Ignorar arquivos temporários
        if Path(event.src_path).name.startswith('~$'):
            return

        # Debounce (evitar múltiplos eventos)
        now = time.time()
        if event.src_path in self.last_modified:
            if now - self.last_modified[event.src_path] < self.debounce_seconds:
                return

        self.last_modified[event.src_path] = now

        # Chamar callback
        logger.info(f"📝 Planilha modificada: {Path(event.src_path).name}")
        self.callback(Path(event.src_path))


class ExcelMonitor:
    """Monitor de alterações em planilhas Excel"""

    def __init__(
        self,
        diretorio: Path = None,
        callback = None,
        config: CanopusConfig = None
    ):
        """
        Inicializa o monitor

        Args:
            diretorio: Diretório para monitorar (padrão: EXCEL_DIR)
            callback: Função a chamar quando planilha for alterada
            config: Configuração
        """
        self.config = config or CanopusConfig
        self.diretorio = diretorio or self.config.EXCEL_DIR
        self.callback = callback or self._callback_padrao
        self.observer = None
        self.importer = ExcelImporter(self.config)
        self.hashes = {}  # Cache de hashes dos arquivos

    def _callback_padrao(self, caminho: Path):
        """Callback padrão quando planilha é alterada"""
        logger.info(f"📊 Planilha alterada: {caminho.name}")

        try:
            # Verificar se realmente mudou (comparar hash)
            hash_novo = self.importer.gerar_hash_planilha(caminho)
            hash_anterior = self.hashes.get(str(caminho))

            if hash_anterior and hash_novo == hash_anterior:
                logger.debug(f"Hash não mudou, ignorando: {caminho.name}")
                return

            # Atualizar hash
            self.hashes[str(caminho)] = hash_novo

            # Processar planilha
            clientes = self.importer.extrair_clientes(caminho)
            logger.info(f"✅ Planilha processada: {len(clientes)} clientes")

        except Exception as e:
            logger.error(f"❌ Erro ao processar planilha: {e}")

    def inicializar_hashes(self):
        """Gera hashes iniciais de todas as planilhas"""
        logger.info("🔄 Inicializando hashes das planilhas...")

        planilhas = self.importer.listar_planilhas(self.diretorio)

        for planilha in planilhas:
            try:
                hash_arquivo = self.importer.gerar_hash_planilha(planilha)
                self.hashes[str(planilha)] = hash_arquivo

            except Exception as e:
                logger.error(f"Erro ao gerar hash de {planilha.name}: {e}")

        logger.info(f"✅ {len(self.hashes)} hashes inicializados")

    def iniciar(self):
        """Inicia o monitoramento"""
        logger.info(f"👀 Iniciando monitoramento: {self.diretorio}")

        # Inicializar hashes
        self.inicializar_hashes()

        # Criar observer
        self.observer = Observer()
        event_handler = ExcelFileHandler(self.callback)

        self.observer.schedule(
            event_handler,
            str(self.diretorio),
            recursive=False
        )

        self.observer.start()
        logger.info("✅ Monitor iniciado")

    def parar(self):
        """Para o monitoramento"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 Monitor parado")

    def __enter__(self):
        """Context manager - entrada"""
        self.iniciar()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.parar()


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def importar_planilha(caminho: str) -> List[Dict[str, Any]]:
    """
    Função helper para importar uma planilha

    Args:
        caminho: Caminho da planilha

    Returns:
        Lista de clientes
    """
    importer = ExcelImporter()
    return importer.extrair_clientes(Path(caminho))


def importar_todas() -> Dict[str, List[Dict[str, Any]]]:
    """
    Função helper para importar todas as planilhas

    Returns:
        Dicionário {arquivo: [clientes]}
    """
    importer = ExcelImporter()
    return importer.importar_todas_planilhas()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DO IMPORTADOR DE EXCEL")
    print("=" * 80)

    # Teste 1: Listar planilhas
    print("\n1️⃣ Listando planilhas...")
    importer = ExcelImporter()
    planilhas = importer.listar_planilhas()

    for p in planilhas:
        print(f"  📄 {p.name}")
        consultor = importer.identificar_consultor(p)
        if consultor:
            print(f"     → Consultor: {consultor.nome} ({consultor.empresa})")

    # Teste 2: Importar uma planilha (se existir)
    if planilhas:
        print(f"\n2️⃣ Importando planilha de teste...")
        planilha_teste = planilhas[0]

        try:
            clientes = importer.extrair_clientes(planilha_teste)
            print(f"\n✅ {len(clientes)} clientes encontrados")

            # Mostrar primeiros 3
            print("\nPrimeiros 3 clientes:")
            for cliente in clientes[:3]:
                print(f"  • CPF: {cliente.get('cpf_formatado')}")
                print(f"    Nome: {cliente.get('nome', 'N/A')}")
                print(f"    Grupo/Cota: {cliente.get('grupo', 'N/A')}/{cliente.get('cota', 'N/A')}")
                print()

        except Exception as e:
            print(f"❌ Erro: {e}")

    # Teste 3: Monitor (comentado - rodar separadamente)
    # print("\n3️⃣ Testando monitor...")
    # with ExcelMonitor() as monitor:
    #     print("Monitor ativo. Altere uma planilha para testar.")
    #     print("Pressione Ctrl+C para parar.")
    #     try:
    #         while True:
    #             time.sleep(1)
    #     except KeyboardInterrupt:
    #         print("\n✅ Monitor encerrado")

    print("\n" + "=" * 80)
