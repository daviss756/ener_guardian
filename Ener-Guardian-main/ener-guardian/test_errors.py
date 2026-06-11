"""Captura detalhes dos erros 500 no Ener-Guardian."""
import requests

base = 'http://127.0.0.1:5000'
session = requests.Session()
session.post(f'{base}/login', data={'email': 'admin@energuardian.com', 'senha': 'admin123'}, allow_redirects=True)

# Testar export excel (500)
r = session.get(f'{base}/relatorios/export?format=excel')
print('=== EXPORT EXCEL (500) ===')
# Extrair a mensagem de erro do HTML se em modo debug
if 'Traceback' in r.text or 'Error' in r.text or 'error' in r.text.lower():
    # Pegar parte relevante
    lines = r.text.split('\n')
    for i, line in enumerate(lines):
        if 'error' in line.lower() or 'traceback' in line.lower() or 'exception' in line.lower() or 'importerror' in line.lower() or 'modulenot' in line.lower():
            start = max(0, i-1)
            end = min(len(lines), i+5)
            for l in lines[start:end]:
                clean = l.strip()
                if clean:
                    print(clean)
            break
else:
    print(f'Status: {r.status_code}')
    print(r.text[:500])

print()

# Testar export pdf (500)
r = session.get(f'{base}/relatorios/export?format=pdf')
print('=== EXPORT PDF (500) ===')
if 'Traceback' in r.text or 'Error' in r.text:
    lines = r.text.split('\n')
    for i, line in enumerate(lines):
        if 'error' in line.lower() or 'traceback' in line.lower() or 'exception' in line.lower():
            start = max(0, i-1)
            end = min(len(lines), i+5)
            for l in lines[start:end]:
                clean = l.strip()
                if clean:
                    print(clean)
            break
else:
    print(f'Status: {r.status_code}')
    print(r.text[:500])

print()

# Testar POST apontamento com horas_uso vazia (500)
r = session.post(f'{base}/apontamentos/novo', data={
    'equipamento_id': '1',
    'horas_uso': '',
    'turno': 'manha',
}, allow_redirects=True)
print('=== POST APONTAMENTO HORAS VAZIA (500) ===')
if 'Traceback' in r.text or 'Error' in r.text:
    lines = r.text.split('\n')
    for i, line in enumerate(lines):
        if 'error' in line.lower() or 'traceback' in line.lower() or 'valueerror' in line.lower() or 'exception' in line.lower():
            start = max(0, i-1)
            end = min(len(lines), i+5)
            for l in lines[start:end]:
                clean = l.strip()
                if clean:
                    print(clean)
            break
else:
    print(f'Status: {r.status_code}')
    print(r.text[:500])
