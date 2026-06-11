"""
Testes de Integração para o Serviço de Alertas — ENER-GUARDIAN (utilizando unittest do Python)
"""
import unittest
from app import create_app
from models import db, Setor, Equipamento, Alerta, Consumo
from services.alerta_service import AlertaService

class TestAlertaService(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
        })
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_verificar_consumo_excedente_equipamento(self):
        setor = Setor(nome="Estamparia Teste", limite_consumo_kwh=100.0)
        db.session.add(setor)
        db.session.commit()
        
        # Equipamento de 10kW has daily capacity of 240 kWh. 75% is 180 kWh.
        equip = Equipamento(
            nome="Prensa Teste",
            tipo="Prensa Hidráulica",
            potencia_watts=10000,
            setor_id=setor.id
        )
        db.session.add(equip)
        db.session.commit()
        
        # 200 kWh exceeds 180 kWh
        alertas = AlertaService.verificar_consumo_equipamento(equip, 200.0)
        
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0].tipo, 'consumo_excessivo')
        self.assertEqual(alertas[0].nivel, 'critico')
        self.assertEqual(alertas[0].equipamento_id, equip.id)

    def test_verificar_consumo_dentro_do_limite(self):
        setor = Setor(nome="Usinagem Teste", limite_consumo_kwh=100.0)
        db.session.add(setor)
        db.session.commit()
        
        equip = Equipamento(
            nome="Torno Teste",
            tipo="Torno CNC",
            potencia_watts=10000,
            setor_id=setor.id
        )
        db.session.add(equip)
        db.session.commit()
        
        # 100 kWh is below 180 kWh (75% capacity)
        alertas = AlertaService.verificar_consumo_equipamento(equip, 100.0)
        self.assertEqual(len(alertas), 0)

if __name__ == "__main__":
    unittest.main()
