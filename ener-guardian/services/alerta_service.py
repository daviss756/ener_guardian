"""
Serviço de Alertas — ENER-GUARDIAN
Verifica limites e gera alertas automáticos.
"""
from datetime import datetime
from models import db, Alerta, Consumo, Setor, Equipamento


class AlertaService:
    """Verificação de limites e geração automática de alertas."""

    @staticmethod
    def verificar_consumo_equipamento(equipamento, consumo_kwh):
        """Verifica se o consumo de um equipamento disparou algum alerta."""
        alertas_gerados = []
        setor = equipamento.setor

        # Regra 1: Consumo do equipamento acima de 75% da capacidade nominal por dia
        capacidade_diaria = (equipamento.potencia_watts / 1000) * 24
        if consumo_kwh > capacidade_diaria * 0.75:
            alerta = Alerta(
                equipamento_id=equipamento.id,
                setor_id=setor.id,
                tipo='consumo_excessivo',
                nivel='critico',
                mensagem=f'Equipamento operando {int((consumo_kwh / capacidade_diaria) * 100)}% acima do limite estabelecido.',
                consumo_detectado=consumo_kwh,
                limite_configurado=capacidade_diaria * 0.75
            )
            db.session.add(alerta)
            alertas_gerados.append(alerta)

        # Regra 2: Consumo acumulado do setor acima do limite
        from sqlalchemy import func
        consumo_setor_hoje = db.session.query(
            func.sum(Consumo.consumo_kwh)
        ).filter(
            Consumo.setor_id == setor.id,
            Consumo.data_referencia == datetime.today().date()
        ).scalar() or 0

        if consumo_setor_hoje > setor.limite_consumo_kwh:
            existe = Alerta.query.filter_by(
                setor_id=setor.id,
                tipo='limite_setor_ultrapassado',
                status='ativo'
            ).first()
            if not existe:
                alerta = Alerta(
                    setor_id=setor.id,
                    tipo='limite_setor_ultrapassado',
                    nivel='alto',
                    mensagem=f'Setor {setor.nome} ultrapassou o limite diário de {setor.limite_consumo_kwh} kWh.',
                    consumo_detectado=consumo_setor_hoje,
                    limite_configurado=setor.limite_consumo_kwh
                )
                db.session.add(alerta)
                alertas_gerados.append(alerta)

        if alertas_gerados:
            db.session.commit()

        return alertas_gerados

    @staticmethod
    def resolver_alerta(alerta_id):
        """Marca um alerta como resolvido."""
        alerta = Alerta.query.get(alerta_id)
        if alerta:
            alerta.status = 'resolvido'
            alerta.resolvido_em = datetime.utcnow()
            db.session.commit()
        return alerta

    @staticmethod
    def ignorar_alerta(alerta_id):
        """Marca um alerta como ignorado."""
        alerta = Alerta.query.get(alerta_id)
        if alerta:
            alerta.status = 'ignorado'
            alerta.resolvido_em = datetime.utcnow()
            db.session.commit()
        return alerta
