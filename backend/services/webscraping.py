"""
Serviço de Web Scraping - Simulador Campus Consórcio
NOTA: Este é um serviço simulado para demonstração
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List


class CampusConsorcioScraper:
    """Scraper simulado para o sistema Campus Consórcio"""

    def __init__(self):
        self.base_url = "https://campusconsorcio.com.br"  # URL fictícia

    def simular_consulta(self, cpf: str) -> Dict:
        """
        Simula uma consulta ao sistema Campus Consórcio

        Args:
            cpf: CPF do cliente

        Returns:
            Dicionário com dados simulados
        """
        # Gera dados aleatórios baseados no CPF para consistência
        random.seed(cpf)

        valor_base = random.uniform(500, 3000)
        parcelas = random.randint(12, 60)

        return {
            'cpf': cpf,
            'status': random.choice(['ativo', 'ativo', 'ativo', 'pendente']),
            'valor_parcela': round(valor_base, 2),
            'parcelas_pagas': random.randint(0, parcelas),
            'parcelas_total': parcelas,
            'proxima_parcela': (datetime.now() + timedelta(days=random.randint(5, 30))).date(),
            'valor_total_contrato': round(valor_base * parcelas, 2),
            'tipo_consorcio': random.choice(['Imóvel', 'Automóvel', 'Serviços']),
            'data_consulta': datetime.now().isoformat()
        }

    def gerar_boleto_simulado(self, cpf: str, mes_referencia: str) -> Dict:
        """
        Gera dados de boleto simulados

        Args:
            cpf: CPF do cliente
            mes_referencia: Mês de referência

        Returns:
            Dados do boleto
        """
        dados_cliente = self.simular_consulta(cpf)

        return {
            'cpf': cpf,
            'mes_referencia': mes_referencia,
            'valor': dados_cliente['valor_parcela'],
            'vencimento': dados_cliente['proxima_parcela'],
            'codigo_barras': self._gerar_codigo_barras(),
            'linha_digitavel': self._gerar_linha_digitavel(),
            'numero_documento': f"{cpf[:3]}{random.randint(1000, 9999)}",
            'status': 'pendente'
        }

    def _gerar_codigo_barras(self) -> str:
        """Gera um código de barras fictício"""
        return ''.join([str(random.randint(0, 9)) for _ in range(44)])

    def _gerar_linha_digitavel(self) -> str:
        """Gera uma linha digitável fictícia"""
        linha = ''.join([str(random.randint(0, 9)) for _ in range(47)])
        # Formata: XXXXX.XXXXX XXXXX.XXXXXX XXXXX.XXXXXX X XXXXXXXXXXXXXXXX
        return f"{linha[:5]}.{linha[5:10]} {linha[10:15]}.{linha[15:21]} {linha[21:26]}.{linha[26:32]} {linha[32]} {linha[33:]}"

    def buscar_boletos_pendentes(self, lista_cpfs: List[str]) -> List[Dict]:
        """
        Busca boletos pendentes para uma lista de CPFs

        Args:
            lista_cpfs: Lista de CPFs para consulta

        Returns:
            Lista de boletos encontrados
        """
        boletos = []

        for cpf in lista_cpfs:
            try:
                boleto = self.gerar_boleto_simulado(cpf, datetime.now().strftime("%B/%Y"))
                boletos.append(boleto)
            except Exception as e:
                print(f"Erro ao consultar CPF {cpf}: {e}")
                continue

        return boletos


# Instância global
campus_scraper = CampusConsorcioScraper()
