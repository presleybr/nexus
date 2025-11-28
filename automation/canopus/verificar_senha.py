import sys
sys.path.insert(0, 'D:/Nexus/backend')
sys.path.insert(0, 'D:/Nexus/automation/canopus')

from db_config import get_connection_params
import psycopg

conn = psycopg.connect(**get_connection_params())
cur = conn.cursor()

cur.execute("""
    SELECT pv.codigo, c.usuario, c.senha_encrypted
    FROM credenciais_canopus c
    LEFT JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
    WHERE pv.codigo LIKE %s
""", ('24627%',))

row = cur.fetchone()

print('PV:', row[0])
print('Usuario:', row[1])

senha = row[2]
print('Tipo:', type(senha))
print('Tamanho:', len(senha))
print('Primeiros 50 chars:', repr(senha[:50]) if len(senha) > 50 else repr(senha))

if isinstance(senha, str):
    print('Comeca com \\x?', senha.startswith('\\x'))
    print('Primeiros 10 chars ASCII:', [ord(c) for c in senha[:10]])

conn.close()
