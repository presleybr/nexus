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
            console.log('='.repeat(60));
            console.log('🔐 DEBUG LOGIN - INÍCIO');
            console.log('='.repeat(60));
            console.log('📧 Email:', email);
            console.log('🔑 Senha length:', password.length);
            console.log('🔑 Senha:', password); // TEMPORÁRIO - REMOVER EM PRODUÇÃO!
            console.log('🌐 URL:', window.location.origin + '/api/auth/login');

            const requestBody = { email, password };
            console.log('📦 Request Body:', JSON.stringify(requestBody, null, 2));

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(requestBody)
            });

            console.log('📡 Response status:', response.status);
            console.log('📡 Response statusText:', response.statusText);
            console.log('📡 Response ok:', response.ok);
            console.log('📡 Response headers:', [...response.headers.entries()]);

            let data;
            const contentType = response.headers.get('content-type');
            console.log('📄 Content-Type:', contentType);

            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
                console.log('📥 Response JSON:', JSON.stringify(data, null, 2));
            } else {
                const text = await response.text();
                console.log('📥 Response Text:', text);
                data = { erro: 'Resposta não é JSON: ' + text };
            }

            if (response.ok && data.sucesso) {
                console.log('✅ LOGIN SUCESSO!');
                console.log('👤 Usuário:', data.usuario);
                showAlert('Login realizado com sucesso! Redirecionando...', 'success');

                setTimeout(() => {
                    if (data.usuario.tipo === 'admin') {
                        console.log('🔀 Redirecionando para /admin/dashboard');
                        window.location.href = '/admin/dashboard';
                    } else {
                        console.log('🔀 Redirecionando para /crm/dashboard');
                        window.location.href = '/crm/dashboard';
                    }
                }, 1000);
            } else {
                console.log('❌ LOGIN FALHOU!');
                console.log('❌ Status:', response.status);
                console.log('❌ Data:', data);
                console.log('❌ Erro:', data.erro);
                console.log('='.repeat(60));

                showAlert(data.erro || 'Credenciais inválidas', 'error');
                btnLogin.disabled = false;
                btnLogin.textContent = 'Entrar';
            }
        } catch (error) {
            console.log('='.repeat(60));
            console.error('💥 EXCEPTION NO LOGIN!');
            console.error('💥 Error type:', error.constructor.name);
            console.error('💥 Error message:', error.message);
            console.error('💥 Error stack:', error.stack);
            console.log('='.repeat(60));

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
