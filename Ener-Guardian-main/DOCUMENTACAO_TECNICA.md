# ENER-GUARDIAN — Documentação Técnica & Guia de Apresentação

Bem-vindo à documentação oficial do **Ener-Guardian**, um sistema focado em gestão, apontamento e cálculo do consumo energético industrial sem depender integralmente de sensores IoT físicos. 

Neste documento, você encontrará todos os detalhes técnicos de estruturação, inicialização do projeto e também um **Guia Completo para Apresentação em Slides**.

---

## 📂 1. Estrutura do Projeto & Onde Encontrar Cada Arquivo

A arquitetura do projeto segue o padrão **MVC (Model-View-Controller)** adaptado para **Flask**, utilizando a separação por responsabilidades e serviços. O projeto está localizado na pasta `c:\Trabalho DAVI\ener-guardian\`.

*   **Raiz do Projeto:**
    *   `app.py`: Ponto de entrada (Entry point) da aplicação. Inicia o Flask, registra os Blueprints (rotas) e inicializa o Banco de Dados.
    *   `models.py`: Modelos de Banco de Dados (ORM SQLAlchemy). Define as tabelas: `Usuario`, `Setor`, `Equipamento`, `Sensor`, `Apontamento`, `Consumo` e `Alerta`.
    *   `requirements.txt`: Lista das dependências do Python.
    *   `seed_data.py`: Script para popular o banco de dados com dados iniciais e usuários padrão (ex: `admin@energuardian.com.br`).
*   **Camada de Controladores (`/routes/`):**
    *   `auth.py`: Autenticação e login.
    *   `apontamentos.py`, `equipamentos.py`, `setores.py`, `alertas.py`: Lidam com as rotas HTTP e processam dados entre as Views e a camada de Negócios.
    *   `relatorios.py`: Gera as queries complexas para os Dashboards e processa exportações de arquivos (PDF, CSV, Excel).
*   **Camada de Negócios (`/services/`):**
    *   `calculo_energia.py`: O "Cérebro" matemático do sistema (detalhes na seção de Lógica).
    *   `alerta_service.py`: Verifica se as medições ultrapassam regras predefinidas (detalhes na seção de Negócios).
    *   `rbac.py`: Regras de *Role-Based Access Control* (permissões de acesso por papel: Admin, Gestor, Operador).
*   **Camada de Visualização (`/templates/` & `/static/`):**
    *   `base.html`: Esqueleto visual padrão contendo menu lateral (Sidebar) e header responsivo.
    *   `/static/css/index.css`: Arquivo com o *Design System* corporativo e as regras de cores / identidade visual.

### Por que foi feito dessa forma?
A separação entre `routes` e `services` garante que a lógica complexa (como os cálculos de física e geração de alertas) não fique poluindo as rotas web. Isso permite que a lógica de cálculo possa ser reaproveitada (ex: por uma API ou script de background) sem depender da tela do usuário.

---

## 🛠️ 2. Como Rodar o Projeto (Setup Passo-a-Passo)

Para executar o sistema em qualquer máquina (Windows):

1.  **Pré-requisitos:** Ter o **Python 3.10+** instalado.
2.  **Abrir o terminal** na pasta do projeto (`c:\Trabalho DAVI\ener-guardian\`).
3.  **Criar um ambiente virtual (Recomendado):**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
4.  **Instalar as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Popular o Banco de Dados (Apenas na Primeira Vez):**
    ```bash
    python seed_data.py
    ```
    *Isso criará o banco de dados `instance/energuardian.db` e registrará equipamentos e relatórios históricos de teste.*
6.  **Iniciar o Servidor:**
    ```bash
    python app.py
    ```
7.  **Acesso:** Abra o navegador e acesse `http://127.0.0.1:5000/`. Você pode logar como:
    *   **Email:** `admin@energuardian.com.br` | **Senha:** `admin123`

---

## 📊 3. Guia para Apresentação em Slides (Pitch do Projeto)

Se você precisa apresentar este projeto de forma comercial ou acadêmica, estruture os seus slides focando nestes 4 pilares principais:

### Slide 1: A Solução (O que é e como funciona?)
*   **O Problema:** Fábricas e indústrias gastam muito com energia porque não sabem *onde* nem *como* seus equipamentos consomem, e sensores IoT custam muito caro para implementar em todas as máquinas.
*   **A Solução (Ener-Guardian):** Um sistema misto focado em **Apontamentos Operacionais**. Em vez de exigir que a empresa compre sensores de $1.000 para cada máquina, um operador insere o turno e o tempo de uso da máquina.
*   **Como Funciona:** O software cruza a folha de dados técnica do equipamento (Potência/Voltagem) com o tempo de operação inserido (em horas) e o regime de uso, gerando um mapa calor e indicadores financeiros e ambientais de altíssima precisão.

### Slide 2: Tecnologias Utilizadas (O Stack Técnico)
*   **Linguagem & Backend:** Desenvolvido em **Python** utilizando o Framework **Flask**.
*   **Banco de Dados:** **SQLite** através do ORM **SQLAlchemy** (permite migrar para PostgreSQL instantaneamente sem reescrever o banco).
*   **Frontend (Interface UI/UX):** **HTML5** e **CSS3** nativo (Custom CSS), projetado com tendências de *Glassmorphism* corporativo focado na usabilidade, usando SVG e *Material Symbols*.
*   **Geração de Relatórios:** Bibliotecas nativas do Python para CSV/Excel e o poderoso `ReportLab` para gerar PDFs autopaginados e corporativos no backend.

### Slide 3: O "Motor Matemático" de Medição (A Física por trás)
O principal trunfo técnico é o serviço `MotorCalculoEnergetico` (localizado em `/services/calculo_energia.py`), que analisa os dados da máquina inteligentemente em 2 métodos:

1.  **Cálculo Avançado por Voltagem/Corrente:** 
    *   *Fórmula:* `Potência (Watts) = Voltagem (V) × Corrente (A) × Fator de Potência`
    *   *Consumo (kWh):* `(Watts / 1000) × Horas de Uso × Fator de Carga`
2.  **Cálculo Tradicional por Potência Nominal:**
    *   Se a corrente real não for conhecida, o sistema usa a potência de placa: `(Potência / 1000) × Horas × Fator de Carga`.
3.  **Conversão de Emissão de CO2:** Multiplica o total de kWh por `0.085 kg CO2/kWh` para estimar emissões na atmosfera (Critério ESG).
4.  **Custo Real:** Multiplica o kWh gerado por uma Tarifa de Energia parametrizável (ex: `R$ 0.85 / kWh`).

### Slide 4: Regras de Negócios e Sustentabilidade (O Impacto)
O Ener-Guardian aplica de forma invisível diversas Regras de Negócios (`alerta_service.py`) para evitar o desperdício:
*   **Automação de Alertas - Regra 1 (Sobrecarga de Equipamento):** Se um apontamento resultar em um consumo superior a **75% da capacidade teórica máxima do equipamento no dia** (24h de operação ininterrupta), o sistema dispara um Alerta **Crítico** automático (Risco de queima / desgaste acelerado).
*   **Automação de Alertas - Regra 2 (Estouro de Meta Setorial):** Cada setor recebe um orçamento diário energético (Ex: 500 kWh/dia). Se o operador apontar uso que, somado, ultrapasse essa cota, um alerta é gerado ao gestor imediatamente.
*   **Segurança (RBAC):** Sistema dividido em permissões. Operadores só fazem "Apontamentos". Gestores veem "Relatórios". Admins editam regras e setores.

Com essa base, você pode explicar de maneira clara e técnica o porquê o **Ener-Guardian** não é "apenas uma tela de cadastro", mas um motor financeiro e físico de inteligência industrial.
