"""Rotas de Alertas."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Alerta, Equipamento, Setor
from services.alerta_service import AlertaService

alertas_bp = Blueprint('alertas', __name__, url_prefix='/alertas')


@alertas_bp.route('/')
@login_required
def listar():
    filtro_nivel = request.args.get('nivel', '')
    filtro_status = request.args.get('status', 'ativo')
    busca = request.args.get('busca', '')

    query = Alerta.query

    if filtro_nivel:
        query = query.filter(Alerta.nivel == filtro_nivel)
    if filtro_status:
        query = query.filter(Alerta.status == filtro_status)
    if busca:
        query = query.filter(Alerta.mensagem.ilike(f'%{busca}%'))

    alertas = query.order_by(Alerta.criado_em.desc()).all()

    # Contadores
    total_ativos = Alerta.query.filter_by(status='ativo').count()
    total_criticos = Alerta.query.filter_by(status='ativo', nivel='critico').count()
    total_resolvidos_hoje = Alerta.query.filter(
        Alerta.status == 'resolvido'
    ).count()
    total_alertas = Alerta.query.count()

    return render_template('alertas/listar.html',
        alertas=alertas,
        total_ativos=total_ativos,
        total_criticos=total_criticos,
        total_resolvidos=total_resolvidos_hoje,
        total_alertas=total_alertas,
        filtro_nivel=filtro_nivel,
        filtro_status=filtro_status,
        busca=busca,
        niveis=Alerta.NIVEIS)


@alertas_bp.route('/<int:id>')
@login_required
def detalhes(id):
    alerta = Alerta.query.get_or_404(id)
    return render_template('alertas/detalhes.html', alerta=alerta)


@alertas_bp.route('/<int:id>/resolver', methods=['POST'])
@login_required
def resolver(id):
    AlertaService.resolver_alerta(id)
    flash('Alerta marcado como resolvido.', 'success')
    return redirect(url_for('alertas.listar'))


@alertas_bp.route('/<int:id>/ignorar', methods=['POST'])
@login_required
def ignorar(id):
    AlertaService.ignorar_alerta(id)
    flash('Alerta ignorado.', 'info')
    return redirect(url_for('alertas.listar'))
