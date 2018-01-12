Simulates wireless network selection in a setting where devices are time-synchronized and are in the service area throughout the experiment. Devices have access to different sets of wireless networks, depending on their location. Some devices move and discover new sets of wireless networks. All devices leverage the same selection approach.

A brief description of the files is as follows:
* wns_mobility.py: Simulates the wireless network selection process using different algorithms; some parameters for the algorithms are set in this file.
* simulation.py: Simulates the selection process and process the results to extract required information. To start the simulation, set the parameter values in this file and run the command 'python3 simulation.py'.
* experiments_parallel.sh: Creates the directories to store the simulation results and extrated details; then starts a set of experiments in parallel.
* experiment.sh: Executes a number of experiment runs in parallel.
* createCSVfile.py: Creates the csv files to save per iteration details corresponding to individual devices, number of devices per network (network.csv) and the iteration when the algorithm was first at Nash equilibrium (rateOfConvergence.csv), each with the appropriate headers; one file is created for each parallel run.
* processResults.sh: Processes the simulation results, and extracts and saves the required details; a copy of the latter is also saved in a separate folder 'dataRates_numUser_numNetwork_processedResult'.
* NetworkGraph.py: Used in determining which devices may switch network to reach a Nash equilibrium state when computing the distance to Nash equilibrium.
* computeDistanceToNE_mobility.py: Compute average per time slot distance to NE over all runs for a specific set of devices during a specific time range (phase when the devices are temporarily stationary).
* extractNumNetworkSwitch_mobility.py: Computes the total number of network switches per run for each device (for each category separately as specified in the input; whether stationary or mobile devices).
