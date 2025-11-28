#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de importação do Canopus
"""
import sys
from pathlib import Path

# Adicionar paths
backend_path = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("TESTE DE IMPORTAÇÃO CANOPUS")
print("=" * 80)

try:
    print("\n1. Tentando importar routes.automation_canopus...")
    from routes.automation_canopus import CANOPUS_DISPONIVEL
    print(f"   ✓ Importação OK")
    print(f"   CANOPUS_DISPONIVEL = {CANOPUS_DISPONIVEL}")

    if not CANOPUS_DISPONIVEL:
        print("\n2. Tentando importar orquestrador diretamente...")
        automation_path = Path(__file__).resolve().parent / "automation" / "canopus"
        sys.path.insert(0, str(automation_path))

        try:
            from orquestrador import CanopusOrquestrador
            print("   ✓ Orquestrador importado COM SUCESSO!")
        except Exception as e:
            print(f"   ✗ Erro ao importar orquestrador: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✅ CANOPUS ESTÁ DISPONÍVEL!")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
