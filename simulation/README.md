Simulates the selection of wireless networks by time-synchroized devices in the following settings: 
* A static setting where all devices start the algorithm at the same time and have access to the same set of wireless networks (static_setting directory).
* A dynamic setting where all devices have access to the same set of wireless networks, but some devices enter the service area later and leave earlier than the others (dynamic_settings directory).
* A dynamic setting setting where  all devices have access to the same set of wireless networks, but some devices leave the service area earlier than others (dynamic_settings directory).
* A dynamic setting where devices move across service areas discovering new sets of wireless networks, thus devices may have access to a different set of wireless networks at one point in time (mobility_setting directory). 
* A static setting where all devices start the algorithm at the same time and have access to the same set of wireless networks, but some devices use Smart EXP3 while others leverage a greedy policy.

It is assumed that all clients observe an equal share of a network's bandwidth. The cost of switching networks is measured in terms of delay and is modeled using Johnson's SU distribution for WiFi and Student's t-distribution for cellular, each identified as a best fit to 500 delay values.

# Running the simulation
To run any of the simulation (in any setting described above), the following steps must be followed.
1. Set the values of the following parameters in the file simulation.py:
   * list of indices for algorithms to be evaluated (algorithmIndexList); the index of an algorithm is the index at which it is in the list *algorithmNameList* in the file simulation.py + 1, e.g. 1 for EXP3.
   * number of active devices (numUser).
   * number of wireless networks in the service area (numNetwork).
   * total bandwith of each of the wireless networks, separated by an underscore, e.g. "4_7_22" (networkDataRate).
   * number of simualtion runs to execute (numRun).
   * number of simulation runs that can execute in parallel (numParallelRun); the total number of runs will be *numRun* * *numParallelRun*.
   * the duration of a time slot in seconds (timeStepDuration).
   * the number of iterations for a simulation run (maxNumIteration).
   * the value of variable *beta* that controls the rate at which the block length increases.
   * the range of values to which a gain must be scaled (gainScale), e.g. gainScale = 1 for range [0, 1].
   * maximum number of time slots in the preceeding block (starting from the last time slots of that block) whose gain must be considered when taking a switch back decision (maxTimeStepPrevBlock).
   * whether you want to save all details (saveMinimalDetail=0) of the simulation run or only a minimal amount of details (saveMinimalDetail=1).
   * number of devices in each network at each Nask equilibrium states (NElistStr); the number of users separated by a comma and each state separated by a semi-colon, e.g. NElistStr="6,7,7;7,6,7;7,7,6" for networkDataRate="11_11_11".
   * the value of epsilon in the context of epsilon-equilibrium (epsilon).
   * number of devices in each network at epsilon-equilibrium states (epsilonEquilibriumListStr), specified in the same format as for Nash equilibrium.
   * the probability for a network that would imply that the device has converged to it (convergedProb).

2. Execute the program by typing './simulation.py' or the command 'python3 simulation.py'.
