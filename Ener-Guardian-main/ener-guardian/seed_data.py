"""
Script de Carga de Dados (Seed Data) — ENER-GUARDIAN
Popula a base de dados com setores, equipamentos, usuários e histórico de consumo de 30 dias.
"""
import os
import random
from datetime import datetime, date, timedelta
from app import create_app
from models import db, Usuario, Setor, Equipamento, Apontamento, Consumo, Alerta, Configuracao
from services.calculo_energia import MotorCalculoEnergetico
from services.alerta_service import AlertaService

def seed_database():
    print("Iniciando a carga de dados de demonstração...")

    # 1. Configurações globais
    if not Configuracao.query.filter_by(chave='TARIFA_ENERGIA').first():
        tarifa = Configuracao(chave='TARIFA_ENERGIA', valor='0.85', descricao='Tarifa de energia elétrica industrial (R$/kWh)')
        db.session.add(tarifa)
        print("Configuração TARIFA_ENERGIA adicionada.")

    # 2. Usuários / Stakeholders do projeto
    users_data = [
        {"nome": "Tim Maia", "email": "admin@energuardian.com", "senha": "admin123", "papel": "admin"},
        {"nome": "Roberto Carlos", "email": "gestor@energuardian.com", "senha": "gestor123", "papel": "gestor"},
        {"nome": "Luiza Sonza", "email": "lider@energuardian.com", "senha": "lider123", "papel": "lider_producao"},
        {"nome": "Bea Duarte", "email": "engenheiro@energuardian.com", "senha": "engenheiro123", "papel": "engenheiro"},
        {"nome": "Justin Bieber", "email": "financeiro@energuardian.com", "senha": "financeiro123", "papel": "financeiro"}
    ]

    usuarios = {}
    for u_info in users_data:
        u = Usuario.query.filter_by(email=u_info["email"]).first()
        if not u:
            u = Usuario(nome=u_info["nome"], email=u_info["email"], papel=u_info["papel"])
            u.set_senha(u_info["senha"])
            db.session.add(u)
            print(f"Usuário criado: {u_info['nome']} ({u_info['papel']})")
        usuarios[u_info["papel"]] = u

    db.session.commit()

    # 3. Setores
    setores_data = [
        {"nome": "Estamparia", "descricao": "Setor de corte e conformação de chapas metálicas", "limite_consumo_kwh": 250.0},
        {"nome": "Usinagem", "descricao": "Centro de usinagem e fresadoras CNC", "limite_consumo_kwh": 350.0},
        {"nome": "Pintura", "descricao": "Cabine de pintura eletrostática e estufas", "limite_consumo_kwh": 180.0},
        {"nome": "Montagem", "descricao": "Linha de montagem final dos produtos", "limite_consumo_kwh": 80.0}
    ]

    setores = {}
    for s_info in setores_data:
        s = Setor.query.filter_by(nome=s_info["nome"]).first()
        if not s:
            s = Setor(nome=s_info["nome"], descricao=s_info["descricao"], limite_consumo_kwh=s_info["limite_consumo_kwh"])
            db.session.add(s)
            print(f"Setor criado: {s_info['nome']}")
        setores[s_info["nome"]] = s

    db.session.commit()

    # 4. Equipamentos
    equipamentos_data = [
        # Estamparia
        {"nome": "Prensa Hidráulica PH-500", "tipo": "Prensa Hidráulica", "potencia_watts": 22000, "voltagem": 380, "corrente_amperes": 42.0, "fator_potencia": 0.85, "fator_carga": 0.8, "regime_carga": "pesado", "setor": "Estamparia"},
        {"nome": "Guilhotina Rotativa GR-10", "tipo": "Furadeira Industrial", "potencia_watts": 7500, "voltagem": 220, "corrente_amperes": 24.0, "fator_potencia": 0.85, "fator_carga": 0.6, "regime_carga": "medio", "setor": "Estamparia"},
        
        # Usinagem
        {"nome": "Centro de Usinagem CNC-01", "tipo": "Torno CNC", "potencia_watts": 15000, "voltagem": 380, "corrente_amperes": 28.5, "fator_potencia": 0.85, "fator_carga": 0.7, "regime_carga": "medio", "setor": "Usinagem"},
        {"nome": "Torno Mecânico TM-03", "tipo": "Torno CNC", "potencia_watts": 5500, "voltagem": 220, "corrente_amperes": 18.0, "fator_potencia": 0.82, "fator_carga": 0.5, "regime_carga": "medio", "setor": "Usinagem"},
        {"nome": "Fresadora Vertical FV-02", "tipo": "Caldeira", "potencia_watts": 9000, "voltagem": 380, "corrente_amperes": 17.0, "fator_potencia": 0.85, "fator_carga": 0.6, "regime_carga": "medio", "setor": "Usinagem"},
        {"nome": "Compressor de Ar Radial CP-15", "tipo": "Compressor", "potencia_watts": 18500, "voltagem": 380, "corrente_amperes": 35.0, "fator_potencia": 0.88, "fator_carga": 0.7, "regime_carga": "medio", "setor": "Usinagem"},
        
        # Pintura
        {"nome": "Estufa de Cura Eletrostática ES-200", "tipo": "Caldeira", "potencia_watts": 30000, "voltagem": 380, "corrente_amperes": 50.0, "fator_potencia": 0.98, "fator_carga": 0.9, "regime_carga": "pleno", "setor": "Pintura"},
        {"nome": "Cabine de Pintura C-02", "tipo": "Ventilador", "potencia_watts": 4000, "voltagem": 220, "corrente_amperes": 13.0, "fator_potencia": 0.85, "fator_carga": 0.7, "regime_carga": "medio", "setor": "Pintura"},
        
        # Montagem
        {"nome": "Linha de Montagem Flexível LM-1", "tipo": "Soldadora", "potencia_watts": 3500, "voltagem": 220, "corrente_amperes": 11.5, "fator_potencia": 0.90, "fator_carga": 0.4, "regime_carga": "leve", "setor": "Montagem"},
        {"nome": "Aparafusadeiras Industriais Sist.", "tipo": "Outro", "potencia_watts": 1500, "voltagem": 110, "corrente_amperes": 15.0, "fator_potencia": 0.92, "fator_carga": 0.3, "regime_carga": "leve", "setor": "Montagem"},
        
        # Comum/Geral
        {"nome": "Iluminação Industrial Galpão Principal", "tipo": "Iluminação", "potencia_watts": 8000, "voltagem": None, "corrente_amperes": None, "fator_potencia": 0.95, "fator_carga": 1.0, "regime_carga": "pleno", "setor": "Montagem"}
    ]

    equipamentos = []
    for e_info in equipamentos_data:
        e = Equipamento.query.filter_by(nome=e_info["nome"]).first()
        if not e:
            e = Equipamento(
                nome=e_info["nome"],
                tipo=e_info["tipo"],
                potencia_watts=e_info["potencia_watts"],
                voltagem=e_info["voltagem"],
                corrente_amperes=e_info["corrente_amperes"],
                fator_potencia=e_info["fator_potencia"],
                fator_carga=e_info["fator_carga"],
                regime_carga=e_info["regime_carga"],
                setor_id=setores[e_info["setor"]].id,
                ativo=True
            )
            db.session.add(e)
            print(f"Equipamento criado: {e_info['nome']}")
        equipamentos.append(e)

    db.session.commit()

    # 5. Histórico de Apontamentos & Consumo (últimos 30 dias)
    has_history = Apontamento.query.first() is not None
    if not has_history:
        print("Gerando histórico de consumo de 30 dias...")
        hoje = date.today()
        lider_user = usuarios["lider_producao"]

        # Gerar de 30 dias atrás até ontem
        for d_offset in range(30, -1, -1):
            data_reg = hoje - timedelta(days=d_offset)
            print(f"-> Gerando registros para o dia: {data_reg.strftime('%d/%m/%Y')}")

            # Para cada setor, controlamos o consumo total diário para simular picos de consumo e alertas
            for setor_nome, setor in setores.items():
                limite = setor.limite_consumo_kwh
                # Se for final de semana (sábado/domingo), a produção é muito menor (20% da normal)
                is_fds = data_reg.weekday() in (5, 6)
                
                # Filtrar equipamentos do setor
                equips_setor = [e for e in equipamentos if e.setor_id == setor.id]
                
                for equip in equips_setor:
                    # Probabilidade de uso
                    prob_uso = 0.15 if is_fds else 0.85
                    if equip.nome.startswith("Iluminação"):
                        prob_uso = 1.0 # Luzes ligadas sempre
                    
                    if random.random() < prob_uso:
                        # Turnos
                        turnos_operados = ['manha', 'tarde']
                        if not is_fds and random.random() < 0.3 and not equip.nome.startswith("Iluminação"):
                            turnos_operados.append('noite')
                        elif equip.nome.startswith("Iluminação"):
                            turnos_operados = ['manha', 'tarde', 'noite']
                        
                        for turno in turnos_operados:
                            # Horas de uso
                            if equip.nome.startswith("Iluminação"):
                                horas = 8.0
                            else:
                                horas = round(random.uniform(5.0, 8.0), 1)

                            # Adiciona alguma anomalia/desperdício esporádico (ex: máquina esquecida ligada na Estamparia)
                            fator_carga_uso = equip.fator_carga
                            if not is_fds and setor_nome == "Estamparia" and d_offset in (2, 8, 15) and equip.tipo == "Prensa Hidráulica":
                                # Fator de carga artificialmente alto (sobrecarga/desperdício)
                                fator_carga_uso = 0.95
                                horas = 12.0 # turno estendido
                                print(f"   [ANOMALIA] prensa operando em sobrecarga na data {data_reg}")

                            # Processa
                            # Para simular o método do motor
                            # Se voltagem/corrente
                            if equip.corrente_amperes and equip.voltagem:
                                fp = equip.fator_potencia or 0.85
                                consumo_val = MotorCalculoEnergetico.calcular_por_voltagem(
                                    voltagem=equip.voltagem,
                                    corrente=equip.corrente_amperes,
                                    fator_potencia=fp,
                                    horas=horas,
                                    fator_carga=fator_carga_uso
                                )
                                metodo = 'voltagem'
                                potencia_real = equip.voltagem * equip.corrente_amperes * fp
                            else:
                                consumo_val = MotorCalculoEnergetico.calcular_por_potencia(
                                    potencia_watts=equip.potencia_watts,
                                    horas=horas,
                                    fator_carga=fator_carga_uso
                                )
                                metodo = 'potencia_nominal'
                                potencia_real = equip.potencia_watts

                            custo_val = MotorCalculoEnergetico.calcular_custo(consumo_val, 0.85)

                            # Salva apontamento
                            apont = Apontamento(
                                equipamento_id=equip.id,
                                usuario_id=lider_user.id,
                                data_operacao=data_reg,
                                turno=turno,
                                horas_uso=horas,
                                observacao="Carga automática do seed" if d_offset > 0 else "Operação normal de turno"
                            )
                            db.session.add(apont)
                            db.session.flush()

                            # Salva consumo
                            cons = Consumo(
                                apontamento_id=apont.id,
                                equipamento_id=equip.id,
                                setor_id=setor.id,
                                consumo_kwh=round(consumo_val, 4),
                                custo_estimado=round(custo_val, 2),
                                potencia_utilizada=round(potencia_real, 2),
                                metodo_calculo=metodo,
                                data_referencia=data_reg,
                                calculado_em=datetime.combine(data_reg, datetime.min.time())
                            )
                            db.session.add(cons)

            db.session.commit()

        # 6. Gerar alguns Alertas históricos e ativos
        # Alerta 1: Ativo por limite ultrapassado no Setor Estamparia hoje/ontem
        estamparia_setor = setores["Estamparia"]
        alerta_ativo = Alerta(
            setor_id=estamparia_setor.id,
            tipo='limite_setor_ultrapassado',
            nivel='alto',
            mensagem=f'Setor Estamparia ultrapassou o limite diário de {estamparia_setor.limite_consumo_kwh} kWh (consumo registrado: 284.2 kWh).',
            status='ativo',
            consumo_detectado=284.2,
            limite_configurado=estamparia_setor.limite_consumo_kwh,
            criado_em=datetime.now()
        )
        db.session.add(alerta_ativo)

        # Alerta 2: Ativo por consumo excessivo no CNC-01 hoje
        cnc_equip = Equipamento.query.filter_by(nome="Centro de Usinagem CNC-01").first()
        alerta_ativo_cnc = Alerta(
            equipamento_id=cnc_equip.id,
            setor_id=cnc_equip.setor_id,
            tipo='consumo_excessivo',
            nivel='critico',
            mensagem=f'Equipamento {cnc_equip.nome} registrou consumo 83% acima do limite operacional (consumo: 120.4 kWh).',
            status='ativo',
            consumo_detectado=120.4,
            limite_configurado=270.0,
            criado_em=datetime.now()
        )
        db.session.add(alerta_ativo_cnc)

        # Alerta 3: Resolvido
        pintura_setor = setores["Pintura"]
        estufa_equip = Equipamento.query.filter_by(nome="Estufa de Cura Eletrostática ES-200").first()
        alerta_resolvido = Alerta(
            equipamento_id=estufa_equip.id,
            setor_id=pintura_setor.id,
            tipo='consumo_excessivo',
            nivel='alto',
            mensagem=f'Equipamento {estufa_equip.nome} operando acima da carga nominal sugerida.',
            status='resolvido',
            consumo_detectado=340.5,
            limite_configurado=300.0,
            criado_em=datetime.now() - timedelta(days=5),
            resolvido_em=datetime.now() - timedelta(days=4)
        )
        db.session.add(alerta_resolvido)

        db.session.commit()
        print("Histórico e alertas de demonstração criados com sucesso!")
    else:
        print("A base de dados já possui registros de demonstração.")

    print("Carga de dados de demonstração concluída com sucesso!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_database()
