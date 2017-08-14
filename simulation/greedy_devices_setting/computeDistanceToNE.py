'''
@date: 18 April 2016
@updated: 18 November 2016 - takes care of settigns with multiple NE states - then at each step it selects the NE state that will require the least number of users to move
@description: Computes distance to NE per time step for each run (individual files) as well over all runs (consolidated file) - in which case it is again the maximum
'''

import csv
from sys import argv
import os

numUser = int(argv[1])
numNetwork = int(argv[2])
dir = argv[3]
MAX_NUM_ITERATION = int(argv[4])
numRun = int(argv[5])
numParallelRun = int(argv[6])
networkBandwidth = argv[7].split("_"); networkBandwidth = [int(x) for x in networkBandwidth]
NElistStrSplit = argv[8].split(";")
NElist = []
for NEstate in NElistStrSplit: NEstate = NEstate.split(","); NElist.append([int(x) for x in NEstate])
epsilon = float(argv[9])    # epsilon = 7.5

DEBUG = 0   # 0 - no output; 1 - print details of computations; 2 - print details of computations and wait for user to press enter after each run is processed

outputDir = dir + "extractedData/"
if os.path.exists(outputDir) == False: os.makedirs(outputDir)

##### scenario 1 -  1 greedy and 19 smart EXP3
userCategory = "greedy"
userBeingConsideredList = [1]

# userCategory = "smartEXP3"
# userBeingConsideredList = [i for i in range(2, numUser + 1)]

##### scenario 2 - 10 greedy and 10 smart EXP3
# userCategory = "greedy"
# userBeingConsideredList = [i for i in range(1, numUser//2 + 1)]

# userCategory = "smartEXP3"
# userBeingConsideredList = [i for i in range(numUser//2 + 1, numUser + 1)]

##### scenario 3 - 19 greedy and 1 smart EXP3
# userCategory = "smartEXP3"
# userBeingConsideredList = [1]

# userCategory = "greedy"
# userBeingConsideredList = [i for i in range(2, numUser + 1)]

outputCSVfile_allRuns = outputDir + "distanceToNE_allRuns_" + userCategory + ".csv"

def computeDistanceToNE():
    distanceToNE_allRuns = [0] * MAX_NUM_ITERATION           # to store distance to NE per time steps (averaged over all runs)
    epsilonEquilibriumPoints = ""

    for j in range(numParallelRun): # runs 20 times in this case; in each iteration, 50 runs are processed
        distanceToNE_perRun = []       # to store distance to NE per time steps (for individual runs)
        for l in range(numRun): distanceToNE_perRun.append([0] * MAX_NUM_ITERATION)

        networkCSVfile = dir + "run_" + str(j + 1) + "/network.csv"
        with open(networkCSVfile, newline='') as networkCSVfile:
            networkReader = csv.reader(networkCSVfile)
            count = 0

            for rowNetwork in networkReader:  # compute total gain of user and that of each expert
                if count != 0:
                    runNum = int(rowNetwork[0])
                    iterationNum = int(rowNetwork[1])
                    numUserPerNet = []
                    for i in range(numNetwork): numUserPerNet.append(int(rowNetwork[3 + i])) # construct list with number of users per network

                    ####################
                    # construct list of users per network
                    userListPerNet = []
                    for i in range(numNetwork):
                        userListCurrentNet = []
                        userListCurrentNetStr = rowNetwork[5 + numNetwork + i]
                        if userListCurrentNetStr != "":
                            userListCurrentNetStrSplit = userListCurrentNetStr.split(",")
                            for ID in userListCurrentNetStrSplit: userListCurrentNet.append(int(ID))

                        userListPerNet.append(userListCurrentNet)
                    print("userListCurrentNet: ", userListPerNet)
                    ####################

                    # compute the distance from the current state to NE
                    if numUserPerNet in NElist: # current state is one of the NE state
                        distance = 0
                        if DEBUG >= 1: print("iteration", iterationNum, ", numUserPerNet: ", numUserPerNet, " --- NE")
                        # print("iteration", iterationNum, ", numUserPerNet: ", numUserPerNet, " --- NE")
                    else: # current state is not any of the NE state
                        distance = 0

                        ### compute sum of all additional bandwidth obtainable by the users by moving to NE state

                        # select the NE state to be considered based on the number of users to move from/to each network to reach each of the NE states
                        countNumUsersToMove = [] # number of users to move to reach each NE state
                        for NEstate in NElist:
                            numUserDiff = list(numUserAtNE - numUserAtPresent for numUserAtNE, numUserAtPresent in zip(NEstate, numUserPerNet))
                            countNumUsersToMove.append(sum(x for x in numUserDiff if x > 0))

                        minNumUsersToMove = min(countNumUsersToMove)
                        NEindex = countNumUsersToMove.index(minNumUsersToMove)
                        NE = NElist[NEindex]

                        numUserDiff = list(numUserAtNE - numUserAtPresent for numUserAtNE, numUserAtPresent in zip(NE, numUserPerNet))

                        if DEBUG >= 1: print("iteration", iterationNum, ", NE: ", NE, ", numUserPerNet: ", numUserPerNet, ", numUserDiff: ", numUserDiff)
                        # print("iteration", iterationNum, ", NE: ", NE, ", numUserPerNet: ", numUserPerNet, ", numUserDiff: ", numUserDiff)
                        # find all negative values in the list numUserDiff (that represent number of users to move away from the particular network)
                        index = 0
                        while index < len(numUserDiff):
                            if numUserDiff[index] < 0: # user need to move from the network
                                for n in range(len(numUserDiff)):
                                    if numUserDiff[n] > 0:
                                        numUsersToBeMoved = min(numUserDiff[n], abs(numUserDiff[index])) # no of users that can be moved to this network

                                        #################### users being moved from network (index + 1) to network (n + 1)
                                        usersToBeMovedList = userListPerNet[index][:numUsersToBeMoved]
                                        for user in usersToBeMovedList:
                                            userListPerNet[index].remove(user)
                                        ####################

                                        if DEBUG >= 1: print (numUsersToBeMoved, "users can be moved from network ", (index + 1), "to network", (n + 1))
                                        #distance += (numUsersToBeMoved * (NETWORK_BANDWIDTH[n]/NE[n] - NETWORK_BANDWIDTH[index]/numUserPerNet[index]))
                                        # distance is the highest % higher gain a user can observe in NE state compared to current state
                                        currentGain = networkBandwidth[index]/numUserPerNet[index]
                                        tmpDistance = ((networkBandwidth[n]/NE[n] - currentGain))*100/currentGain

                                        #################
                                        if any(user in userBeingConsideredList for user in usersToBeMovedList):
                                            print("moving users from", (index + 1), "to", (n + 1), ", users", usersToBeMovedList, "is being considered ----- tmpDistance = ", tmpDistance, "is being considered")
                                            if tmpDistance > distance: distance = tmpDistance
                                        else: print("users", usersToBeMovedList, "is not being considered ----- tmpDistance not being considered")
                                        #################
                                        # if tmpDistance > distance: distance = tmpDistance

                                        if DEBUG >= 1: print("tmpDistance = ", tmpDistance, "; distance = ", distance)
                                        # update the number of users to move in the 2 corresponding networks
                                        numUserDiff[index] += numUsersToBeMoved
                                        numUserDiff[n] -= numUsersToBeMoved
                                    if numUserDiff[index] == 0:
                                        if NE[index] != 0:
                                            #distance += (NE[index] * (NETWORK_BANDWIDTH[index]/NE[index] - NETWORK_BANDWIDTH[index]/numUserPerNet[index]))
                                            currentGain = networkBandwidth[index]/numUserPerNet[index]
                                            tmpDistance = ((networkBandwidth[index]/NE[index] - currentGain))*100/currentGain

                                            #################
                                            if any(user in userBeingConsideredList for user in userListPerNet[index]):
                                                print("for users left in network", index  + 1, ", tmpDistance = ", tmpDistance, "is being considered")
                                                if tmpDistance > distance: distance = tmpDistance
                                            else: print("users", userListPerNet[index], "is not being considered ----- tmpDistance not being considered")
                                            #################

                                            # if tmpDistance > distance: distance = tmpDistance
                                            if DEBUG >= 1: print("tmpDistance = ", tmpDistance, "; distance = ", distance)
                                        break
                            index += 1
                    if DEBUG >= 1: print("iteration", iterationNum, ", distance = ", distance)
                    distanceToNE_perRun[runNum - 1][iterationNum - 1] = distance
                    distanceToNE_allRuns[iterationNum - 1] += distance	### for average over runs
                    if DEBUG >= 2: input()
                count += 1
        print("done for parallel run", (j + 1))

        #savePerRunCSVfile((j + 1), distanceToNE_perRun)
    #for i in range(MAX_NUM_ITERATION):
	#distanceCurrentIteration = [x[i] for x in distanceToNE_perRun]
	#numIdistanceToNE_avgAllRuns[i] = max(distanceCurrentIteration)
    distanceToNE_allRuns = [distance/(numParallelRun * numRun) for distance in distanceToNE_allRuns]  # compute the average	### for average over runs
    for i in range(len(distanceToNE_allRuns)):
        if distanceToNE_allRuns[i] <= epsilon:
            if epsilonEquilibriumPoints == "": epsilonEquilibriumPoints += str(i + 1)
            else: epsilonEquilibriumPoints += "," + str(i + 1)

    return distanceToNE_allRuns, epsilonEquilibriumPoints

def savePerRunCSVfile(j, distanceToNE_perRun):
    for i in range(numRun):
        outputCSVfile_singleRun = outputDir + "distanceToNE_run" + str((j - 1) * numRun + (i + 1)) + ".csv"
        outfile = open(outputCSVfile_singleRun, "w")
        out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(["Time step", "Total % higher gain observable by a user"])
        for l in range(len(distanceToNE_perRun[i])): out.writerow([(l + 1), distanceToNE_perRun[i][l]])
        outfile.close()


distanceToNE_allRuns, epsilonEquilibriumPoints = computeDistanceToNE()

outfile = open(outputCSVfile_allRuns, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
out.writerow(["Time step", "Average % higher gain observable by a user"])
for i in range(len(distanceToNE_allRuns)): out.writerow([(i + 1), distanceToNE_allRuns[i]])
outfile.close()