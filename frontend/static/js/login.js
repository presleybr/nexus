// Login JavaScript - Nexus CRM

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const btnLogin = document.getElementById('btnLogin');
    const alertDiv = document.getElementById('alert');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (!email || !password) {
            showAlert('Por favor, preencha todos os campos', 'error');
            return;
        }

        // Desabilita o botão
        btnLogin.disabled = true;
        btnLogin.textContent = 'Entrando...';

        try {
            console.log('[LOGIN] Enviando requisição para /api/auth/login');
            console.log('[LOGIN] Email:', email);

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include', // IMPORTANTE: Para cookies/sessões
                body: JSON.stringify({ email, password })
            });

            console.log('[LOGIN] Response status:', response.status);
            console.log('[LOGIN] Response ok:', response.ok);

            const data = await response.json();
            console.log('[LOGIN] Response data:', data);

            if (response.ok && data.sucesso) {
                console.log('[LOGIN] ✅ Login bem-sucedido!');
                showAlert('Login realizado com sucesso! Redirecionando...', 'success');

                // Redireciona baseado no tipo de usuário
                setTimeout(() => {
                    if (data.usuario.tipo === 'admin') {
                        console.log('[LOGIN] Redirecionando para admin dashboard');
                        window.location.href = '/admin/dashboard';
                    } else {
                        console.log('[LOGIN] Redirecionando para CRM dashboard');
                        window.location.href = '/crm/dashboard';
                    }
                }, 1000);
            } else {
                console.error('[LOGIN] ❌ Falha no login:', data);
                showAlert(data.erro || 'Credenciais inválidas', 'error');
                btnLogin.disabled = false;
                btnLogin.textContent = 'Entrar';
            }
        } catch (error) {
            console.error('[LOGIN] ❌ Erro no login:', error);
            showAlert('Erro ao conectar com o servidor', 'error');
            btnLogin.disabled = false;
            btnLogin.textContent = 'Entrar';
        }
    });

    function showAlert(message, type) {
        alertDiv.textContent = message;
        alertDiv.className = `alert alert-${type} show`;

        setTimeout(() => {
            alertDiv.classList.remove('show');
        }, 5000);
    }
});
