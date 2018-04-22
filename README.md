This repository provides all source code for simulations and experiments for the paper "[Shrewd Selection Speeds Surfing: Use Smart EXP3](https://arxiv.org/abs/1712.03038)".

You will find source code to perform the following:
* Simulation in static and dynamic settings.
* Trace-driven simulation.
* Controlled experiment.
* In-the-wild experiment.
* Measure delay observed when switching between networks and identify the probability distribution that best fits the delay values.

## Brief overview of Smart EXP3
We formulate the wireless network selection problem as a repeated congestion game (in each round, each device chooses a network and receives some reward, i.e., bandwidth), and model the behavior of devices using online learning in the adversarial bandit setting. We propose Smart EXP3, a novel bandit-style algorithm that retains the good properties of EXP3 while addressing the issues that prevent it from achieving good performance in practice. From a theoretical perspective, we focus on the static version of the problem; in our experiments, we explore dynamic settings. There are a few key insights underlying Smart EXP3. The first observation is that we can minimize the cost of switching networks by using *adaptive blocking* techniques. The second observation is that we can speed up the rate of reaching a *stable state*
by carefully adding *initial exploration* and a *greedy policy*.  The third observation is that once the system is stable, we want to remain in a good state; we rely on a *switch-back* mechanism.  Finally, in a dynamic setting, a careful *minimal reset mechanism* is needed to ensure that the system adapts efficiently to changes.

## Note: The code is not optimized and this repository will not be maintained.
