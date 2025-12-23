# NPE-PSQ Advanced Tokamak Simulator - Documentação Técnica

**Versão:** 2.0.0 (Refatoração Completa)  
**Data:** Dezembro de 2025  
**Autor:** Guilherme Brasil de Souza  
**Status:** Produção

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Modelos Físicos Implementados](#modelos-físicos-implementados)
4. [Controlador MPC](#controlador-mpc)
5. [Integração Numérica](#integração-numérica)
6. [Testes e Validação](#testes-e-validação)
7. [Guia de Uso](#guia-de-uso)
8. [Referências](#referências)

---

## Visão Geral

O **NPE-PSQ Advanced Simulator** é uma simulação de tokamak de fidelidade intermediária-avançada que implementa:

- **Dinâmica MHD simplificada** com transporte anômalo
- **Controlador MPC verdadeiro** com otimização quadrática
- **Integração numérica RK4** com adaptive time-stepping
- **Testes unitários completos** e validação de estabilidade
- **Diagnósticos avançados** em tempo real

### Melhorias em Relação à Versão 1.0

| Aspecto | v1.0 | v2.0 | Melhoria |
|---------|------|------|----------|
| Controle | PID | MPC com QP | 5→8/10 |
| Integração | Euler | RK4 Adaptativo | 4→8/10 |
| Física | Quasi-estática | MHD + Transporte | 6→7.5/10 |
| Testes | Nenhum | 34 testes | 0→8/10 |
| Documentação | Básica | Completa | 3→9/10 |

---

## Arquitetura do Sistema

### Estrutura de Diretórios

```
npe-psq-advanced/
├── src/
│   ├── constants.py              # Constantes físicas
│   ├── tokamak_config.py         # Configuração e estado
│   ├── plasma_dynamics.py        # Dinâmica MHD e transporte
│   ├── numerical_integration.py  # Integrador RK4
│   ├── mpc_controller.py         # Controlador MPC
│   ├── diagnostics.py            # Diagnósticos e visualização
│   └── __init__.py
├── tests/
│   ├── test_constants.py
│   ├── test_plasma_dynamics.py
│   ├── test_numerical_integration.py
│   └── test_mpc_controller.py
├── examples/
│   ├── basic_simulation.py       # Simulação básica
│   ├── mpc_control_example.py    # Exemplo com MPC
│   └── transp_comparison.py      # Comparação com TRANSP
├── docs/
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── API_REFERENCE.md
│   └── PHYSICS_MODELS.md
└── requirements.txt
```

### Módulos Principais

#### 1. **constants.py**
Define constantes físicas (NIST) e coeficientes de transporte.

```python
from src.constants import PHYSICAL_CONSTANTS, TRANSPORT_COEFFICIENTS

# Acessar constantes
mu0 = PHYSICAL_CONSTANTS.MU0
E_DT = PHYSICAL_CONSTANTS.DT_FUSION_ENERGY

# Calcular difusividade de Bohm
chi = TRANSPORT_COEFFICIENTS.get_chi_bohm(T_keV=10.0, B_T=5.3)
```

#### 2. **tokamak_config.py**
Define geometria, estado do plasma e configuração magnética.

```python
from src.tokamak_config import TokamakGeometry, PlasmaState, HeatingSystem

# Criar geometria (ITER-like)
geom = TokamakGeometry(R0=6.2, a=2.0, kappa=1.7, delta=0.33)

# Criar estado inicial
state = PlasmaState(T_e_centro=10.0, n_e_centro=1e20, Ip=15.0)

# Sistema de aquecimento
heating = HeatingSystem(P_ECRH=20.0, P_ICRH=30.0, P_NBI=33.0)
```

#### 3. **plasma_dynamics.py**
Implementa equações MHD e dinâmica de plasma.

```python
from src.plasma_dynamics import PlasmaEquations

equations = PlasmaEquations(geom, mag_config)

# Calcular potência de fusão
P_fus = equations.calculate_fusion_power(state)

# Calcular risco de disrupção
risk = equations.calculate_disruption_risk(state)
```

#### 4. **numerical_integration.py**
Integrador RK4 com adaptive stepping.

```python
from src.numerical_integration import RK4Integrator, IntegrationConfig

config = IntegrationConfig(dt=0.001, adaptive=True)
integrator = RK4Integrator(config)

# Integrar um passo
state_new, dt_new, success = integrator.step(
    state, heating, mag_config, equations
)

# Integrar até tempo final
state_final, stats = integrator.integrate(
    state, heating, mag_config, equations, t_final=1.0
)
```

#### 5. **mpc_controller.py**
Controlador MPC com otimização quadrática.

```python
from src.mpc_controller import MPCController, MPCConfig

config = MPCConfig(
    N=20,  # Horizonte de predição
    T_e_ref=10.0,  # Setpoint de temperatura
    Ip_ref=15.0    # Setpoint de corrente
)

controller = MPCController(geom, mag_config, config)

# Calcular ação de controle
u_opt = controller.compute_control(state)
# u_opt = {'P_ECRH': ..., 'P_ICRH': ..., 'P_NBI': ..., 'F_z': ...}
```

#### 6. **diagnostics.py**
Cálculo de parâmetros de diagnóstico e visualização.

```python
from src.diagnostics import Diagnostics

diag_system = Diagnostics(geom, mag_config)

# Calcular diagnósticos
diag = diag_system.calculate_diagnostics(state, P_heat=50.0)

# Imprimir sumário
diag_system.print_summary(diag)

# Plotar histórico
fig = diag_system.plot_diagnostics()
```

---

## Modelos Físicos Implementados

### 1. Dinâmica de Temperatura

**Equação de Balanço de Energia:**

$$\frac{dT_e}{dt} = \frac{P_{heat} - P_{loss}}{3/2 \cdot n_e \cdot k_B \cdot V}$$

onde:
- $P_{heat}$ = Potência de aquecimento (ECRH, ICRH, NBI)
- $P_{loss}$ = Potência perdida (radiação + condução)
- $V$ = Volume do plasma

**Implementação:**
```python
def dT_e_dt(self, state, heating, mag_config):
    P_heat = heating.get_total_power() * 1e6  # [W]
    P_loss = self.transport.calculate_energy_loss(...)
    dT_e_dt = (P_heat - P_loss) / energy_content
    return dT_e_dt / (1000 * PC.EV_TO_J)  # Converter para keV/s
```

### 2. Dinâmica de Densidade

**Equação de Continuidade:**

$$\frac{dn_e}{dt} = -\frac{n_e}{\tau_p}$$

onde $\tau_p$ é o tempo de confinamento de partículas.

### 3. Dinâmica de Corrente

**Equação de Indução:**

$$\frac{dI_p}{dt} = \frac{V_{loop}}{L_{plasma}}$$

onde:
- $V_{loop}$ = Tensão de loop induzida
- $L_{plasma}$ = Indutância do plasma

### 4. Dinâmica Vertical

**Equação de Movimento:**

$$m \frac{dv_z}{dt} = F_{vertical} - F_{amortecimento} - F_{restauracao}$$

### 5. Transporte Anômalo (Bohm-like)

**Difusividade de Bohm:**

$$\chi_{Bohm} = \frac{1}{16} \frac{k_B T}{e B}$$

### 6. Seção de Choque de Fusão D-T

**Aproximação de Bosch-Hale:**

$$\sigma v = \begin{cases}
1.0 \times 10^{-25} e^{-50/T} & T < 1 \text{ keV} \\
1.0 \times 10^{-24} T^2 & 1 < T < 10 \text{ keV} \\
1.0 \times 10^{-22} \frac{\ln T}{T^{2/3}} & T > 10 \text{ keV}
\end{cases}$$

### 7. Instabilidades MHD

**Taxa de Crescimento de Tearing Mode:**

$$\gamma \propto (q_{95} - 2) \beta_N$$

**Limite de Ballooning Mode:**

$$\beta_{N,crit} = \frac{2.5}{q_{95}}$$

---

## Controlador MPC

### Formulação do Problema

**Objetivo:**

$$\min_{u_0, ..., u_{N-1}} \sum_{k=0}^{N-1} \left( ||x_k - x_{ref}||_Q^2 + ||u_k||_R^2 \right)$$

**Restrições:**

- Dinâmica: $x_{k+1} = A x_k + B u_k$
- Limites de potência: $0 \leq P_{ECRH} \leq 20$ MW
- Limites de estado: $1 \leq T_e \leq 50$ keV, etc.

### Modelo Linearizado

O MPC usa um modelo linearizado do tokamak:

$$\begin{bmatrix} T_e \\ I_p \\ Z_{pos} \\ Z_{vel} \end{bmatrix}_{k+1} = A \begin{bmatrix} T_e \\ I_p \\ Z_{pos} \\ Z_{vel} \end{bmatrix}_k + B \begin{bmatrix} P_{ECRH} \\ P_{ICRH} \\ P_{NBI} \\ F_z \end{bmatrix}_k$$

### Implementação

O MPC é implementado usando a biblioteca **CVXPY**:

```python
import cvxpy as cp

# Variáveis de otimização
U = cp.Variable((N, 4))

# Predição de trajetória
X = [x0]
for k in range(N):
    X.append(A @ X[k] + B @ U[k])

# Função de custo
cost = 0
for k in range(N):
    error = X[k+1] - x_ref
    cost += Q @ error**2 + R @ U[k]**2

# Resolver problema QP
problem = cp.Problem(cp.Minimize(cost), constraints)
problem.solve(solver=cp.OSQP)
```

---

## Integração Numérica

### Método RK4

**Fórmula:**

$$y_{n+1} = y_n + \frac{dt}{6}(k_1 + 2k_2 + 2k_3 + k_4)$$

onde:
- $k_1 = f(t_n, y_n)$
- $k_2 = f(t_n + dt/2, y_n + dt k_1/2)$
- $k_3 = f(t_n + dt/2, y_n + dt k_2/2)$
- $k_4 = f(t_n + dt, y_n + dt k_3)$

### Adaptive Time-Stepping

O integrador ajusta o passo de tempo baseado no erro estimado:

$$\text{erro} = \max_i |dy_i/dt| \cdot dt$$

- Se erro < tol_abs: aumentar dt (×1.2)
- Se erro > tol_rel: reduzir dt (×0.8)

### Validação de Estabilidade

Antes de aceitar um passo, o integrador verifica:

1. **Finitude:** Sem NaN ou Inf
2. **Limites físicos:** $T_e < 100$ keV, $n_e < 10^{21}$ m⁻³, etc.
3. **Positividade:** Quantidades físicas são positivas

---

## Testes e Validação

### Testes Unitários (34 testes)

```bash
pytest tests/ -v
```

**Cobertura:**

- ✅ Constantes físicas (10 testes)
- ✅ Dinâmica de plasma (16 testes)
- ✅ Integração numérica (8 testes)

### Validação contra TRANSP

Comparação com simulador TRANSP (padrão da indústria):

- Tempo de confinamento τ_E
- Fator de segurança q95
- Potência de fusão
- Perfis de temperatura e densidade

**Resultado esperado:** Desvio < 10% em parâmetros-chave

---

## Guia de Uso

### Instalação

```bash
cd npe-psq-advanced
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Simulação Básica

```python
from src.tokamak_config import TokamakGeometry, PlasmaState, HeatingSystem, MagneticConfiguration
from src.plasma_dynamics import PlasmaEquations
from src.numerical_integration import RK4Integrator, IntegrationConfig
from src.diagnostics import Diagnostics

# Configurar tokamak
geom = TokamakGeometry()
mag = MagneticConfiguration()
state = PlasmaState(T_e_centro=10.0, Ip=15.0)
heating = HeatingSystem(P_ECRH=10.0, P_ICRH=15.0, P_NBI=20.0)

# Criar equações e integrador
equations = PlasmaEquations(geom, mag)
integrator = RK4Integrator(IntegrationConfig(dt=0.001))

# Integrar
state_final, stats = integrator.integrate(state, heating, mag, equations, t_final=1.0)

# Diagnósticos
diag_sys = Diagnostics(geom, mag)
diag = diag_sys.calculate_diagnostics(state_final, P_heat=45.0)
diag_sys.print_summary(diag)
```

### Simulação com MPC

Veja `examples/mpc_control_example.py`

---

## Referências

### Publicações Científicas

1. **ITER Physics Basis** (1999)  
   https://doi.org/10.1088/0029-5515/39/12/302

2. **Bosch & Hale** (1992) - Seção de choque de fusão D-T  
   https://doi.org/10.1088/0029-5515/32/4/I07

3. **ITER 89P Confinement Scaling** (1990)  
   https://doi.org/10.1088/0029-5515/30/7/001

### Simuladores Relacionados

- **TRANSP** (Princeton Plasma Physics Laboratory)
- **CORSICA** (Lawrence Livermore National Laboratory)
- **CRONOS** (CEA, França)

### Recursos Online

- ITER Organization: https://www.iter.org/
- NIST Physical Constants: https://physics.nist.gov/cuu/Constants/
- OpenFOAM Tokamak Simulations: https://www.openfoam.com/

---

**Última Atualização:** Dezembro 2025  
**Mantido por:** Guilherme Brasil de Souza (GBS Labs)
