'''
@description: Computes the mean and standard deviation of total user gain, user regret and number of network switches
Ref: https://pythonprogramming.net/threading-tutorial-python/
@output: 
    (1) csv file with the stable state, time to converge to the stable state and time spent at that state for each run 
    (2) txt file with the following: mean, sd, min and max user gain, regret and no of network switch
    (3) txt files with per user total gain, regret and total number of network switch
'''

import csv
from sys import argv
from math import sqrt
import time
from multiprocessing import Process, Lock, Manager
import os
from numpy import std

numUser = int(argv[1]) 
numNetwork = int(argv[2])
dir = argv[3]
MAX_NUM_ITERATION = int(argv[4])
numRun = int(argv[5])
numParallelRun = int(argv[6])
NElistStr = argv[7]                 # NE list is provided as a string with different NE states separated with a semi-colon (;) and number of users per network in one state with a comma (,)
epsilonEquilibriumListStr = argv[8] # epsilon equilibrium list is provided as a string with different states separated with a semi-colon (;) and number of users per network in one state with a comma (,)
convergedProb = float(argv[9])      # the correct number of users must favor the right networks with a prob of at least this value
print("converged prob:", convergedProb)
SAVE_MINIMAL_DETAIL = True if int(argv[10]) == 1 else 0

NElistStrSplit = NElistStr.split(";")
NElist = []
for NEstate in NElistStrSplit: NEstate = NEstate.split(","); NElist.append([int(x) for x in NEstate])

epsilonEquilibriumListStrSplit = epsilonEquilibriumListStr.split(";")
epsilonEquilibriumList = []
if len(epsilonEquilibriumListStrSplit) == numNetwork:
	for epsilonEquilibriumState in epsilonEquilibriumListStrSplit:
		epsilonEquilibriumState = epsilonEquilibriumState.split(","); 	
		epsilonEquilibriumList.append([int(x) for x in epsilonEquilibriumState])

print(">>> NE list: ", NElist)
print(">>> Epsilon equilibrium list: ", epsilonEquilibriumList)

outputDir = dir + "extractedData/"
if os.path.exists(outputDir) == False: os.makedirs(outputDir)
outputGainRegretNetSwitchFile = outputDir + "gainRegretSwitchFreq_meanSD.txt"
outputConvergenceFile = outputDir + "convergence_stability.csv"

def processSimulationData(task, userGainList, userRegretList, numNetSwitchList, stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, convergenceTimePerRunList, lock):
    findStableState(task, stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, lock)
    processGainRegretNetSwitchConvergence(task, userGainList, userRegretList, numNetSwitchList, stableStatePerRunList, convergenceTimePerRunList, lock)
    # end processSimulationData
    
def findStableState(task, stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, lock):
    ''' '''
    ''' stores a list of states and their count, and the number of times at NE and epsilon equilibrium state '''
    ''' determines the stable state for each run '''
    networkCSVfile = dir + "run_" + str(task) + "/network.csv"

    with open(networkCSVfile, newline='') as networkCSVfile:
        networkReader = csv.reader(networkCSVfile)
        count = 0
        stateList, stateCount = [], []

        for rowNetwork in networkReader:  
            if count != 0:
                runNum = int(rowNetwork[0])
                iterationNum = int(rowNetwork[1])
                state = [int(numUser) for numUser in rowNetwork[3: 3 + numNetwork]] # get the current state
                # update the count for the state
                if state not in stateList: stateList.append(state); stateCount.append(1) # state encountered for the first time in this run 
                else: index = stateList.index(state); stateCount[index] += 1                    # state already encountered in this run
                
                # if reached last iteration in current run
                if iterationNum == MAX_NUM_ITERATION:
                    # get the state with the maximum count
                    maxCount = max(stateCount); index = stateCount.index(maxCount); stableState = stateList[index]
                    with lock: stableStatePerRunList[(task - 1) * numRun + runNum-1] = stableState; stableStateCountPerRunList[(task - 1) * numRun + runNum-1] = maxCount

                    # store count for NE
                    for i in range(len(NElist)):
                        NE = NElist[i]
                        if NE in stateList: index = stateList.index(NE); countNE = stateCount[index]
                        else: countNE = 0                        
                        with lock:
                            tmpRow =  NECountPerRunList[(task - 1) * numRun + runNum-1]
                            tmpRow[i] = countNE
                            NECountPerRunList[(task - 1) * numRun + runNum-1] = tmpRow 
                        
                    # store count for epsilon-equilibrium
                    for i in range(len(epsilonEquilibriumList)):
                        epsilonEquilibrium = epsilonEquilibriumList[i]
                        if epsilonEquilibrium in stateList: index = stateList.index(epsilonEquilibrium); countEpsilon = stateCount[index]
                        else: countEpsilon = 0
                        with lock: 
                            tmpRow = epsilonCountPerRunList[(task - 1) * numRun + runNum-1]
                            tmpRow[i] = countEpsilon
                            epsilonCountPerRunList[(task - 1) * numRun + runNum-1] = tmpRow
                                                
                    stateList, stateCount = [], []
            count = count + 1
        networkCSVfile.close()
        print("stability --- done parallel task", task)        
        # end findStableState
        
def processGainRegretNetSwitchConvergence(task, userGainList, userRegretList, numNetSwitchList, stableStatePerRunList, convergenceTimePerRunList, lock):
    userGainList_proc, userRegretList_proc, numNetSwitchList_proc = [], [], []      # lists local to the process
    highestProbNetPerUserPerIterPerRunList_proc = []                                           # list local to the process

    ''' for each user, store the network with highest probability '''
    for i in range(numRun): # append a 2D list
        highestProbNetPerUserPerIter = []
        for k in range(MAX_NUM_ITERATION):
            highestProbNetPerUser = [0] * numUser
            highestProbNetPerUserPerIter.append(highestProbNetPerUser)
        highestProbNetPerUserPerIterPerRunList_proc.append(highestProbNetPerUserPerIter)
    
    fileDir = dir + "run_" + str(task) + "/"

    for i in range(numUser):
        userCSVfile = fileDir + "user" + str(i + 1) + ".csv"
        
        with open(userCSVfile, newline='') as userCSVfile:
            userReader = csv.reader(userCSVfile)
            count = 0   # to skip the header of the file

            # variables to be initialized at the beginning of every run
            prevNetwork = -1    # to differentiate between a switch and initially joining a network
            totalExpertGain = [0] * numNetwork
            totalUserGain = totalUserGain_fromSecondTimeSlot = totalNumNetSwitch = 0

            for rowUser in userReader:  
                if count != 0:
                    runNum = int(rowUser[0])
                    iterationNum = int(rowUser[1])

                    # user gain
                    if SAVE_MINIMAL_DETAIL == True:
                        gain = float(rowUser[4 + (2 * numNetwork)])
                        # compute total expert gain
                        if iterationNum > 1:
                            for netIndex in range(numNetwork): totalExpertGain[netIndex] += float(rowUser[6 + (2 * numNetwork) + netIndex])
                        currentNetwork = int(rowUser[2 + (2 * numNetwork)])
                        probPerNet = [float(numUser) for numUser in rowUser[2 + numNetwork: 2 + 2* numNetwork]] # get the current prob distribution
                    else:
                        gain = float(rowUser[7 + (2 * numNetwork)])
                        # compute total expert gain
                        if iterationNum > 1:
                            for netIndex in range(numNetwork): totalExpertGain[netIndex] += float(rowUser[12 + (2 * numNetwork) + netIndex])
                        currentNetwork = int(rowUser[4 + (2 * numNetwork)])
                        probPerNet = [float(numUser) for numUser in rowUser[4 + numNetwork: 4 + 2* numNetwork]] # get the current prob distribution
                    totalUserGain += gain
                    if iterationNum > 1: totalUserGain_fromSecondTimeSlot += gain

                    highestProb = max(probPerNet)
                    if highestProb >= convergedProb: highestProbNet = probPerNet.index(highestProb) + 1; highestProbNetPerUserPerIterPerRunList_proc[runNum - 1][iterationNum - 1][i] = highestProbNet
                    else: highestProbNetPerUserPerIterPerRunList_proc[runNum - 1][iterationNum - 1][i] = -1

                    if prevNetwork != -1 and prevNetwork != currentNetwork: totalNumNetSwitch += 1
                    prevNetwork = currentNetwork

                    # at end of a run; reset the total expert gain and compute user regret for current run
                    if(iterationNum == MAX_NUM_ITERATION):
                        userGainList_proc.append(totalUserGain)
                        userRegretList_proc.append(max(totalExpertGain) - totalUserGain_fromSecondTimeSlot)
                        numNetSwitchList_proc.append(totalNumNetSwitch)

                        prevNetwork = -1    # to differentiate between a switch and initially joining a network
                        totalExpertGain = [0] * numNetwork
                        totalUserGain = totalUserGain_fromSecondTimeSlot = totalNumNetSwitch = 0
                count +=1
        print("done user", (i + 1))
        userCSVfile.close()

    with lock: userGainList += userGainList_proc;
    with lock: userRegretList += userRegretList_proc
    with lock: numNetSwitchList += numNetSwitchList_proc
    
    for i in range(numRun):
        state = stableStatePerRunList[(task - 1) * numRun + i]
        for k in range(MAX_NUM_ITERATION):
            favoredNetPerUserPerIter = highestProbNetPerUserPerIterPerRunList_proc[i][k] # retrieve a row of networks favored by each user in the current iteration of the current run
            converged = True
            for n in range(numNetwork):
                if favoredNetPerUserPerIter.count(n+1) != state[n]: 
                    converged = False
                    if convergenceTimePerRunList[(task - 1) * numRun + i] != -1: 
                        with lock: convergenceTimePerRunList[(task - 1) * numRun + i] = -1
            if converged == True and convergenceTimePerRunList[(task - 1) * numRun + i] == -1:
                with lock: convergenceTimePerRunList[(task - 1) * numRun + i] = k + 1 # k + 1 refers to the current iteration
                #break # no need to look at remaining iterations for the current run    
    print("gain_regret_netSwitch_convergence --- done parallel task -", task)
    # save processGainRegretNetSwitchConvergence
    
def saveGainRegretNetSwitch(userGainList, userRegretList, numNetSwitchList):
    # compute mean
    meanUserGain = sum(userGainList)/len(userGainList); minUserGain = min(userGainList); maxUserGain = max(userGainList)
    meanUserRegret = sum(userRegretList)/len(userRegretList); minUserRegret = min(userRegretList); maxUserRegret = max(userRegretList)
    meanNumNetSwitch = sum(numNetSwitchList)/len(numNetSwitchList); minNumNetSwitch = min(numNetSwitchList); maxNumNetSwitch = max(numNetSwitchList)
    
    # compute sd
    userGainSubMeanSqr = [(gain - meanUserGain)** 2 for gain in userGainList]
    userRegretSubMeanSqr = [(regret - meanUserRegret)** 2 for regret in userRegretList]
    numNetSwitchSubMeanSqr = [(numSwitch - meanNumNetSwitch)** 2 for numSwitch in numNetSwitchList]
    sdUserGain = sqrt(sum(userGainSubMeanSqr)/len(userGainSubMeanSqr))
    sdUserRegret = sqrt(sum(userRegretSubMeanSqr)/len(userRegretSubMeanSqr))
    sdNumNetSwitch= sqrt(sum(numNetSwitchSubMeanSqr)/len(numNetSwitchSubMeanSqr))
    
    file = open(outputGainRegretNetSwitchFile, "w")
    file.write("Mean user gain: " + str(meanUserGain) + "\n")
    file.write("SD user gain: " + str(std(userGainList)) + "\n")
    file.write("Min user gain: " + str(minUserGain) + "\n")
    file.write("Max user gain: " + str(maxUserGain)  + "\n\n")
    
    file.write("Mean user regret: " + str(meanUserRegret) + "\n")
    file.write("SD user regret: " + str(std(userRegretList)) + "\n")
    file.write("Min user regret: " + str(minUserRegret) + "\n")
    file.write("Max user regret: " + str(maxUserRegret)  + "\n\n")
    
    file.write("% average gain compared to best expert: " + str((meanUserGain * 100)/(meanUserGain + meanUserRegret))  + "\n\n")
    
    file.write("Mean network switch: " + str(meanNumNetSwitch) + "\n")
    file.write("SD network switch: " + str(std(numNetSwitchList)) + "\n")
    file.write("Min no of network switch: " + str(minNumNetSwitch) + "\n")
    file.write("Max no of network switch: " + str(maxNumNetSwitch) + "\n")
    file.close()    
    # end saveGainRegretNetSwitch

def saveStabilityConvergence(stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, convergenceTimePerRunList):
    # saving data to csv file
    outfile = open(outputConvergenceFile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
    
    # add header to output file
    rowData = ["Run no.", "Stable state", "No of iterations at stable state", " No of iterations at NE"]
    for i in range(len(NElist) - 1): rowData.append("")
    if len(epsilonEquilibriumList) > 0:
        rowData.append("No of iterations at epsilon-equilibrium")
        for i in range(len(epsilonEquilibriumList) - 1): rowData.append("")
    rowData += ["Time for prob distribution to converge to stable state (prob >= " + str(convergedProb) + ")", "Stable state is NE", "Stable state is epsilon-equilibrium (incl NE)", "Stable state is neither NE nor epsilon equilibrium"]
    out.writerow(rowData)
    
    rowData = ["", "", ""]
    for NE in NElist: rowData.append(NE)
    for epsilonEquilibrium in epsilonEquilibriumList: rowData.append(epsilonEquilibrium)
    rowData.append("")
    out.writerow(rowData)
    
    # data to output file
    for i in range(len(stableStatePerRunList)):
        rowData = [(i + 1), stableStatePerRunList[i], stableStateCountPerRunList[i]]
        for j in range(len(NElist)): rowData.append(NECountPerRunList[i][j])
        for j in range(len(epsilonEquilibriumList)): rowData.append(epsilonCountPerRunList[i][j])
        rowData.append(convergenceTimePerRunList[i])
        rowData.append(1 if stableStatePerRunList[i] in NElist else 0)
        rowData.append(1 if (stableStatePerRunList[i] in NElist or stableStatePerRunList[i] in epsilonEquilibriumList) else 0)
        rowData.append(1 if ((stableStatePerRunList[i] not in NElist) and (stableStatePerRunList[i] not in epsilonEquilibriumList)) else 0)
        out.writerow(rowData)
    outfile.close()
    # end saveStabilityConvergence
    
# main program 
manager = Manager()
# for user gain, regret and number of network switch
userGainList = manager.list()
userRegretList = manager.list()
numNetSwitchList = manager.list()
# for stability
stableStatePerRunList = manager.list() 
for i in range(numParallelRun * numRun): stableStatePerRunList.append([])           # store the stable states for each run
stableStateCountPerRunList = manager.list()
for i in range(numParallelRun * numRun): stableStateCountPerRunList.append(0)   # store the number of iterations with the stable state for each run
NECountPerRunList = manager.list()
epsilonCountPerRunList = manager.list()
if len(NElist) > 0: 
    for i in range(numParallelRun * numRun): NECountPerRunList.append([0] * len(NElist)) # store the number of iterations in NE for each run; can have multiple NE
if len(epsilonEquilibriumList) > 0: 
    for i in range(numParallelRun * numRun): epsilonCountPerRunList.append([0] * len(epsilonEquilibriumList)) # store the number of iterations in epsilon-equilibrium for each run; can have multiple epsilon-equilibrium  

# for convergence
convergenceTimePerRunList = manager.list()
for i in range(numParallelRun * numRun): convergenceTimePerRunList.append(-1)        # store the time at which the algorithm converged to the stable state in each run
 
lock = Lock()

procs = [Process(target=processSimulationData, args=(i, userGainList, userRegretList, numNetSwitchList, stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, convergenceTimePerRunList, lock)) for i in range(1, numParallelRun + 1)]

start = time.time()
for p in procs: p.start()
for p in procs: p.join()

fileOpen = open(outputDir + "perClientGain.txt", 'w')
fileOpen.write(str(userGainList)[1:-1].replace(", ", "\n"))
fileOpen.close()

fileOpen = open(outputDir + "perClientRegret.txt", 'w')
fileOpen.write(str(userRegretList)[1:-1].replace(", ", "\n"))
fileOpen.close()

fileOpen = open(outputDir + "perClientNumNetSwitch.txt", 'w')
fileOpen.write(str(numNetSwitchList)[1:-1].replace(", ", "\n"))
fileOpen.close()
#print("userGainList:", userGainList)
#print("userRegretList: ", userRegretList)
#print("numNetSwitchList: ", numNetSwitchList)
    
saveGainRegretNetSwitch(userGainList, userRegretList, numNetSwitchList)
saveStabilityConvergence(stableStatePerRunList, stableStateCountPerRunList, NECountPerRunList, epsilonCountPerRunList, convergenceTimePerRunList) 
print('Entire job took:',(time.time() - start)/60, "mins")

# 40 users, 3 networks
# NElist = [[7, 12, 21]]
# epsilonEquilibriumList = [[6, 12, 22], [6, 13, 21], [7, 11, 22], [7, 13, 20]]

# 80 users, 3 networks
#NElist = [[13, 25, 42]]
#epsilonEquilibriumList = [[12, 25, 43], [13, 23, 44], [13, 24, 43], [13, 26, 41], [14, 23, 43], [14, 24, 42], [14, 25, 41]]

# 160 users, 3 networks
#NElist = [[27, 49, 84]]
#epsilonEquilibriumList = [[25, 49, 86], [25, 50, 85], [26, 47, 87], [26, 48, 86], [26, 49, 85], [26, 50, 84], [26, 51, 83], [26, 52, 82], [27, 47, 86], [27, 48, 85], [27, 50, 83], [27, 51, 82], [28, 47, 85], [28, 48, 84], [28, 49, 83], [28, 50, 82], [28, 51, 81], [29, 48, 83]]
### 20 users
# 2 networks with bandwidth [27, 49]
#NElist = [[7, 13]]
#epsilonEquilibriumList = []

# 2 networks with bandwidth [27, 49, 84, 19]
#NElist = [[7, 13]]
#epsilonEquilibriumList =[]

# 3 networks with bandwidth [27, 49, 84]
# NElist = [[3, 6, 11]]
# epsilonEquilibriumList =[]

#4 networks
#NElist = [[3, 5, 10, 2]]
#epsilonEquilibriumList = [[3, 6, 9, 2]]

# 5 networks with bandwidth [27, 49, 84, 19, 16]
#NElist = [[3, 5, 9, 2, 1]]
#epsilonEquilibriumList = [[2, 5, 10, 2, 1]]

# 8 networks
#NElist = [[2, 3, 6, 1, 1, 1, 4, 2]]
#epsilonEquilibriumList = [[1, 3, 6, 1, 1, 2, 4, 2], [2, 3, 6, 1, 1, 2, 3, 2]]

# 10 networks
#NElist = [[1, 2, 5, 1, 0, 1, 3, 1, 4, 2]]
#epsilonEquilibriumList = [[1, 2, 4, 1, 0, 1, 3, 1, 4, 3], [1, 2, 4, 1, 1, 1, 3, 1, 4, 2], [1, 3, 4, 1, 0, 1, 3, 1, 4, 2], [1, 3, 5, 1, 0, 1, 3, 1, 3, 2]]

# 16 networks
#NElist = [[1, 1, 3, 0, 0, 0, 2, 1, 2, 1, 3, 3, 1, 1, 1, 0]]
#epsilonEquilibriumList = [[0, 1, 3, 0, 0, 0, 1, 1, 2, 2, 3, 3, 2, 1, 1, 0], [0, 1, 3, 0, 0, 0, 2, 1, 2, 1, 3, 3, 2, 1, 1, 0], [0, 1, 3, 0, 0, 0, 2, 1, 2, 2, 3, 3, 1, 1, 1, 0], [0, 1, 3, 0, 0, 0, 2, 1, 2, 2, 3, 3, 2, 0, 1, 0], [0, 1, 3, 0, 0, 1, 1, 1, 2, 1, 3, 3, 2, 1, 1, 0], [0, 1, 3, 0, 0, 1, 1, 1, 2, 2, 3, 3, 1, 1, 1, 0], [0, 1, 3, 0, 0, 1, 1, 1, 2, 2, 3, 3, 2, 0, 1, 0], [0, 1, 3, 0, 0, 1, 2, 1, 2, 1, 3, 3, 1, 1, 1, 0], [0, 1, 3, 0, 0, 1, 2, 1, 2, 1, 3, 3, 2, 0, 1, 0], [0, 1, 3, 0, 0, 1, 2, 1, 2, 2, 3, 3, 1, 0, 1, 0], [1, 1, 3, 0, 0, 0, 1, 1, 2, 1, 3, 3, 2, 1, 1, 0], [1, 1, 3, 0, 0, 0, 1, 1, 2, 1, 3, 4, 1, 1, 1, 0], [1, 1, 3, 0, 0, 0, 1, 1, 2, 2, 3, 3, 1, 1, 1, 0], [1, 1, 3, 0, 0, 0, 1, 1, 2, 2, 3, 3, 2, 0, 1, 0], [1, 1, 3, 0, 0, 0, 2, 1, 2, 1, 3, 3, 2, 0, 1, 0], [1, 1, 3, 0, 0, 0, 2, 1, 2, 2, 3, 3, 1, 0, 1, 0], [1, 1, 3, 0, 0, 1, 1, 1, 2, 1, 3, 3, 1, 1, 1, 0], [1, 1, 3, 0, 0, 1, 1, 1, 2, 1, 3, 3, 2, 0, 1, 0], [1, 1, 3, 0, 0, 1, 1, 1, 2, 2, 3, 3, 1, 0, 1, 0], [1, 1, 3, 0, 0, 1, 2, 1, 2, 1, 3, 3, 1, 0, 1, 0]]

# 32 networks
#NElist = [[0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 2, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 2, 2, 1, 0, 0, 0]]
#epsilonEquilibriumList = []

# number of users = 3
# 3 networks with bandwidth [27, 49, 84]
#NElist = [[0, 1, 2]]
#epsilonEquilibriumList = []
