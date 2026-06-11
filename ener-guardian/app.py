"""
ENER-GUARDIAN — Aplicação Flask Principal
Sistema de Monitoramento Inteligente de Consumo Energético
"""
import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from services.cache import cache
from models import db, Usuario

load_dotenv()

login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__)

    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ener_guardian.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TARIFA_ENERGIA'] = float(os.getenv('TARIFA_ENERGIA', '0.85'))

    if test_config is not None:
        app.config.update(test_config)

    # Inicializar extensões
    db.init_app(app)
    cache.init_app(app)

    login_manager.init_app(app)
    import logging, json
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                'time': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno
            }
            return json.dumps(log_record)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)

    # Health check endpoint
    @app.route('/health')
    def health():
        return {"status": "ok"}

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar o sistema.'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.equipamentos import equipamentos_bp
    from routes.apontamentos import apontamentos_bp
    from routes.alertas import alertas_bp
    from routes.relatorios import relatorios_bp
    from routes.setores import setores_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(equipamentos_bp)
    app.register_blueprint(apontamentos_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(setores_bp)

    # Criar tabelas na primeira execução
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
