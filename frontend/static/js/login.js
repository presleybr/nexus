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
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.sucesso) {
                showAlert('Login realizado com sucesso! Redirecionando...', 'success');

                // Redireciona baseado no tipo de usuário
                setTimeout(() => {
                    if (data.usuario.tipo === 'admin') {
                        window.location.href = '/admin/dashboard';
                    } else {
                        window.location.href = '/crm/dashboard';
                    }
                }, 1000);
            } else {
                showAlert(data.erro || 'Credenciais inválidas', 'error');
                btnLogin.disabled = false;
                btnLogin.textContent = 'Entrar';
            }
        } catch (error) {
            console.error('Erro no login:', error);
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
