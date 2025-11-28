"""
Rotas de Autenticação - Login e gerenciamento de sessões
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Usuario, ClienteNexus, log_sistema

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

print("="*60)
print("[*] BLUEPRINT AUTH.PY CARREGADO COM MODIFICACOES DE DEBUG")
print("="*60)


# Manipulador de erro para este blueprint
@auth_bp.errorhandler(Exception)
def handle_auth_error(e):
    import traceback
    error_trace = traceback.format_exc()
    print("\n" + "="*60)
    print("❌ ERRO CAPTURADO NO BLUEPRINT AUTH")
    print("="*60)
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    print(f"\nTraceback:")
    print(error_trace)
    print("="*60 + "\n")

    from flask import jsonify
    return jsonify({
        'erro': f'{type(e).__name__}: {str(e)}',
        'detalhes': error_trace
    }), 500


def login_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'erro': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para rotas que requerem permissão de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'erro': 'Não autenticado'}), 401

        if session.get('tipo') != 'admin':
            return jsonify({'erro': 'Acesso negado - Apenas administradores'}), 403

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login
    Body: { "email": "...", "password": "..." }
    """
    print("\n" + "#"*60)
    print("### FUNÇÃO LOGIN() CHAMADA ###")
    print("#"*60 + "\n")

    try:
        print("\n=== INICIANDO LOGIN ===")
        data = request.get_json()
        print(f"Data recebida: {data}")

        email = data.get('email')
        password = data.get('password')
        print(f"Email: {email}")

        if not email or not password:
            print("Email ou senha vazios")
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

        # Autentica o usuário
        print("Chamando Usuario.autenticar()...")
        usuario = Usuario.autenticar(email, password)
        print(f"Resultado autenticacao: {usuario}")

        if not usuario:
            print("Credenciais invalidas")
            return jsonify({'erro': 'Credenciais inválidas'}), 401

        # Cria a sessão
        print("Criando sessao...")
        session['usuario_id'] = usuario['id']
        session['email'] = usuario['email']
        session['tipo'] = usuario['tipo']
        session.permanent = True
        print("Sessao criada")

        # Se for cliente, busca dados do cliente_nexus
        cliente_nexus = None
        if usuario['tipo'] == 'cliente':
            print("Buscando dados do cliente_nexus...")
            cliente_nexus = ClienteNexus.buscar_por_usuario_id(usuario['id'])
            if cliente_nexus:
                session['cliente_nexus_id'] = cliente_nexus['id']
            print(f"Cliente nexus: {cliente_nexus}")

        print("Registrando log de sucesso...")
        try:
            log_sistema('success', f'Login realizado: {email}', 'autenticacao',
                       {'usuario_id': usuario['id']})
            print("Log registrado com sucesso")
        except Exception as log_error:
            print(f"ERRO ao registrar log (continuando): {log_error}")

        print("Preparando resposta JSON...")
        resposta = {
            'sucesso': True,
            'mensagem': 'Login realizado com sucesso',
            'usuario': {
                'id': usuario['id'],
                'email': usuario['email'],
                'tipo': usuario['tipo']
            },
            'cliente_nexus': cliente_nexus
        }
        print(f"Resposta: {resposta}")

        return jsonify(resposta), 200

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"❌ ERRO NO LOGIN:")
        print(f"Erro: {e}")
        print(f"Tipo: {type(e)}")
        print(f"\nTraceback completo:")
        print(error_trace)
        print(f"{'='*60}\n")

        try:
            log_sistema('error', f'Erro no login: {str(e)}', 'autenticacao')
        except:
            print("ERRO ao registrar log do erro (ignorando)")

        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Endpoint de logout"""
    try:
        email = session.get('email', 'Desconhecido')

        session.clear()

        log_sistema('info', f'Logout realizado: {email}', 'autenticacao')

        return jsonify({
            'sucesso': True,
            'mensagem': 'Logout realizado com sucesso'
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@auth_bp.route('/verificar-sessao', methods=['GET'])
def verificar_sessao():
    """Verifica se há uma sessão ativa"""
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'usuario': {
                'id': session['usuario_id'],
                'email': session.get('email'),
                'tipo': session['tipo']
            }
        }), 200
    else:
        return jsonify({'autenticado': False}), 200


@auth_bp.route('/registrar', methods=['POST'])
def registrar():
    """
    Endpoint de registro de novo usuário
    Body: {
        "email": "...",
        "password": "...",
        "nome_empresa": "...",
        "cnpj": "...",
        "whatsapp": "..."
    }
    """
    try:
        data = request.get_json()

        # Validações básicas
        campos_obrigatorios = ['email', 'password', 'nome_empresa', 'cnpj']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'erro': f'Campo obrigatório: {campo}'}), 400

        # Verifica se email já existe
        if Usuario.verificar_email_existe(data['email']):
            return jsonify({'erro': 'Email já cadastrado'}), 400

        # Cria o usuário
        usuario_id = Usuario.criar(
            email=data['email'],
            password=data['password'],
            tipo='cliente'
        )

        # Cria o cliente Nexus associado
        cliente_nexus_id = ClienteNexus.criar(
            nome_empresa=data['nome_empresa'],
            cnpj=data['cnpj'],
            usuario_id=usuario_id,
            whatsapp_numero=data.get('whatsapp')
        )

        log_sistema('success', f'Novo registro: {data["email"]}', 'autenticacao',
                   {'usuario_id': usuario_id, 'cliente_nexus_id': cliente_nexus_id})

        return jsonify({
            'sucesso': True,
            'mensagem': 'Cadastro realizado com sucesso',
            'usuario_id': usuario_id,
            'cliente_nexus_id': cliente_nexus_id
        }), 201

    except Exception as e:
        log_sistema('error', f'Erro no registro: {str(e)}', 'autenticacao')
        return jsonify({'erro': str(e)}), 500


@auth_bp.route('/alterar-senha', methods=['POST'])
@login_required
def alterar_senha():
    """
    Altera a senha do usuário logado
    Body: { "senha_atual": "...", "senha_nova": "..." }
    """
    try:
        data = request.get_json()

        senha_atual = data.get('senha_atual')
        senha_nova = data.get('senha_nova')

        if not senha_atual or not senha_nova:
            return jsonify({'erro': 'Senhas são obrigatórias'}), 400

        # Verifica senha atual
        usuario = Usuario.autenticar(session.get('email'), senha_atual)

        if not usuario:
            return jsonify({'erro': 'Senha atual incorreta'}), 401

        # Atualiza a senha
        sucesso = Usuario.atualizar_senha(session['usuario_id'], senha_nova)

        if sucesso:
            log_sistema('info', 'Senha alterada', 'autenticacao',
                       {'usuario_id': session['usuario_id']})

            return jsonify({
                'sucesso': True,
                'mensagem': 'Senha alterada com sucesso'
            }), 200
        else:
            return jsonify({'erro': 'Erro ao atualizar senha'}), 500

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@auth_bp.route('/perfil', methods=['GET'])
@login_required
def get_perfil():
    """Retorna dados do perfil do usuário logado"""
    try:
        usuario = Usuario.buscar_por_id(session['usuario_id'])

        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Se for cliente, busca dados do cliente_nexus
        cliente_nexus = None
        if usuario['tipo'] == 'cliente':
            cliente_nexus = ClienteNexus.buscar_por_usuario_id(usuario['id'])

        return jsonify({
            'usuario': usuario,
            'cliente_nexus': cliente_nexus
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500
