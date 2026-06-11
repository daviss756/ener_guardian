"""Rotas de Apontamentos Operacionais."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Apontamento, Consumo, Equipamento, Setor
from services.calculo_energia import MotorCalculoEnergetico
from services.alerta_service import AlertaService
from datetime import date

apontamentos_bp = Blueprint('apontamentos', __name__, url_prefix='/apontamentos')


@apontamentos_bp.route('/')
@login_required
def historico():
    filtro_setor = request.args.get('setor', '')
    query = Apontamento.query.join(Equipamento).join(Setor)

    if filtro_setor:
        query = query.filter(Setor.id == filtro_setor)

    apontamentos = query.order_by(Apontamento.criado_em.desc()).limit(50).all()
    setores = Setor.query.order_by(Setor.nome).all()
    return render_template('apontamentos/historico.html',
        apontamentos=apontamentos, setores=setores, filtro_setor=filtro_setor)


@apontamentos_bp.route('/<int:id>')
@login_required
def detalhes(id):
    apontamento = Apontamento.query.get_or_404(id)
    return render_template('apontamentos/detalhes.html', apontamento=apontamento)


@apontamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def registrar():
    equipamentos = Equipamento.query.filter_by(ativo=True).order_by(Equipamento.nome).all()

    if request.method == 'POST':
        # ---------- Validation ----------
        try:
            equipamento_id = int(request.form.get('equipamento_id', '').strip())
        except (ValueError, TypeError):
            flash('Equipamento inválido.', 'danger')
            return redirect(url_for('apontamentos.registrar'))
        horas_raw = request.form.get('horas_uso', '').strip()
        if not horas_raw:
            flash('Horas de uso são obrigatórias.', 'danger')
            return redirect(url_for('apontamentos.registrar'))
        try:
            horas_uso = float(horas_raw)
        except ValueError:
            flash('Horas de uso devem ser numéricas.', 'danger')
            return redirect(url_for('apontamentos.registrar'))
        turno = request.form.get('turno', '').strip()
        data_op = request.form.get('data_operacao', '').strip()
        observacao = request.form.get('observacao', '').strip()

        # ---------- Business Logic ----------
        equipamento = Equipamento.query.get_or_404(equipamento_id)
        tarifa = current_app.config.get('TARIFA_ENERGIA', 0.85)

        # Calcular consumo usando o motor
        resultado = MotorCalculoEnergetico.processar_apontamento(equipamento, horas_uso, tarifa)

        # Criar apontamento
        apontamento = Apontamento(
            equipamento_id=equipamento_id,
            usuario_id=current_user.id,
            data_operacao=date.fromisoformat(data_op) if data_op else date.today(),
            turno=turno,
            horas_uso=horas_uso,
            observacao=observacao
        )
        db.session.add(apontamento)
        db.session.flush()

        # Criar registro de consumo
        consumo = Consumo(
            apontamento=apontamento,
            equipamento_id=equipamento.id,
            setor_id=equipamento.setor_id,
            consumo_kwh=resultado['consumo_kwh'],
            custo_estimado=resultado['custo_estimado'],
            potencia_utilizada=resultado['potencia_utilizada'],
            metodo_calculo=resultado['metodo_calculo'],
            data_referencia=apontamento.data_operacao
        )
        db.session.add(consumo)
        db.session.commit()

        # Verificar alertas
        AlertaService.verificar_consumo_equipamento(equipamento, resultado['consumo_kwh'])

        flash(
            f'Apontamento registrado! Consumo: {resultado["consumo_kwh"]} kWh | '
            f'Custo: R$ {resultado["custo_estimado"]} | '
            f'Método: {resultado["metodo_calculo"]}',
            'success'
        )
        return redirect(url_for('apontamentos.historico'))

    return render_template('apontamentos/registrar.html',
        equipamentos=equipamentos, turnos=Apontamento.TURNOS, hoje=date.today().isoformat())
