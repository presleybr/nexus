#!/usr/bin/env python3
"""
Script para atualizar logos em todos os templates CRM
"""

import os
import re

# Templates CRM Cliente para atualizar
templates_crm = [
    "frontend/templates/crm-cliente/cadastro-clientes.html",
    "frontend/templates/crm-cliente/disparos.html",
    "frontend/templates/crm-cliente/graficos.html",
    "frontend/templates/crm-cliente/monitoramento.html",
    "frontend/templates/crm-cliente/whatsapp-baileys.html",
    "frontend/templates/crm-cliente/whatsapp-conexao.html",
]

# Template Admin
templates_admin = [
    "frontend/templates/crm-admin/dashboard-admin.html",
]

# Pattern antigo (emoji no sidebar)
old_pattern_sidebar = r'''            <div class="sidebar-logo">
                <h2>⚡ NEXUS CRM</h2>'''

# Novo padrão com logo
new_template_sidebar = '''            <div class="sidebar-logo">
                <img src="/static/images/nexus_Logotipo.png" alt="Nexus CRM" style="height: 50px; margin-bottom: 10px;">
                <h2>NEXUS CRM</h2>'''

base_dir = "D:/Nexus"

print("Atualizando logos nos templates CRM...")

for template_path in templates_crm + templates_admin:
    full_path = os.path.join(base_dir, template_path)

    if not os.path.exists(full_path):
        print(f"[SKIP] Arquivo nao encontrado: {template_path}")
        continue

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Substituir
    new_content = content.replace(old_pattern_sidebar, new_template_sidebar)

    if new_content != content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[OK] Atualizado: {template_path}")
    else:
        print(f"[OK] Ja atualizado: {template_path}")

print("\n[OK] Processo concluido!")
print("\nResumo:")
print("- Landing page: Logo no header e footer")
print("- Login pages: Logo no card de login")
print("- CRM Dashboards: Logo na sidebar")
