/**
 * Funções comuns para todas as páginas do CRM
 */

// Carregar informações da empresa/usuário logado
async function carregarInformacoesEmpresa() {
    try {
        const response = await fetch('/api/auth/verificar-sessao');
        const result = await response.json();

        if (result.autenticado) {
            const nomeEmpresa = document.getElementById('empresaNome');
            if (nomeEmpresa) {
                nomeEmpresa.textContent = result.usuario.email;
            }
        } else {
            window.location.href = '/login-cliente';
        }
    } catch (error) {
        console.error('Erro ao carregar informações:', error);
    }
}

// Função de logout
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login-cliente';
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        window.location.href = '/login-cliente';
    }
}

// Formatar data
function formatarData(data) {
    if (!data) return '-';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR');
}

// Formatar valor monetário
function formatarValor(valor) {
    if (!valor) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

// Formatar telefone
function formatarTelefone(telefone) {
    if (!telefone) return '-';
    const limpo = telefone.replace(/\D/g, '');
    if (limpo.length === 11) {
        return `(${limpo.slice(0, 2)}) ${limpo.slice(2, 7)}-${limpo.slice(7)}`;
    } else if (limpo.length === 10) {
        return `(${limpo.slice(0, 2)}) ${limpo.slice(2, 6)}-${limpo.slice(6)}`;
    }
    return telefone;
}

// Mostrar notificação toast
function mostrarNotificacao(mensagem, tipo = 'info') {
    // Criar elemento de notificação
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.textContent = mensagem;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${tipo === 'success' ? '#10b981' : tipo === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Adicionar animações CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
