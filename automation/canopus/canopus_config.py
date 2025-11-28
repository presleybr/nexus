"""
Configurações da Automação Canopus
Gerencia todas as configurações, URLs, timeouts e mapeamentos
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging


# ============================================================================
# DATACLASSES - MODELOS DE DADOS
# ============================================================================

@dataclass
class PontoVenda:
    """Modelo de dados para Ponto de Venda"""
    codigo: str  # Ex: '17.308'
    nome: str
    empresa: str  # 'credms' ou 'semicredito'
    url_base: str = 'https://cnp3.consorciocanopus.com.br'
    ativo: bool = True


@dataclass
class Consultor:
    """Modelo de dados para Consultor"""
    id: Optional[int] = None
    nome: str = ''
    email: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    empresa: str = ''  # 'credms' ou 'semicredito'
    ponto_venda: str = ''  # Código do ponto
    pasta_boletos: str = ''  # Nome da pasta
    cor_identificacao: Optional[str] = None  # 'rosa', 'verde', etc
    ativo: bool = True


@dataclass
class ExcelColumns:
    """Mapeamento de colunas da planilha Excel"""
    # Possíveis nomes de colunas para cada campo
    cpf_variations: List[str] = field(default_factory=lambda: [
        'CPF', 'DOCUMENTO', 'DOC', 'CPF_CLIENTE', 'CLIENTE_CPF'
    ])

    nome_variations: List[str] = field(default_factory=lambda: [
        'NOME', 'NOME_COMPLETO', 'CLIENTE', 'NOME_CLIENTE', 'CONSUMIDOR'
    ])

    grupo_variations: List[str] = field(default_factory=lambda: [
        'GRUPO', 'GR', 'GRUPO_CONSORCIO', 'NR_GRUPO'
    ])

    cota_variations: List[str] = field(default_factory=lambda: [
        'COTA', 'CT', 'COTA_CONSORCIO', 'NR_COTA'
    ])

    ponto_venda_variations: List[str] = field(default_factory=lambda: [
        'PONTO_VENDA', 'PONTO', 'PV', 'PDV', 'LOJA'
    ])

    whatsapp_variations: List[str] = field(default_factory=lambda: [
        'WHATSAPP', 'TELEFONE', 'CELULAR', 'FONE', 'CONTATO', 'TEL'
    ])

    contemplado_variations: List[str] = field(default_factory=lambda: [
        'CONTEMPLADO', 'CONTEMPLADA', 'STATUS', 'SITUACAO'
    ])


# ============================================================================
# CLASSE PRINCIPAL DE CONFIGURAÇÃO
# ============================================================================

class CanopusConfig:
    """Configurações centralizadas da automação Canopus"""

    # ========================================================================
    # DIRETÓRIOS E CAMINHOS
    # ========================================================================

    # Diretório base da automação
    BASE_DIR = Path(__file__).resolve().parent

    # Diretórios principais
    DOWNLOADS_DIR = BASE_DIR / "downloads"
    EXCEL_DIR = BASE_DIR / "excel_files"
    LOGS_DIR = BASE_DIR / "logs"
    TEMP_DIR = BASE_DIR / "temp"

    # Criar diretórios se não existirem
    for directory in [DOWNLOADS_DIR, EXCEL_DIR, LOGS_DIR, TEMP_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # BANCO DE DADOS
    # ========================================================================

    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5434')),
        'database': os.getenv('DB_NAME', 'nexus_crm'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }

    @classmethod
    def get_db_connection_string(cls) -> str:
        """Retorna string de conexão PostgreSQL"""
        return (
            f"host={cls.DB_CONFIG['host']} "
            f"port={cls.DB_CONFIG['port']} "
            f"dbname={cls.DB_CONFIG['database']} "
            f"user={cls.DB_CONFIG['user']} "
            f"password={cls.DB_CONFIG['password']}"
        )

    # ========================================================================
    # URLs DO SISTEMA CANOPUS
    # ========================================================================

    CANOPUS_BASE_URL = 'https://cnp3.consorciocanopus.com.br'

    # URLs específicas (URLs REAIS do sistema)
    URLS = {
        'login': f'{CANOPUS_BASE_URL}/WWW/frmCorCCCnsLogin.aspx',
        'home': f'{CANOPUS_BASE_URL}/WWW/',
        'busca_avancada': f'{CANOPUS_BASE_URL}/WWW/busca-avancada',
        'emissao_cobranca': f'{CANOPUS_BASE_URL}/WWW/emissao-cobranca',
    }

    # ========================================================================
    # SELETORES CSS/XPATH (PLACEHOLDERS - AJUSTAR DEPOIS)
    # ========================================================================

    SELECTORS = {
        # Login - SELETORES REAIS MAPEADOS ✅
        'login': {
            'usuario_input': '#edtUsuario',  # Campo usuário (ex: 24627)
            'senha_input': '#edtSenha',  # Campo senha
            'botao_entrar': '#btnLogin',  # Botão Login
            'erro_login': '.error-message, .alert-danger',
        },

        # Busca Avançada - SELETORES REAIS MAPEADOS ✅
        'busca': {
            # Ícone de Atendimento (pessoa) - clicar após login
            'icone_atendimento': '#ctl00_img_Atendimento',

            # Botão "Busca avançada" na tela de atendimento
            'botao_busca_avancada': '#ctl00_Conteudo_btnBuscaAvancada',

            # Dropdown para selecionar tipo de busca (Nome, CPF, CNPJ, etc)
            'select_tipo_busca': '#ctl00_Conteudo_cbxCriterioBusca',

            # Campo de input para digitar CPF
            'cpf_input': '#ctl00_Conteudo_edtContextoBusca',

            # Botão "Buscar"
            'botao_buscar': '#ctl00_Conteudo_btnBuscar',

            # Resultados da busca
            # Link do cliente (com ID do documento/grupo-cota)
            # Padrão: a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]
            'cliente_link': 'a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]',

            # Mensagens
            'nenhum_resultado': '.sem-resultado',
        },

        # Emissão de Cobrança - SELETORES REAIS MAPEADOS ✅
        'emissao': {
            # Link "Emissão de Cobrança" no menu do cliente
            'menu_emissao': '#ctl00_Conteudo_Menu_CONAT_grdMenu_CONAT_ctl05_hlkFormulario',

            # Checkbox do boleto na lista (segundo item - índice ctl03)
            # Padrão: input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"]
            'checkbox_boleto': 'input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"]',

            # Botão "Emitir Cobrança"
            'botao_emitir': '#ctl00_Conteudo_btnEmitir',

            # PDF abre em nova aba automaticamente
            # Não precisa de seletor de download pois o PDF já abre
        },

        # Mensagens gerais
        'geral': {
            'loading': '.loading, .spinner, .carregando',
            'erro': '.error, .erro, .alert-danger',
            'sucesso': '.success, .sucesso, .alert-success',
        }
    }

    # ========================================================================
    # TIMEOUTS E DELAYS (em milissegundos)
    # ========================================================================

    TIMEOUTS = {
        'navegacao': 30000,      # 30s - timeout padrão de navegação
        'elemento': 10000,       # 10s - timeout para encontrar elemento
        'download': 60000,       # 60s - timeout para download de PDF
        'login': 15000,          # 15s - timeout para login
        'busca': 20000,          # 20s - timeout para busca de cliente
    }

    DELAYS = {
        'apos_login': 2.0,           # 2s após login
        'apos_busca': 1.5,           # 1.5s após buscar cliente
        'entre_downloads': 3.0,      # 3s entre downloads
        'entre_tentativas': 5.0,     # 5s entre tentativas de retry
        'minimo_humanizado': 0.5,    # 0.5s delay mínimo
        'maximo_humanizado': 2.0,    # 2s delay máximo
    }

    # ========================================================================
    # CONFIGURAÇÕES DO PLAYWRIGHT
    # ========================================================================

    PLAYWRIGHT_CONFIG = {
        'headless': os.getenv('CANOPUS_HEADLESS', 'false').lower() == 'true',
        'browser_type': 'chromium',  # chromium, firefox, webkit
        'slow_mo': 100,  # Atraso entre ações (ms) - ajuda em debug

        'browser_args': [
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
        ],

        'viewport': {
            'width': 1920,
            'height': 1080
        },

        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),

        'accept_downloads': True,
        'downloads_path': str(TEMP_DIR),
    }

    # ========================================================================
    # CONFIGURAÇÕES DE EXECUÇÃO
    # ========================================================================

    EXECUCAO = {
        'max_tentativas': 3,              # Máx tentativas por cliente
        'batch_size': 50,                  # Clientes por lote
        'reiniciar_navegador_apos': 100,  # Reiniciar após N downloads
        'mes_padrao': 'DEZEMBRO',          # Mês padrão para download
        'codigo_empresa_padrao': '0101',   # Código empresa padrão
    }

    # ========================================================================
    # MAPEAMENTO DE COLUNAS EXCEL
    # ========================================================================

    EXCEL_COLUMNS = ExcelColumns()

    # ========================================================================
    # CONFIGURAÇÕES DE LOGGING
    # ========================================================================

    LOG_CONFIG = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',

        'files': {
            'main': LOGS_DIR / 'canopus_automation.log',
            'downloads': LOGS_DIR / 'downloads.log',
            'errors': LOGS_DIR / 'errors.log',
            'excel': LOGS_DIR / 'excel_import.log',
        },

        'rotation': {
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
        }
    }

    # ========================================================================
    # PONTOS DE VENDA PRÉ-DEFINIDOS
    # ========================================================================

    PONTOS_VENDA = {
        '17.308': PontoVenda(
            codigo='17.308',
            nome='CredMS - Ponto 17.308',
            empresa='credms'
        ),
        '17.309': PontoVenda(
            codigo='17.309',
            nome='Semicrédito - Ponto 17.309',
            empresa='semicredito'
        ),
    }

    # ========================================================================
    # CONSULTORES PRÉ-DEFINIDOS (baseado em nomes de arquivo)
    # ========================================================================

    CONSULTORES_MAPEAMENTO = {
        'dayler': Consultor(
            nome='Dayler',
            empresa='credms',
            ponto_venda='17.308',
            pasta_boletos='Dayler'
        ),
        'neto': Consultor(
            nome='Neto',
            empresa='credms',
            ponto_venda='17.308',
            pasta_boletos='Neto',
            cor_identificacao='verde'
        ),
        'mirelli': Consultor(
            nome='Mirelli',
            empresa='semicredito',
            ponto_venda='17.309',
            pasta_boletos='Mirelli',
            cor_identificacao='rosa'
        ),
        'danner': Consultor(
            nome='Danner',
            empresa='credms',
            ponto_venda='17.308',
            pasta_boletos='Danner'
        ),
    }

    # ========================================================================
    # FORMATAÇÃO DE NOMES DE ARQUIVOS
    # ========================================================================

    ARQUIVO_PATTERNS = {
        'boleto_pdf': '{cpf}_{mes}_{ano}.pdf',  # Ex: 12345678901_DEZEMBRO_2024.pdf
        'log_execucao': 'execucao_{data}_{hora}.log',
        'relatorio': 'relatorio_{consultor}_{data}.csv',
    }

    # ========================================================================
    # STATUS E CONSTANTES
    # ========================================================================

    class Status:
        """Status possíveis de download"""
        SUCESSO = 'sucesso'
        ERRO = 'erro'
        CPF_NAO_ENCONTRADO = 'cpf_nao_encontrado'
        SEM_BOLETO = 'sem_boleto'
        TIMEOUT = 'timeout'
        CREDENCIAIS_INVALIDAS = 'credenciais_invalidas'
        ERRO_NAVEGACAO = 'erro_navegacao'

    class StatusExecucao:
        """Status de execução batch"""
        INICIADA = 'iniciada'
        EM_ANDAMENTO = 'em_andamento'
        CONCLUIDA = 'concluida'
        ERRO = 'erro'
        CANCELADA = 'cancelada'

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    @staticmethod
    def limpar_cpf(cpf: str) -> str:
        """Remove formatação do CPF mantendo apenas números"""
        if not cpf:
            return ''
        return ''.join(filter(str.isdigit, str(cpf)))

    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        """Formata CPF para XXX.XXX.XXX-XX"""
        cpf_limpo = CanopusConfig.limpar_cpf(cpf)
        if len(cpf_limpo) != 11:
            return cpf
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida se CPF tem 11 dígitos"""
        cpf_limpo = CanopusConfig.limpar_cpf(cpf)
        return len(cpf_limpo) == 11 and cpf_limpo.isdigit()

    @staticmethod
    def limpar_telefone(telefone: str) -> str:
        """Remove formatação do telefone"""
        if not telefone:
            return ''
        return ''.join(filter(str.isdigit, str(telefone)))

    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """Formata telefone para padrão WhatsApp (55DDNNNNNNNNN)"""
        tel_limpo = CanopusConfig.limpar_telefone(telefone)

        # Se já tem código do país
        if len(tel_limpo) == 13 and tel_limpo.startswith('55'):
            return tel_limpo

        # Se tem DDD + número (11 dígitos)
        if len(tel_limpo) == 11:
            return f"55{tel_limpo}"

        # Se tem DDD + número sem 9 (10 dígitos)
        if len(tel_limpo) == 10:
            return f"55{tel_limpo}"

        return tel_limpo

    @classmethod
    def get_consultor_dir(cls, nome_consultor: str) -> Path:
        """Retorna diretório de downloads do consultor"""
        pasta = cls.DOWNLOADS_DIR / nome_consultor
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta

    @classmethod
    def get_consultor_by_filename(cls, filename: str) -> Optional[Consultor]:
        """Identifica consultor pelo nome do arquivo"""
        filename_lower = filename.lower()

        for key, consultor in cls.CONSULTORES_MAPEAMENTO.items():
            if key in filename_lower:
                return consultor

        return None

    @classmethod
    def gerar_nome_boleto(cls, cpf: str, mes: str, ano: int) -> str:
        """Gera nome padronizado para arquivo de boleto"""
        cpf_limpo = cls.limpar_cpf(cpf)
        return cls.ARQUIVO_PATTERNS['boleto_pdf'].format(
            cpf=cpf_limpo,
            mes=mes.upper(),
            ano=ano
        )

    @classmethod
    def configurar_logging(cls):
        """Configura sistema de logging"""
        import logging.handlers

        # Criar formatador
        formatter = logging.Formatter(
            cls.LOG_CONFIG['format'],
            datefmt=cls.LOG_CONFIG['date_format']
        )

        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(cls.LOG_CONFIG['level'])

        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Handler para arquivo principal com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_CONFIG['files']['main'],
            maxBytes=cls.LOG_CONFIG['rotation']['max_bytes'],
            backupCount=cls.LOG_CONFIG['rotation']['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Handler para erros
        error_handler = logging.handlers.RotatingFileHandler(
            cls.LOG_CONFIG['files']['errors'],
            maxBytes=cls.LOG_CONFIG['rotation']['max_bytes'],
            backupCount=cls.LOG_CONFIG['rotation']['backup_count'],
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        return root_logger


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

# Configurar logging ao importar módulo
CanopusConfig.configurar_logging()

# Logger do módulo
logger = logging.getLogger(__name__)
logger.info(f"Configuração carregada - Base: {CanopusConfig.BASE_DIR}")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CONFIGURAÇÃO CANOPUS")
    print("=" * 80)

    print(f"\n📂 Diretórios:")
    print(f"  Base: {CanopusConfig.BASE_DIR}")
    print(f"  Downloads: {CanopusConfig.DOWNLOADS_DIR}")
    print(f"  Excel: {CanopusConfig.EXCEL_DIR}")
    print(f"  Logs: {CanopusConfig.LOGS_DIR}")

    print(f"\n🌐 URLs:")
    for nome, url in CanopusConfig.URLS.items():
        print(f"  {nome}: {url}")

    print(f"\n⏱️ Timeouts:")
    for nome, timeout in CanopusConfig.TIMEOUTS.items():
        print(f"  {nome}: {timeout}ms")

    print(f"\n👥 Consultores:")
    for nome, consultor in CanopusConfig.CONSULTORES_MAPEAMENTO.items():
        print(f"  {consultor.nome} ({consultor.empresa}) - Pasta: {consultor.pasta_boletos}")

    print(f"\n🔧 Playwright:")
    print(f"  Headless: {CanopusConfig.PLAYWRIGHT_CONFIG['headless']}")
    print(f"  Browser: {CanopusConfig.PLAYWRIGHT_CONFIG['browser_type']}")

    print(f"\n✅ Configuração carregada com sucesso!")
    print("=" * 80)
