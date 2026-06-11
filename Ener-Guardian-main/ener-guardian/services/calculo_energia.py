"""
Motor de Cálculo Energético — ENER-GUARDIAN
Baseado em Apontamento Operacional (Regimes de Carga)
Sem IoT: calcula consumo cruzando especificações técnicas × tempo de operação.
"""
from services.cache import cache


class MotorCalculoEnergetico:
    """Motor de cálculo baseado em Apontamento Operacional."""

    FATORES_CARGA = {
        'leve': 0.4,
        'medio': 0.6,
        'pesado': 0.8,
        'pleno': 0.95
    }

    FATORES_POTENCIA = {
        'motor_vazio': 0.20,
        'motor_50': 0.75,
        'motor_pleno': 0.87,
        'iluminacao': 0.95,
        'resistencia': 1.00
    }

    @staticmethod
    def calcular_por_potencia(potencia_watts, horas, fator_carga=0.7):
        """
        Fórmula Principal:
        Consumo (kWh) = (Potência em Watts / 1000) × Horas de Uso × Fator de Carga
        """
        return (potencia_watts / 1000) * horas * fator_carga

    @staticmethod
    def calcular_por_voltagem(voltagem, corrente, fator_potencia, horas, fator_carga=0.7):
        """
        Fórmula por Voltagem:
        Potência (W) = Voltagem (V) × Corrente (A) × Fator de Potência
        Consumo (kWh) = (V × I × FP / 1000) × Horas × Fator de Carga
        """
        potencia_watts = voltagem * corrente * fator_potencia
        return (potencia_watts / 1000) * horas * fator_carga

    @staticmethod
    def calcular_custo(consumo_kwh, tarifa=0.85):
        """Calcula custo em R$ baseado na tarifa energética."""
        return consumo_kwh * tarifa



    @classmethod
    def processar_apontamento(cls, equipamento, horas_uso, tarifa=0.85):
        """
        Processa um apontamento completo e retorna resultado.
        Escolhe automaticamente o método de cálculo mais preciso:
        - Se voltagem E corrente estão cadastrados → usa fórmula por voltagem
        - Caso contrário → usa potência nominal
        """
        if equipamento.corrente_amperes and equipamento.voltagem:
            fp = equipamento.fator_potencia or 0.85
            fc = equipamento.fator_carga or cls.FATORES_CARGA.get(equipamento.regime_carga, 0.7)
            consumo = cls.calcular_por_voltagem(
                voltagem=equipamento.voltagem,
                corrente=equipamento.corrente_amperes,
                fator_potencia=fp,
                horas=horas_uso,
                fator_carga=fc
            )
            metodo = 'voltagem'
            potencia_real = equipamento.voltagem * equipamento.corrente_amperes * fp
        else:
            fc = equipamento.fator_carga or cls.FATORES_CARGA.get(equipamento.regime_carga, 0.7)
            consumo = cls.calcular_por_potencia(
                potencia_watts=equipamento.potencia_watts,
                horas=horas_uso,
                fator_carga=fc
            )
            metodo = 'potencia_nominal'
            potencia_real = equipamento.potencia_watts

        custo = cls.calcular_custo(consumo, tarifa)

        return {
            'consumo_kwh': round(consumo, 4),
            'custo_estimado': round(custo, 2),
            'potencia_utilizada': round(potencia_real, 2),
            'metodo_calculo': metodo
        }
