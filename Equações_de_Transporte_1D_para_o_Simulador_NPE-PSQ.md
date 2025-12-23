# Equações de Transporte 1D para o Simulador NPE-PSQ

## 1. Introdução

Este documento define o modelo físico 1D para o simulador NPE-PSQ, que resolve as equações de transporte radial de energia e partículas em um tokamak. O modelo 1D representa um avanço significativo em relação ao modelo 0D, pois captura a **estrutura espacial dos perfis de temperatura e densidade** no plasma.

## 2. Coordenadas e Geometria

### 2.1 Coordenada Radial

Utilizamos a **coordenada de fluxo normalizada** ρ (rho) como variável espacial:

$$\rho = \sqrt{\frac{\Psi - \Psi_0}{\Psi_a - \Psi_0}}$$

onde:
- Ψ é o fluxo poloidal magnético
- Ψ₀ é o fluxo no eixo magnético (centro)
- Ψₐ é o fluxo na borda do plasma

**Propriedades:**
- ρ = 0 no centro do plasma (eixo magnético)
- ρ = 1 na borda do plasma (LCFS - Last Closed Flux Surface)
- ρ é monotônico e facilita a discretização numérica

### 2.2 Geometria Toroidal

Para um tokamak com seção circular:
- Raio maior: R₀ = 6.2 m
- Raio menor: a = 2.0 m
- Razão de aspecto: ε = a/R₀ = 0.323
- Volume: V(ρ) = 2π²R₀a²ρ²

## 3. Equações de Transporte

### 3.1 Equação de Energia dos Elétrons

A evolução temporal da temperatura dos elétrons Tₑ(ρ,t) é governada pela equação de difusão:

$$\frac{3}{2} n_e \frac{\partial T_e}{\partial t} = \frac{1}{V'} \frac{\partial}{\partial \rho} \left( V' n_e \chi_e \frac{\partial T_e}{\partial \rho} \right) + Q_e$$

onde:
- **nₑ**: densidade eletrônica [10²⁰ m⁻³]
- **Tₑ**: temperatura eletrônica [keV]
- **χₑ**: difusividade térmica eletrônica [m²/s]
- **V'**: derivada do volume em relação a ρ
- **Qₑ**: termo fonte de aquecimento [MW/m³]

### 3.2 Equação de Energia dos Íons

Similarmente, para a temperatura dos íons Tᵢ(ρ,t):

$$\frac{3}{2} n_i \frac{\partial T_i}{\partial t} = \frac{1}{V'} \frac{\partial}{\partial \rho} \left( V' n_i \chi_i \frac{\partial T_i}{\partial \rho} \right) + Q_i + Q_{ei}$$

onde:
- **χᵢ**: difusividade térmica iônica [m²/s]
- **Qᵢ**: aquecimento iônico (NBI, ICRH) [MW/m³]
- **Qₑᵢ**: transferência colisional elétron-íon [MW/m³]

### 3.3 Equação de Densidade

A evolução da densidade eletrônica nₑ(ρ,t):

$$\frac{\partial n_e}{\partial t} = \frac{1}{V'} \frac{\partial}{\partial \rho} \left( V' D \frac{\partial n_e}{\partial \rho} \right) + S_n$$

onde:
- **D**: coeficiente de difusão de partículas [m²/s]
- **Sₙ**: fonte de partículas (fueling, NBI) [10²⁰ m⁻³/s]

## 4. Coeficientes de Transporte

### 4.1 Modelo de Transporte Neoclássico + Anômalo

Os coeficientes de transporte são decompostos em:

$$\chi_e = \chi_e^{neo} + \chi_e^{anom}$$
$$\chi_i = \chi_i^{neo} + \chi_i^{anom}$$
$$D = D^{neo} + D^{anom}$$

### 4.2 Transporte Neoclássico

Baseado na teoria de colisões:

$$\chi_e^{neo} = \frac{q^2 R_0}{\tau_e} \left( \frac{r}{R_0} \right)^{3/2}$$

onde:
- **q**: fator de segurança
- **τₑ**: tempo de colisão elétron-íon

### 4.3 Transporte Anômalo (Modelo Bohm-gyro-Bohm)

Modelo empírico baseado em dados experimentais:

$$\chi_e^{anom} = F_e \times \chi_{gB}$$
$$\chi_i^{anom} = F_i \times \chi_{gB}$$

onde:

$$\chi_{gB} = \frac{\rho_i^2 c_s}{a}$$

com:
- **ρᵢ**: raio de Larmor iônico
- **cₛ**: velocidade do som
- **Fₑ, Fᵢ**: fatores multiplicativos (tipicamente 0.5-2.0)

### 4.4 Modelo ITG/TEM (Instabilidades de Microescala)

Para maior fidelidade, podemos usar modelos de turbulência:

$$\chi_e^{anom} = C_{TEM} \left( \frac{R}{L_{T_e}} \right)^{\alpha} \chi_{gB}$$
$$\chi_i^{anom} = C_{ITG} \left( \frac{R}{L_{T_i}} \right)^{\beta} \chi_{gB}$$

onde:
- **R/Lₜ**: gradiente normalizado de temperatura (drive da instabilidade)
- **α, β**: expoentes (tipicamente 1.5-3.0)

## 5. Termos Fonte

### 5.1 Aquecimento por ECRH

O ECRH (Electron Cyclotron Resonance Heating) deposita energia nos elétrons de forma localizada:

$$Q_{ECRH}(\rho) = \frac{P_{ECRH}}{\sqrt{2\pi} \sigma_{ECRH}} \exp\left( -\frac{(\rho - \rho_{ECRH})^2}{2\sigma_{ECRH}^2} \right)$$

onde:
- **P_ECRH**: potência total [MW]
- **ρ_ECRH**: posição radial de deposição (tipicamente 0.3-0.5)
- **σ_ECRH**: largura da deposição (tipicamente 0.1-0.2)

### 5.2 Aquecimento por ICRH

O ICRH (Ion Cyclotron Resonance Heating) aquece íons:

$$Q_{ICRH}(\rho) = \frac{P_{ICRH}}{\sqrt{2\pi} \sigma_{ICRH}} \exp\left( -\frac{(\rho - \rho_{ICRH})^2}{2\sigma_{ICRH}^2} \right)$$

### 5.3 Aquecimento por NBI

O NBI (Neutral Beam Injection) deposita energia em ambos (elétrons e íons):

$$Q_{NBI,e}(\rho) = f_e \times P_{NBI} \times \text{Profile}(\rho)$$
$$Q_{NBI,i}(\rho) = f_i \times P_{NBI} \times \text{Profile}(\rho)$$

onde:
- **fₑ**: fração de energia para elétrons (tipicamente 0.3)
- **fᵢ**: fração de energia para íons (tipicamente 0.7)

Perfil de deposição:

$$\text{Profile}(\rho) = \frac{1 - \rho^2}{1 + \rho^2}$$

### 5.4 Aquecimento Ôhmico

$$Q_{Ohm}(\rho) = \eta_{||} j_\phi^2$$

onde:
- **η_∥**: resistividade paralela
- **j_φ**: densidade de corrente toroidal

### 5.5 Aquecimento por Fusão (Partículas Alfa)

$$Q_\alpha(\rho) = P_{fusion}(\rho) \times (1 - f_{loss})$$

onde:

$$P_{fusion}(\rho) = \frac{n_e^2}{4} \langle \sigma v \rangle_{DT} E_\alpha$$

com:
- **⟨σv⟩_DT**: reatividade de fusão D-T
- **E_α**: energia das partículas alfa (3.5 MeV)

### 5.6 Transferência Colisional Elétron-Íon

$$Q_{ei}(\rho) = \frac{3 m_e n_e}{\tau_e} (T_i - T_e)$$

onde:
- **τₑ**: tempo de colisão elétron-íon

## 6. Condições de Contorno

### 6.1 Centro do Plasma (ρ = 0)

Condição de simetria (derivada nula):

$$\frac{\partial T_e}{\partial \rho}\bigg|_{\rho=0} = 0$$
$$\frac{\partial T_i}{\partial \rho}\bigg|_{\rho=0} = 0$$
$$\frac{\partial n_e}{\partial \rho}\bigg|_{\rho=0} = 0$$

### 6.2 Borda do Plasma (ρ = 1)

Condições de Dirichlet (valores fixos):

$$T_e(\rho=1) = T_{e,edge} = 0.1 \text{ keV}$$
$$T_i(\rho=1) = T_{i,edge} = 0.1 \text{ keV}$$
$$n_e(\rho=1) = n_{e,edge} = 0.5 \times 10^{20} \text{ m}^{-3}$$

Alternativamente, podemos usar condições de Robin (mistas):

$$\chi_e \frac{\partial T_e}{\partial \rho}\bigg|_{\rho=1} = \alpha (T_e - T_{e,edge})$$

## 7. Discretização Espacial

### 7.1 Grade Radial

Utilizamos uma grade uniforme em ρ:

$$\rho_i = \frac{i-1}{N-1}, \quad i = 1, 2, ..., N$$

onde **N** é o número de pontos radiais (tipicamente 100-200).

### 7.2 Método das Diferenças Finitas

Para a derivada espacial, usamos diferenças finitas centradas:

$$\frac{\partial T_e}{\partial \rho}\bigg|_i \approx \frac{T_{e,i+1} - T_{e,i-1}}{2\Delta\rho}$$

$$\frac{\partial^2 T_e}{\partial \rho^2}\bigg|_i \approx \frac{T_{e,i+1} - 2T_{e,i} + T_{e,i-1}}{\Delta\rho^2}$$

### 7.3 Forma Discretizada da Equação de Transporte

Para cada ponto radial i:

$$\frac{3}{2} n_{e,i} \frac{dT_{e,i}}{dt} = \frac{1}{V'_i} \frac{1}{\Delta\rho} \left[ (V' n_e \chi_e)_{i+1/2} \frac{T_{e,i+1} - T_{e,i}}{\Delta\rho} - (V' n_e \chi_e)_{i-1/2} \frac{T_{e,i} - T_{e,i-1}}{\Delta\rho} \right] + Q_{e,i}$$

onde os índices fracionários (i±1/2) indicam valores interpolados nas interfaces da célula.

## 8. Integração Temporal

### 8.1 Método de Euler Implícito

Devido à natureza difusiva (stiff) das equações, usamos um método implícito:

$$\frac{T_e^{n+1} - T_e^n}{\Delta t} = F(T_e^{n+1}, T_i^{n+1}, n_e^{n+1})$$

Isso requer a solução de um sistema linear a cada passo de tempo.

### 8.2 Método de Crank-Nicolson

Para maior precisão, podemos usar o método de Crank-Nicolson (ordem 2):

$$\frac{T_e^{n+1} - T_e^n}{\Delta t} = \frac{1}{2} \left[ F(T_e^{n+1}) + F(T_e^n) \right]$$

## 9. Parâmetros Típicos

| Parâmetro | Valor | Unidade |
|-----------|-------|---------|
| Número de pontos radiais (N) | 100 | - |
| Passo de tempo (Δt) | 0.001-0.01 | s |
| Temperatura central (Tₑ₀) | 10-20 | keV |
| Densidade central (nₑ₀) | 10 | 10²⁰ m⁻³ |
| χₑ (típico) | 0.5-2.0 | m²/s |
| χᵢ (típico) | 1.0-5.0 | m²/s |
| D (típico) | 0.1-1.0 | m²/s |

## 10. Diagnósticos Derivados

### 10.1 Valores Médios Volumétricos

$$\langle T_e \rangle = \frac{\int_0^1 T_e(\rho) V'(\rho) d\rho}{\int_0^1 V'(\rho) d\rho}$$

### 10.2 Conteúdo de Energia

$$W_e = \frac{3}{2} \int_0^1 n_e(\rho) T_e(\rho) V'(\rho) d\rho$$

### 10.3 Tempo de Confinamento de Energia

$$\tau_E = \frac{W_e + W_i}{P_{heat} - P_{rad}}$$

### 10.4 Fator de Segurança q(ρ)

Para um tokamak circular:

$$q(\rho) = \frac{2\pi a^2 B_0}{R_0 \mu_0 I_p} \times \rho$$

onde:
- **B₀**: campo magnético toroidal
- **I_p**: corrente de plasma

### 10.5 Beta Normalizado

$$\beta_N = \frac{\beta}{I_p/(aB_0)} \times 100$$

onde:

$$\beta = \frac{2\mu_0 \langle p \rangle}{B_0^2}$$

## 11. Próximos Passos

1. **Implementar o solver de EDPs** usando diferenças finitas
2. **Validar o solver** com soluções analíticas simples
3. **Integrar com o sistema de controle NPE-PSQ**
4. **Comparar com resultados do modelo 0D**
5. **Validar com dados de códigos de referência (TRANSP, ASTRA)**

---

**Autor:** Sistema NPE-PSQ  
**Data:** Dezembro 2025  
**Versão:** 1.0
