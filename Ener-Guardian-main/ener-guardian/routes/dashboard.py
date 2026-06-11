"""
# Rotas do Dashboard Simplificado (Corporate UI)
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import db, Consumo, Alerta, Equipamento, Setor
from sqlalchemy import func
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    # KPI: Consumo total hoje
    consumo_hoje = db.session.query(
        func.coalesce(func.sum(Consumo.consumo_kwh), 0)
    ).filter(Consumo.data_referencia == hoje).scalar()

    consumo_ontem = db.session.query(
        func.coalesce(func.sum(Consumo.consumo_kwh), 0)
    ).filter(Consumo.data_referencia == ontem).scalar()

    variacao_consumo = 0
    if consumo_ontem > 0:
        variacao_consumo = round(((consumo_hoje - consumo_ontem) / consumo_ontem) * 100, 1)

    # KPI: Custo estimado hoje
    custo_hoje = db.session.query(
        func.coalesce(func.sum(Consumo.custo_estimado), 0)
    ).filter(Consumo.data_referencia == hoje).scalar()

    custo_ontem = db.session.query(
        func.coalesce(func.sum(Consumo.custo_estimado), 0)
    ).filter(Consumo.data_referencia == ontem).scalar()

    variacao_custo = 0
    if custo_ontem > 0:
        variacao_custo = round(((custo_hoje - custo_ontem) / custo_ontem) * 100, 1)

    # KPI: Alertas ativos
    alertas_ativos = Alerta.query.filter_by(status='ativo').count()
    alertas_hoje = Alerta.query.filter(
        Alerta.criado_em >= hoje.isoformat()
    ).count()

    # KPI: Eficiência (equipamentos ativos vs total)
    total_equip = Equipamento.query.count()
    equip_ativos = Equipamento.query.filter_by(ativo=True).count()
    eficiencia = round((equip_ativos / total_equip * 100) if total_equip > 0 else 0)

    # Consumo por setor (para gráfico de barras)
    consumo_por_setor = db.session.query(
        Setor.nome,
        func.coalesce(func.sum(Consumo.consumo_kwh), 0).label('total_kwh')
    ).outerjoin(Consumo, Consumo.setor_id == Setor.id).group_by(
        Setor.nome
    ).all()

    # Top equipamentos ativos
    top_equipamentos = db.session.query(
        Equipamento.nome,
        Equipamento.tipo,
        Setor.nome.label('setor_nome'),
        Equipamento.ativo,
        func.coalesce(func.sum(Consumo.consumo_kwh), 0).label('consumo_total')
    ).outerjoin(Consumo, Consumo.equipamento_id == Equipamento.id).join(
        Setor, Equipamento.setor_id == Setor.id
    ).group_by(
        Equipamento.id, Equipamento.nome, Equipamento.tipo, Setor.nome, Equipamento.ativo
    ).order_by(func.sum(Consumo.consumo_kwh).desc()).limit(5).all()

    # Consumo últimos 7 dias (para gráfico de linha)
    consumo_7dias = []
    for i in range(6, -1, -1):
        d = hoje - timedelta(days=i)
        total = db.session.query(
            func.coalesce(func.sum(Consumo.consumo_kwh), 0)
        ).filter(Consumo.data_referencia == d).scalar()
        consumo_7dias.append({'data': d.strftime('%d/%m'), 'valor': round(total, 1)})

    return render_template('dashboard.html',
        consumo_hoje=round(consumo_hoje, 1),
        variacao_consumo=variacao_consumo,
        custo_hoje=round(custo_hoje, 2),
        variacao_custo=variacao_custo,
        alertas_ativos=alertas_ativos,
        alertas_hoje=alertas_hoje,
        eficiencia=eficiencia,
        consumo_por_setor=consumo_por_setor,
        top_equipamentos=top_equipamentos,
        consumo_7dias=consumo_7dias,
    )
