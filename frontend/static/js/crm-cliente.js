// CRM Cliente - JavaScript Principal

// Carrega dados ao iniciar
document.addEventListener('DOMContentLoaded', async function() {
    await carregarDashboard();
});

// Carrega dados do dashboard - DADOS DO PORTAL CONSÓRCIO
async function carregarDashboard() {
    try {
        const response = await fetch('/api/crm/dashboard');

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login-cliente';
                return;
            }
            throw new Error('Erro ao carregar dashboard');
        }

        const data = await response.json();

        console.log('Dashboard data:', data); // Debug

        // Atualiza estatísticas do Portal Consórcio
        if (data.success && data.dashboard) {
            const dash = data.dashboard;

            // Elementos que podem existir
            if (document.getElementById('empresaNome')) {
                document.getElementById('empresaNome').textContent = 'Portal Consórcio';
            }

            // Clientes finais
            if (document.getElementById('totalClientes')) {
                document.getElementById('totalClientes').textContent = dash.total_clientes_finais || 0;
            }

            // Boletos
            if (document.getElementById('totalBoletos')) {
                document.getElementById('totalBoletos').textContent = dash.total_boletos || 0;
            }

            if (document.getElementById('boletosEnviados')) {
                document.getElementById('boletosEnviados').textContent = dash.boletos_enviados || 0;
            }

            if (document.getElementById('boletosPendentes')) {
                document.getElementById('boletosPendentes').textContent = dash.boletos_pendentes || 0;
            }

            if (document.getElementById('boletosPagos')) {
                document.getElementById('boletosPagos').textContent = dash.boletos_pagos || 0;
            }

            if (document.getElementById('boletosVencidos')) {
                document.getElementById('boletosVencidos').textContent = dash.boletos_vencidos || 0;
            }

            // Valores
            if (document.getElementById('valorTotalCredito')) {
                document.getElementById('valorTotalCredito').textContent = formatarMoeda(dash.valor_total_credito || 0);
            }

            if (document.getElementById('valorTotalPendente')) {
                document.getElementById('valorTotalPendente').textContent = formatarMoeda(dash.valor_total_pendente || 0);
            }
        }

        // REMOVIDO: carregarUltimosBoletos() - agora usa apenas o card de boletos-baixados do Canopus
        // O card de boletos é carregado pelo dashboard.html inline via carregarDashboardStats()

    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        alert('Erro ao carregar dados do dashboard: ' + error.message);
    }
}

// Carrega últimos boletos do Portal
async function carregarUltimosBoletos() {
    try {
        const response = await fetch('/api/crm/boletos-portal?limit=5');
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.boletos) {
                exibirUltimosBoletos(data.boletos);
            }
        }
    } catch (error) {
        console.error('Erro ao carregar boletos:', error);
    }
}

// Formata valor em moeda brasileira
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor || 0);
}

// Exibe tabela de últimos boletos
function exibirUltimosBoletos(boletos) {
    const container = document.getElementById('ultimosBoletos');

    if (!boletos || boletos.length === 0) {
        container.innerHTML = '<p style="color: var(--cor-texto-secundario);">Nenhum boleto encontrado</p>';
        return;
    }

    let html = `
        <table class="table-nexus">
            <thead>
                <tr>
                    <th>Cliente</th>
                    <th>Mês Referência</th>
                    <th>Valor</th>
                    <th>Vencimento</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
    `;

    boletos.forEach(boleto => {
        const status = boleto.status_envio === 'enviado' ? 'success' :
                      boleto.status_envio === 'erro' ? 'error' : 'warning';

        const statusTexto = boleto.status_envio === 'enviado' ? 'Enviado' :
                           boleto.status_envio === 'erro' ? 'Erro' : 'Pendente';

        html += `
            <tr>
                <td>${boleto.nome_completo || boleto.cliente_nome || 'N/A'}</td>
                <td>${boleto.mes_referencia}/${boleto.ano_referencia || ''}</td>
                <td>R$ ${parseFloat(boleto.valor_original || boleto.valor || 0).toFixed(2)}</td>
                <td>${formatarData(boleto.data_vencimento || boleto.vencimento)}</td>
                <td><span class="badge-status badge-${status}">${statusTexto}</span></td>
                <td>
                    <button onclick="visualizarBoletoCRM(${boleto.id})" class="btn-icon-table" title="Visualizar PDF">👁️</button>
                    <button onclick="downloadBoletoCRM(${boleto.id})" class="btn-icon-table" title="Download PDF">📥</button>
                    <button onclick="enviarBoletoWhatsAppCRM(${boleto.id})" class="btn-icon-table" title="Enviar WhatsApp">📱</button>
                </td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// Formata data
function formatarData(data) {
    if (!data) return 'N/A';
    const d = new Date(data);
    return d.toLocaleDateString('pt-BR');
}

// Função para logout
async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST'
        });

        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Erro ao fazer logout:', error);
        window.location.href = '/';
    }
}

// Função para visualizar boleto inline
function visualizarBoletoCRM(boletoId) {
    // Criar modal para visualização
    const modal = document.createElement('div');
    modal.id = 'modalVisualizadorPDF';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; justify-content: center; align-items: center; z-index: 10000;';

    modal.innerHTML = `
        <div style="position: relative; width: 90%; height: 90%; background: white; border-radius: 8px; overflow: hidden;">
            <button onclick="document.getElementById('modalVisualizadorPDF').remove()"
                    style="position: absolute; top: 10px; right: 10px; z-index: 10001; background: var(--cor-erro); color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-size: 16px;">
                ✕ Fechar
            </button>
            <iframe id="iframePDF" src="/api/crm/boletos/${boletoId}/visualizar"
                    style="width: 100%; height: 100%; border: none;">
            </iframe>
        </div>
    `;

    document.body.appendChild(modal);

    // Fechar com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('modalVisualizadorPDF');
            if (modal) modal.remove();
        }
    });

    // Fechar clicando fora
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Função para download de boleto
function downloadBoletoCRM(boletoId) {
    window.open(`/api/crm/boletos/${boletoId}/download`, '_blank');
}

// Função para enviar boleto via WhatsApp
async function enviarBoletoWhatsAppCRM(boletoId) {
    if (!confirm('Deseja enviar este boleto via WhatsApp?')) {
        return;
    }

    try {
        const response = await fetch(`/api/crm/boletos/${boletoId}/enviar-whatsapp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('Boleto enviado com sucesso via WhatsApp!');
            // Recarregar boletos para atualizar status
            carregarDashboard();
        } else {
            alert('Erro ao enviar boleto: ' + (result.erro || result.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao enviar boleto:', error);
        alert('Erro ao enviar boleto via WhatsApp');
    }
}

// Função para gerar boletos
async function gerarBoletos() {
    if (!confirm('Deseja gerar boletos para todos os clientes?')) {
        return;
    }

    try {
        const response = await fetch('/api/automation/gerar-boletos', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Sucesso! ${data.total_gerados} boletos gerados.`);
            await carregarDashboard();
        } else {
            alert('Erro ao gerar boletos: ' + (data.erro || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao gerar boletos:', error);
        alert('Erro ao gerar boletos');
    }
}
