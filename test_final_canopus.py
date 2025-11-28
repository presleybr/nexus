import sys
from pathlib import Path

# Setup paths
backend_path = Path(__file__).parent / "backend"
automation_path = Path(__file__).parent / "automation" / "canopus"

sys.path.insert(0, str(backend_path))
sys.path.append(str(automation_path))

# Test import
try:
    from routes.automation_canopus import CANOPUS_DISPONIVEL
    print(f"RESULTADO: CANOPUS_DISPONIVEL = {CANOPUS_DISPONIVEL}")
    if CANOPUS_DISPONIVEL:
        print("SUCCESS - Automacao Canopus funcionando!")
        sys.exit(0)
    else:
        print("FALHOU - Canopus nao disponivel")
        sys.exit(1)
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(2)
