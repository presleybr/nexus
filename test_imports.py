#!/usr/bin/env python3
"""Script de teste para validar imports"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("1. Testando import de database...")
try:
    from backend.models.database import db, Database
    print("   ✅ db importado com sucesso")
    print(f"   ✅ DatabaseWrapper disponível: {type(db)}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

print("\n2. Testando import de routes...")
try:
    from backend.routes.crm import crm_bp
    print("   ✅ crm_bp importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

print("\n3. Testando import de portal_consorcio...")
try:
    from backend.routes.portal_consorcio import register_portal_routes
    print("   ✅ portal_consorcio importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

print("\n4. Testando import de app...")
try:
    from backend.app import app
    print("   ✅ app importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ TODOS OS IMPORTS FUNCIONARAM!")
print("Sistema pronto para iniciar!")
