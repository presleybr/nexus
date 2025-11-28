"""
Testar normalização automática de WhatsApp
Formato esperado: 55 + DDD + 8 dígitos (SEM o 9 inicial)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def normalizar_whatsapp(numero):
    """Remove formatação, adiciona código do país e remove 9 inicial"""
    import re

    if not numero:
        return ""

    # Remove tudo exceto dígitos
    apenas_digitos = re.sub(r'[^\d]', '', str(numero))

    # Adiciona código do país se não tiver
    if apenas_digitos and not apenas_digitos.startswith('55'):
        apenas_digitos = '55' + apenas_digitos

    # Remove 9º dígito se for um 9 (formato: 55 + DDD + 8 dígitos)
    if len(apenas_digitos) == 13 and apenas_digitos[4] == '9':
        # 55 + DDD (2) + 9 + 8 dígitos → 55 + DDD + 8 dígitos
        apenas_digitos = apenas_digitos[:4] + apenas_digitos[5:]

    return apenas_digitos

print("\n" + "="*80)
print("TESTE DE NORMALIZACAO DE WHATSAPP")
print("="*80 + "\n")

# Casos de teste
testes = [
    # Formato: (entrada, esperado)
    ("+55 67 9 6391-1866", "556763911866"),  # Com 9 inicial e formatação
    ("67 9 6391-1866", "556763911866"),     # Com 9 inicial sem código
    ("(67) 99999-9999", "556799999999"),    # 9 dígitos após DDD -> remove 9
    ("67 9 9999-9999", "556799999999"),     # Com 9 inicial
    ("5567963911866", "556763911866"),      # 13 dígitos com 9
    ("5567999999999", "556799999999"),      # 13 dígitos com 9
    ("+55 67 9999-9999", "556799999999"),   # Com 9 inicial
    ("67 8403-5987", "556784035987"),       # Sem 9 inicial (8 dígitos)
    ("556784035987", "556784035987"),       # Já correto (sem 9)
    ("+55 67 9812-1311", "556798121311"),   # Com 9 inicial
    ("+55 67 9669-5041", "556796695041"),   # Com 9 inicial
    ("", ""),
    (None, ""),
]

print("Formato esperado: 55 + DDD + 8 dígitos (sem o 9 inicial)\n")

todos_ok = True
for entrada, esperado in testes:
    resultado = normalizar_whatsapp(entrada)
    status = "[OK]" if resultado == esperado else "[ERRO]"

    if resultado != esperado:
        todos_ok = False

    print(f"{status} Entrada: {str(entrada):<25} -> Saída: {resultado:<20} (Esperado: {esperado})")

print("\n" + "="*80)
if todos_ok:
    print("[OK] TODOS OS TESTES PASSARAM!")
    print("[INFO] Formato correto: 55 + DDD + 8 dígitos")
    print("[INFO] Exemplo: 556763911866 (sem o 9 inicial)")
else:
    print("[ERRO] ALGUNS TESTES FALHARAM!")
print("="*80 + "\n")
