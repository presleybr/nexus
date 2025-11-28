"""
Extrator robusto de planilha Excel do Dener
Processa dados de clientes com validações completas e distribuição por Ponto de Venda
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExcelExtractor:
    """
    Extrator de dados da planilha Excel do Dener

    Características:
    - Detecta automaticamente o Ponto de Venda pela coluna
    - Valida CPF, nome e outros campos obrigatórios
    - Remove duplicatas
    - Normaliza dados (nomes, CPFs, etc)
    - Suporta múltiplos pontos de venda na mesma planilha
    """

    def __init__(self, arquivo_excel: str):
        """
        Inicializa o extrator

        Args:
            arquivo_excel: Caminho completo do arquivo Excel
        """
        self.arquivo_excel = Path(arquivo_excel)
        self.df_raw = None
        self.clientes = []

        if not self.arquivo_excel.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo_excel}")


    def detectar_ponto_venda(self, nome_coluna: str) -> Optional[str]:
        """
        Detecta o ponto de venda pelo nome da coluna

        Args:
            nome_coluna: Nome da coluna a verificar

        Returns:
            '17308', '24627' ou None
        """
        nome_upper = str(nome_coluna).upper()

        if '17308' in nome_upper or 'PV 17308' in nome_upper or 'PONTO 17308' in nome_upper:
            return '17308'
        elif '24627' in nome_upper or 'PV 24627' in nome_upper or 'PONTO 24627' in nome_upper:
            return '24627'

        return None


    def validar_cpf(self, cpf: str) -> Optional[str]:
        """
        Valida e normaliza CPF

        Args:
            cpf: CPF para validar (pode ter pontos/hífens)

        Returns:
            CPF limpo (apenas números) ou None se inválido
        """
        if pd.isna(cpf) or str(cpf).lower() in ['nan', 'none', '']:
            return None

        # Remover tudo que não é número
        cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))

        # Verificar tamanho
        if len(cpf_limpo) != 11:
            logger.warning(f"CPF inválido (tamanho != 11): {cpf}")
            return None

        # Verificar se não é sequência repetida (ex: 111.111.111-11)
        if cpf_limpo == cpf_limpo[0] * 11:
            logger.warning(f"CPF inválido (sequência repetida): {cpf}")
            return None

        return cpf_limpo


    def normalizar_nome(self, nome: str) -> Optional[str]:
        """
        Normaliza nome do cliente

        Args:
            nome: Nome para normalizar

        Returns:
            Nome normalizado ou None se inválido
        """
        if pd.isna(nome) or str(nome).lower() in ['nan', 'none', '']:
            return None

        nome_str = str(nome).strip()

        # Remover sufixos como "- 70%", "70%", etc
        nome_str = re.sub(r'\s*-?\s*\d+%?', '', nome_str).strip()

        # Remover espaços múltiplos
        nome_str = re.sub(r'\s+', ' ', nome_str)

        # Validar tamanho mínimo
        if len(nome_str) < 3:
            logger.warning(f"Nome muito curto: {nome}")
            return None

        return nome_str.upper()


    def extrair_dados(self, pontos_venda_filtro: List[str] = None) -> Dict:
        """
        Extrai todos os dados da planilha

        Args:
            pontos_venda_filtro: Lista de PVs para filtrar (ex: ['17308', '24627'])
                                Se None, extrai todos

        Returns:
            Dicionário com resultados:
            {
                'sucesso': bool,
                'clientes': List[Dict],
                'total_processado': int,
                'total_valido': int,
                'total_invalido': int,
                'erros': List[str]
            }
        """
        logger.info(f"📊 Iniciando extração de dados: {self.arquivo_excel.name}")

        erros = []
        clientes_validos = []
        total_processado = 0
        total_invalido = 0

        try:
            # Ler Excel (header=11 conforme código existente)
            logger.info("   Lendo arquivo Excel...")
            self.df_raw = pd.read_excel(self.arquivo_excel, sheet_name=0, header=11)

            # Pular primeira linha (cabeçalhos duplicados)
            self.df_raw = self.df_raw[1:].reset_index(drop=True)

            logger.info(f"   Total de linhas no Excel: {len(self.df_raw)}")
            logger.info(f"   Colunas encontradas: {len(self.df_raw.columns)}")

            # Analisar estrutura da planilha
            # Tipicamente: Coluna 0 = CPF, Coluna 5 = Nome
            # Mas vamos detectar automaticamente as colunas de PV

            colunas_pv = {}
            for idx, col in enumerate(self.df_raw.columns):
                pv = self.detectar_ponto_venda(col)
                if pv:
                    colunas_pv[pv] = idx
                    logger.info(f"   ✓ Detectado PV {pv} na coluna {idx}: '{col}'")

            # Se não detectou PV nas colunas, assumir estrutura padrão
            # (todos os clientes pertencem ao mesmo PV baseado no filtro)
            if not colunas_pv and pontos_venda_filtro:
                logger.info(f"   ℹ️ Nenhuma coluna de PV detectada, assumindo PV único: {pontos_venda_filtro}")

            # Processar cada linha
            for index, row in self.df_raw.iterrows():
                total_processado += 1

                try:
                    # Extrair CPF (coluna 0)
                    cpf_raw = row.iloc[0] if len(row) > 0 else None
                    cpf = self.validar_cpf(cpf_raw)

                    if not cpf:
                        total_invalido += 1
                        continue

                    # Extrair Nome (coluna 5)
                    nome_raw = row.iloc[5] if len(row) > 5 else None
                    nome = self.normalizar_nome(nome_raw)

                    if not nome:
                        total_invalido += 1
                        erros.append(f"Linha {index + 13}: CPF {cpf_raw} sem nome válido")
                        continue

                    # Determinar ponto de venda da COLUNA 6
                    ponto_venda = None

                    # Ler PV da coluna 6 (baseado na estrutura da planilha)
                    pv_raw = row.iloc[6] if len(row) > 6 else None

                    if pd.notna(pv_raw):
                        # Pode vir como int (17308) ou string ("17308")
                        pv_str = str(int(pv_raw)) if isinstance(pv_raw, (int, float)) else str(pv_raw).strip()

                        # Verificar se é 17308 ou 24627
                        if pv_str == '17308':
                            ponto_venda = '17308'
                        elif pv_str == '24627':
                            ponto_venda = '24627'
                        elif '17308' in pv_str:
                            ponto_venda = '17308'
                        elif '24627' in pv_str:
                            ponto_venda = '24627'

                    # Se não encontrou PV na coluna 6, tentar detectar por colunas (fallback)
                    if not ponto_venda and colunas_pv:
                        for pv, col_idx in colunas_pv.items():
                            valor_pv = row.iloc[col_idx] if len(row) > col_idx else None
                            if pd.notna(valor_pv) and str(valor_pv).strip():
                                ponto_venda = pv
                                break

                    # Se ainda não tem PV, usar 24627 como padrão
                    if not ponto_venda:
                        logger.warning(f"   ⚠️ PV não identificado na linha {index + 13} (coluna 6: {repr(pv_raw)}), usando 24627 como padrão")
                        ponto_venda = '24627'

                    # Verificar se o PV está no filtro (se houver)
                    if pontos_venda_filtro and ponto_venda not in pontos_venda_filtro:
                        continue

                    # Formatar CPF para XXX.XXX.XXX-XX
                    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

                    # Criar registro do cliente
                    cliente = {
                        'cpf': cpf,
                        'cpf_formatado': cpf_formatado,
                        'nome': nome,
                        'ponto_venda': ponto_venda,
                        'linha_origem': index + 13,  # +13 porque header=11 e +1 linha pulada
                    }

                    # Verificar duplicatas
                    if any(c['cpf'] == cpf for c in clientes_validos):
                        logger.warning(f"   ⚠️ CPF duplicado ignorado: {cpf_formatado} - {nome}")
                        continue

                    clientes_validos.append(cliente)

                except Exception as e:
                    total_invalido += 1
                    erros.append(f"Linha {index + 13}: {str(e)}")
                    logger.error(f"   ❌ Erro na linha {index + 13}: {e}")

            # Estatísticas por PV
            estatisticas_pv = {}
            for cliente in clientes_validos:
                pv = cliente['ponto_venda']
                if pv not in estatisticas_pv:
                    estatisticas_pv[pv] = 0
                estatisticas_pv[pv] += 1

            logger.info(f"\n   📊 Estatísticas da extração:")
            logger.info(f"   Total processado: {total_processado}")
            logger.info(f"   Clientes válidos: {len(clientes_validos)}")
            logger.info(f"   Registros inválidos: {total_invalido}")

            for pv, count in estatisticas_pv.items():
                logger.info(f"   PV {pv}: {count} clientes")

            self.clientes = clientes_validos

            return {
                'sucesso': True,
                'clientes': clientes_validos,
                'total_processado': total_processado,
                'total_valido': len(clientes_validos),
                'total_invalido': total_invalido,
                'estatisticas_pv': estatisticas_pv,
                'erros': erros[:10]  # Máximo de 10 erros no retorno
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados: {e}")
            import traceback
            logger.error(traceback.format_exc())

            return {
                'sucesso': False,
                'erro': str(e),
                'clientes': [],
                'total_processado': total_processado,
                'total_valido': 0,
                'total_invalido': total_invalido,
                'erros': erros
            }


# Função helper para uso simples
def extrair_clientes_planilha(
    arquivo_excel: str,
    pontos_venda: List[str] = None
) -> Dict:
    """
    Função helper para extrair clientes da planilha

    Args:
        arquivo_excel: Caminho do arquivo Excel
        pontos_venda: Lista de PVs para filtrar (['17308', '24627'] ou ['24627'])

    Returns:
        Dicionário com resultado da extração
    """
    extrator = ExcelExtractor(arquivo_excel)
    return extrator.extrair_dados(pontos_venda_filtro=pontos_venda)


# Teste standalone
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    arquivo = r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx"

    print("="*70)
    print("TESTE DO EXTRATOR DE EXCEL")
    print("="*70)

    # Teste 1: Extrair todos os PVs
    print("\n1. Extraindo TODOS os pontos de venda...")
    resultado = extrair_clientes_planilha(arquivo)

    if resultado['sucesso']:
        print(f"\n✓ Extração bem-sucedida!")
        print(f"  Total de clientes: {resultado['total_valido']}")
        print(f"\n  Distribuição por PV:")
        for pv, count in resultado['estatisticas_pv'].items():
            print(f"    PV {pv}: {count} clientes")

    # Teste 2: Extrair apenas PV 24627
    print("\n2. Extraindo apenas PV 24627...")
    resultado2 = extrair_clientes_planilha(arquivo, pontos_venda=['24627'])

    if resultado2['sucesso']:
        print(f"  Clientes do PV 24627: {resultado2['total_valido']}")
