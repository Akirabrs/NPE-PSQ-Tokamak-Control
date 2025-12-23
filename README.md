# ⚛️ NPE-PSQ: Neural Predictive Engine for Tokamak Stabilization

O **NPE-PSQ** é uma arquitetura de simulação e controlo de alta fidelidade para reatores de fusão nuclear (Tokamaks). O projeto foca-se na estabilização de instabilidades plasmáticas não-lineares através de Controlo Preditivo Baseado em Modelos (MPC) e Redes Neurais Adaptativas.

### 🌟 Destaques do Projeto
* [cite_start]**Validação Científica:** Validado contra o simulador **TRANSP** da Universidade de Princeton, atingindo desvios inferiores a 3% em parâmetros críticos como o tempo de confinamento de energia ($\tau_E$) e potência de fusão [cite: 16, 236-241, 273].
* [cite_start]**Controlo Preditivo (MPC):** Implementação de otimização via programação quadrática (QP) para gestão de restrições em tempo real[cite: 14, 160].
* **IA Adaptativa:** Utilização de um Estimador Neural Adaptativo (LSTM) para correção online da dinâmica do plasma.
* [cite_start]**Integração Numérica:** Implementação de RK4 com passo de tempo adaptativo para garantir estabilidade MHD[cite: 15, 197, 210].

### 📁 Estrutura de Pastas
* `/ia`: Simuladores de física e lógica do estimador neural.
* [cite_start]`/docs`: Artigo científico completo e gráficos de validação[cite: 5, 10, 524].

> [cite_start]**Nota de Metodologia:** O desenvolvimento deste projeto utilizou ferramentas de IA para aceleração de prototipagem e otimização de código, com toda a validação física e análise de dados conduzida manualmente pelo autor[cite: 682].
