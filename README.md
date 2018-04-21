This repository provides all source code for simulations and experiments for the paper "[Shrewd Selection Speeds Surfing: Use Smart EXP3](https://arxiv.org/abs/1712.03038)".

You will find source code to perform the following:
* Simulation in static and dynamic settings.
* Trace-driven simulation.
* Controlled experiment.
* In-the-wild experiment.
* Measure delay observed when switching between networks and identify the probability distribution that best fits the delay values.

## Brief overview of SmartEXP3
The wireless network selection problem is formulated as a congestion game and the behavior of devices modeled using online learning in the adversarial bandit setting. Smart EXP3 is a wireless network selection algorithm that has good theoretical and practical performance. Empirical results show that it gracefully deals with transient behaviors, has relatively fast convergence to the optimal network with reduced switching, and achieves fairness among devices. It has the same convergence and regret properties as EXP3, a standard bandit algorithm.

## Note: The code is not optimized and this repository will not be maintained.
