"""
Script de Testes da Automação Canopus
Testa cada componente isoladamente para debug e mapeamento
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

# Importar módulos da automação
from config import CanopusConfig
from excel_importer import ExcelImporter
from canopus_automation import CanopusAutomation

# Importar DatabaseManager só quando necessário (evita conflito de imports)
try:
    from orquestrador import DatabaseManager
    DB_MANAGER_AVAILABLE = True
except ImportError:
    DB_MANAGER_AVAILABLE = False
    DatabaseManager = None


# ============================================================================
# TESTE 1: CONEXÃO COM BANCO DE DADOS
# ============================================================================

def testar_conexao_db():
    """Testa conexão com PostgreSQL"""
    print("\n" + "=" * 80)
    print("TESTE 1: CONEXÃO COM BANCO DE DADOS")
    print("=" * 80)

    if not DB_MANAGER_AVAILABLE:
        print("\n❌ DatabaseManager não disponível (conflito de imports)")
        print("   Use: python testar_conexao_db.py")
        return

    try:
        print("\n1️⃣ Tentando conectar ao PostgreSQL...")
        print(f"   Host: {CanopusConfig.DB_CONFIG['host']}")
        print(f"   Port: {CanopusConfig.DB_CONFIG['port']}")
        print(f"   Database: {CanopusConfig.DB_CONFIG['database']}")

        with DatabaseManager() as db:
            print("✅ Conexão estabelecida com sucesso!")

            # Testar query simples
            print("\n2️⃣ Testando query simples...")
            with db.conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"✅ PostgreSQL Version: {version[:50]}...")

            # Verificar tabelas da automação
            print("\n3️⃣ Verificando tabelas da automação...")
            tabelas_necessarias = [
                'consultores',
                'pontos_venda',
                'credenciais_canopus',
                'clientes_planilha_staging',
                'log_downloads_boletos',
                'execucoes_automacao'
            ]

            tabelas_encontradas = []
            tabelas_faltando = []

            with db.conn.cursor() as cur:
                for tabela in tabelas_necessarias:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (tabela,))

                    existe = cur.fetchone()[0]

                    if existe:
                        tabelas_encontradas.append(tabela)
                        print(f"   ✅ {tabela}")
                    else:
                        tabelas_faltando.append(tabela)
                        print(f"   ❌ {tabela} - NÃO EXISTE!")

            # Verificar consultores cadastrados
            print("\n4️⃣ Verificando consultores cadastrados...")
            with db.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, nome, empresa, ponto_venda, ativo
                    FROM consultores
                    ORDER BY nome
                """)
                consultores = cur.fetchall()

            if consultores:
                print(f"✅ {len(consultores)} consultores encontrados:")
                for cons in consultores:
                    status = "✅ Ativo" if cons[4] else "❌ Inativo"
                    print(f"   [{cons[0]}] {cons[1]} ({cons[2]}) - PV: {cons[3]} - {status}")
            else:
                print("⚠️ Nenhum consultor cadastrado")

            # Resumo
            print("\n" + "=" * 80)
            print("RESUMO DO TESTE DE BANCO")
            print("=" * 80)
            print(f"✅ Conexão: OK")
            print(f"✅ Tabelas encontradas: {len(tabelas_encontradas)}/{len(tabelas_necessarias)}")
            if tabelas_faltando:
                print(f"❌ Tabelas faltando: {', '.join(tabelas_faltando)}")
                print(f"\n💡 Execute: psql -f backend/sql/criar_tabelas_automacao.sql")
            print(f"📊 Consultores cadastrados: {len(consultores)}")
            print("=" * 80 + "\n")

            return len(tabelas_faltando) == 0

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\n💡 Verifique:")
        print("   1. PostgreSQL está rodando?")
        print("   2. Porta 5434 está correta?")
        print("   3. Credenciais estão corretas?")
        print("   4. Banco 'nexus_crm' existe?")
        return False


# ============================================================================
# TESTE 2: IMPORTAÇÃO DE EXCEL
# ============================================================================

def testar_importacao_excel(caminho_planilha: str):
    """
    Testa importação de planilha Excel

    Args:
        caminho_planilha: Caminho da planilha para testar
    """
    print("\n" + "=" * 80)
    print("TESTE 2: IMPORTAÇÃO DE PLANILHA EXCEL")
    print("=" * 80)

    caminho = Path(caminho_planilha)

    if not caminho.exists():
        print(f"\n❌ Arquivo não encontrado: {caminho}")
        print(f"\n💡 Coloque a planilha em: {CanopusConfig.EXCEL_DIR}")
        return False

    try:
        print(f"\n📄 Arquivo: {caminho.name}")
        print(f"   Tamanho: {caminho.stat().st_size / 1024:.2f} KB")

        # Criar importador
        importer = ExcelImporter()

        # 1. Identificar consultor
        print("\n1️⃣ Identificando consultor pelo nome do arquivo...")
        consultor = importer.identificar_consultor(caminho)

        if consultor:
            print(f"✅ Consultor identificado: {consultor.nome}")
            print(f"   Empresa: {consultor.empresa}")
            print(f"   Ponto de Venda: {consultor.ponto_venda}")
            print(f"   Pasta: {consultor.pasta_boletos}")
            if consultor.cor_identificacao:
                print(f"   Cor: {consultor.cor_identificacao}")
        else:
            print("⚠️ Consultor NÃO identificado pelo nome do arquivo")
            print("   A planilha será processada, mas sem consultor vinculado")

        # 2. Ler planilha
        print("\n2️⃣ Lendo planilha Excel...")
        import pandas as pd

        df = pd.read_excel(caminho, dtype=str)
        print(f"✅ Planilha carregada: {len(df)} linhas")

        # 3. Mostrar colunas encontradas
        print("\n3️⃣ Colunas encontradas na planilha:")
        for idx, col in enumerate(df.columns, 1):
            print(f"   [{idx:2d}] {col}")

        # 4. Mapear colunas automaticamente
        print("\n4️⃣ Mapeamento automático de colunas...")
        mapeamento = importer.mapear_colunas(df)

        if mapeamento:
            print("✅ Colunas mapeadas:")
            for campo, coluna in mapeamento.items():
                print(f"   {campo:15s} → {coluna}")
        else:
            print("❌ Nenhuma coluna foi mapeada!")

        if 'cpf' not in mapeamento:
            print("\n❌ ERRO: Coluna CPF não encontrada!")
            print("💡 A planilha deve ter uma coluna com nome:")
            print(f"   {CanopusConfig.EXCEL_COLUMNS.cpf_variations}")
            return False

        # 5. Extrair clientes
        print("\n5️⃣ Extraindo dados dos clientes...")
        clientes = importer.extrair_clientes(caminho)

        print(f"✅ {len(clientes)} clientes extraídos")

        # 6. Mostrar amostra de clientes
        print("\n6️⃣ Amostra de clientes (primeiros 5):")
        for idx, cliente in enumerate(clientes[:5], 1):
            print(f"\n   Cliente {idx}:")
            print(f"      CPF: {cliente.get('cpf_formatado')}")
            print(f"      Nome: {cliente.get('nome', 'N/A')}")
            print(f"      Grupo/Cota: {cliente.get('grupo', 'N/A')}/{cliente.get('cota', 'N/A')}")
            print(f"      Ponto Venda: {cliente.get('ponto_venda', 'N/A')}")
            if 'whatsapp' in cliente:
                print(f"      WhatsApp: {cliente['whatsapp']}")
            print(f"      Linha Excel: {cliente.get('linha_planilha')}")

        # 7. Estatísticas
        print("\n7️⃣ Estatísticas:")

        # Contar por ponto de venda
        pontos = {}
        for cliente in clientes:
            pv = cliente.get('ponto_venda', 'Não informado')
            pontos[pv] = pontos.get(pv, 0) + 1

        print(f"   Clientes por ponto de venda:")
        for pv, qtd in pontos.items():
            print(f"      {pv}: {qtd}")

        # Clientes com WhatsApp
        com_whatsapp = sum(1 for c in clientes if 'whatsapp' in c)
        print(f"   Clientes com WhatsApp: {com_whatsapp}/{len(clientes)} ({com_whatsapp/len(clientes)*100:.1f}%)")

        # Resumo
        print("\n" + "=" * 80)
        print("RESUMO DO TESTE DE IMPORTAÇÃO")
        print("=" * 80)
        print(f"✅ Arquivo lido: {caminho.name}")
        print(f"✅ Consultor: {consultor.nome if consultor else 'Não identificado'}")
        print(f"✅ Colunas mapeadas: {len(mapeamento)}")
        print(f"✅ Clientes extraídos: {len(clientes)}")
        print(f"✅ Dados prontos para staging!")
        print("=" * 80 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ ERRO ao importar planilha: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TESTE 3: LOGIN NO CANOPUS
# ============================================================================

async def testar_login_canopus(
    usuario: str,
    senha: str,
    codigo_empresa: str = '0101',
    ponto_venda: str = '17.308'
):
    """
    Testa login no sistema Canopus
    IMPORTANTE: Este teste VAI FALHAR nos seletores - é para mapeá-los!

    Args:
        usuario: Usuário de login
        senha: Senha
        codigo_empresa: Código da empresa (padrão: 0101)
        ponto_venda: Código do ponto de venda (padrão: 17.308)
    """
    print("\n" + "=" * 80)
    print("TESTE 3: LOGIN NO SISTEMA CANOPUS")
    print("=" * 80)

    print("\n⚠️ ATENÇÃO:")
    print("   Este teste vai FALHAR nos seletores CSS - é esperado!")
    print("   Use este teste para MAPEAR os seletores corretos.")
    print("   O navegador ficará ABERTO para você inspecionar.\n")

    print("🔐 Credenciais:")
    print(f"   Empresa: {codigo_empresa}")
    print(f"   Ponto de Venda: {ponto_venda}")
    print(f"   Usuário: {usuario}")
    print(f"   Senha: {'*' * len(senha)}")

    input("\n▶️ Pressione ENTER para iniciar o teste...")

    try:
        # Criar automação com headless=False (navegador visível)
        print("\n1️⃣ Iniciando navegador (visível para debug)...")

        async with CanopusAutomation(headless=False) as bot:
            print("✅ Navegador iniciado")

            # Tentar fazer login
            print("\n2️⃣ Tentando fazer login...")
            print(f"   URL: {CanopusConfig.URLS['login']}")

            try:
                login_ok = await bot.login(
                    codigo_empresa=codigo_empresa,
                    ponto_venda=ponto_venda,
                    usuario=usuario,
                    senha=senha
                )

                if login_ok:
                    print("✅ LOGIN BEM-SUCEDIDO!")
                    print("\n🎉 Parabéns! Os seletores estão corretos!")

                    # Aguardar para ver a página logada
                    print("\n📸 Tirando screenshot da página logada...")
                    await bot.screenshot("login_sucesso")

                    input("\n▶️ Navegador ficará aberto. Pressione ENTER para fechar...")

                    return True

                else:
                    print("❌ LOGIN FALHOU")
                    print("\n🔍 PRÓXIMOS PASSOS:")

            except Exception as e:
                print(f"❌ ERRO durante login: {e}")
                print("\n🔍 ANÁLISE DO ERRO:")

            # Se chegou aqui, login falhou - hora de mapear
            print("\n" + "=" * 80)
            print("INSTRUÇÕES PARA MAPEAR SELETORES CSS")
            print("=" * 80)

            print("\n📋 O navegador está ABERTO. Faça o seguinte:")
            print("\n1️⃣ Pressione F12 para abrir DevTools")
            print("2️⃣ Clique na setinha de seleção (canto superior esquerdo)")
            print("3️⃣ Clique em cada campo e copie o seletor CSS\n")

            print("📝 Campos para mapear:")
            print("\n   CAMPO                SELETOR ATUAL")
            print("   " + "-" * 70)

            selectors = CanopusConfig.SELECTORS['login']
            for campo, seletor in selectors.items():
                print(f"   {campo:20s} {seletor}")

            print("\n💡 Como copiar o seletor CSS:")
            print("   1. Clique com botão direito no elemento (no DevTools)")
            print("   2. Copy → Copy selector")
            print("   3. Atualize em config.py → SELECTORS['login']")

            print("\n📸 Tirando screenshot para análise...")
            await bot.screenshot("login_falhou")
            screenshot_path = CanopusConfig.LOGS_DIR / "login_falhou.png"
            print(f"   Salvo em: {screenshot_path}")

            print("\n🔍 URL atual:")
            print(f"   {bot.page.url}")

            input("\n▶️ Pressione ENTER quando terminar de mapear os seletores...")

            return False

    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TESTE 4: FLUXO COMPLETO MOCK
# ============================================================================

def testar_fluxo_completo_mock():
    """
    Testa fluxo completo com dados MOCK (sem acessar Canopus)
    Valida integração com banco de dados
    """
    print("\n" + "=" * 80)
    print("TESTE 4: FLUXO COMPLETO COM DADOS MOCK")
    print("=" * 80)

    print("\n📝 Este teste simula todo o fluxo sem acessar o Canopus:")
    print("   1. Cria consultor (se não existir)")
    print("   2. Cria clientes no staging")
    print("   3. Registra execução")
    print("   4. Simula downloads (dados fake)")
    print("   5. Registra logs")

    try:
        with DatabaseManager() as db:
            # 1. Criar consultor de teste
            print("\n1️⃣ Criando consultor de teste...")

            with db.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO consultores (
                        nome, empresa, ponto_venda, pasta_boletos, ativo
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (nome) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                    RETURNING id, nome
                """, ('Teste Mock', 'credms', '17.308', 'TesteMock', True))

                consultor = cur.fetchone()
                db.conn.commit()

            consultor_id = consultor['id']
            print(f"✅ Consultor: {consultor['nome']} (ID: {consultor_id})")

            # 2. Criar clientes fake no staging
            print("\n2️⃣ Criando clientes fake no staging...")

            clientes_fake = [
                {
                    'cpf': '12345678901',
                    'nome': 'Cliente Mock 1',
                    'ponto_venda': '17.308',
                    'grupo': '1234',
                    'cota': '001',
                    'consultor_nome': 'Teste Mock',
                    'arquivo_origem': 'teste_mock.xlsx',
                    'linha_planilha': 2
                },
                {
                    'cpf': '98765432100',
                    'nome': 'Cliente Mock 2',
                    'ponto_venda': '17.308',
                    'grupo': '1234',
                    'cota': '002',
                    'consultor_nome': 'Teste Mock',
                    'arquivo_origem': 'teste_mock.xlsx',
                    'linha_planilha': 3
                },
            ]

            for cliente in clientes_fake:
                staging_id = db.salvar_cliente_staging(cliente)
                print(f"   ✅ Cliente staging criado: {cliente['nome']} (ID: {staging_id})")

            # 3. Registrar execução
            print("\n3️⃣ Registrando execução mock...")

            automacao_id = db.registrar_execucao(
                tipo='teste',
                consultor_id=consultor_id,
                parametros={'teste': 'mock', 'clientes': len(clientes_fake)}
            )

            print(f"✅ Execução registrada: {automacao_id}")

            db.atualizar_execucao(
                automacao_id,
                status='em_andamento',
                total_clientes=len(clientes_fake),
                mensagem_atual='Processando clientes mock'
            )

            # 4. Simular downloads
            print("\n4️⃣ Simulando downloads (dados fake)...")

            for idx, cliente in enumerate(clientes_fake, 1):
                print(f"\n   Processando cliente {idx}/{len(clientes_fake)}: {cliente['nome']}")

                # Simular resultado de download
                resultado_fake = {
                    'cpf': cliente['cpf'],
                    'mes': 'DEZEMBRO',
                    'ano': 2024,
                    'status': 'sucesso',
                    'mensagem': 'Download simulado com sucesso',
                    'dados_cliente': {
                        'nome': cliente['nome'],
                        'encontrado': True
                    },
                    'dados_boleto': {
                        'arquivo_nome': f"{cliente['cpf']}_DEZEMBRO_2024.pdf",
                        'arquivo_caminho': f"/fake/path/{cliente['cpf']}.pdf",
                        'arquivo_tamanho': 45678,
                        'numero_boleto': f"1234567890{idx}",
                        'valor': '350.00',
                        'vencimento': '2024-12-10'
                    },
                    'tempo_execucao_segundos': 2.5
                }

                # Registrar log
                log_id = db.registrar_download_boleto(
                    automacao_id=automacao_id,
                    consultor_id=consultor_id,
                    cliente_final_id=None,
                    resultado=resultado_fake
                )

                print(f"   ✅ Log registrado (ID: {log_id})")

                # Atualizar progresso
                db.atualizar_execucao(
                    automacao_id,
                    processados_sucesso=idx,
                    progresso_percentual=(idx / len(clientes_fake)) * 100
                )

            # 5. Finalizar execução
            print("\n5️⃣ Finalizando execução...")

            db.atualizar_execucao(
                automacao_id,
                status='concluida',
                total_clientes=len(clientes_fake),
                processados_sucesso=len(clientes_fake),
                processados_erro=0,
                progresso_percentual=100.0,
                mensagem_atual='Teste mock concluído'
            )

            print("✅ Execução finalizada")

            # 6. Verificar dados salvos
            print("\n6️⃣ Verificando dados salvos...")

            with db.conn.cursor() as cur:
                # Verificar execução
                cur.execute("""
                    SELECT * FROM execucoes_automacao
                    WHERE automacao_id = %s
                """, (automacao_id,))

                execucao = cur.fetchone()
                print(f"\n   📊 Execução {automacao_id}:")
                print(f"      Status: {execucao['status']}")
                print(f"      Total clientes: {execucao['total_clientes']}")
                print(f"      Sucessos: {execucao['processados_sucesso']}")
                print(f"      Progresso: {execucao['progresso_percentual']}%")

                # Verificar logs
                cur.execute("""
                    SELECT COUNT(*) as total, status
                    FROM log_downloads_boletos
                    WHERE automacao_id = %s
                    GROUP BY status
                """, (automacao_id,))

                logs = cur.fetchall()
                print(f"\n   📋 Logs de download:")
                for log in logs:
                    print(f"      {log['status']}: {log['total']}")

            # Resumo
            print("\n" + "=" * 80)
            print("RESUMO DO TESTE MOCK")
            print("=" * 80)
            print(f"✅ Consultor criado: Teste Mock (ID: {consultor_id})")
            print(f"✅ Clientes staging: {len(clientes_fake)}")
            print(f"✅ Execução registrada: {automacao_id}")
            print(f"✅ Logs de download: {len(clientes_fake)}")
            print(f"✅ Integração com banco: OK")
            print("=" * 80 + "\n")

            return True

    except Exception as e:
        print(f"\n❌ ERRO no teste mock: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# FUNÇÃO PRINCIPAL COM CLI
# ============================================================================

def main():
    """Função principal com CLI"""
    parser = argparse.ArgumentParser(
        description="Testes da Automação Canopus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Testar conexão com banco
  python teste_automacao.py --teste conexao

  # Testar importação de planilha
  python teste_automacao.py --teste excel --arquivo excel_files/Dayler.xlsx

  # Testar login no Canopus (para mapear seletores)
  python teste_automacao.py --teste login --usuario SEU_USER --senha SUA_SENHA

  # Testar fluxo completo com dados mock
  python teste_automacao.py --teste mock

  # Rodar todos os testes (exceto login)
  python teste_automacao.py --teste all
        """
    )

    parser.add_argument(
        '--teste',
        choices=['conexao', 'excel', 'login', 'mock', 'all'],
        required=True,
        help='Tipo de teste a executar'
    )

    parser.add_argument(
        '--arquivo',
        help='Caminho da planilha Excel (para teste excel)'
    )

    parser.add_argument(
        '--usuario',
        help='Usuário de login (para teste login)'
    )

    parser.add_argument(
        '--senha',
        help='Senha de login (para teste login)'
    )

    parser.add_argument(
        '--empresa',
        default='0101',
        help='Código da empresa (padrão: 0101)'
    )

    parser.add_argument(
        '--ponto-venda',
        default='17.308',
        help='Código do ponto de venda (padrão: 17.308)'
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "=" * 80)
    print(" " * 20 + "TESTES DE AUTOMAÇÃO CANOPUS")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)

    sucesso = False

    try:
        if args.teste == 'conexao' or args.teste == 'all':
            sucesso = testar_conexao_db()

        if args.teste == 'excel':
            if not args.arquivo:
                print("\n❌ Erro: --arquivo é obrigatório para teste excel")
                print("💡 Uso: python teste_automacao.py --teste excel --arquivo planilha.xlsx")
                return 1

            sucesso = testar_importacao_excel(args.arquivo)

        elif args.teste == 'all':
            # Procurar primeira planilha disponível
            planilhas = list(CanopusConfig.EXCEL_DIR.glob('*.xlsx'))
            if planilhas:
                print(f"\n🔍 Usando planilha: {planilhas[0].name}")
                sucesso = testar_importacao_excel(str(planilhas[0]))
            else:
                print(f"\n⚠️ Nenhuma planilha encontrada em {CanopusConfig.EXCEL_DIR}")

        if args.teste == 'login':
            if not args.usuario or not args.senha:
                print("\n❌ Erro: --usuario e --senha são obrigatórios para teste login")
                print("💡 Uso: python teste_automacao.py --teste login --usuario X --senha Y")
                return 1

            sucesso = asyncio.run(testar_login_canopus(
                usuario=args.usuario,
                senha=args.senha,
                codigo_empresa=args.empresa,
                ponto_venda=args.ponto_venda
            ))

        if args.teste == 'mock' or args.teste == 'all':
            sucesso = testar_fluxo_completo_mock()

        # Resultado final
        print("\n" + "=" * 80)
        if sucesso:
            print("✅ TESTE CONCLUÍDO COM SUCESSO")
        else:
            print("❌ TESTE FALHOU - Verifique os erros acima")
        print("=" * 80 + "\n")

        return 0 if sucesso else 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        return 1

    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
