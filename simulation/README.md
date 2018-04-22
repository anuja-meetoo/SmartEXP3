Simulates the selection of wireless networks by time-synchroized devices in the following settings: 
* A static setting where all devices start the algorithm at the same time and have access to the same set of wireless networks (static_setting directory).
* A dynamic setting where all devices have access to the same set of wireless networks, but some devices enter the service area later and leave earlier than the others (dynamic_settings directory).
* A dynamic setting setting where  all devices have access to the same set of wireless networks, but some devices leave the service area earlier than others (dynamic_settings directory).
* A dynamic setting where devices move across service areas discovering new sets of wireless networks, thus devices may have access to a different set of wireless networks at one point in time (mobility_setting directory). 
* A static setting where all devices start the algorithm at the same time and have access to the same set of wireless networks, but some devices use Smart EXP3 while others leverage a greedy policy.

It is assumed that all clients observe an equal share of a network's bandwidth. The cost of switching networks is measured in terms of delay and is modeled using Johnson's SU distribution for WiFi and Student's t-distribution for cellular, each identified as a best fit to 500 delay values.

# Running the simulation
1. Set the values of the following parameters in the file simulation.py:
   * number of active devices (numUser).
   * number of wireless networks in the service area (numNetwork).
   * total bandwith of each of the wireless networks, separated by an underscore, e.g. "4_7_22" (networkDataRate).
   * number of simualtion runs to execute (numRun).
   
numUser=20
numNetwork=3
networkDataRate="4_7_22"	#"11_11_11"
numRun=100 #25
numParallelRun=5 #20
timeStepDuration=15
maxNumIteration =1200
beta=0.1
gainScale=1
maxTimeStepPrevBlock=8
saveMinimalDetail=1

NElistStr="2,4,14" #"6,7,7;7,6,7;7,7,6"
epsilonEquilibriumListStr="0"
convergedProb=0.75
epsilon=7.5

2. Execute the program by typing './simulation.py' or the command 'python3 simulation.py'.


20 users 5 networks
NE when: [(1, 2, 7, 5, 5)]
Epsilon equilibrium when: [(1, 2, 7, 6, 4), (1, 2, 8, 5, 4)]

20 users 7 networks
NE when: [(1, 1, 5, 4, 3, 2, 4)]
Epsilon equilibrium when: []
