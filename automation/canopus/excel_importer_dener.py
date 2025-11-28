"""
Importador ESPECÍFICO para a planilha do Dener
Estrutura: DENER__PLANILHA_GERAL.xlsx

Cabeçalho na linha 12 (header=12)
Colunas:
  0: CPF (formato 000.000.000-00)
  1: G/C (Grupo/Cota ex: "8200 2118")
  2: LANCE
  3: BOLETOS
  4: SITUAÇÃO ("Em dia", "INADIMPLENTE", "CANCELAMENTO", "CANCELADO")
  5: Concorciado (Nome + info ex: "JEFFERSON DOURADO MENDES - 70%")
  6: P.V (Ponto de Venda: 17308 ou 24627)
  7: Valor (Valor do crédito)
  8+: Colunas de datas
"""

import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExcelImporterDener:
    """Importador específico para planilha do Dener"""

    # Arquivo padrão
    ARQUIVO_PADRAO = Path("D:/Nexus/planilhas/DENER__PLANILHA_GERAL.xlsx")

    # Linha do cabeçalho (índice 0-based, então linha 12 = índice 11)
    HEADER_ROW = 11  # pandas header=11 para ler da linha 12

    # Mapeamento de colunas (índice)
    COL_CPF = 0
    COL_GRUPO_COTA = 1
    COL_LANCE = 2
    COL_BOLETOS = 3
    COL_SITUACAO = 4
    COL_NOME = 5
    COL_PONTO_VENDA = 6
    COL_VALOR = 7

    # Situações válidas (aceitas)
    SITUACOES_VALIDAS = ['EM DIA', 'Em dia', 'em dia']

    def __init__(self, caminho_planilha: Path = None):
        """
        Inicializa o importador

        Args:
            caminho_planilha: Caminho da planilha (usa padrão se não fornecido)
        """
        self.caminho = caminho_planilha or self.ARQUIVO_PADRAO

    def validar_cpf(self, cpf: str) -> Optional[str]:
        """
        Valida e limpa CPF

        Args:
            cpf: CPF bruto

        Returns:
            CPF limpo (apenas números) ou None se inválido
        """
        if pd.isna(cpf) or not cpf:
            return None

        # Remover formatação
        cpf_limpo = re.sub(r'[^\d]', '', str(cpf))

        # Verificar comprimento
        if len(cpf_limpo) != 11:
            return None

        # Verificar se todos os dígitos são iguais (CPF inválido)
        if cpf_limpo == cpf_limpo[0] * 11:
            return None

        return cpf_limpo

    def extrair_grupo_cota(self, grupo_cota_str: str) -> Dict[str, Optional[str]]:
        """
        Extrai grupo e cota do formato "8200 2118"

        Args:
            grupo_cota_str: String no formato "GRUPO COTA"

        Returns:
            Dict com 'grupo' e 'cota'
        """
        if pd.isna(grupo_cota_str) or not grupo_cota_str:
            return {'grupo': None, 'cota': None}

        # Separar por espaço
        partes = str(grupo_cota_str).strip().split()

        if len(partes) >= 2:
            return {
                'grupo': partes[0].strip(),
                'cota': partes[1].strip()
            }
        elif len(partes) == 1:
            return {
                'grupo': partes[0].strip(),
                'cota': None
            }
        else:
            return {'grupo': None, 'cota': None}

    def limpar_nome(self, nome: str) -> Optional[str]:
        """
        Limpa o nome do cliente removendo sufixos

        Remove:
        - "- 70%", "- 50%", etc.
        - "MEGAZAP"
        - Espaços extras

        Args:
            nome: Nome bruto

        Returns:
            Nome limpo ou None
        """
        if pd.isna(nome) or not nome:
            return None

        nome_limpo = str(nome).strip()

        # Remover porcentagem (ex: "- 70%")
        nome_limpo = re.sub(r'\s*-\s*\d+%', '', nome_limpo)

        # Remover "MEGAZAP"
        nome_limpo = re.sub(r'\s*MEGAZAP\s*', '', nome_limpo, flags=re.IGNORECASE)

        # Remover espaços extras
        nome_limpo = ' '.join(nome_limpo.split())

        return nome_limpo if nome_limpo else None

    def limpar_ponto_venda(self, pv: Any) -> Optional[str]:
        """
        Limpa e valida ponto de venda

        Args:
            pv: Ponto de venda bruto

        Returns:
            String do ponto (ex: "17308") ou None
        """
        if pd.isna(pv):
            return None

        # Converter para string e remover formatação
        pv_str = str(pv).strip().replace('.', '').replace(',', '')

        # Verificar se é número válido
        if pv_str.isdigit():
            return pv_str

        return None

    def ler_planilha(self) -> pd.DataFrame:
        """
        Lê a planilha do Dener

        Returns:
            DataFrame com os dados brutos
        """
        if not self.caminho.exists():
            raise FileNotFoundError(f"Planilha nao encontrada: {self.caminho}")

        logger.info(f"Lendo planilha: {self.caminho}")

        # Ler Excel com header na linha 12 (índice 11)
        df = pd.read_excel(
            self.caminho,
            header=self.HEADER_ROW,
            engine='openpyxl'
        )

        logger.info(f"Planilha lida: {len(df)} linhas, {len(df.columns)} colunas")
        logger.info(f"Colunas: {list(df.columns)}")

        return df

    def extrair_clientes(self) -> List[Dict[str, Any]]:
        """
        Extrai clientes da planilha do Dener

        Returns:
            Lista de dicionários com dados dos clientes
        """
        # Ler planilha
        df = self.ler_planilha()

        clientes = []
        clientes_validos = 0
        clientes_invalidos = 0

        for idx, row in df.iterrows():
            try:
                # Usar índice de coluna em vez de nome
                cpf_bruto = row.iloc[self.COL_CPF] if len(row) > self.COL_CPF else None
                grupo_cota_bruto = row.iloc[self.COL_GRUPO_COTA] if len(row) > self.COL_GRUPO_COTA else None
                situacao = row.iloc[self.COL_SITUACAO] if len(row) > self.COL_SITUACAO else None
                nome_bruto = row.iloc[self.COL_NOME] if len(row) > self.COL_NOME else None
                pv_bruto = row.iloc[self.COL_PONTO_VENDA] if len(row) > self.COL_PONTO_VENDA else None
                valor_bruto = row.iloc[self.COL_VALOR] if len(row) > self.COL_VALOR else None

                # Validar CPF
                cpf = self.validar_cpf(cpf_bruto)
                if not cpf:
                    clientes_invalidos += 1
                    continue

                # Filtrar situação
                if pd.isna(situacao) or str(situacao).strip() not in self.SITUACOES_VALIDAS:
                    continue

                # Extrair grupo e cota
                grupo_cota = self.extrair_grupo_cota(grupo_cota_bruto)

                # Limpar nome
                nome = self.limpar_nome(nome_bruto)
                if not nome:
                    continue

                # Limpar ponto de venda
                ponto_venda = self.limpar_ponto_venda(pv_bruto)
                if not ponto_venda:
                    continue

                # Montar cliente
                cliente = {
                    'cpf': cpf,
                    'nome': nome,
                    'grupo': grupo_cota['grupo'],
                    'cota': grupo_cota['cota'],
                    'ponto_venda': ponto_venda,
                    'situacao': str(situacao).strip(),
                    'valor_credito': valor_bruto,
                    'consultor_nome': 'Dener',
                    'arquivo_origem': self.caminho.name,
                    'linha_planilha': int(idx) + self.HEADER_ROW + 2  # +2 porque: +1 pelo header, +1 por índice base 0
                }

                clientes.append(cliente)
                clientes_validos += 1

            except Exception as e:
                logger.error(f"Erro ao processar linha {idx}: {e}")
                clientes_invalidos += 1
                continue

        logger.info(f"Clientes extraidos: {clientes_validos} validos, {clientes_invalidos} invalidos")

        return clientes

    def estatisticas(self, clientes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera estatísticas dos clientes

        Args:
            clientes: Lista de clientes

        Returns:
            Dicionário com estatísticas
        """
        if not clientes:
            return {
                'total': 0,
                'por_ponto_venda': {},
                'por_situacao': {}
            }

        # Contar por ponto de venda
        por_pv = {}
        for cliente in clientes:
            pv = cliente['ponto_venda']
            por_pv[pv] = por_pv.get(pv, 0) + 1

        # Contar por situação
        por_situacao = {}
        for cliente in clientes:
            sit = cliente['situacao']
            por_situacao[sit] = por_situacao.get(sit, 0) + 1

        return {
            'total': len(clientes),
            'por_ponto_venda': por_pv,
            'por_situacao': por_situacao
        }


# ============================================================================
# TESTE RÁPIDO
# ============================================================================

if __name__ == '__main__':
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("=" * 80)
    print("TESTE DO IMPORTADOR DENER")
    print("=" * 80)
    print()

    # Criar importador
    importador = ExcelImporterDener()

    try:
        # Extrair clientes
        clientes = importador.extrair_clientes()

        # Mostrar primeiros 5
        print(f"\nPrimeiros 5 clientes:")
        print("-" * 80)
        for i, cliente in enumerate(clientes[:5], 1):
            print(f"\n{i}. {cliente['nome']}")
            print(f"   CPF: {cliente['cpf']}")
            print(f"   Grupo/Cota: {cliente['grupo']}/{cliente['cota']}")
            print(f"   Ponto: {cliente['ponto_venda']}")
            print(f"   Situacao: {cliente['situacao']}")

        # Estatísticas
        stats = importador.estatisticas(clientes)
        print("\n" + "=" * 80)
        print("ESTATISTICAS")
        print("=" * 80)
        print(f"Total de clientes: {stats['total']}")
        print(f"\nPor Ponto de Venda:")
        for pv, qtd in stats['por_ponto_venda'].items():
            print(f"  {pv}: {qtd} clientes")
        print(f"\nPor Situacao:")
        for sit, qtd in stats['por_situacao'].items():
            print(f"  {sit}: {qtd} clientes")

        # Salvar JSON de teste
        json_path = Path(__file__).parent / "temp" / "dener_clientes.json"
        json_path.parent.mkdir(exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(clientes, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] JSON salvo em: {json_path}")
        print()

    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
