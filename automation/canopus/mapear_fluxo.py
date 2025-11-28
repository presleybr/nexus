"""
Analisa o arquivo de requisições capturadas e identifica o fluxo HTTP

Uso:
    python mapear_fluxo.py                    # Analisa último arquivo
    python mapear_fluxo.py arquivo.json       # Analisa arquivo específico
"""

import json
import sys
import os
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
from collections import defaultdict


def limpar_post_data(post_data: str) -> dict:
    """Parse POST data e retorna campos importantes"""
    if not post_data:
        return {}

    campos = {}
    pares = post_data.split('&')

    for par in pares:
        if '=' in par:
            chave, valor = par.split('=', 1)
            chave = unquote(chave)
            valor = unquote(valor)

            # Ignorar campos muito grandes (ViewState, etc)
            if len(valor) < 100:
                campos[chave] = valor

    return campos


def analisar(arquivo_json: str):
    """Analisa arquivo de requisições e mapeia o fluxo"""

    print("\n" + "=" * 80)
    print("ANÁLISE DE REQUISIÇÕES - CANOPUS")
    print("=" * 80)

    # Carregar JSON
    with open(arquivo_json, 'r', encoding='utf-8') as f:
        requisicoes = json.load(f)

    print(f"\n📊 Total de requisições: {len(requisicoes)}")

    # ========================================================================
    # ESTATÍSTICAS GERAIS
    # ========================================================================

    print("\n" + "-" * 80)
    print("📈 ESTATÍSTICAS GERAIS")
    print("-" * 80)

    # Contar por método
    metodos = defaultdict(int)
    for r in requisicoes:
        metodos[r['method']] += 1

    for metodo, count in sorted(metodos.items()):
        print(f"   {metodo:6} : {count:4} requisições")

    # Contar por tipo de recurso
    print("\n📦 Por tipo de recurso:")
    tipos = defaultdict(int)
    for r in requisicoes:
        tipos[r.get('resource_type', 'unknown')] += 1

    for tipo, count in sorted(tipos.items(), key=lambda x: -x[1])[:10]:
        print(f"   {tipo:15} : {count:4}")

    # ========================================================================
    # PÁGINAS ASPX
    # ========================================================================

    print("\n" + "-" * 80)
    print("📄 PÁGINAS ASPX")
    print("-" * 80)

    aspx = [r for r in requisicoes if '.aspx' in r['url']]
    print(f"\nTotal: {len(aspx)} páginas\n")

    paginas_visitadas = {}
    for r in aspx:
        url = urlparse(r['url'])
        caminho = url.path

        if caminho not in paginas_visitadas:
            paginas_visitadas[caminho] = []

        paginas_visitadas[caminho].append({
            'metodo': r['method'],
            'timestamp': r['timestamp'],
            'status': r.get('status'),
        })

    # Listar páginas na ordem de acesso
    print("Ordem de navegação:")
    for i, (caminho, acessos) in enumerate(paginas_visitadas.items(), 1):
        get_count = len([a for a in acessos if a['metodo'] == 'GET'])
        post_count = len([a for a in acessos if a['metodo'] == 'POST'])

        print(f"\n{i:2}. {caminho}")
        print(f"    GET: {get_count}  |  POST: {post_count}")

    # ========================================================================
    # FLUXO DE LOGIN
    # ========================================================================

    print("\n" + "-" * 80)
    print("🔐 FLUXO DE LOGIN")
    print("-" * 80)

    login_reqs = [r for r in aspx if 'login' in r['url'].lower() or 'main' in r['url'].lower()]

    if login_reqs:
        for r in login_reqs[:5]:
            url = urlparse(r['url'])
            print(f"\n[{r['method']}] {url.path}")
            print(f"   Status: {r.get('status', 'N/A')}")

            if r['method'] == 'POST' and r.get('post_data'):
                campos = limpar_post_data(r['post_data'])
                print(f"   Campos POST:")
                for k, v in campos.items():
                    if 'viewstate' not in k.lower() and 'validation' not in k.lower():
                        print(f"      {k}: {v}")
    else:
        print("   Nenhuma requisição de login encontrada")

    # ========================================================================
    # FLUXO DE BUSCA
    # ========================================================================

    print("\n" + "-" * 80)
    print("🔍 FLUXO DE BUSCA")
    print("-" * 80)

    busca_reqs = [r for r in aspx if any(x in r['url'].lower() for x in ['busca', 'pesq', 'consulta', 'search'])]

    if busca_reqs:
        for r in busca_reqs[:5]:
            url = urlparse(r['url'])
            print(f"\n[{r['method']}] {url.path}")
            print(f"   Status: {r.get('status', 'N/A')}")

            if r['method'] == 'POST' and r.get('post_data'):
                campos = limpar_post_data(r['post_data'])
                print(f"   Campos POST importantes:")
                for k, v in campos.items():
                    if 'viewstate' not in k.lower() and 'validation' not in k.lower():
                        # Destacar campos de busca
                        if any(x in k.lower() for x in ['cpf', 'cnpj', 'nome', 'busca', 'pesq', 'tipo']):
                            print(f"      ⭐ {k}: {v}")
                        else:
                            print(f"      {k}: {v}")
    else:
        print("   Nenhuma requisição de busca encontrada")

    # ========================================================================
    # FLUXO DE EMISSÃO/BOLETO
    # ========================================================================

    print("\n" + "-" * 80)
    print("📝 FLUXO DE EMISSÃO/BOLETO")
    print("-" * 80)

    emissao_reqs = [r for r in aspx if any(x in r['url'].lower() for x in ['emiss', 'cobran', 'impress', 'boleto'])]

    if emissao_reqs:
        for r in emissao_reqs[:10]:
            url = urlparse(r['url'])
            print(f"\n[{r['method']}] {url.path}")
            print(f"   Status: {r.get('status', 'N/A')}")

            # Verificar se retornou PDF
            headers = r.get('response_headers', {})
            content_type = headers.get('content-type', '')
            if 'pdf' in content_type.lower():
                print(f"   📄 RETORNOU PDF!")

            if r['method'] == 'POST' and r.get('post_data'):
                campos = limpar_post_data(r['post_data'])
                print(f"   Campos POST importantes:")
                for k, v in campos.items():
                    if 'viewstate' not in k.lower() and 'validation' not in k.lower():
                        print(f"      {k}: {v}")

            # Mostrar query params se houver
            if '?' in r['url']:
                params = parse_qs(urlparse(r['url']).query)
                if params:
                    print(f"   Query params:")
                    for k, v in params.items():
                        print(f"      {k}: {v[0] if len(v) == 1 else v}")
    else:
        print("   Nenhuma requisição de emissão encontrada")

    # ========================================================================
    # CAMPOS DE FORMULÁRIO ASP.NET
    # ========================================================================

    print("\n" + "-" * 80)
    print("🔧 CAMPOS ASP.NET IDENTIFICADOS")
    print("-" * 80)

    campos_asp = set()
    campos_formulario = defaultdict(set)

    for r in aspx:
        if r['method'] == 'POST' and r.get('post_data'):
            campos = limpar_post_data(r['post_data'])

            for campo in campos.keys():
                # Campos ASP.NET
                if campo.startswith('__'):
                    campos_asp.add(campo)
                # Campos de formulário
                elif campo.startswith('ctl00$'):
                    url = urlparse(r['url'])
                    campos_formulario[url.path].add(campo)

    print("\nCampos ASP.NET padrão encontrados:")
    for campo in sorted(campos_asp):
        print(f"   {campo}")

    print("\nCampos de formulário por página:")
    for pagina, campos in sorted(campos_formulario.items()):
        print(f"\n   {pagina}:")
        for campo in sorted(campos):
            print(f"      {campo}")

    # ========================================================================
    # COOKIES
    # ========================================================================

    print("\n" + "-" * 80)
    print("🍪 COOKIES IDENTIFICADOS")
    print("-" * 80)

    cookies = set()
    for r in requisicoes:
        cookie_header = r.get('headers', {}).get('cookie', '')
        if cookie_header:
            # Extrair nomes de cookies
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    nome = cookie.split('=')[0].strip()
                    cookies.add(nome)

    if cookies:
        for cookie in sorted(cookies):
            print(f"   {cookie}")
    else:
        print("   Nenhum cookie identificado nos headers")

    # ========================================================================
    # RESUMO FINAL
    # ========================================================================

    print("\n" + "=" * 80)
    print("✅ RESUMO - PRÓXIMOS PASSOS")
    print("=" * 80)

    print("\n1. Ajustar canopus_api.py com os campos identificados acima")
    print("2. Testar login com os campos corretos")
    print("3. Implementar busca de cliente")
    print("4. Implementar emissão de boleto")
    print("\n💡 Dica: Procure por campos com 'txt', 'btn', 'ddl' nos nomes")
    print("   txt = TextBox (input)")
    print("   btn = Button (botão)")
    print("   ddl = DropDownList (select)")

    print("\n📁 Arquivo analisado:")
    print(f"   {arquivo_json}")
    print()


def main():
    """Função principal"""

    if len(sys.argv) > 1:
        # Arquivo específico fornecido
        arquivo = sys.argv[1]

        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            return 1

        analisar(arquivo)

    else:
        # Pegar último arquivo da pasta logs
        pasta = Path(r'D:\Nexus\automation\canopus\logs')

        if not pasta.exists():
            print(f"❌ Pasta não encontrada: {pasta}")
            print("\nExecute primeiro:")
            print("   python capturar_requisicoes.py")
            return 1

        arquivos = list(pasta.glob('requisicoes_*.json'))

        if not arquivos:
            print(f"❌ Nenhum arquivo de requisições encontrado em: {pasta}")
            print("\nExecute primeiro:")
            print("   python capturar_requisicoes.py")
            return 1

        # Pegar mais recente
        ultimo = max(arquivos, key=lambda p: p.stat().st_mtime)

        print(f"Analisando arquivo mais recente: {ultimo.name}")
        analisar(str(ultimo))

    return 0


if __name__ == '__main__':
    sys.exit(main())
