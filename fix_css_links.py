#!/usr/bin/env python3
"""
Script para corrigir links CSS nos templates HTML
Adiciona variables.css, components.css, animations.css antes do CSS específico
"""

import os
import re

# Templates para atualizar
templates = [
    "frontend/templates/crm-cliente/cadastro-clientes.html",
    "frontend/templates/crm-cliente/disparos.html",
    "frontend/templates/crm-cliente/graficos.html",
    "frontend/templates/crm-cliente/monitoramento.html",
    "frontend/templates/crm-cliente/whatsapp-baileys.html",
    "frontend/templates/crm-cliente/whatsapp-conexao.html",
    "frontend/templates/crm-admin/dashboard-admin.html",
]

# Pattern antigo (Poppins + um CSS)
old_pattern = r'''    <link rel="preconnect" href="https://fonts\.googleapis\.com">
    <link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>
    <link href="https://fonts\.googleapis\.com/css2\?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/([^"]+)">'''

# Novo padrão (Inter + Space Grotesk + Design System)
new_template = '''    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Nexus Design System -->
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/animations.css">
    <link rel="stylesheet" href="/static/css/{css_file}">'''

base_dir = "D:/Nexus"

for template_path in templates:
    full_path = os.path.join(base_dir, template_path)

    if not os.path.exists(full_path):
        print(f"[SKIP] Arquivo nao encontrado: {full_path}")
        continue

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Substituir
    def replace_func(match):
        css_file = match.group(1)
        return new_template.format(css_file=css_file)

    new_content = re.sub(old_pattern, replace_func, content)

    if new_content != content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[OK] Atualizado: {template_path}")
    else:
        print(f"[OK] Ja atualizado: {template_path}")

print("\n[OK] Processo concluido!")
