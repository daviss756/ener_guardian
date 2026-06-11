"""
Testes Unitários para o Motor de Cálculo Energético — ENER-GUARDIAN (utilizando unittest do Python)
"""
import unittest
from services.calculo_energia import MotorCalculoEnergetico

class DummyEquipamento:
    def __init__(self, potencia_watts, voltagem=None, corrente_amperes=None, fator_potencia=0.85, fator_carga=0.7, regime_carga='medio'):
        self.potencia_watts = potencia_watts
        self.voltagem = voltagem
        self.corrente_amperes = corrente_amperes
        self.fator_potencia = fator_potencia
        self.fator_carga = fator_carga
        self.regime_carga = regime_carga

class TestCalculoEnergia(unittest.TestCase):
    def test_calcular_por_potencia(self):
        # Prensa Hidráulica de 5000W por 6 horas com fator de carga 0.7
        # Consumo = (5000 / 1000) * 6 * 0.7 = 21.0 kWh
        consumo = MotorCalculoEnergetico.calcular_por_potencia(
            potencia_watts=5000,
            horas=6,
            fator_carga=0.7
        )
        self.assertEqual(consumo, 21.0)

    def test_calcular_por_voltagem(self):
        # Voltagem: 380V, Corrente: 13.16A, Fator Potência: 1.0, Horas: 6, Fator Carga: 0.7
        # Potência real = 380 * 13.16 * 1.0 = 5000.8 W
        # Consumo = (5000.8 / 1000) * 6 * 0.7 = 21.00336 kWh
        consumo = MotorCalculoEnergetico.calcular_por_voltagem(
            voltagem=380,
            corrente=13.16,
            fator_potencia=1.0,
            horas=6,
            fator_carga=0.7
        )
        self.assertEqual(round(consumo, 4), 21.0034)

    def test_calcular_custo(self):
        # Consumo 21 kWh com tarifa de R$ 0.85/kWh
        # Custo = 21 * 0.85 = R$ 17.85
        custo = MotorCalculoEnergetico.calcular_custo(21.0, 0.85)
        self.assertAlmostEqual(custo, 17.85, places=2)

    def test_processar_apontamento_potencia(self):
        # Equipamento sem voltagem/corrente especificada
        equip = DummyEquipamento(potencia_watts=5000, fator_carga=0.7)
        resultado = MotorCalculoEnergetico.processar_apontamento(equip, horas_uso=6, tarifa=0.85)
        
        self.assertEqual(resultado['consumo_kwh'], 21.0)
        self.assertEqual(resultado['custo_estimado'], 17.85)
        self.assertEqual(resultado['potencia_utilizada'], 5000)
        self.assertEqual(resultado['metodo_calculo'], 'potencia_nominal')

    def test_processar_apontamento_voltagem(self):
        # Equipamento com voltagem/corrente especificada
        equip = DummyEquipamento(potencia_watts=5000, voltagem=380, corrente_amperes=13.16, fator_potencia=1.0, fator_carga=0.7)
        resultado = MotorCalculoEnergetico.processar_apontamento(equip, horas_uso=6, tarifa=0.85)
        
        self.assertEqual(round(resultado['consumo_kwh'], 1), 21.0)
        self.assertEqual(round(resultado['custo_estimado'], 2), 17.85)
        self.assertEqual(resultado['metodo_calculo'], 'voltagem')

if __name__ == "__main__":
    unittest.main()
