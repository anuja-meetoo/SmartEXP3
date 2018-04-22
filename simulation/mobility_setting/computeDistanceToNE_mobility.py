'''
TO BE UPDATED BEFORE RUNNING FOR A DIFFERENT SCENARIO:-
1. NE
2. output filename
3. current phase number and directory of network file
4. method that builds the networks available per user, buildAvailableNetworkPerUserList
5. offset for the iteration number
6. the network ID in ascending order of their accessibility (number of networks from which they can ne accessed, based on networks available to users)
*** check the total bandwidth per network list
'''
import csv
from sys import argv
from copy import deepcopy
from NetworkGraph import NetworkGraph
import os

numUser = int(argv[1])
numNetwork = int(argv[2])
dir = argv[3]
MAX_NUM_ITERATION = int(argv[4])
numRun = int(argv[5])
numParallelRun = int(argv[6])
currentPhase = int(argv[7])
NE = argv[8].split(","); NE = [int(x) for x in NE]
userBeingConsideredList = argv[9].split(","); userBeingConsideredList = [int(x) for x in userBeingConsideredList]
NETWORK_BANDWIDTH = argv[10].split("_"); NETWORK_BANDWIDTH = [int(x) for x in NETWORK_BANDWIDTH] #[27, 49, 84, 19, 16] #, 26, 53, 28, 69, 51, 87, 99, 52, 27, 32, 20, 76, 49, 24, 22, 24, 26, 49, 27, 67, 54, 86, 98, 46, 28, 30, 23] # in Mbps - [LTE, 802.11n, 802.11ac, 3G, 802.11g]
NETWORK_ID = [2, 3, 4, 5, 1] # network ID in ascending order of accessibility (users from how many networks can have access to it)

numMobileUser = 8
DEBUG = 0   # 0 - no output; 1 - print details of computations; 2 - print details of computations and wait for user to press enter after each run is processed

outputDir = dir + "extractedData/"
if os.path.exists(outputDir) == False: os.makedirs(outputDir)
# outputCSVfile_allRuns = outputDir + "distanceToNE_allRuns.csv"


CURRENT_PHASE = "PHASE_" + str(currentPhase)
iterationNumOffset = (MAX_NUM_ITERATION) * (currentPhase - 1)
# print("currentPhase:", currentPhase, ", iterationNumOffset", iterationNumOffset)
outputCSVfile_allRuns = outputDir + "distanceToNE_avgAllRuns_phase_" + str(currentPhase) + "_users" + str(userBeingConsideredList[0]) + "_" + str(userBeingConsideredList[-1]) + ".csv"

epsilon = 7.5

DEBUG = 0

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def computeDistanceToNE():
    '''
    @desc:      at each iteration of every run, computes the distance of the current state to Nash equilibrium
    @param:     none
    @returns:   list of distances to Nash equilibrium for each iteration (averaged over all runs), string containing all epsilon equilibrium points
    '''

    distanceToNE_avgAllRuns = [0] * MAX_NUM_ITERATION           # to store distance to NE per time steps (averaged over all runs)
    epsilonEquilibriumPoints = ""                                                  # stores list of epsilon equilibrium points; may be used if plot is required
    availableNetworkPerUser = buildAvailableNetworkPerUserList()
    sortedUserList = sortUserListAscNumAvailableNetwork(availableNetworkPerUser)
    # print(">>> availableNetworkPerUser: ", availableNetworkPerUser, " --- sortedUserList: ", sortedUserList)
    if DEBUG >= 1: print(">>> availableNetworkPerUser: ", availableNetworkPerUser, " --- sortedUserList: ", sortedUserList)

    for j in range(numParallelRun):     # runs 20 times in this case; in each iteration, 25 runs are processed
        # create list to store distance to NE per time steps (for individual runs)
        distanceToNE_perRun = []        
        for l in range(numRun): distanceToNE_perRun.append([0] * MAX_NUM_ITERATION)

        #networkCSVfile = dir + str(numUser) + "users_" + str(numRun) + "runs_" + str(j + 1) + "/network.csv"
        networkCSVfile = dir + "run_" + str(j + 1) + "/" + CURRENT_PHASE + "/network.csv"
        with open(networkCSVfile, newline='') as networkCSVfile:
            networkReader = csv.reader(networkCSVfile)
            count = 0

            for rowNetwork in networkReader:  # compute total gain of user and that of each expert
                if count != 0:
                    runNum = int(rowNetwork[0])
                    iterationNum = int(rowNetwork[1])
                    numUserPerNet = []

                    # print(">>> iteration: ", iterationNum)
                    for i in range(numNetwork): numUserPerNet.append(int(rowNetwork[3 + i])) # construct list with number of users per network

                    # construct list of users per network
                    userListPerNet = []
                    for i in range(numNetwork):
                        userListCurrentNet = []
                        userListCurrentNetStr = rowNetwork[5 + numNetwork + i]
                        if userListCurrentNetStr != "":
                            userListCurrentNetStrSplit = userListCurrentNetStr.split(",")
                            for ID in userListCurrentNetStrSplit: userListCurrentNet.append(int(ID))
                        
                        userListCurrentNetSorted = sortUserListAscNumAvailableNetwork(availableNetworkPerUser, userListCurrentNet)
                        userListPerNet.append(userListCurrentNetSorted)
                    
                    # construct graph of networks and users
                    networkGraph = buildNetworkGraph(numNetwork, numUser, availableNetworkPerUser, userListPerNet)
                    
                    if DEBUG >= 1: print("\n\n### run no:", runNum, ", iteration no: ", iterationNum)

                    if DEBUG >= 1: print("availableNetworkPerUser: ", availableNetworkPerUser, "\n userListPerNet: ", userListPerNet)
                    if DEBUG >= 1: print("graph built: ", networkGraph)
                    #if iterationNum == 148 or iterationNum == 149: input()
                    
                    distance = computeDistance(iterationNum, numUserPerNet, userListPerNet, availableNetworkPerUser, networkGraph)

                    if DEBUG >= 1: print("run", (j + 1), ", iteration", iterationNum, ", distance = ", distance); #distance_timestep_1801.append(distance)#input();
                    #if iterationNum == 1801: print("run", (j + 1), ", iteration", iterationNum, ", distance = ", distance); distance_timestep_1801.append(distance)#input();
                    # print("iterationNumOffset", iterationNumOffset, ", iterationNum - iterationNumOffset- 1: ", iterationNum - iterationNumOffset- 1)
                    distanceToNE_perRun[runNum - 1][iterationNum - iterationNumOffset- 1] = distance
                    distanceToNE_avgAllRuns[iterationNum - iterationNumOffset - 1] += distance
                    
                    # if DEBUG >= 1: input()
                    # input()
                    if (iterationNum - iterationNumOffset) == MAX_NUM_ITERATION: print("done for run no", runNum)
                count += 1
                #print("Done for row ", count)
        print("done for parallel run", (j + 1))

        #savePerRunCSVfile((j + 1), distanceToNE_perRun)
    distanceToNE_avgAllRuns = [distance/(numParallelRun * numRun) for distance in distanceToNE_avgAllRuns]  # compute the average
    for i in range(len(distanceToNE_avgAllRuns)):
        if distanceToNE_avgAllRuns[i] <= epsilon:
            if epsilonEquilibriumPoints == "": epsilonEquilibriumPoints += str(i + 1)
            else: epsilonEquilibriumPoints += "," + str(i + 1)

    return distanceToNE_avgAllRuns, epsilonEquilibriumPoints #, distance_timestep_1801

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def buildAvailableNetworkPerUserList():
    '''
    @desc:      constructs the list of networks available to each user
    @param:     none
    @returns:   list consisting of sub-lists representing list of networks available to each user
    '''

    availableNetworkPerUser = []

    for i in range(1, numMobileUser + 1):
        if currentPhase == 1: availableNetworkPerUser.append([1, 2, 3])
        elif currentPhase == 2: availableNetworkPerUser.append([1, 3, 4, 5])
        else: availableNetworkPerUser.append([1, 4, 5])
    for i in range(numMobileUser + 1, 11):
        availableNetworkPerUser.append([1, 2, 3])
    for i in range(11, 16):
        availableNetworkPerUser.append([1, 3, 4, 5])
    for i in range(16, 21):
        availableNetworkPerUser.append([1, 4, 5])

    return availableNetworkPerUser

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def sortUserListAscNumAvailableNetwork(availableNetworkPerUserList, userIDlist = list((i + 1) for i in range(numUser))):
    '''
    @desc: sorts a list of users in ascending order of number of networks available to them
    @param: list of available networks per user, list of users to sort in ascending order of number of networks available to them
    @returns: list of users to sort in ascending order of number of networks available to them
    '''
    availableNetworkPerUser = list(availableNetworkPerUserList[ID - 1] for ID in userIDlist) # construct a list of available networks for users in list userIDlist
    availableNetworkPerUserCopy = deepcopy(availableNetworkPerUser)
    sortedUserList = []     # resulting list of users sorted in asc order of the number of networks available
    availableNetworkPerUserSortedList = sorted(availableNetworkPerUserCopy, key=len) # sorted in ascending order of list (elements) size
    for elem in availableNetworkPerUserSortedList:
        elemIndexOriginalList = availableNetworkPerUserCopy.index(elem)
        if len(availableNetworkPerUserSortedList) > 1: availableNetworkPerUserSortedList = availableNetworkPerUserSortedList[1:]
        else: availableNetworkPerUserSortedList = []
        availableNetworkPerUserCopy[elemIndexOriginalList] = [-1] # so that index doesn't return the same index next time
        sortedUserList.append(userIDlist[elemIndexOriginalList])
    return sortedUserList

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def buildNetworkGraph(numNetwork, numUser, availableNetworkPerUser, userListPerNet): # ???numUser???
    networkGraph = NetworkGraph([(i + 1) for i in range(numNetwork)], []) # build graph, initializing the list of network ID
    for netIndex in range(len(userListPerNet)): # for each network
        netID = netIndex + 1
        for userID in userListPerNet[netIndex]:    # for each user in the specific network
            userIndex = userID - 1
            # get networks available to the user            
            availableNetList = availableNetworkPerUser[userIndex]
            
            # create an edge between the current network and each of the network to which the user can go, if it does not exist
            for availableNetID in availableNetList: 
                if availableNetID != netID:
                    if networkGraph.edgeExist(netID, availableNetID) == False: networkGraph.addEdge(netID, availableNetID, [userID])                        
                    else: networkGraph.addUserToEdge(netID, availableNetID, userID)
                    
    for edge in networkGraph.edges: sortUserListAscNumAvailableNetwork(availableNetworkPerUser, edge.userList) # sort list of users
    return networkGraph
    # end buildNetworkGraph    

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''     
def findNetToMoveTo(currentNetIndex, numUserDiff):
    '''
    @desc:         gets ID of the next network to which users must be moved
    @input:        current index in network list, number of users to be moved from/to for each network
    @returns:     index of network to which users must be moved
    '''
    index = currentNetIndex
    while index < len(numUserDiff):
        #if numUserDiff[index] > 0:
        if numUserDiff[NETWORK_ID[index] - 1] > 0:  # the networks are considered in ascending order of accessibility (as per order in list NETWORK_ID)
            return NETWORK_ID[index]    # index iterates over list NETWORK_ID
        index += 1
    return -1

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def transferUser(fromNetID, toNetID, verticesAlongPath, networkGraph, maxNumUserToBeMoved, numUserPerNet, userListPerNet):

    distance = 0

    # find the minimum number of users who can be moved along the edges
    fromVertex = fromNetID
    toVertex = verticesAlongPath[1]
    for edge in networkGraph.edges:   # get number of users along edge(   fromVertex, toVertex)
        if edge.sourceVertex == fromVertex and edge.destinationVertex == toVertex:
            numUsersOnEdge = len(edge.userList)
            break
    numUserMoved = min(maxNumUserToBeMoved, numUsersOnEdge)
    
    if DEBUG >= 1: print("-----> in transferUser; fromNetID:", fromNetID, ", toNetID:", toNetID, ", totalNumUserToBeMoved: ", maxNumUserToBeMoved, ", number of users who can be moved: ", numUserMoved, "; pathLength: ", verticesAlongPath, "---", len(verticesAlongPath))
    prevVertex = fromNetID
    for vertex in verticesAlongPath[1:]:  # ignore the start vertex
        if DEBUG >= 1: print("considering edge ", prevVertex, "to", vertex)
        for edge in networkGraph.edges[::-1]:  # get number of users along edge(prevVertex, vertex)
            if edge.sourceVertex == prevVertex and edge.destinationVertex == vertex: # edge along which user will be moved
                if DEBUG >= 1: print("going to move", numUserMoved, "from edge (", prevVertex,",", vertex,") with user list", edge.userList)
                for i in range(numUserMoved): # move 'numUserMoved' users
                    userBeingMoved = edge.userList[0]
                    networkGraph.removeUserFromEdge(prevVertex, vertex, userBeingMoved)

                    ##### remove the user from the network so that I know who is/are in the network to know if their distance must be considered...
                    if DEBUG >= 1: print("user being moved from network", prevVertex, ": ", userBeingMoved, ", userListPerNet[",prevVertex - 1,"]: ",  userListPerNet[prevVertex - 1], " to network", vertex ," : userListPerNet:", userListPerNet)
                    userListPerNet[prevVertex - 1].remove(userBeingMoved)
                    userListPerNet[vertex - 1].append(userBeingMoved)

                    # path length > 1, add the users moved to the set of outgoing edges of the intermediary network
                    if (len(verticesAlongPath) - 1) > 1: 
                        for edgeIntermediaryNet in networkGraph.edges[::-1]:
                            if edgeIntermediaryNet.sourceVertex == vertex: networkGraph.addUserToEdge(edgeIntermediaryNet.sourceVertex, edgeIntermediaryNet.destinationVertex, userBeingMoved)
                    
                    if DEBUG >= 1: print("@@@ moving user", userBeingMoved, "from network", prevVertex, "to network", vertex)
                
                prevVertexIndex = prevVertex - 1
                vertexIndex = vertex - 1
                oldGain = NETWORK_BANDWIDTH[prevVertexIndex]/numUserPerNet[prevVertexIndex]
                newGain = NETWORK_BANDWIDTH[vertexIndex]/NE[vertexIndex]

                ##### include distance only if the user is being considered
                tmpDistance = (newGain - oldGain) * 100 / oldGain
                #if tmpDistance > 45: print("tmpDistance: ", tmpDistance, ", moving user", userBeingMoved, "from network", prevVertex, "to network", vertex)
                if isUserBeingConsidered([userBeingMoved]):
                    if tmpDistance > distance: distance = tmpDistance
                    #if tmpDistance > 45: print("tmpDistance is taken into consideration, distance = ", distance)
                else:
                    if DEBUG >= 1: print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~Will not consider distance...; user being moved is ", userBeingMoved)#; input()
                    #if tmpDistance > 45: print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~Will not consider distance...; user being moved is ", userBeingMoved)
        prevVertex = vertex
    if DEBUG >= 1: print("updated graph: ", networkGraph)
    return numUserMoved, distance
    # end transferUser

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def isUserBeingConsidered(uList):
    for user in uList:
        if user in userBeingConsideredList: return True
    return False
    # end isUserBeingConsidered

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def computeDistance(iterationNum, numUserPerNet, userListPerNet, availableNetworkPerUser, networkGraph):
    '''
    @desc:       computes the distance of a particular state from Nash equilibrium
    @param:    the iteration number in the run being processed, list of users in ascending  order of number of networks available, number 
                      of users per network, list of users per network (user ID), networks available to each user 
    returns:     distance of the particular state from Nash equilibrium
    '''
    # compute the distance from the current state to NE as sum of all additional bandwidth obtainable by the users by moving to NE state
    distance = 0
    numUserDiff = [] # only for the print statement at end of the function...
    
    if numUserPerNet != NE:  # current state is not NE
        distance = 0

        numUserDiff = list(numUserAtNE - numUserAtPresent for numUserAtNE, numUserAtPresent in zip(NE, numUserPerNet))

        if DEBUG >= 1:
            #print("NE:", NE ,"; numUserPerNet: ", numUserPerNet)
            print("numUserDiff: ", numUserDiff)

        currentPathLength = 1
        while any(x < 0 for x in numUserDiff) and currentPathLength < numNetwork:
            # find network from which to move user(s), fromNetID at index fromNetIndex
            # for fromNetIndex in range(len(numUserDiff)):
            for i in range(len(numUserDiff)):
                fromNetID = NETWORK_ID[i]
                fromNetIndex = fromNetID - 1    # iterate over networks in ascending order of accessibility

                if numUserDiff[fromNetIndex] < 0:  # need to move user from this network
                    totalNumUserToBeMoved = abs(numUserDiff[fromNetIndex])  # total number to be moved from the network

                    toNetStartIndex = 0
                    while totalNumUserToBeMoved > 0 and toNetStartIndex < numNetwork:  # not reached end of the list, can still check if
                        # find network to which to move user(s)
                        toNetID = findNetToMoveTo(toNetStartIndex, numUserDiff)
                        if DEBUG >= 1: print("going to check transfer from network", fromNetID, "to network", toNetID, "going to break?", toNetID == -1)
                        if toNetID == -1:
                            if DEBUG >= 1: print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> cannot transfer!!!")
                            break
                        toNetIndex = toNetID - 1
                        pathLength, verticesAlongPath = networkGraph.shortestPath(fromNetID, toNetID)
                        if DEBUG >= 1: print("trying to move users from network ", fromNetID, "to network", toNetID, ", currentPathLength: ", currentPathLength, ", path length: ", pathLength, ", vertices along path:", verticesAlongPath)
                        if pathLength == currentPathLength: # number of 'hops' along the path is same as the path length being considered in this iteration                            
                            maxNumUserToBeMoved = min(totalNumUserToBeMoved, numUserDiff[toNetIndex])
                            numUserMoved, tmpDistance = transferUser(fromNetID, toNetID, verticesAlongPath, networkGraph, maxNumUserToBeMoved, numUserPerNet, userListPerNet)
                            numUserDiff[fromNetIndex] += numUserMoved # it's initially a negative value
                            numUserDiff[toNetIndex] -= numUserMoved  # it's initially a positive value
                            if numUserDiff[fromNetIndex] == 0: # all users moved from the network, compute the % higher gain users in that network can get
                                oldGain = NETWORK_BANDWIDTH[fromNetIndex]/numUserPerNet[fromNetIndex]
                                newGain = NETWORK_BANDWIDTH[fromNetIndex]/NE[fromNetIndex]
                                tmpDistance = max( tmpDistance, (newGain - oldGain) * 100 / oldGain)                
                            if DEBUG >= 1: print("successfully transferred", numUserMoved, "from network", fromNetID, "to network", toNetID, "; numUserDiff:", numUserDiff)

                            #if tmpDistance > 45: print("tmpDistance for users left in network", fromNetID, ":", tmpDistance)
                            ##### include distance only if the user is being considered
                            if isUserBeingConsidered(userListPerNet[fromNetIndex]):
                                if tmpDistance > distance: distance = tmpDistance
                                #if tmpDistance > 45: print("tmpDistance is taken into consideration, distance = ", distance)
                            else:
                                if DEBUG >= 1: print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~Will not consider distance..., user(s) left in the network is/are ", userListPerNet[fromNetIndex]); input()
                                #if tmpDistance > 45: print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~Will not consider distance..., user(s) left in the network is/are ", userListPerNet[fromNetIndex])
                            totalNumUserToBeMoved -= numUserMoved
                        #toNetStartIndex = toNetIndex + 1
                        toNetStartIndex = NETWORK_ID.index(toNetID) + 1
                        #input()

            currentPathLength += 1
        
    else:  # current state is NE
        if DEBUG >= 1: print("iteration", iterationNum, ", numUserPerNet: ", numUserPerNet, " --- NE")
        
    if any(x < 0 for x in numUserDiff): print("@", iterationNum, "--- numUserDiff:", numUserDiff, ", SOMETHING WENT WRONG!!!") ; input()
    return distance

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
def savePerRunCSVfile(j, distanceToNE_perRun):
    for i in range(numRun):
        outputCSVfile_singleRun = dir + "distanceToNE_run" + str((j - 1) * numRun + (i + 1)) + ".csv"
        outfile = open(outputCSVfile_singleRun, "w")
        out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(["Time step", "Total higher gain observable by a user"])
        for l in range(len(distanceToNE_perRun[i])): out.writerow([(l + 1), distanceToNE_perRun[i][l]])
        outfile.close()

''' ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ '''
# main program

distanceToNE_avgAllRuns, epsilonEquilibriumPoints = computeDistanceToNE()

outfile = open(outputCSVfile_allRuns, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
out.writerow(["Time step", "Total higher gain observable by a user (average over all runs)"])
for i in range(len(distanceToNE_avgAllRuns)): out.writerow([(i + 1) + iterationNumOffset, distanceToNE_avgAllRuns[i]])
outfile.close()
