"""Script de teste de rotas HTTP do Ener-Guardian."""
import requests

base = 'http://127.0.0.1:5000'
session = requests.Session()

# Login correto baseado no seed
r = session.post(f'{base}/login', data={'email': 'admin@energuardian.com', 'senha': 'admin123'}, allow_redirects=True)
print(f'LOGIN admin: {r.status_code} -> {r.url}')

# Testar todas as rotas autenticadas
rotas = [
    ('GET', '/'),
    ('GET', '/equipamentos/'),
    ('GET', '/equipamentos/novo'),
    ('GET', '/equipamentos/1/editar'),
    ('GET', '/apontamentos/'),
    ('GET', '/apontamentos/novo'),
    ('GET', '/alertas/'),
    ('GET', '/relatorios/'),
    ('GET', '/setores/'),
    ('GET', '/setores/novo'),
    ('GET', '/health'),
]

for method, rota in rotas:
    r = session.get(f'{base}{rota}', allow_redirects=True)
    status = r.status_code
    tag = 'OK' if status == 200 else 'ERRO'
    print(f'[{tag}] {method} {rota}: {status}')

# Exportações
for fmt in ['csv', 'excel', 'pdf']:
    r = session.get(f'{base}/relatorios/export?format={fmt}')
    ct = r.headers.get('Content-Type', '')
    print(f'[export/{fmt}] status={r.status_code} content-type={ct[:40]}')

# Filtros de equipamentos
for qs in ['status=ativo', 'status=inativo', 'setor=1']:
    r = session.get(f'{base}/equipamentos/?{qs}')
    print(f'[equip-filtro] ?{qs}: {r.status_code}')

# Filtros de alertas
for qs in ['nivel=critico', 'status=resolvido', 'busca=limite']:
    r = session.get(f'{base}/alertas/?{qs}')
    print(f'[alerta-filtro] ?{qs}: {r.status_code}')

# Filtros de relatorios
for qs in ['periodo=7', 'periodo=30']:
    r = session.get(f'{base}/relatorios/?{qs}')
    print(f'[relatorio-filtro] ?{qs}: {r.status_code}')

# Apontamentos: filtro por setor
r = session.get(f'{base}/apontamentos/?setor=1')
print(f'[apontamento-filtro] ?setor=1: {r.status_code}')

# POST apontamento valido
r = session.post(f'{base}/apontamentos/novo', data={
    'equipamento_id': '1',
    'horas_uso': '4.0',
    'turno': 'manha',
    'data_operacao': '2025-06-10',
    'observacao': 'Teste automatizado'
}, allow_redirects=True)
print(f'[POST apontamento valido]: {r.status_code} -> {r.url}')

# POST apontamento com dados invalidos (horas_uso vazia)
try:
    r = session.post(f'{base}/apontamentos/novo', data={
        'equipamento_id': '1',
        'horas_uso': '',
        'turno': 'manha',
    }, allow_redirects=True)
    print(f'[POST apontamento invalido (horas vazia)]: {r.status_code}')
except Exception as e:
    print(f'[POST apontamento invalido] EXCECAO: {e}')

# POST apontamento com equipamento inexistente
r = session.post(f'{base}/apontamentos/novo', data={
    'equipamento_id': '9999',
    'horas_uso': '4.0',
    'turno': 'manha',
    'data_operacao': '2025-06-10',
}, allow_redirects=True)
print(f'[POST apontamento equip inexistente]: {r.status_code}')

# Resolver alerta
r = session.post(f'{base}/alertas/1/resolver', allow_redirects=True)
print(f'[POST resolver alerta 1]: {r.status_code}')

# Ignorar alerta
r = session.post(f'{base}/alertas/2/ignorar', allow_redirects=True)
print(f'[POST ignorar alerta 2]: {r.status_code}')

# Excluir equipamento (CRITICO - apaga dados com relacionamentos)
r = session.post(f'{base}/equipamentos/99/excluir', allow_redirects=True)
print(f'[POST excluir equip inexistente]: {r.status_code}')

print('\n=== TESTES CONCLUIDOS ===')
