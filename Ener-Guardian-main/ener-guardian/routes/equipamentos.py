"""Rotas de Equipamentos — CRUD completo."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from services.rbac import requires_role
from models import db, Equipamento, Setor

equipamentos_bp = Blueprint('equipamentos', __name__, url_prefix='/equipamentos')


@equipamentos_bp.route('/')
@login_required
def listar():
    filtro_setor = request.args.get('setor', '')
    filtro_status = request.args.get('status', '')
    query = Equipamento.query.join(Setor)

    if filtro_setor:
        query = query.filter(Setor.id == filtro_setor)
    if filtro_status == 'ativo':
        query = query.filter(Equipamento.ativo == True)
    elif filtro_status == 'inativo':
        query = query.filter(Equipamento.ativo == False)

    equipamentos = query.order_by(Equipamento.nome).all()
    setores = Setor.query.order_by(Setor.nome).all()
    return render_template('equipamentos/listar.html',
        equipamentos=equipamentos, setores=setores,
        filtro_setor=filtro_setor, filtro_status=filtro_status)


@equipamentos_bp.route('/<int:id>')
@login_required
def detalhes(id):
    equipamento = Equipamento.query.get_or_404(id)
    return render_template('equipamentos/detalhes.html', equipamento=equipamento)


@equipamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def cadastrar():
    setores = Setor.query.order_by(Setor.nome).all()
    if request.method == 'POST':
        equip = Equipamento(
            nome=request.form['nome'],
            tipo=request.form['tipo'],
            potencia_watts=float(request.form['potencia_watts']),
            voltagem=float(request.form.get('voltagem') or 0) or None,
            corrente_amperes=float(request.form.get('corrente_amperes') or 0) or None,
            fator_potencia=float(request.form.get('fator_potencia') or 0.85),
            fator_carga=float(request.form.get('fator_carga') or 0.7),
            regime_carga=request.form.get('regime_carga', 'medio'),
            setor_id=int(request.form['setor_id']),
            ativo=True
        )
        db.session.add(equip)
        db.session.commit()
        flash('Equipamento cadastrado com sucesso!', 'success')
        return redirect(url_for('equipamentos.listar'))

    return render_template('equipamentos/cadastrar.html',
        setores=setores, tipos=Equipamento.TIPOS, regimes=Equipamento.REGIMES)


@equipamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    equip = Equipamento.query.get_or_404(id)
    setores = Setor.query.order_by(Setor.nome).all()

    if request.method == 'POST':
        equip.nome = request.form['nome']
        equip.tipo = request.form['tipo']
        equip.potencia_watts = float(request.form['potencia_watts'])
        equip.voltagem = float(request.form.get('voltagem') or 0) or None
        equip.corrente_amperes = float(request.form.get('corrente_amperes') or 0) or None
        equip.fator_potencia = float(request.form.get('fator_potencia') or 0.85)
        equip.fator_carga = float(request.form.get('fator_carga') or 0.7)
        equip.regime_carga = request.form.get('regime_carga', 'medio')
        equip.setor_id = int(request.form['setor_id'])
        equip.ativo = 'ativo' in request.form
        db.session.commit()
        flash('Equipamento atualizado com sucesso!', 'success')
        return redirect(url_for('equipamentos.listar'))

    return render_template('equipamentos/cadastrar.html',
        equip=equip, setores=setores, tipos=Equipamento.TIPOS,
        regimes=Equipamento.REGIMES, editando=True)


@equipamentos_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    equip = Equipamento.query.get_or_404(id)
    db.session.delete(equip)
    db.session.commit()
    flash('Equipamento excluído com sucesso!', 'success')
    return redirect(url_for('equipamentos.listar'))
