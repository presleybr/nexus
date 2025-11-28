# 🚀 COMO USAR A IDENTIDADE VISUAL NEXUS

**Guia rápido de integração da identidade visual verde neon nos templates HTML**

---

## ✅ ARQUIVOS CSS CRIADOS

Todos os arquivos CSS estão em `D:\Nexus\frontend\static\css\`:

1. ✅ **`variables.css`** - Design System (variáveis globais)
2. ✅ **`components.css`** - Componentes reutilizáveis
3. ✅ **`animations.css`** - Efeitos e animações
4. ✅ **`landing.css`** - Landing page (atualizado)
5. ✅ **`login.css`** - Página de login (atualizado)
6. ✅ **`crm-cliente.css`** - Dashboard CRM (atualizado)

---

## 📋 PASSO 1: ATUALIZAR `<head>` DOS TEMPLATES HTML

### Para TODOS os templates, adicione no `<head>`:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus CRM</title>

    <!-- ✅ DESIGN SYSTEM NEXUS -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/animations.css">

    <!-- ✅ CSS ESPECÍFICO DA PÁGINA -->
    <!-- Para Landing Page: -->
    <link rel="stylesheet" href="/static/css/landing.css">

    <!-- OU Para Login: -->
    <!-- <link rel="stylesheet" href="/static/css/login.css"> -->

    <!-- OU Para CRM Dashboard: -->
    <!-- <link rel="stylesheet" href="/static/css/crm-cliente.css"> -->

    <!-- Google Fonts (já incluído nos CSS, mas pode adicionar aqui também) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Conteúdo aqui -->
</body>
</html>
```

---

## 📐 ESTRUTURAS HTML PRONTAS

### 1. LANDING PAGE

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus CRM - Aqui seu tempo vale ouro</title>
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/animations.css">
    <link rel="stylesheet" href="/static/css/landing.css">
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <div class="navbar-container">
            <a href="/" class="logo">
                <img src="/static/images/nexus_Logotipo.png" alt="Nexus">
                <span class="logo-text">NEXUS</span>
            </a>
            <a href="/login" class="nav-btn">Entrar</a>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <span class="hero-badge fade-in">Sistema Inteligente</span>
            <h1 class="fade-in-up">
                <span class="hero-title-line1">Transforme Seu Negócio com</span><br>
                <span class="hero-title-line2">Nexus CRM</span>
            </h1>
            <p class="subtitle fade-in-up delay-200">
                Gestão completa de clientes, vendas e finanças em um único lugar.
            </p>
            <p class="tagline fade-in-up delay-300">
                Aqui seu tempo vale ouro ⚡
            </p>
            <div class="cta-buttons fade-in-up delay-400">
                <a href="/login" class="btn-primary">Entrar no Sistema</a>
                <a href="#features" class="btn-secondary">Conheça Mais</a>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features">
        <div class="features-container">
            <h2 class="section-title">Recursos Poderosos</h2>
            <p class="section-subtitle">Tudo que você precisa para gerenciar seu negócio</p>

            <div class="features-grid">
                <!-- Feature Card 1 -->
                <div class="feature-card fade-in-up delay-100">
                    <div class="feature-icon">📊</div>
                    <h3>Dashboard Inteligente</h3>
                    <p>Visualize métricas em tempo real com gráficos modernos e intuitivos.</p>
                </div>

                <!-- Feature Card 2 -->
                <div class="feature-card fade-in-up delay-200">
                    <div class="feature-icon">👥</div>
                    <h3>Gestão de Clientes</h3>
                    <p>Organize todos os dados dos seus clientes em um só lugar.</p>
                </div>

                <!-- Feature Card 3 -->
                <div class="feature-card fade-in-up delay-300">
                    <div class="feature-icon">💰</div>
                    <h3>Controle Financeiro</h3>
                    <p>Acompanhe receitas, despesas e boletos automaticamente.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-container">
            <div class="footer-section">
                <h3>Nexus CRM</h3>
                <p>Sistema completo de gestão empresarial.</p>
            </div>
            <div class="footer-section">
                <h3>Links</h3>
                <a href="/login">Login</a>
                <a href="#features">Recursos</a>
                <a href="#contato">Contato</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2025 Nexus CRM. Todos os direitos reservados.</p>
            <p class="tagline">Aqui seu tempo vale ouro ⚡</p>
        </div>
    </footer>
</body>
</html>
```

### 2. LOGIN PAGE

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Nexus CRM</title>
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/animations.css">
    <link rel="stylesheet" href="/static/css/login.css">
</head>
<body>
    <div class="login-container">
        <div class="login-card">
            <!-- Header -->
            <div class="login-header">
                <div class="logo-login">
                    <img src="/static/images/nexus_Logotipo.png" alt="Nexus" class="glow">
                    NEXUS CRM
                </div>
                <p class="login-subtitle">Entre para começar</p>
            </div>

            <!-- Alert (opcional) -->
            <div class="alert alert-error" style="display: none;">
                Erro ao fazer login. Verifique suas credenciais.
            </div>

            <!-- Form -->
            <form action="/login" method="POST">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" name="email" class="form-input" placeholder="seu@email.com" required>
                </div>

                <div class="form-group">
                    <label class="form-label">Senha</label>
                    <input type="password" name="senha" class="form-input" placeholder="********" required>
                </div>

                <button type="submit" class="btn-login">Entrar</button>
            </form>

            <!-- Divider -->
            <div class="divider">ou</div>

            <!-- Footer -->
            <div class="login-footer">
                <p>Não tem uma conta? <a href="/cadastro" class="login-link">Cadastre-se</a></p>
            </div>
        </div>
    </div>
</body>
</html>
```

### 3. CRM DASHBOARD

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Nexus CRM</title>
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/animations.css">
    <link rel="stylesheet" href="/static/css/crm-cliente.css">
</head>
<body>
    <div class="crm-container">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-logo">
                <h2>⚡ NEXUS CRM</h2>
                <p>Dashboard</p>
            </div>

            <nav>
                <ul class="sidebar-menu">
                    <li class="menu-item">
                        <a href="/crm/dashboard" class="menu-link active">
                            <span class="menu-icon">📊</span>
                            Dashboard
                        </a>
                    </li>
                    <li class="menu-item">
                        <a href="/crm/clientes" class="menu-link">
                            <span class="menu-icon">👥</span>
                            Clientes
                        </a>
                    </li>
                    <li class="menu-item">
                        <a href="/crm/boletos" class="menu-link">
                            <span class="menu-icon">💰</span>
                            Boletos
                        </a>
                    </li>
                    <li class="menu-item">
                        <a href="/crm/whatsapp" class="menu-link">
                            <span class="menu-icon">📱</span>
                            WhatsApp
                        </a>
                    </li>
                </ul>
            </nav>

            <button class="logout-btn" onclick="window.location.href='/logout'">
                🚪 Sair
            </button>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Header -->
            <div class="content-header fade-in">
                <h1>Dashboard</h1>
                <p>Visão geral do seu negócio</p>
            </div>

            <!-- Stats Cards -->
            <div class="dashboard-stats">
                <!-- Stat Card 1 -->
                <div class="stat-card fade-in-up delay-100">
                    <div class="stat-card-header">
                        <span class="stat-card-title">Total de Clientes</span>
                        <span class="stat-card-icon">👥</span>
                    </div>
                    <div class="stat-card-value">1,234</div>
                    <div class="stat-card-change positive">
                        ↑ 12% este mês
                    </div>
                </div>

                <!-- Stat Card 2 -->
                <div class="stat-card fade-in-up delay-200">
                    <div class="stat-card-header">
                        <span class="stat-card-title">Receita Mensal</span>
                        <span class="stat-card-icon">💰</span>
                    </div>
                    <div class="stat-card-value">R$ 45.2K</div>
                    <div class="stat-card-change positive">
                        ↑ 8% este mês
                    </div>
                </div>

                <!-- Stat Card 3 -->
                <div class="stat-card fade-in-up delay-300">
                    <div class="stat-card-header">
                        <span class="stat-card-title">Boletos Pendentes</span>
                        <span class="stat-card-icon">📄</span>
                    </div>
                    <div class="stat-card-value">23</div>
                    <div class="stat-card-change negative">
                        ↓ 5% este mês
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div class="table-container fade-in-up delay-400">
                <div class="table-header">
                    <h2>Últimos Clientes</h2>
                    <button class="btn-primary btn-sm">+ Novo Cliente</button>
                </div>

                <table class="table-nexus">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Email</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>João Silva</td>
                            <td>joao@email.com</td>
                            <td><span class="status-badge ativo">Ativo</span></td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-action">✏️</button>
                                    <button class="btn-action delete">🗑️</button>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td>Maria Santos</td>
                            <td>maria@email.com</td>
                            <td><span class="status-badge pendente">Pendente</span></td>
                            <td>
                                <div class="table-actions">
                                    <button class="btn-action">✏️</button>
                                    <button class="btn-action delete">🗑️</button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </main>
    </div>
</body>
</html>
```

---

## 🎨 COMPONENTES PRONTOS PARA USAR

### Botões

```html
<!-- Botão Primary (Verde Neon) -->
<button class="btn-primary">Salvar</button>

<!-- Botão Secondary (Outline) -->
<button class="btn-secondary">Cancelar</button>

<!-- Botão Ghost (Transparente) -->
<button class="btn-ghost">Voltar</button>

<!-- Botões com tamanhos -->
<button class="btn-primary btn-sm">Pequeno</button>
<button class="btn-primary">Normal</button>
<button class="btn-primary btn-lg">Grande</button>
<button class="btn-primary btn-block">Largura Total</button>
```

### Cards

```html
<!-- Card Glass -->
<div class="card-glass">
    <h3>Título do Card</h3>
    <p>Conteúdo com efeito glassmorphism.</p>
</div>

<!-- Card Gradient -->
<div class="card-gradient">
    <h3>Card com Gradiente</h3>
    <p>Efeito radial interno.</p>
</div>
```

### Badges

```html
<span class="badge-neon">NOVO</span>
<span class="badge-success">ATIVO</span>
<span class="badge-warning">PENDENTE</span>
<span class="badge-error">ERRO</span>
```

### Inputs

```html
<div class="form-group">
    <label class="form-label">Nome</label>
    <input type="text" class="input-nexus" placeholder="Digite seu nome">
</div>
```

### Alerts

```html
<div class="alert alert-success">
    ✅ Operação realizada com sucesso!
</div>

<div class="alert alert-error">
    ❌ Erro ao processar a solicitação.
</div>

<div class="alert alert-warning">
    ⚠️ Atenção: Verifique os dados.
</div>

<div class="alert alert-info">
    ℹ️ Nova atualização disponível.
</div>
```

### Loading

```html
<div class="loading-spinner">
    <div class="spinner"></div>
</div>
```

---

## 🎬 ANIMAÇÕES

### Fade Animations

```html
<div class="fade-in">Aparece com fade</div>
<div class="fade-in-up">Aparece de baixo</div>
<div class="fade-in-down">Aparece de cima</div>
<div class="fade-in-left">Aparece da esquerda</div>
<div class="fade-in-right">Aparece da direita</div>
```

### Delays

```html
<div class="fade-in-up delay-100">Atraso 0.1s</div>
<div class="fade-in-up delay-200">Atraso 0.2s</div>
<div class="fade-in-up delay-300">Atraso 0.3s</div>
<div class="fade-in-up delay-500">Atraso 0.5s</div>
```

### Efeitos Especiais

```html
<div class="pulse-neon">Pulsação Neon</div>
<img src="logo.png" class="glow">
<div class="float">Flutuação</div>
<div class="hover-lift">Eleva no hover</div>
```

---

## 🔧 VARIÁVEIS CSS DISPONÍVEIS

Você pode usar essas variáveis diretamente no seu CSS ou inline styles:

```css
/* Cores */
var(--nexus-primary)        /* Verde Neon #39FF14 */
var(--nexus-success)        /* Verde Sucesso #00FF88 */
var(--nexus-warning)        /* Amarelo #FFD700 */
var(--nexus-error)          /* Vermelho #FF1744 */

/* Backgrounds */
var(--nexus-bg-primary)     /* Preto #000000 */
var(--nexus-bg-card)        /* Card transparente */
var(--nexus-bg-glass)       /* Glassmorphism */

/* Texto */
var(--nexus-text-primary)   /* Branco #FFFFFF */
var(--nexus-text-secondary) /* Cinza Claro #E0E0E0 */
var(--nexus-text-muted)     /* Cinza Escuro #707070 */

/* Tamanhos de Fonte */
var(--nexus-text-sm)        /* 14px */
var(--nexus-text-base)      /* 16px */
var(--nexus-text-lg)        /* 18px */
var(--nexus-text-xl)        /* 20px */
var(--nexus-text-2xl)       /* 24px */

/* Espaçamentos */
var(--nexus-space-sm)       /* 8px */
var(--nexus-space-md)       /* 16px */
var(--nexus-space-lg)       /* 24px */
var(--nexus-space-xl)       /* 32px */
var(--nexus-space-2xl)      /* 48px */

/* Border Radius */
var(--nexus-radius-sm)      /* 4px */
var(--nexus-radius-md)      /* 8px */
var(--nexus-radius-lg)      /* 16px */
var(--nexus-radius-xl)      /* 24px */
var(--nexus-radius-full)    /* 9999px */

/* Sombras */
var(--nexus-shadow-neon)    /* Sombra Neon Média */
var(--nexus-shadow-neon-strong) /* Sombra Neon Forte */
```

---

## ✅ CHECKLIST DE INTEGRAÇÃO

- [ ] Incluir `variables.css` em todos os templates
- [ ] Incluir `components.css` em todos os templates
- [ ] Incluir `animations.css` em todos os templates
- [ ] Incluir CSS específico (landing.css, login.css ou crm-cliente.css)
- [ ] Atualizar logo para usar `/static/images/nexus_Logotipo.png`
- [ ] Adicionar classes de animação (fade-in, fade-in-up, etc.)
- [ ] Usar componentes prontos (btn-primary, card-glass, etc.)
- [ ] Testar responsividade em mobile
- [ ] Verificar performance e loading

---

## 🚀 PRONTO PARA USAR!

Todos os arquivos CSS estão criados e prontos. Basta:

1. Adicionar os `<link>` no `<head>` dos templates HTML
2. Usar as classes CSS nos elementos
3. Customizar conforme necessário

**Nexus CRM** - "Aqui seu tempo vale ouro" ⚡

---

**Versão:** 1.0.0
**Data:** 2025-11-16
**Identidade:** Verde Neon #39FF14 + Preto + Glassmorphism
**Status:** ✅ COMPLETO
