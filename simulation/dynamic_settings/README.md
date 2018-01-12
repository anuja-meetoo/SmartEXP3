Simulates wireless network selection in a setting where devices are time-synchronized and have access to the same set of wireless networks. While some devices are in the service area throughout the experiment, others join and leave the area at different times. All devices leverage the same selection approach.

A brief description of the files is as follows:
* wns_dynamicEnc_setup1.py: Simulates the wireless network selection process using different algorithms in a setting where 9 devices join late and leave early; the run is divided into 3 phases of equal time; 9 devices (device IDs 12 - 20) join at the beginning of phase 2 and leave at the end that phase; some parameters for the algorithms are set in this file.
* wns_dynamicEnc_setup2.py: Simulates the wireless network selection process using different algorithms in a setting where all devices join at the beginning but some leave early; 16 devices (device IDs 5 - 20) leave at the middle of the run; some parameters for the algorithms are set in this file.
* simulation.py: Simulates the selection process and process the results to extract required information. To start the simulation, set the parameter values in this file and run the command 'python3 simulation.py'.
* experiments_parallel.sh: Creates the directories to store the simulation results and extrated details; then starts a set of experiments in parallel.
* experiment.sh: Executes a number of experiment runs in parallel.
* createCSVfile.py: Creates the csv files to save per iteration details corresponding to individual devices, number of devices per network (network.csv) and the iteration when the algorithm was first at Nash equilibrium (rateOfConvergence.csv), each with the appropriate headers; one file is created for each parallel run.
* processResults.sh: Processes the simulation results, and extracts and saves the required details; a copy of the latter is also saved in a separate folder 'dataRates_numUser_numNetwork_processedResult'.
* NetworkGraph.py: Used in determining which devices may switch network to reach a Nash equilibrium state when computing the distance to Nash equilibrium.
* computeDistanceToNE_dynamicEnv.py: Compute average per time slot distance to NE over all runs.
* extractNumNetworkSwitch_dynamic.py: Computes the total number of network switches per run for each stationary device.
