"""Rotas de Setores — CRUD."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Setor

setores_bp = Blueprint('setores', __name__, url_prefix='/setores')


@setores_bp.route('/')
@login_required
def listar():
    setores = Setor.query.order_by(Setor.nome).all()
    return render_template('setores/listar.html', setores=setores)


@setores_bp.route('/<int:id>')
@login_required
def detalhes(id):
    setor = Setor.query.get_or_404(id)
    return render_template('setores/detalhes.html', setor=setor)



@setores_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def cadastrar():
    if request.method == 'POST':
        setor = Setor(
            nome=request.form['nome'],
            descricao=request.form.get('descricao', ''),
            limite_consumo_kwh=float(request.form.get('limite_consumo_kwh', 500))
        )
        db.session.add(setor)
        db.session.commit()
        flash('Setor cadastrado com sucesso!', 'success')
        return redirect(url_for('setores.listar'))
    return render_template('setores/cadastrar.html')


@setores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    setor = Setor.query.get_or_404(id)
    if request.method == 'POST':
        setor.nome = request.form['nome']
        setor.descricao = request.form.get('descricao', '')
        setor.limite_consumo_kwh = float(request.form.get('limite_consumo_kwh', 500))
        db.session.commit()
        flash('Setor atualizado com sucesso!', 'success')
        return redirect(url_for('setores.listar'))
    return render_template('setores/cadastrar.html', setor=setor, editando=True)
