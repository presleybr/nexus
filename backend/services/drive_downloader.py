"""
Serviço para fazer download de arquivos do Google Drive

Suporta:
- Links públicos do Google Drive
- Download direto de planilhas Excel
- Substituição de arquivos existentes
"""

import requests
import re
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def extrair_file_id_drive(url: str) -> Optional[str]:
    """
    Extrai o ID do arquivo de uma URL do Google Drive ou Google Sheets

    Suporta formatos:
    - https://drive.google.com/file/d/FILE_ID/view
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID
    - https://docs.google.com/spreadsheets/d/FILE_ID/edit (Google Sheets)
    - FILE_ID (direto)

    Args:
        url: URL do Google Drive/Sheets ou ID direto

    Returns:
        ID do arquivo ou None se não encontrado
    """
    if not url:
        return None

    # Se já é um ID (sem https), retorna direto
    # IDs do Drive geralmente têm entre 25-50 caracteres, mas aceitamos >= 10 para testes
    if 'http' not in url and len(url) >= 10:
        return url.strip()

    # Padrões de URL do Drive e Google Sheets
    padroes = [
        r'/file/d/([a-zA-Z0-9_-]+)',                    # https://drive.google.com/file/d/ID/view
        r'/spreadsheets/d/([a-zA-Z0-9_-]+)',           # https://docs.google.com/spreadsheets/d/ID/edit
        r'id=([a-zA-Z0-9_-]+)',                         # https://drive.google.com/open?id=ID
        r'/folders/([a-zA-Z0-9_-]+)',                   # https://drive.google.com/drive/folders/ID
    ]

    for padrao in padroes:
        match = re.search(padrao, url)
        if match:
            return match.group(1)

    logger.warning(f"Não foi possível extrair ID do Drive da URL: {url}")
    return None


def detectar_tipo_url(url: str) -> str:
    """
    Detecta se a URL é de um arquivo do Drive ou de um Google Sheets

    Args:
        url: URL do Google Drive ou Sheets

    Returns:
        'sheets' ou 'drive'
    """
    if 'docs.google.com/spreadsheets' in url or 'sheets.google.com' in url:
        return 'sheets'
    return 'drive'


def gerar_url_download_drive(file_id: str, tipo: str = 'drive') -> str:
    """
    Gera URL de download direto do Google Drive ou Google Sheets

    Args:
        file_id: ID do arquivo no Google Drive/Sheets
        tipo: 'drive' para arquivos ou 'sheets' para planilhas

    Returns:
        URL de download direto
    """
    if tipo == 'sheets':
        # URL de exportação de Google Sheets para Excel
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    else:
        # URL de download direto (funciona para arquivos públicos do Drive)
        return f"https://drive.google.com/uc?export=download&id={file_id}"


def baixar_arquivo_drive(
    url_drive: str,
    caminho_destino: Path,
    nome_arquivo: Optional[str] = None,
    substituir: bool = True
) -> Dict:
    """
    Baixa um arquivo do Google Drive

    Args:
        url_drive: URL do Google Drive ou ID do arquivo
        caminho_destino: Pasta de destino
        nome_arquivo: Nome do arquivo (opcional, usa o do Drive se None)
        substituir: Se True, substitui arquivo existente

    Returns:
        Dicionário com resultado:
        {
            'sucesso': bool,
            'arquivo_path': str,
            'tamanho': int,
            'mensagem': str,
            'erro': str (se sucesso=False)
        }
    """
    try:
        logger.info(f"📥 Iniciando download do Google Drive...")
        logger.info(f"   URL/ID: {url_drive}")

        # Extrair ID do arquivo
        file_id = extrair_file_id_drive(url_drive)
        if not file_id:
            return {
                'sucesso': False,
                'erro': 'Não foi possível extrair o ID do arquivo da URL do Drive'
            }

        logger.info(f"   ✅ File ID extraído: {file_id}")

        # Detectar tipo (Sheets ou Drive)
        tipo = detectar_tipo_url(url_drive)
        logger.info(f"   📋 Tipo detectado: {'Google Sheets' if tipo == 'sheets' else 'Google Drive'}")

        # Gerar URL de download
        url_download = gerar_url_download_drive(file_id, tipo)

        # Fazer requisição inicial
        logger.info(f"   🌐 Fazendo requisição para o {'Google Sheets' if tipo == 'sheets' else 'Drive'}...")
        session = requests.Session()

        response = session.get(url_download, stream=True, allow_redirects=True)

        # Google Sheets retorna direto, mas Drive pode ter confirmação para arquivos grandes
        if tipo == 'drive' and 'content-disposition' not in response.headers:
            # Procurar por link de confirmação (apenas para Drive)
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    url_download = f"{url_download}&confirm={value}"
                    response = session.get(url_download, stream=True, allow_redirects=True)
                    break

        # Verificar se download foi bem-sucedido
        if response.status_code != 200:
            logger.error(f"   ❌ Erro HTTP {response.status_code}")
            logger.error(f"   URL: {url_download}")
            return {
                'sucesso': False,
                'erro': f'Erro ao baixar arquivo: HTTP {response.status_code}'
            }

        # Extrair nome do arquivo do header Content-Disposition (se disponível)
        if not nome_arquivo:
            content_disposition = response.headers.get('content-disposition', '')
            if content_disposition:
                match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if match:
                    nome_arquivo = match.group(1)

            # Se ainda não tem nome, usar genérico
            if not nome_arquivo:
                nome_arquivo = f"planilha_{file_id}.xlsx"

        # Garantir que termina com .xlsx
        if not nome_arquivo.endswith('.xlsx'):
            nome_arquivo += '.xlsx'

        # Criar pasta de destino se não existir
        caminho_destino = Path(caminho_destino)
        caminho_destino.mkdir(parents=True, exist_ok=True)

        # Caminho completo do arquivo
        arquivo_path = caminho_destino / nome_arquivo

        # Verificar se arquivo já existe
        if arquivo_path.exists():
            if substituir:
                logger.info(f"   ⚠️  Arquivo existente será substituído: {arquivo_path}")
                arquivo_path.unlink()  # Remove o arquivo antigo
            else:
                # Gerar nome único
                contador = 1
                while arquivo_path.exists():
                    nome_base = arquivo_path.stem
                    nome_arquivo = f"{nome_base}_{contador}.xlsx"
                    arquivo_path = caminho_destino / nome_arquivo
                    contador += 1
                logger.info(f"   ℹ️  Salvando com nome alternativo: {arquivo_path}")

        # Baixar arquivo
        logger.info(f"   💾 Salvando arquivo em: {arquivo_path}")

        tamanho_total = 0
        with open(arquivo_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    tamanho_total += len(chunk)

        logger.info(f"   ✅ Download concluído! Tamanho: {tamanho_total / 1024:.2f} KB")

        return {
            'sucesso': True,
            'arquivo_path': str(arquivo_path),
            'arquivo_nome': nome_arquivo,
            'tamanho': tamanho_total,
            'mensagem': f'Arquivo baixado com sucesso: {nome_arquivo}'
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"   ❌ Erro de rede ao baixar arquivo: {e}")
        return {
            'sucesso': False,
            'erro': f'Erro de rede: {str(e)}'
        }

    except Exception as e:
        logger.error(f"   ❌ Erro ao baixar arquivo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }


def baixar_planilha_consultor(
    link_drive: str,
    nome_consultor: str,
    substituir: bool = True
) -> Dict:
    """
    Baixa planilha de um consultor específico do Google Drive

    Args:
        link_drive: URL do Google Drive
        nome_consultor: Nome do consultor (usado no nome do arquivo)
        substituir: Se True, substitui arquivo existente

    Returns:
        Dicionário com resultado do download
    """
    # Pasta de destino
    pasta_destino = Path("D:/Nexus/automation/canopus/excel_files")

    # Nome do arquivo baseado no consultor
    # Normalizar nome do consultor (remover caracteres especiais)
    nome_limpo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_consultor.upper())
    nome_arquivo = f"{nome_limpo}__PLANILHA_GERAL.xlsx"

    logger.info(f"📋 Baixando planilha do consultor: {nome_consultor}")
    logger.info(f"   Arquivo destino: {nome_arquivo}")

    return baixar_arquivo_drive(
        url_drive=link_drive,
        caminho_destino=pasta_destino,
        nome_arquivo=nome_arquivo,
        substituir=substituir
    )


# Função auxiliar para testar
if __name__ == "__main__":
    # Teste
    logging.basicConfig(level=logging.INFO)

    # Exemplo de uso
    url_teste = "https://drive.google.com/file/d/SEU_FILE_ID_AQUI/view"
    resultado = baixar_planilha_consultor(url_teste, "DENER", substituir=True)

    print("\nResultado:", resultado)
