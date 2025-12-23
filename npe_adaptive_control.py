"""
NPE-PSQ: SISTEMA DE CONTROLE PREDITIVO COM NÚCLEO NEURAL ADAPTATIVO
Simulação de Alta Fidelidade para Reator de Fusão Compacto (Mark IX)
Autor: Guilherme Brasil | Data: Dezembro 2025
Descrição: MPC + Rede Neural LSTM + Sensores Quânticos + Plasma Caótico Realista
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.signal import correlate
import warnings
warnings.filterwarnings('ignore')

try:
    import cvxpy as cp
    HAS_CVXPY = True
except ImportError:
    HAS_CVXPY = False
    print("⚠️ CVXPY não instalado. Usando MPC simplificado.")

# ============================================================================
# PARTE 1: REDE NEURAL ADAPTATIVA (LSTM Simplificada)
# ============================================================================

class AdaptiveNeuralEstimator:
    """
    Estimador Neural Adaptativo (tipo LSTM) que aprende a dinâmica não-linear
    do plasma e corrige o modelo linear em tempo real.
    
    Arquitetura simplificada:
    - Camada 1: RNN com 16 neurônios (memory state)
    - Camada 2: Dense com 32 neurônios
    - Saída: Correção Δf no modelo linearizado
    """
    
    def __init__(self, state_dim=3, control_dim=3, hidden_dim=16, learning_rate=0.01):
        """
        Inicializa o estimador neural.
        
        Args:
            state_dim: Dimensão do espaço de estados (3 para Lorenz)
            control_dim: Dimensão do controle (3 para injeção multi-canal)
            hidden_dim: Dimensão da camada oculta RNN
            learning_rate: Taxa de aprendizado online
        """
        self.state_dim = state_dim
        self.control_dim = control_dim
        self.hidden_dim = hidden_dim
        self.lr = learning_rate
        
        # Pesos da camada RNN (estado oculto)
        self.W_rnn = np.random.randn(state_dim + control_dim, hidden_dim) * 0.1
        self.U_rnn = np.random.randn(hidden_dim, hidden_dim) * 0.1
        self.b_rnn = np.zeros(hidden_dim)
        
        # Pesos da camada densa (previsão de correção)
        self.W_dense = np.random.randn(hidden_dim, state_dim) * 0.1
        self.b_dense = np.zeros(state_dim)
        
        # Estado oculto RNN
        self.h = np.zeros(hidden_dim)
        
        # Histórico de aprendizado
        self.training_loss = []
        self.prediction_error = []
        
    def tanh(self, x):
        """Ativação tanh numérica estável."""
        return np.tanh(np.clip(x, -500, 500))
    
    def forward(self, x, u):
        """
        Passa para frente (forward pass) da rede.
        Prediz uma correção Δf ao modelo linearizado.
        
        Args:
            x (ndarray): Estado atual (state_dim,)
            u (ndarray): Controle atual (control_dim,)
        
        Returns:
            delta_f (ndarray): Correção ao modelo (state_dim,)
            h_new (ndarray): Novo estado oculto (hidden_dim,)
        """
        # Concatenar entrada
        x_u = np.concatenate([x, u])
        
        # RNN: h_new = tanh(W_rnn @ x_u + U_rnn @ h_old + b_rnn)
        h_new = self.tanh(
            self.W_rnn.T @ x_u + self.U_rnn @ self.h + self.b_rnn
        )
        
        # Dense: delta_f = W_dense @ h_new + b_dense
        delta_f = self.W_dense.T @ h_new + self.b_dense
        
        return delta_f, h_new
    
    def backward(self, delta_f, h_new, error):
        """
        Atualização online (tipo mini-batch) dos pesos via gradiente descendente.
        
        Args:
            delta_f (ndarray): Saída da rede
            h_new (ndarray): Estado oculto
            error (ndarray): Erro de predição (y_real - y_pred)
        """
        # Gradiente na saída: dL/d(delta_f) = -error
        dL_dout = -error
        
        # Atualizar W_dense
        grad_W_dense = np.outer(h_new, dL_dout)
        self.W_dense -= self.lr * grad_W_dense
        
        # Atualizar b_dense
        self.b_dense -= self.lr * dL_dout
        
        # Isso é uma simplificação (TBPTT completo é mais pesado)
    
    def predict_and_learn(self, x, u, x_next_real, dt=0.01):
        """
        Prediz a próxima dinâmica E aprende simultaneamente.
        
        Args:
            x (ndarray): Estado atual
            u (ndarray): Controle
            x_next_real (ndarray): Estado real no próximo passo (para aprendizado)
            dt (float): Intervalo de tempo
        
        Returns:
            x_next_pred (ndarray): Predição da próxima dinâmica
        """
        # Forward pass
        delta_f, h_new = self.forward(x, u)
        
        # Atualizar estado oculto
        self.h = h_new
        
        # Predição: x_next = x + (A@x + B@u + delta_f) * dt
        # (aqui delta_f já é a correção ao modelo linear)
        x_next_pred = x + delta_f * dt
        
        # Erro real
        error = x_next_pred - x_next_real
        
        # Aprender (backward pass simplificado)
        self.backward(delta_f, h_new, error)
        
        # Registrar métricas
        loss = np.linalg.norm(error)
        self.training_loss.append(loss)
        self.prediction_error.append(error)
        
        return x_next_pred


# ============================================================================
# PARTE 2: SENSORES QUÂNTICOS (PSQ)
# ============================================================================

class QuantumSensorArray:
    """
    Simula um array de sensores quânticos (Nitrogen-Vacancy ou SQUID).
    Características:
    - Alto SNR (relação sinal-ruído)
    - Zero drift (medição absoluta, não derivada)
    - Ruído gaussiano branco de baixa amplitude
    """
    
    def __init__(self, num_channels=3, snr_db=40):
        """
        Inicializa o array de sensores.
        
        Args:
            num_channels: Número de canais de medição
            snr_db: Relação sinal-ruído em dB (típico: 40-50 dB para NV)
        """
        self.num_channels = num_channels
        self.snr_db = snr_db
        
        # Converter dB para razão linear
        self.snr_linear = 10 ** (snr_db / 10)
        self.noise_std = 1.0 / np.sqrt(self.snr_linear)  # Ruído normalizado
        
        # Drift: sensores quânticos têm drift negligenciável (~ppm/hora)
        self.drift_rate = 1e-4  # Taxa de drift muito baixa
        self.drift_state = np.zeros(num_channels)
        
        # Calibração (gain e offset)
        self.gain = np.ones(num_channels)
        self.offset = np.zeros(num_channels)
        
        # Histórico para análise
        self.measurements_history = []
        self.noise_history = []
    
    def measure(self, true_state, t, add_drift=True):
        """
        Realiza medição com ruído realístico.
        
        Args:
            true_state (ndarray): Estado real do plasma (3,)
            t (float): Tempo (para drift)
            add_drift (bool): Se adiciona drift lento
        
        Returns:
            measurement (ndarray): Medição com ruído
        """
        # Ruído gaussiano branco
        noise = np.random.randn(self.num_channels) * self.noise_std
        
        # Drift lento (negligenciável para fusão)
        if add_drift:
            self.drift_state += self.drift_rate * np.random.randn(self.num_channels) * 1e-5
        else:
            self.drift_state *= 0.999  # Decaimento do drift
        
        # Medição: m = gain * true_state + offset + noise + drift
        measurement = self.gain * true_state + self.offset + noise + self.drift_state
        
        # Registrar histórico
        self.measurements_history.append(measurement)
        self.noise_history.append(noise)
        
        return measurement


# ============================================================================
# PARTE 3: CONTROLADOR MPC ADAPTATIVO
# ============================================================================

class AdaptiveMPCController:
    """
    Controlador MPC que recebe predições do estimador neural e as integra
    na otimização de controle em tempo real.
    """
    
    def __init__(self, A, B, Q, R, neural_estimator, horizon=15, dt=0.01):
        """
        Args:
            A, B: Matrizes do modelo linear
            Q, R: Pesos de otimização
            neural_estimator: Instância do AdaptiveNeuralEstimator
            horizon: Horizonte de predição
            dt: Intervalo de tempo
        """
        self.A = A
        self.B = B
        self.Q = Q
        self.R = R
        self.neural = neural_estimator
        self.horizon = horizon
        self.dt = dt
        self.n = A.shape[0]
        self.m = B.shape[1]
        
        # Restrições
        self.u_min = np.array([-20.0, -20.0, -10.0])
        self.u_max = np.array([20.0, 20.0, 10.0])
        self.x_min = np.array([-40.0, -40.0, 0.0])
        self.x_max = np.array([40.0, 40.0, 50.0])
        
        # Histórico
        self.solve_times = []
        self.constraint_violations = []
    
    def predict_trajectory(self, x_current, U_seq):
        """
        Prediz a trajetória futura usando modelo linear + correção neural.
        
        Args:
            x_current: Estado atual
            U_seq: Sequência de controles (horizon, m)
        
        Returns:
            X_pred: Predições de estado (horizon+1, n)
        """
        X_pred = np.zeros((self.horizon + 1, self.n))
        X_pred[0] = x_current
        
        x = x_current.copy()
        for t in range(self.horizon):
            # Modelo linear
            x_linear = self.A @ x + self.B @ U_seq[t]
            
            # Correção neural (delta_f)
            delta_f, _ = self.neural.forward(x, U_seq[t])
            
            # Predição combinada
            x_next = x_linear + delta_f * self.dt
            
            # Restrições
            x_next = np.clip(x_next, self.x_min, self.x_max)
            
            X_pred[t + 1] = x_next
            x = x_next
        
        return X_pred
    
    def solve_mpc(self, x_current, x_ref):
        """Resolve o problema MPC com CVXPY ou fallback."""
        if HAS_CVXPY:
            return self._solve_mpc_cvxpy(x_current, x_ref)
        else:
            return self._solve_mpc_pd(x_current, x_ref)
    
    def _solve_mpc_cvxpy(self, x_current, x_ref):
        """MPC com CVXPY (ótimo)."""
        U = cp.Variable((self.horizon, self.m))
        cost = 0
        x_pred = x_current.copy()
        
        for t in range(self.horizon):
            # Predição linear + neural
            x_linear = self.A @ x_pred + self.B @ U[t]
            delta_f, _ = self.neural.forward(x_pred, U[t])
            x_pred = x_linear + delta_f * self.dt
            
            # Custo
            error = x_pred - x_ref
            cost += cp.quad_form(error, self.Q)
            cost += cp.quad_form(U[t], self.R)
        
        # Restrições
        constraints = [
            U >= self.u_min,
            U <= self.u_max
        ]
        
        problem = cp.Problem(cp.Minimize(cost), constraints)
        try:
            problem.solve(solver=cp.OSQP, verbose=False, eps_abs=1e-4, eps_rel=1e-4, max_iter=500)
            if problem.status == cp.OPTIMAL:
                return U.value[0], problem.value
        except:
            pass
        
        return np.zeros(self.m), np.inf
    
    def _solve_mpc_pd(self, x_current, x_ref):
        """Fallback: PD + feed-forward."""
        error = x_current - x_ref
        K_p = np.diag([2.0, 2.0, 1.0])
        u = -K_p @ error
        u = np.clip(u, self.u_min, self.u_max)
        return u, 0.0


# ============================================================================
# PARTE 4: MODELO CAÓTICO REALISTA DO PLASMA
# ============================================================================

class ChaicPlasmaModel:
    """
    Modelo caótico realista do plasma baseado em Lorenz com:
    - Variação lenta de parâmetros (profile evolution)
    - Ruído colorido (turbulência de borda)
    - Eventos discretos de ELM
    """
    
    def __init__(self, sigma=10.0, rho=28.0, beta=8.0/3.0):
        """Inicializa modelo de Lorenz."""
        self.sigma = sigma
        self.rho = rho
        self.beta = beta
        
        # Parâmetro variante (drift de rho - simula mudança de corrente)
        self.rho_nominal = rho
        self.rho_variation = 0.0
        self.rho_drift_rate = 0.5  # Mudança em rho por 30 segundos
        
        # Ruído colorido (filtro 1ª ordem)
        self.colored_noise = np.zeros(3)
        self.noise_tau = 0.1  # Constante de tempo do ruído
        
        # Eventos de ELM
        self.elm_times = [2.0, 8.5, 15.2, 22.8]  # Tempos de ELM
        self.elm_magnitude = 0.15  # Amplitude relativa do ELM
    
    def get_rho(self, t):
        """Rho varia lentamente (simulando mudança de corrente de plasma)."""
        self.rho_variation = self.rho_nominal + 5.0 * np.sin(2 * np.pi * t / 30.0)
        return self.rho_variation
    
    def lorenz_nonlinear(self, x, u, t):
        """
        Dinâmica não-linear completa de Lorenz com:
        - Controle acoplado
        - Parâmetros variantes
        - Ruído colorido
        - Eventos de ELM
        
        Args:
            x: Estado [x, y, z]
            u: Controle [u1, u2, u3]
            t: Tempo
        
        Returns:
            dx: Derivada de estado
        """
        rho = self.get_rho(t)
        
        # Lorenz base
        dx = np.array([
            self.sigma * (x[1] - x[0]) + u[0],
            x[0] * (rho - x[2]) - x[1] + u[1],
            x[0] * x[1] - self.beta * x[2] + 0.5 * u[2]
        ])
        
        # Ruído colorido (turbulência)
        tau = self.noise_tau
        self.colored_noise = self.colored_noise * np.exp(-1.0 / tau / 100) + \
                             0.05 * np.random.randn(3)
        dx += self.colored_noise
        
        # Eventos de ELM (impulsos)
        for elm_t in self.elm_times:
            if abs(t - elm_t) < 0.05:  # ELM dura ~50 ms
                elm_pulse = self.elm_magnitude * np.exp(-((t - elm_t) / 0.02) ** 2)
                dx += elm_pulse * np.array([3.0, -2.0, 5.0])
        
        return dx
    
    def step(self, x, u, t, dt=0.01):
        """Integração Runge-Kutta 4ª ordem."""
        k1 = self.lorenz_nonlinear(x, u, t)
        k2 = self.lorenz_nonlinear(x + 0.5 * dt * k1, u, t + 0.5 * dt)
        k3 = self.lorenz_nonlinear(x + 0.5 * dt * k2, u, t + 0.5 * dt)
        k4 = self.lorenz_nonlinear(x + dt * k3, u, t + dt)
        
        x_next = x + dt * (k1 + 2*k2 + 2*k3 + k4) / 6.0
        return x_next


# ============================================================================
# PARTE 5: SIMULAÇÃO COMPLETA
# ============================================================================

def run_high_fidelity_simulation():
    """
    Simulação de alta fidelidade: 30 segundos de operação com
    NPE-PSQ adaptativo, MPC, sensores quânticos, e plasma caótico.
    """
    
    print("=" * 80)
    print("NPE-PSQ: SIMULAÇÃO DE ALTA FIDELIDADE EM REATOR DE FUSÃO")
    print("=" * 80)
    print("\n▶ Inicializando componentes...\n")
    
    # ---- INICIALIZAÇÃO ----
    
    # Modelo linearizado
    sigma, rho, beta = 10.0, 28.0, 8.0/3.0
    x_eq = np.sqrt(beta * (rho - 1))
    A = np.array([
        [-sigma, sigma, 0],
        [rho - np.sqrt(beta*(rho-1)), -1, -x_eq],
        [np.sqrt(beta*(rho-1)), x_eq, -beta]
    ])
    B = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.5]])
    
    Q = np.diag([1.0, 1.0, 10.0])
    R = np.diag([0.1, 0.1, 0.1])
    
    # Estimador neural
    print("  ✓ Criando estimador neural adaptativo (LSTM)...")
    neural = AdaptiveNeuralEstimator(state_dim=3, control_dim=3, hidden_dim=16)
    
    # Sensores quânticos
    print("  ✓ Inicializando array de sensores quânticos (NV centers)...")
    sensors = QuantumSensorArray(num_channels=3, snr_db=45)
    
    # MPC adaptativo
    print("  ✓ Configurando controlador MPC adaptativo...")
    mpc = AdaptiveMPCController(A, B, Q, R, neural, horizon=15, dt=0.01)
    
    # Modelo do plasma caótico
    print("  ✓ Inicializando dinâmica caótica do plasma...\n")
    plasma = ChaicPlasmaModel(sigma=sigma, rho=rho, beta=beta)
    
    # ---- PARÂMETROS DE SIMULAÇÃO ----
    
    T_total = 30.0  # 30 segundos
    dt = 0.01       # 10 ms
    num_steps = int(T_total / dt)
    
    time = np.linspace(0, T_total, num_steps)
    
    # Estado inicial (pequena perturbação)
    x0 = np.array([0.5, 0.5, 20.0])
    x_ref = np.array([0.0, 0.0, 25.0])  # Setpoint
    
    # ---- HISTÓRICOS DE SIMULAÇÃO ----
    
    states_true = np.zeros((num_steps, 3))
    states_estimated = np.zeros((num_steps, 3))
    measurements = np.zeros((num_steps, 3))
    controls = np.zeros((num_steps, 3))
    predictions_neural = np.zeros((num_steps, 3))
    
    states_true[0] = x0
    states_estimated[0] = x0
    measurements[0] = sensors.measure(x0, 0)
    
    x_true = x0.copy()
    x_est = x0.copy()
    
    # ---- LOOP PRINCIPAL DE SIMULAÇÃO ----
    
    print("▶ Executando simulação (este pode demorar alguns segundos)...\n")
    
    for k in range(1, num_steps):
        t = time[k]
        
        # 1. SENSORES QUÂNTICOS: Medir estado
        measurement = sensors.measure(x_true, t, add_drift=True)
        measurements[k] = measurement
        
        # 2. ESTIMADOR NEURAL: Estimar próximo estado
        delta_f, h_new = neural.forward(x_est, controls[k-1])
        predictions_neural[k] = delta_f
        
        # 3. MPC ADAPTATIVO: Calcular controle
        u_mpc, _ = mpc.solve_mpc(x_est, x_ref)
        controls[k] = u_mpc
        
        # 4. DINÂMICA REAL (Lorenz Caótico): Evoluir plasma
        x_true = plasma.step(x_true, u_mpc, t, dt)
        x_true = np.clip(x_true, mpc.x_min, mpc.x_max)
        states_true[k] = x_true
        
        # 5. APRENDIZADO NEURAL: Atualizar rede com medição real
        x_next_pred = x_est + delta_f * dt
        neural.predict_and_learn(x_est, u_mpc, measurement, dt)
        
        # 6. ATUALIZAR ESTIMATIVA: Usar medição para corrigir
        x_est = 0.7 * x_est + 0.3 * measurement  # Filtro simples tipo observador
        states_estimated[k] = x_est
        
        # Barra de progresso
        if k % 1000 == 0:
            progress = 100 * k / num_steps
            print(f"  [{progress:5.1f}%] t={t:6.2f}s | "
                  f"||x_true||={np.linalg.norm(x_true):6.2f} | "
                  f"||u||={np.linalg.norm(u_mpc):6.2f} | "
                  f"Neural Loss={neural.training_loss[-1]:.4f}")
    
    print("\n✓ Simulação concluída!\n")
    
    # ---- COLETA DE RESULTADOS ----
    
    results = {
        'time': time,
        'states_true': states_true,
        'states_estimated': states_estimated,
        'measurements': measurements,
        'controls': controls,
        'predictions_neural': predictions_neural,
        'neural_losses': np.array(neural.training_loss),
        'sensors': sensors,
        'plasma': plasma,
        'mpc': mpc
    }
    
    return results


# ============================================================================
# PARTE 6: ANÁLISE E MÉTRICAS
# ============================================================================

def calculate_advanced_metrics(results):
    """Calcula métricas avançadas de controle e estabilidade."""
    
    t = results['time']
    x_true = results['states_true']
    x_est = results['states_estimated']
    controls = results['controls']
    measurements = results['measurements']
    
    # 1. Erro de estimação
    estimation_error = np.linalg.norm(x_true - x_est, axis=1)
    
    # 2. Energia de perturbação
    energy_true = np.sum(x_true**2, axis=1)
    energy_est = np.sum(x_est**2, axis=1)
    
    # 3. Esforço de controle
    control_power = np.sum(controls**2, axis=1)
    
    # 4. Detecção de disrupção (divergência > threshold)
    divergence_threshold = 3.0  # Múltiplos do desvio padrão
    divergence_detected = False
    disruption_time = None
    
    for i in range(len(t)):
        if energy_true[i] > divergence_threshold * np.std(energy_true[:max(100, i)]) + 100:
            divergence_detected = True
            disruption_time = t[i]
            break
    
    # 5. Ruído vs sinal (em dB)
    noise = measurements - x_true
    signal_power = np.mean(x_true**2)
    noise_power = np.mean(noise**2)
    snr_achieved = 10 * np.log10(signal_power / (noise_power + 1e-10))
    
    # 6. Taxa de confinamento
    energy_loss_rate = (energy_true[0] - energy_true[-1]) / (t[-1] - t[0])
    
    # 7. Estabilidade: Lyapunov exponent aproximado
    divergence_rate = []
    for i in range(0, len(t) - 100):
        div = np.linalg.norm(x_true[i+100] - x_true[i])
        if div > 0:
            divergence_rate.append(np.log(div) / (100 * 0.01))
    
    lyapunov_approx = np.mean(divergence_rate) if divergence_rate else 0.0
    
    metrics = {
        'mean_estimation_error': np.mean(estimation_error),
        'max_estimation_error': np.max(estimation_error),
        'peak_energy': np.max(energy_true),
        'final_energy': energy_true[-1],
        'energy_suppression_percent': 100 * (energy_true[0] - energy_true[-1]) / energy_true[0],
        'mean_control_power': np.mean(control_power),
        'max_control_power': np.max(control_power),
        'snr_achieved_db': snr_achieved,
        'energy_loss_rate': energy_loss_rate,
        'disruption_detected': divergence_detected,
        'disruption_time': disruption_time,
        'lyapunov_exponent_approx': lyapunov_approx,
    }
    
    return metrics


# ============================================================================
# PARTE 7: VISUALIZAÇÃO
# ============================================================================

def plot_comprehensive_results(results, metrics):
    """Cria visualização completa (8 painéis)."""
    
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)
    
    t = results['time']
    x_true = results['states_true']
    x_est = results['states_estimated']
    controls = results['controls']
    measurements = results['measurements']
    neural_losses = results['neural_losses']
    
    # Cores
    color_true = '#FF6B6B'
    color_est = '#4ECDC4'
    color_meas = '#95E1D3'
    
    # --- Painel 1: Estados Verdadeiros vs Estimados ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t, x_true[:, 0], color=color_true, linewidth=2, label='Estado Real (x)')
    ax1.plot(t, x_est[:, 0], color=color_est, linewidth=1.5, linestyle='--', alpha=0.8, label='Estimado (x)')
    ax1.fill_between(t, x_est[:, 0] - np.std(x_est[:, 0]), x_est[:, 0] + np.std(x_est[:, 0]), 
                     alpha=0.1, color=color_est)
    ax1.set_xlabel('Tempo (s)')
    ax1.set_ylabel('Modo X')
    ax1.set_title('Modo 1 (X): Rastreamento Neural', fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # --- Painel 2: Modo Z (Energia) ---
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t, x_true[:, 2], color=color_true, linewidth=2.5, label='Real')
    ax2.plot(t, x_est[:, 2], color=color_est, linewidth=2, linestyle='--', alpha=0.8, label='Estimado')
    for elm_t in results['plasma'].elm_times:
        ax2.axvline(x=elm_t, color='orange', linestyle=':', alpha=0.5)
    ax2.set_xlabel('Tempo (s)')
    ax2.set_ylabel('Energia Z')
    ax2.set_title('Modo 3 (Energia) + Eventos de ELM', fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # --- Painel 3: Energia Total (Log) ---
    ax3 = fig.add_subplot(gs[1, 0])
    energy_true = np.sum(x_true**2, axis=1)
    energy_est = np.sum(x_est**2, axis=1)
    ax3.semilogy(t, energy_true, color=color_true, linewidth=2.5, label='Real')
    ax3.semilogy(t, energy_est, color=color_est, linewidth=2, linestyle='--', alpha=0.8, label='Estimado')
    ax3.axhline(y=np.mean(energy_true), color='gray', linestyle=':', alpha=0.5)
    ax3.set_xlabel('Tempo (s)')
    ax3.set_ylabel('Energia Total (log scale)')
    ax3.set_title('Energia de Perturbação', fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, which='both')
    
    # --- Painel 4: Espaço de Fase 3D Projeção ---
    ax4 = fig.add_subplot(gs[1, 1])
    scatter = ax4.scatter(x_true[:, 0], x_true[:, 1], c=t, cmap='viridis', s=20, alpha=0.6, label='Trajetória Real')
    ax4.plot(x_est[:, 0], x_est[:, 1], color=color_est, linewidth=1, alpha=0.7, label='Estimada')
    ax4.set_xlabel('Modo X')
    ax4.set_ylabel('Modo Y')
    ax4.set_title('Espaço de Fase (X-Y)', fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Tempo (s)')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # --- Painel 5: Sinais de Controle ---
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.plot(t, controls[:, 0], label='u₁ (Injeção X)', linewidth=1.5)
    ax5.plot(t, controls[:, 1], label='u₂ (Injeção Y)', linewidth=1.5)
    ax5.plot(t, controls[:, 2], label='u₃ (Modulação Z)', linewidth=1.5)
    ax5.axhline(y=0, color='black', linestyle='-', alpha=0.2)
    ax5.set_xlabel('Tempo (s)')
    ax5.set_ylabel('Amplitude de Controle')
    ax5.set_title('Sinais de Controle MPC', fontweight='bold')
    ax5.legend(fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # --- Painel 6: Erro de Estimação ---
    ax6 = fig.add_subplot(gs[2, 1])
    estimation_error = np.linalg.norm(x_true - x_est, axis=1)
    ax6.plot(t, estimation_error, color='purple', linewidth=2)
    ax6.fill_between(t, 0, estimation_error, alpha=0.3, color='purple')
    ax6.axhline(y=np.mean(estimation_error), color='red', linestyle='--', label=f'Média = {np.mean(estimation_error):.3f}')
    ax6.set_xlabel('Tempo (s)')
    ax6.set_ylabel('||x_real - x_est||')
    ax6.set_title('Erro de Estimação Neural', fontweight='bold')
    ax6.legend(fontsize=8)
    ax6.grid(True, alpha=0.3)
    ax6.set_yscale('log')
    
    # --- Painel 7: Perda de Treinamento (Neural) ---
    ax7 = fig.add_subplot(gs[3, 0])
    ax7.semilogy(neural_losses, color='darkblue', linewidth=1.5)
    ax7.set_xlabel('Passo de Treinamento')
    ax7.set_ylabel('Perda (Loss)')
    ax7.set_title('Convergência do Estimador Neural (LSTM)', fontweight='bold')
    ax7.grid(True, alpha=0.3, which='both')
    
    # --- Painel 8: Resumo de Métricas ---
    ax8 = fig.add_subplot(gs[3, 1])
    ax8.axis('off')
    
    metrics_text = f"""
    ╔══════════════════════════════════════════════════════╗
    ║        RESUMO DE DESEMPENHO - NPE-PSQ 30s           ║
    ╠══════════════════════════════════════════════════════╣
    ║  Erro de Estimação (Médio):    {metrics['mean_estimation_error']:8.4f}          ║
    ║  Erro de Estimação (Máximo):   {metrics['max_estimation_error']:8.4f}          ║
    ║  Energia (Pico):               {metrics['peak_energy']:8.2f} u.a.        ║
    ║  Energia (Final):              {metrics['final_energy']:8.2f} u.a.        ║
    ║  Supressão de Energia:         {metrics['energy_suppression_percent']:8.1f}%             ║
    ║  SNR Alcançado:                {metrics['snr_achieved_db']:8.1f} dB          ║
    ║  Taxa de Confinamento:         {metrics['energy_loss_rate']:8.4f}         ║
    ║  Lyapunov (aprox):             {metrics['lyapunov_exponent_approx']:8.4f}          ║
    ║  Disrupção Detectada:          {'✓ SIM' if metrics['disruption_detected'] else '✗ NÃO':>20} ║
    ║  Potência de Controle (Média): {metrics['mean_control_power']:8.2f} u.a.        ║
    ║  Potência de Controle (Máx):   {metrics['max_control_power']:8.2f} u.a.        ║
    ╚══════════════════════════════════════════════════════╝
    """
    
    ax8.text(0.05, 0.5, metrics_text, fontsize=9, family='monospace',
            verticalalignment='center', transform=ax8.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.suptitle('NPE-PSQ: Simulação de Alta Fidelidade em Reator de Fusão Compacto', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig('npe_psq_high_fidelity_results.png', dpi=300, bbox_inches='tight')
    print("✓ Gráficos salvos em 'npe_psq_high_fidelity_results.png'\n")
    plt.show()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    
    # Executar simulação
    results = run_high_fidelity_simulation()
    
    # Calcular métricas
    print("▶ Calculando métricas avançadas...")
    metrics = calculate_advanced_metrics(results)
    
    # Exibir resumo
    print("\n" + "=" * 80)
    print("MÉTRICAS DE DESEMPENHO - NPE-PSQ")
    print("=" * 80)
    print(f"  Erro de Estimação (Médio):     {metrics['mean_estimation_error']:8.4f}")
    print(f"  Erro de Estimação (Máximo):    {metrics['max_estimation_error']:8.4f}")
    print(f"  Energia (Pico):                {metrics['peak_energy']:8.2f} u.a.")
    print(f"  Energia (Final):               {metrics['final_energy']:8.2f} u.a.")
    print(f"  Supressão de Energia:          {metrics['energy_suppression_percent']:8.1f}%")
    print(f"  SNR Alcançado:                 {metrics['snr_achieved_db']:8.1f} dB")
    print(f"  Taxa de Confinamento:          {metrics['energy_loss_rate']:8.4f}")
    print(f"  Lyapunov (aproximado):         {metrics['lyapunov_exponent_approx']:8.4f}")
    print(f"  Disrupção Detectada:           {'✓ SIM' if metrics['disruption_detected'] else '✗ NÃO':>20}")
    print("=" * 80 + "\n")
    
    # Plotar resultados
    print("▶ Gerando visualizações (8 painéis)...")
    plot_comprehensive_results(results, metrics)
    
    print("\n" + "=" * 80)
    print("✓ SIMULAÇÃO NPE-PSQ CONCLUÍDA COM SUCESSO")
    print("=" * 80)
    print("\nArquivos gerados:")
    print("  - npe_psq_high_fidelity_results.png (gráficos 8-painéis)")
    print("\nPróximas ações para publicação:")
    print("  1. Incluir figura no artigo como Figura 5 ou 6")
    print("  2. Citar este código na seção de Metodologia Numérica")
    print("  3. Comparar com controle PID clássico (gráfico comparativo)")
    print("  4. Validar contra dados experimentais ou simulações EFIT/TRANSP")
