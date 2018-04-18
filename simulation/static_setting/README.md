Simulates wireless network selection in a static setting where time-synchronized devices are in the service area throughout the experiment and have access to the same set of wireless networks. All devices leverage the same selection approach.

# Running the simulation
1. Set the values of the following parameters in the file simulation.py:
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


# Brief description of files
A brief description of the files is as follows:
* wns.py: Simulates the wireless network selection process using different algorithms; some parameters for the algorithms are set in this file.
* simulation.py: Simulates the selection process and process the results to extract required information. To start the simulation, set the parameter values in this file and run the command 'python3 simulation.py'.
* experiments_parallel.sh: Creates the directories to store the simulation results and extrated details; then starts a set of experiments in parallel.
* experiment.sh: Executes a number of experiment runs in parallel.
* createCSVfile.py: Creates the csv files to save per iteration details corresponding to individual devices, number of devices per network (network.csv) and the iteration when the algorithm was first at Nash equilibrium (rateOfConvergence.csv), each with the appropriate headers; one file is created for each parallel run.
* processResults.sh: Processes the simulation results, and extracts and saves the required details; a copy of the latter is also saved in a separate folder 'dataRates_numUser_numNetwork_processedResult'.
* NetworkGraph.py: Used in determining which devices may switch network to reach a Nash equilibrium state when computing the distance to Nash equilibrium.
* processCSVfile_mean_sd_convergence_multiprocessing.py: Extracts and saves details pertaining to per run convergence, rate or convergence and stability; per device gain, regret and number of network switches.
* computeNumNetworkSwitchPerTimeStep.py: Computes the number of network switch per time step for every run; and on average over all runs.
* computeDistanceToNE.py: Compute average per time slot distance to NE over all runs.
* computeAverageGainRegretParallel.py: Calculates average gain and average regret of all devices per iteration across all runs.
* extractResetTimeSlot.py: Computes the minimum, maximum, average and median number of resets and extracts and outputs (in the proper format for pgfplot) the time slot at which there was a reset.
* extractLoss.py: Computes per run loss due to switching networks and unutilized network.
* combineDistanceToNE.py: Reads the distance to NE of each algorithm, compute their rolling average and save the later into a single CSV file; useful for plot.
* convergence_stability.py: Extracts the percentage runs that converged, percentage runs that converged to Nash equilibrium, and the percentage time a run spends at the converged state.
* entropy.py: Computes the per time slot entropy of a specific algorithm.
