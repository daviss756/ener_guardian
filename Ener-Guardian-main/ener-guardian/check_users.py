from app import create_app
from models import Usuario
app = create_app()
with app.app_context():
    users = Usuario.query.all()
    print("Users found:", len(users))
    for u in users:
        print(f'User: {u.email}, Hash: {u.senha_hash}')
