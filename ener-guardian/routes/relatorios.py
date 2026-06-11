"""Rotas de Relatórios."""
from flask import Blueprint, render_template, request, send_file, make_response
import pandas as pd
from io import BytesIO
from services.rbac import requires_role
from flask_login import login_required
from models import db, Consumo, Setor, Equipamento, Apontamento, Alerta
from sqlalchemy import func
from datetime import datetime, date, timezone, timedelta

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')


@relatorios_bp.route('/')
@login_required
def index():
    # New filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    equipamento_id = request.args.get('equipamento', '')
    turno = request.args.get('turno', '')
    alerta_status = request.args.get('alerta_status', '')
    # Ensure setor_id is captured once
    setor_id = request.args.get('setor', '')
    consumo_min = request.args.get('consumo_min')
    consumo_max = request.args.get('consumo_max')

    # Determine date range
    periodo = request.args.get('periodo', '7')
    if start_date_str and end_date_str:
        try:
            data_inicio = datetime.strptime(start_date_str, '%d/%m/%Y').date()
            data_fim = datetime.strptime(end_date_str, '%d/%m/%Y').date()
        except ValueError:
            data_inicio = date.today() - timedelta(days=7)
            data_fim = date.today()
    else:
        # Default period handling
        dias = int(periodo)
        data_inicio = date.today() - timedelta(days=dias)
        data_fim = date.today()

    # Build base filtered query for Consumo
    consumo_query = db.session.query(Consumo).filter(Consumo.data_referencia >= data_inicio, Consumo.data_referencia <= data_fim)
    if setor_id:
        consumo_query = consumo_query.filter(Consumo.setor_id == setor_id)
    if equipamento_id:
        consumo_query = consumo_query.filter(Consumo.equipamento_id == equipamento_id)
    if turno:
        consumo_query = consumo_query.join(Apontamento, Consumo.apontamento_id == Apontamento.id).filter(Apontamento.turno == turno)
    # Alerta filter omitted due to model relationship constraints
    if consumo_min:
        try:
            consumo_min_val = float(consumo_min)
            consumo_query = consumo_query.filter(Consumo.consumo_kwh >= consumo_min_val)
        except ValueError:
            pass
    if consumo_max:
        try:
            consumo_max_val = float(consumo_max)
            consumo_query = consumo_query.filter(Consumo.consumo_kwh <= consumo_max_val)
        except ValueError:
            pass

    # Consumo por setor no período (filtered)
    query_setor = consumo_query.with_entities(
        Setor.nome.label('nome'),
        func.coalesce(func.sum(Consumo.consumo_kwh), 0).label('total_kwh'),
        func.coalesce(func.sum(Consumo.custo_estimado), 0).label('total_custo'),
        func.count(Consumo.id).label('total_registros')
    ).join(Setor, Consumo.setor_id == Setor.id).group_by(Setor.nome).all()


    # Consumo diário no período (filtered)
    consumo_diario = []
    delta_days = (data_fim - data_inicio).days
    for i in range(delta_days, -1, -1):
        d = data_fim - timedelta(days=i)
        total = consumo_query.filter(Consumo.data_referencia == d).with_entities(
            func.coalesce(func.sum(Consumo.consumo_kwh), 0)
        ).scalar()
        consumo_diario.append({'data': d.strftime('%d/%m'), 'valor': round(total or 0, 1)})



    # Totais gerais
    total_kwh = sum(s.total_kwh for s in query_setor)
    total_custo = sum(s.total_custo for s in query_setor)

    # Top 10 equipamentos que mais consomem (filtered)
    top_equip = db.session.query(
        Equipamento.nome,
        Setor.nome.label('setor_nome'),
        func.sum(Consumo.consumo_kwh).label('total_kwh'),
        func.sum(Consumo.custo_estimado).label('total_custo')
    ).join(Consumo, Consumo.equipamento_id == Equipamento.id).join(
        Setor, Equipamento.setor_id == Setor.id
    ).filter(
        Consumo.data_referencia >= data_inicio,
        Consumo.data_referencia <= data_fim
    )
    if setor_id:
        top_equip = top_equip.filter(Consumo.setor_id == setor_id)
    if equipamento_id:
        top_equip = top_equip.filter(Consumo.equipamento_id == equipamento_id)
    if turno:
        top_equip = top_equip.join(Apontamento, Consumo.apontamento_id == Apontamento.id).filter(Apontamento.turno == turno)
    if alerta_status:
        top_equip = top_equip.join(Alerta, Alerta.id == Consumo.id).filter(Alerta.status == alerta_status)
    if consumo_min:
        try:
            top_equip = top_equip.filter(Consumo.consumo_kwh >= float(consumo_min))
        except ValueError:
            pass
    if consumo_max:
        try:
            top_equip = top_equip.filter(Consumo.consumo_kwh <= float(consumo_max))
        except ValueError:
            pass
    top_equip = top_equip.group_by(Equipamento.id, Equipamento.nome, Setor.nome).order_by(
        func.sum(Consumo.consumo_kwh).desc()
    ).limit(10).all()



    setores = Setor.query.order_by(Setor.nome).all()

    # ODS metrics
    co2_evitado = total_kwh * 0.0817  # kg CO2 por kWh (fator Brasil)

    # Additional context lists
    turnos = list(Apontamento.TURNOS.items())
    alerta_statuses = list(Alerta.NIVEIS.items())
    equipamentos = Equipamento.query.order_by(Equipamento.nome).all()

    return render_template('relatorios/index.html',
        consumo_por_setor=query_setor,
        consumo_diario=consumo_diario,
        total_kwh=round(total_kwh, 1),
        total_custo=round(total_custo, 2),
        top_equipamentos=top_equip,
        setores=setores,
        equipamentos=equipamentos,
        turnos=turnos,
        alerta_statuses=alerta_statuses,
        periodo=periodo,
        setor_id=setor_id,
        equipamento_id=equipamento_id,
        turno=turno,
        alerta_status=alerta_status,
        consumo_min=consumo_min,
        consumo_max=consumo_max,
        start_date=data_inicio.strftime('%d/%m/%Y'),
        end_date=data_fim.strftime('%d/%m/%Y'),
        co2_evitado=round(co2_evitado, 2),
        data_inicio=data_inicio.strftime('%d/%m/%Y'),
        data_fim=data_fim.strftime('%d/%m/%Y'))

@relatorios_bp.route('/export')
@login_required
@requires_role('admin')
def export():
    fmt = request.args.get('format', 'csv').lower()
    # Filter parameters (same as index)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    equipamento_id = request.args.get('equipamento', '')
    turno = request.args.get('turno', '')
    # Alerta filter omitted
    consumo_min = request.args.get('consumo_min')
    consumo_max = request.args.get('consumo_max')
    periodo = request.args.get('periodo', '7')
    setor_id = request.args.get('setor', '')

    if start_date_str and end_date_str:
        try:
            data_inicio = datetime.strptime(start_date_str, '%d/%m/%Y').date()
            data_fim = datetime.strptime(end_date_str, '%d/%m/%Y').date()
        except ValueError:
            data_inicio = date.today() - timedelta(days=7)
            data_fim = date.today()
    else:
        dias = int(periodo)
        data_inicio = date.today() - timedelta(days=dias)
        data_fim = date.today()

    # Base filtered query for Consumo (used for export)
    consumo_query = db.session.query(Consumo).filter(Consumo.data_referencia >= data_inicio, Consumo.data_referencia <= data_fim)
    if setor_id:
        consumo_query = consumo_query.filter(Consumo.setor_id == setor_id)
    if equipamento_id:
        consumo_query = consumo_query.filter(Consumo.equipamento_id == equipamento_id)
    if turno:
        consumo_query = consumo_query.join(Apontamento).filter(Apontamento.turno == turno)
    # Alerta filter omitted
    if consumo_min:
        try:
            consumo_query = consumo_query.filter(Consumo.consumo_kwh >= float(consumo_min))
        except ValueError:
            pass
    if consumo_max:
        try:
            consumo_query = consumo_query.filter(Consumo.consumo_kwh <= float(consumo_max))
        except ValueError:
            pass

    # Detailed query for export
    detalhes_query = db.session.query(
        Consumo.data_referencia.label('Data'),
        Equipamento.nome.label('Equipamento'),
        Setor.nome.label('Setor'),
        func.coalesce(Apontamento.turno, '-').label('Turno'),
        Consumo.consumo_kwh.label('Consumo_kWh'),
        Consumo.custo_estimado.label('Custo')
    ).join(Equipamento, Consumo.equipamento_id == Equipamento.id)\
     .join(Setor, Consumo.setor_id == Setor.id)\
     .outerjoin(Apontamento, Consumo.id == Apontamento.id)\
     .filter(
        Consumo.data_referencia >= data_inicio,
        Consumo.data_referencia <= data_fim
    )
    if setor_id:
        detalhes_query = detalhes_query.filter(Consumo.setor_id == setor_id)
    if equipamento_id:
        detalhes_query = detalhes_query.filter(Consumo.equipamento_id == equipamento_id)
    if turno:
        detalhes_query = detalhes_query.filter(Apontamento.turno == turno)
    if consumo_min:
        try:
            detalhes_query = detalhes_query.filter(Consumo.consumo_kwh >= float(consumo_min))
        except ValueError:
            pass
    if consumo_max:
        try:
            detalhes_query = detalhes_query.filter(Consumo.consumo_kwh <= float(consumo_max))
        except ValueError:
            pass

    detalhes = detalhes_query.order_by(Consumo.data_referencia.desc()).all()

    # Build DataFrame
    df = pd.DataFrame([{
        'Data': r.Data.strftime('%d/%m/%Y'),
        'Equipamento': r.Equipamento,
        'Setor': r.Setor,
        'Turno': str(r.Turno).title() if r.Turno != '-' else '-',
        'Consumo_kWh': round(r.Consumo_kWh, 2),
        'Custo_R$': round(r.Custo, 2)
    } for r in detalhes])

    if fmt == 'csv':
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='relatorio.csv')
    elif fmt == 'excel':
        try:
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='relatorio.xlsx')
        except ImportError:
            flash('Dependência "openpyxl" não encontrada. Instale o pacote para gerar Excel.', 'danger')
            return redirect(url_for('relatorios.index'))
    elif fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            flash('Dependência "reportlab" não encontrada. Instale o pacote para gerar PDF.', 'danger')
            return redirect(url_for('relatorios.index'))
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CorporateTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#006c49')
        )
        subtitle_style = ParagraphStyle(
            'CorporateSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=15,
            textColor=colors.HexColor('#3c4a42')
        )
        
        elements.append(Paragraph('Relatório de Consumo por Setor', title_style))
        elements.append(Paragraph(f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}', subtitle_style))
        
        data = [['Data', 'Equipamento', 'Setor', 'Turno', 'Consumo (kWh)', 'Custo (R$)']]
        for idx, row in df.iterrows():
            data.append([
                row['Data'], 
                row['Equipamento'], 
                row['Setor'], 
                row['Turno'],
                f"{row['Consumo_kWh']:.2f}", 
                f"R$ {row['Custo_R$']:.2f}"
            ])
            
        table = Table(data, colWidths=[65, 120, 100, 65, 85, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006c49')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9ff')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0b1c30')),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbdbf5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8f9ff')])
        ]))
        
        elements.append(table)
        doc.build(elements)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='relatorio.pdf')
    else:
        return make_response('Formato não suportado', 400)

