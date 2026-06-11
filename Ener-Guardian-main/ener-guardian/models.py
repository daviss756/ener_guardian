"""
ENER-GUARDIAN — Modelos do Banco de Dados
Sistema de Monitoramento Inteligente de Consumo Energético
"""
from datetime import datetime, date, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    """Modelo de usuário com controle de acesso por papéis."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    papel = db.Column(db.String(30), nullable=False, default='lider_producao')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    apontamentos = db.relationship('Apontamento', backref='usuario', lazy='dynamic')

    PAPEIS = {
        'admin': 'Administrador',
        'gestor': 'Gestor Industrial',
        'lider_producao': 'Líder de Produção',
        'tecnico': 'Técnico de Manutenção',
        'financeiro': 'Financeiro',
        'engenheiro': 'Engenheiro Chefe',
    }

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def papel_display(self):
        return self.PAPEIS.get(self.papel, self.papel)

    @property
    def iniciais(self):
        partes = self.nome.split()
        if len(partes) >= 2:
            return (partes[0][0] + partes[-1][0]).upper()
        return self.nome[:2].upper()


class Setor(db.Model):
    """Setores da empresa com limites de consumo."""
    __tablename__ = 'setores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    limite_consumo_kwh = db.Column(db.Float, default=500.0)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    equipamentos = db.relationship('Equipamento', backref='setor', lazy='dynamic')
    consumos = db.relationship('Consumo', backref='setor', lazy='dynamic')
    alertas = db.relationship('Alerta', backref='setor', lazy='dynamic')


class Equipamento(db.Model):
    """Equipamentos industriais com especificações elétricas."""
    __tablename__ = 'equipamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(80), nullable=False)
    potencia_watts = db.Column(db.Float, nullable=False)
    voltagem = db.Column(db.Float, nullable=True)
    corrente_amperes = db.Column(db.Float, nullable=True)
    fator_potencia = db.Column(db.Float, default=0.85)
    fator_carga = db.Column(db.Float, default=0.7)
    regime_carga = db.Column(db.String(20), default='medio')
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    sensores = db.relationship('Sensor', backref='equipamento', lazy='dynamic')
    apontamentos = db.relationship('Apontamento', backref='equipamento', lazy='dynamic')
    consumos = db.relationship('Consumo', backref='equipamento', lazy='dynamic')
    alertas = db.relationship('Alerta', backref='equipamento', lazy='dynamic')

    REGIMES = {
        'leve': 'Carga Leve (0.3-0.5)',
        'medio': 'Carga Média (0.5-0.7)',
        'pesado': 'Carga Pesada (0.7-0.9)',
        'pleno': 'Carga Plena (0.9-1.0)',
    }

    TIPOS = [
        'Motor Elétrico', 'Prensa Hidráulica', 'Compressor', 'Torno CNC',
        'Caldeira', 'Bomba', 'Ventilador', 'Iluminação', 'Ar Condicionado',
        'Soldadora', 'Furadeira Industrial', 'Serra Elétrica', 'Outro'
    ]

    @property
    def potencia_kw(self):
        return self.potencia_watts / 1000

    @property
    def status_display(self):
        return 'Ativo' if self.ativo else 'Inativo'


class Sensor(db.Model):
    """Sensores vinculados a equipamentos (pode ser simulado)."""
    __tablename__ = 'sensores'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    modelo = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ativo')
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class Apontamento(db.Model):
    """Registro de apontamento operacional (tempo de uso de equipamento)."""
    __tablename__ = 'apontamentos'

    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_operacao = db.Column(db.Date, nullable=False, default=date.today)
    turno = db.Column(db.String(20), nullable=False)
    horas_uso = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationship
    consumo = db.relationship('Consumo', backref='apontamento', uselist=False)

    TURNOS = {
        'manha': 'Manhã (06h-14h)',
        'tarde': 'Tarde (14h-22h)',
        'noite': 'Noite (22h-06h)',
        'integral': 'Integral',
    }


class Consumo(db.Model):
    """Registro de consumo calculado a partir do apontamento."""
    __tablename__ = 'consumos'

    id = db.Column(db.Integer, primary_key=True)
    apontamento_id = db.Column(db.Integer, db.ForeignKey('apontamentos.id'), nullable=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    consumo_kwh = db.Column(db.Float, nullable=False)
    custo_estimado = db.Column(db.Float, nullable=False)
    potencia_utilizada = db.Column(db.Float)
    metodo_calculo = db.Column(db.String(30))
    data_referencia = db.Column(db.Date, nullable=False)
    calculado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class Alerta(db.Model):
    """Alertas gerados pelo sistema quando limites são ultrapassados."""
    __tablename__ = 'alertas'

    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.String(20), nullable=False, default='medio')
    mensagem = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='ativo')
    consumo_detectado = db.Column(db.Float)
    limite_configurado = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    resolvido_em = db.Column(db.DateTime, nullable=True)

    NIVEIS = {
        'critico': 'Crítico',
        'alto': 'Alto',
        'medio': 'Médio',
        'baixo': 'Baixo',
    }

    TIPOS = [
        'consumo_excessivo',
        'equipamento_fora_horario',
        'pico_consumo',
        'desperdicio_detectado',
        'limite_setor_ultrapassado',
    ]


class Configuracao(db.Model):
    """Configurações globais do sistema."""
    __tablename__ = 'configuracoes'

    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.String(255))
