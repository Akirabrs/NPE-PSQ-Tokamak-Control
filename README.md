⚛️ NPE-PSQ: Neural Predictive Engine for Tokamak Stabilization
O NPE-PSQ é uma arquitetura de simulação e controle de alta fidelidade para reatores de fusão nuclear. O projeto foca na estabilização de instabilidades plasmáticas através de Controle Preditivo Baseado em Modelos (MPC) e Redes Neurais Adaptativas.
+4

🌟 Destaques do Projeto
* Validação Científica: Validado contra o simulador TRANSP (Princeton), atingindo desvios inferiores a 3% em parâmetros como o tempo de confinamento (τ 
E
​
 ) e potência de fusão .
+2

IA Adaptativa: Utilização de um Estimador Neural Adaptativo (LSTM) para correção online da dinâmica do plasma. * Controle de Precisão: Implementação de MPC com otimização via programação quadrática (QP).
+1

📁 Estrutura
/ia: Códigos do estimador neural e simuladores físicos. * /docs: Artigo científico completo e gráficos de validação.
+1

2. Para o Repositório: AION-1-FPGA-Safety
(Focado em Engenharia e Hardware para a FEBRACE)

🛡️ AION-1: Acelerador FPGA para Segurança de Fusão Nuclear
O AION-1 Alpha é um sistema de segurança crítica (Watchdog) baseado em hardware dedicado (FPGA). O foco é a proteção ultra-rápida contra disrupções plasmáticas.

🛠️ Especificações Técnicas
Latência de Hardware: Resposta determinística validada em 21 nanossegundos para disparo de segurança. * Protocolo PSQ: Sincronização de hardware que garante jitter inferior a 2 µs, superando sistemas operacionais convencionais.
+1

Validação RTL: Ciclo de controle testado e comprovado via simulação de hardware (Icarus Verilog).

📁 Estrutura
/hardware: Descrição de hardware em Verilog (RTL) e Testbenches.

/docs: Roadmap para FEBRACE e evidências de timing.
