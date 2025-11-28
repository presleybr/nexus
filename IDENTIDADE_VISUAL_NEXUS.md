# 🎨 IDENTIDADE VISUAL NEXUS CRM
**Verde Neon + Preto + Glassmorphism + Tech**

---

## ✅ STATUS DA IMPLEMENTAÇÃO

### Arquivos Criados/Atualizados

- ✅ **`frontend/static/css/variables.css`** - Design System completo
- ✅ **`frontend/static/css/components.css`** - Componentes reutilizáveis
- ✅ **`frontend/static/css/animations.css`** - Efeitos e animações
- ✅ **`frontend/static/css/landing.css`** - Landing page moderna
- ✅ **`frontend/static/css/login.css`** - Login com glassmorphism
- ⏳ **`frontend/static/css/crm-cliente.css`** - Dashboard CRM (em progresso)

---

## 🎨 PALETA DE CORES

### Cores Primárias
```css
--nexus-primary: #39FF14           /* Verde Neon Principal */
--nexus-primary-dark: #2DD10D      /* Verde Neon Escuro */
--nexus-primary-light: #5FFF3D     /* Verde Neon Claro */
--nexus-primary-glow: rgba(57, 255, 20, 0.5) /* Brilho Neon */
```

### Cores Secundárias
```css
--nexus-secondary: #0A4D0A         /* Verde Escuro */
--nexus-secondary-dark: #053505    /* Verde Muito Escuro */
--nexus-secondary-light: #0D660D   /* Verde Médio */
```

### Backgrounds
```css
--nexus-bg-primary: #000000        /* Preto Absoluto */
--nexus-bg-secondary: #0A0E0A      /* Preto Esverdeado */
--nexus-bg-tertiary: #0F140F       /* Cinza Muito Escuro */
--nexus-bg-card: rgba(15, 20, 15, 0.8) /* Card com transparência */
--nexus-bg-glass: rgba(255, 255, 255, 0.05) /* Glassmorphism */
```

### Textos
```css
--nexus-text-primary: #FFFFFF      /* Branco */
--nexus-text-secondary: #E0E0E0    /* Cinza Claro */
--nexus-text-tertiary: #A0A0A0     /* Cinza Médio */
--nexus-text-muted: #707070        /* Cinza Escuro */
```

### Cores de Status
```css
--nexus-success: #00FF88           /* Verde Sucesso */
--nexus-warning: #FFD700           /* Amarelo Aviso */
--nexus-error: #FF1744             /* Vermelho Erro */
--nexus-info: #00E5FF              /* Azul Info */
```

---

## 📐 TIPOGRAFIA

### Fontes
```css
--nexus-font-primary: 'Inter'       /* Texto geral */
--nexus-font-display: 'Space Grotesk' /* Títulos e destaques */
--nexus-font-mono: 'Fira Code'     /* Código */
```

### Tamanhos
```css
--nexus-text-xs: 0.75rem     /* 12px */
--nexus-text-sm: 0.875rem    /* 14px */
--nexus-text-base: 1rem      /* 16px */
--nexus-text-lg: 1.125rem    /* 18px */
--nexus-text-xl: 1.25rem     /* 20px */
--nexus-text-2xl: 1.5rem     /* 24px */
--nexus-text-3xl: 1.875rem   /* 30px */
--nexus-text-4xl: 2.25rem    /* 36px */
--nexus-text-5xl: 3rem       /* 48px */
--nexus-text-6xl: 3.75rem    /* 60px */
```

---

## 🎭 EFEITOS VISUAIS

### Sombras Neon
```css
/* Sombra Neon Pequena */
box-shadow: 0 0 10px var(--nexus-primary-glow);

/* Sombra Neon Média */
box-shadow: 0 0 20px var(--nexus-primary-glow),
            0 0 40px var(--nexus-primary-glow);

/* Sombra Neon Forte */
box-shadow: 0 0 10px var(--nexus-primary),
            0 0 20px var(--nexus-primary),
            0 0 40px var(--nexus-primary-glow);
```

### Gradientes
```css
/* Gradiente Primary */
background: linear-gradient(135deg, #39FF14 0%, #0A4D0A 100%);

/* Gradiente Glass */
background: linear-gradient(135deg,
  rgba(255, 255, 255, 0.1) 0%,
  rgba(255, 255, 255, 0.05) 100%);

/* Gradiente Dark */
background: linear-gradient(135deg, #0A0E0A 0%, #000000 100%);
```

### Glassmorphism
```css
background: rgba(255, 255, 255, 0.05);
backdrop-filter: blur(10px);
-webkit-backdrop-filter: blur(10px);
border: 1px solid rgba(57, 255, 20, 0.2);
border-radius: 1rem;
```

---

## 🧩 COMPONENTES

### Botões

**Botão Primary:**
- Background: Gradiente verde neon
- Efeito: Sombra neon + animação de brilho
- Hover: Eleva + intensifica sombra

**Botão Secondary:**
- Background: Transparente
- Border: Verde neon
- Hover: Preenche com verde neon

**Botão Ghost:**
- Background: Transparente
- Border sutil
- Hover: Glassmorphism + cor verde

### Cards

**Card Glass:**
- Background: Glassmorphism
- Border: Verde neon sutil
- Hover: Eleva + sombra neon

**Card Gradient:**
- Background: Gradiente glass
- Efeito radial interno
- Blur forte

### Inputs

**Input Nexus:**
- Background: Card escuro
- Border: Verde neon sutil
- Focus: Border verde + sombra neon
- Placeholder: Cinza muted

### Badges

**Badge Neon:**
- Background: Verde neon 10% opacidade
- Border: Verde neon
- Text: Verde neon
- Sombra neon pequena

---

## 🎬 ANIMAÇÕES

### Fade Animations
- `fadeIn` - Aparece com opacidade
- `fadeInUp` - Aparece de baixo
- `fadeInDown` - Aparece de cima
- `fadeInLeft/Right` - Aparece dos lados

### Glow & Pulse
- `pulseNeon` - Pulsação de sombra neon
- `glow` - Brilho contínuo
- `textGlow` - Texto brilhando

### Float & Hover
- `float` - Flutuação suave
- `hover-lift` - Eleva no hover
- `hover-glow` - Brilho no hover

### Special Effects
- `glitch` - Efeito glitch tech
- `scanline` - Linha de scan
- `ripple` - Ondas concêntricas
- `aurora` - Aurora boreal

---

## 📱 RESPONSIVIDADE

### Breakpoints
```css
--nexus-breakpoint-sm: 640px
--nexus-breakpoint-md: 768px
--nexus-breakpoint-lg: 1024px
--nexus-breakpoint-xl: 1280px
--nexus-breakpoint-2xl: 1536px
```

### Mobile First
Todos os componentes são mobile-first e adaptam-se automaticamente.

---

## 🎯 COMO USAR

### 1. Incluir CSS nos templates HTML

```html
<head>
  <!-- Variáveis e Design System -->
  <link rel="stylesheet" href="/static/css/variables.css">

  <!-- Componentes Reutilizáveis -->
  <link rel="stylesheet" href="/static/css/components.css">

  <!-- Animações -->
  <link rel="stylesheet" href="/static/css/animations.css">

  <!-- CSS Específico da Página -->
  <link rel="stylesheet" href="/static/css/landing.css">
  <!-- OU -->
  <link rel="stylesheet" href="/static/css/login.css">
  <!-- OU -->
  <link rel="stylesheet" href="/static/css/crm-cliente.css">
</head>
```

### 2. Usar Logo

```html
<div class="nexus-logo">
  <img src="/static/images/nexus_Logotipo.png" alt="Nexus">
  <span class="nexus-logo-text">NEXUS</span>
</div>
```

### 3. Criar Botão

```html
<!-- Botão Primary -->
<button class="btn-primary">Começar Agora</button>

<!-- Botão Secondary -->
<button class="btn-secondary">Saiba Mais</button>

<!-- Botão Ghost -->
<button class="btn-ghost">Cancelar</button>
```

### 4. Criar Card

```html
<div class="card-glass">
  <h3>Título do Card</h3>
  <p>Conteúdo do card com glassmorphism e efeito neon.</p>
</div>
```

### 5. Criar Badge

```html
<span class="badge-neon">NOVO</span>
<span class="badge-success">ATIVO</span>
<span class="badge-warning">PENDENTE</span>
<span class="badge-error">ERRO</span>
```

### 6. Criar Input

```html
<div class="form-group">
  <label class="form-label">Email</label>
  <input type="email" class="input-nexus" placeholder="seu@email.com">
</div>
```

### 7. Adicionar Animações

```html
<!-- Fade In Up com delay -->
<div class="fade-in-up delay-200">Conteúdo</div>

<!-- Pulse Neon -->
<div class="pulse-neon">Badge Pulsante</div>

<!-- Glow -->
<img src="logo.png" class="glow">

<!-- Float -->
<div class="float">Card Flutuante</div>
```

---

## 🌟 EXEMPLOS DE USO

### Hero Section
```html
<section class="hero">
  <div class="hero-content">
    <span class="hero-badge">SISTEMA INTELIGENTE</span>
    <h1>
      <span class="hero-title-line1">Transforme Seu Negócio com</span><br>
      <span class="hero-title-line2">Nexus CRM</span>
    </h1>
    <p class="subtitle">Gestão completa de clientes, vendas e finanças em um único lugar.</p>
    <p class="tagline">Aqui seu tempo vale ouro ⚡</p>
    <div class="cta-buttons">
      <a href="/login" class="btn-primary">Entrar no Sistema</a>
      <a href="#features" class="btn-secondary">Conheça Mais</a>
    </div>
  </div>
</section>
```

### Card Feature
```html
<div class="feature-card">
  <div class="feature-icon">📊</div>
  <h3>Dashboard Inteligente</h3>
  <p>Visualize métricas em tempo real com gráficos modernos e intuitivos.</p>
</div>
```

### Login Form
```html
<div class="login-card">
  <div class="login-header">
    <div class="logo-login">
      <img src="/static/images/nexus_Logotipo.png" alt="Nexus">
      NEXUS CRM
    </div>
    <p class="login-subtitle">Entre para começar</p>
  </div>

  <form>
    <div class="form-group">
      <label class="form-label">Email</label>
      <input type="email" class="form-input" placeholder="seu@email.com">
    </div>
    <button type="submit" class="btn-login">Entrar</button>
  </form>
</div>
```

---

## 🎨 BACKGROUND TECH

Todos os arquivos incluem automaticamente:

### 1. Background Animado
- Gradientes radiais verde neon
- Pulso suave (15s)
- Opacidade variável

### 2. Grid Tech
- Linhas verde neon sutis
- Espaçamento 50px
- Opacidade 30%

---

## ✨ FEATURES ESPECIAIS

### Efeito Glassmorphism
- Blur de 10-24px
- Transparência 5-10%
- Bordas sutis verde neon

### Efeito Neon
- Sombras com glow verde
- Bordas iluminadas
- Texto com brilho

### Efeito Tech
- Grid de fundo
- Partículas (opcional)
- Scanlines (opcional)
- Glitch effects

---

## 📊 HIERARQUIA VISUAL

1. **Primário (Verde Neon):** CTAs, títulos principais, destaques
2. **Secundário (Verde Escuro):** Subtítulos, cards, bordas
3. **Terciário (Branco/Cinza):** Textos, descrições
4. **Backgrounds (Preto/Escuro):** Fundo geral, cards

---

## 🚀 PRÓXIMOS PASSOS

- [x] Variables.css
- [x] Components.css
- [x] Animations.css
- [x] Landing.css
- [x] Login.css
- [ ] CRM-cliente.css
- [ ] Atualizar templates HTML
- [ ] Testes de responsividade
- [ ] Otimização de performance

---

**Nexus CRM** - "Aqui seu tempo vale ouro" ⚡

**Identidade:** Verde Neon #39FF14 + Preto #000000 + Glassmorphism
**Estilo:** Tech, Futurista, Moderno, Profissional
**Versão:** 1.0.0
**Data:** 2025-11-16
