# NPE-PSQ: Neural Predictive Engine & Plasma Stability Quenching
### Advanced Tokamak Control Suite (Hybrid AI/Deterministic)

![Status](https://img.shields.io/badge/Status-Prototype-yellow)
![Platform](https://img.shields.io/badge/Platform-Python%20%7C%20PyTorch%20%7C%20RaspberryPi-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **[PT]** Um sistema de controle de fusão nuclear híbrido que integra Redes Neurais Profundas para otimização de performance e Lógica Determinística (PSQ) para segurança crítica e mitigação de disrupções em tempo real.
>
> **[EN]** A hybrid nuclear fusion control suite integrating Deep Neural Networks for performance optimization and Deterministic Logic (PSQ) for critical safety and real-time disruption mitigation.

---

## 🏗 Architecture / Arquitetura

The system operates on a **Biomimetic Architecture** (Brain + Spine):

1.  **NPE (The Brain):** A Convolutional Neural Network (CNN) trained on 2D plasma profiles to optimize heating ($P_{aux}$) and vertical stability ($B_z$) in milliseconds.
2.  **PSQ (The Spine):** An Active Safety Interlock layer running on high-frequency loops (Simulated FPGA/Microcontroller). It enforces physical limits (Greenwald, Troyon) and overrides the AI to prevent structural damage.

![System Architecture](https://via.placeholder.com/800x400?text=Diagrama+Cerebro+Medula+Aqui)
*(Place your architecture diagram here / Coloque seu diagrama aqui)*

---

## 🚀 Key Features / Recursos Principais

* **⚡ 2D Plasma Physics Engine:**
    * Custom **ADI Solver (Alternating Direction Implicit)** for real-time heat transport simulation ($\chi \nabla^2 T$).
    * Full toroidal geometry support ($\kappa=1.7$, $\delta=0.33$).
* **🛡️ Active Mitigation (Not just SCRAM):**
    * Unlike traditional interlocks that shut down the reactor, PSQ attempts **Active Correction** (e.g., Vertical push back during VDEs) before triggering a shutdown.
* **🧠 JIT-Compiled Neural Control:**
    * PyTorch models optimized with **TorchScript** for near-C++ inference speed on embedded hardware (Raspberry Pi 5).
* **🔋 Hardware-in-the-Loop (HIL) Ready:**
    * Designed to interface with Arduino/STM32 for physical status visualization (Traffic Light Protocol).

---

## 📊 Simulation Results / Resultados

**Plasma Evolution (200ms Simulation):**
The system successfully stabilizes the plasma temperature at **15 keV** while maintaining safety margins.

![Simulation Graph](https://via.placeholder.com/800x400?text=Coloque+o+Print+do+Grafico+Aqui)
*(Insert your 'download (1).png' here)*

**2D Thermal Profile:**
Cross-section showing core confinement and edge gradients.

![2D Map](https://via.placeholder.com/400x400?text=Coloque+o+Ovo+de+Plasma+Aqui)
*(Insert your 'download.png' here)*

---

## 🛠️ Installation & Usage / Instalação

### Prerequisites
* Python 3.9+
* PyTorch, NumPy, Matplotlib

### Running the Simulator (Digital Twin)
```bash
# Clone the repository
git clone [https://github.com/SEU-USER/NPE-PSQ.git](https://github.com/SEU-USER/NPE-PSQ.git)

# Install dependencies
pip install -r requirements.txt

# Run the Firmware V1 (Simulation Mode)
python main_controller_v1.py
