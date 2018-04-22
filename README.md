This repository provides all source code for simulations and experiments for the paper "[Shrewd Selection Speeds Surfing: Use Smart EXP3](https://arxiv.org/abs/1712.03038)". 

Smart EXP3 is a novel bandit-style algorithm that (a) retains the good theoretical properties of EXP3, i.e. minimizing regret and converging to (weak) Nash equilibrium, (b) bounds the number of switches, and (c) yields significantly better performance in practice. It stabilizes at the optimal state, achieves fairness among devices and gracefully deals with transient behaviors. In real world experiments, it can achieve 18% faster download over alternate strategies.

You will find source code to perform each of the following:
* Simulation in static and dynamic settings.
* Trace-driven simulation.
* Controlled experiment.
* In-the-wild experiment.
* Measure delay observed when switching between networks and identify the probability distribution that best fits the delay values.

## Note: The code is not optimized and this repository will not be maintained.
