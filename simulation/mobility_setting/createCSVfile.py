'''
@description: Creates the rateOfConvergence.csv, network.csv and user files with appropriate headers 
'''

import csv
from sys import argv
from os import mkdir, chmod, umask

numUser = int(argv[1])
numNetwork = int(argv[2])
dir = argv[3]

SAVE_MINIMAL_DETAIL = True if int(argv[4]) == 1 else False
'''
### for general scenario
# create a csv file rateOfConvergence.csv to save the rate of convergence
filename = dir+"rateOfConvergence.csv"
data=["Run no.", "Iteration", "User ID"]
for i in range(numNetwork):
    data.append("No. of users in network " + str(i + 1))
myfile = open(filename,"a")
out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
out.writerow(data)
myfile.close()

# create a csv file network.csv to store the number of users per network in every iteration
filename = dir+"network.csv"
data=["Run no.", "Iteration", "User ID"]
for i in range(numNetwork):
    data.append("No. of users in network " + str(i + 1))
myfile = open(filename,"a")
out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
out.writerow(data)
myfile.close()

for i in range(numUser):
    filename = dir+"user"+str(i + 1)+".csv"

    if SAVE_MINIMAL_DETAIL == True:
        data=["Run no.", "Iteration"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "Delay", "# Megabytes recv", "self.gain(MB)"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1) + "(MB)")
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length", "resetBlockLength?"]
    else:
        data=["Run no.", "Iteration", "User ID", "gamma"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "No. of users in current network", "Delay", "# Megabytes recv", "self.gain(MB)", "Gain", "Scaled gain", "Estimated gain"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1) + "(MB)")
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
        data += ["Block length", "netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock", "resetBlockLength?", "recentGainFavoredNetwork", "favored network", "favoredNetworkPrevReset", "countResetFavoredSameNetwork", "totalNumReset"]

    myfile = open(filename,"a")
    out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()

### end for general scenario and dynamic env scenario
'''

### for mobility scenario and dynamic env scenario
NUM_PHASES = 3

for i in range(NUM_PHASES): # create a directory for each phase
    mkdir(dir + "PHASE_" + str(i + 1))
    chmod(dir + "PHASE_" + str(i + 1), 0o777)
for phase in range(1, NUM_PHASES + 1):
    # create a csv file rateOfConvergence.csv to save the rate of convergence  
    filename = dir+ "PHASE_" + str(phase) + "/" + "rateOfConvergence.csv"
    data=["Run no.", "Iteration", "User ID"]
    for i in range(numNetwork):
        data.append("No. of users in network " + str(i + 1))
    myfile = open(filename,"a")
    out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()
    
    # create a csv file network.csv to store the number of users per network in every iteration 
    filename = dir+ "PHASE_" + str(phase) + "/" +"network.csv"
    data=["Run no.", "Iteration", "User ID"]
    for i in range(numNetwork): data.append("No. of users in network " + str(i + 1))
    data += ["NE?", "Epsilon equilibrium?"]
    for i in range(numNetwork): data.append("List of users in network " + str(i + 1))
    myfile = open(filename,"a")
    out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()

# initially 10 users in each of the 3 areas; then 5 users move from area 1 to area 2 and eventually to area 3
networkPerPhase = [[1, 2, 3], [1, 3, 4, 5], [1, 4, 5]]
for phase in range(1, NUM_PHASES + 1):   # for each directory (each part (static environment setting) has a directory)
    for user in range(1, 9):    # users 1 - 8 --- mobile users
        filename = dir+"PHASE_" + str(phase) + "/" + "user"+str(user)+".csv"
        availableNetworkList = networkPerPhase[phase - 1]
        # print("creating file for user", user, ", for part", phase)
        # print("networks available are ", availableNetworkList)
        if SAVE_MINIMAL_DETAIL == True:
            data = ["Run no.", "Iteration"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "Delay", "# Megabytes recv", "self.gain(MB)"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length", "resetBlockLength?"]
        else:
            data = ["Run no.", "Iteration", "User ID", "gamma"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "No. of users in current network", "Delay", "# Megabytes recv",
                           "self.gain(MB)", "Gain", "Scaled gain", "Estimated gain"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
            data += ["Block length", "netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock", "resetBlockLength?", "recentGainFavoredNetwork", "favored network", "favoredNetworkPrevReset", "countResetFavoredSameNetwork", "totalNumReset"]

        myfile = open(filename, "a")
        out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()

    for user in range(9, 11):    # users 9 - 10 - networks in phase 1
        filename = dir + "PHASE_" + str(phase) + "/" + "user" + str(user) + ".csv"
        availableNetworkList = networkPerPhase[0]
        # print("creating file for user", user, ", for part", phase)
        # print("networks available are ", availableNetworkList)
        if SAVE_MINIMAL_DETAIL == True:
            data = ["Run no.", "Iteration"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "Delay", "# Megabytes recv", "self.gain(MB)"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length", "resetBlockLength?"]
        else:
            data = ["Run no.", "Iteration", "User ID", "gamma"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "No. of users in current network", "Delay", "# Megabytes recv",
                           "self.gain(MB)", "Gain", "Scaled gain", "Estimated gain"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
            data += ["Block length", "netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock", "resetBlockLength?", "recentGainFavoredNetwork", "favored network", "favoredNetworkPrevReset", "countResetFavoredSameNetwork", "totalNumReset"]
        myfile = open(filename, "a")
        out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()

    for user in range(11, 16):  # users 11 - 15 - networks in phase 2
        filename = dir + "PHASE_" + str(phase) + "/" + "user" + str(user) + ".csv"
        availableNetworkList = networkPerPhase[1]
        # print("creating file for user", user, ", for part", phase)
        # print("networks available are ", availableNetworkList)
        if SAVE_MINIMAL_DETAIL == True:
            data = ["Run no.", "Iteration"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "Delay", "# Megabytes recv", "self.gain(MB)"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length", "resetBlockLength?"]
        else:
            data = ["Run no.", "Iteration", "User ID", "gamma"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "No. of users in current network", "Delay", "# Megabytes recv",
                           "self.gain(MB)", "Gain", "Scaled gain", "Estimated gain"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
            data += ["Block length", "netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock", "resetBlockLength?", "recentGainFavoredNetwork", "favored network", "favoredNetworkPrevReset", "countResetFavoredSameNetwork", "totalNumReset"]
        myfile = open(filename, "a")
        out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()

    for user in range(16, 21):  # users 16 - 20 - networks in phase 3
        filename = dir + "PHASE_" + str(phase) + "/" + "user" + str(user) + ".csv"
        availableNetworkList = networkPerPhase[2]
        # print("creating file for user", user, ", for part", phase)
        # print("networks available are ", availableNetworkList)
        if SAVE_MINIMAL_DETAIL == True:
            data = ["Run no.", "Iteration"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "Delay", "# Megabytes recv", "self.gain(MB)"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length", "resetBlockLength?"]
        else:
            data = ["Run no.", "Iteration", "User ID", "gamma"]
            for networkID in availableNetworkList: data.append("Weight (net " + str(networkID) + ")")
            for networkID in availableNetworkList: data.append("Probability (net " + str(networkID) + ")")
            data = data + ["Current network", "No. of users in current network", "Delay", "# Megabytes recv",
                           "self.gain(MB)", "Gain", "Scaled gain", "Estimated gain"]
            for networkID in availableNetworkList: data.append("Bandwidth in network " + str(networkID) + "(MB)")
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
            data += ["Block length", "netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock", "resetBlockLength?", "recentGainFavoredNetwork", "favored network", "favoredNetworkPrevReset", "countResetFavoredSameNetwork", "totalNumReset"]
        myfile = open(filename, "a")
        out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()
### end for mobility scenario and dynamic env scenario

'''
# create a csv file for every user to store details pertaining to the user in every iteration
'''
'''
### for different number of networks available to different users ###
for i in range(numUser//2):
    filename = dir+"user"+str(i + 1)+".csv"
    if SAVE_MINIMAL_DETAIL == True:
        data=["Run no.", "Iteration"]
        for j in range(numNetwork - 2): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork - 2): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "Actual bandwidth (Gain)"]
        for j in range(numNetwork - 2): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length"]
    else:  
        data=["Run no.", "Iteration", "User ID", "gamma"]
        for j in range(numNetwork - 2): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork - 2): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "No. of users in current network", "Actual bandwidth - not utility", "Available bandwidth - not utility", "Actual bandwidth (utility)", "Gain", "Scaled gain", "Estimated gain", "Actual bandwidth (Gain - not utility)"]
        for j in range(numNetwork - 2): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
        data += ["netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock"]
    
    myfile = open(filename,"a")
    out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()
    
for i in range(numUser//2, numUser):
    filename = dir+"user"+str(i + 1)+".csv"
    
    if SAVE_MINIMAL_DETAIL == True:
        data=["Run no.", "Iteration"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "Actual bandwidth (Gain)"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length"]
    else:  
        data=["Run no.", "Iteration", "User ID", "gamma"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "No. of users in current network", "Actual bandwidth - not utility", "Available bandwidth - not utility", "Actual bandwidth (utility)", "Gain", "Scaled gain", "Estimated gain", "Actual bandwidth (Gain - not utility)"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
        data += ["netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock"]
    
    myfile = open(filename,"a")
    out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()
### end for different number of networks available to different users ###
'''
'''
### for dynamic env scenario
for part in range(NUM_PHASES):
    for i in range(2*numUser//3):
        filename = dir + "PHASE_" + str(part + 1) + "/" + "user"+str(i + 1)+".csv"

        if SAVE_MINIMAL_DETAIL == True:
            data=["Run no.", "Iteration"]
            for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
            for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
            data = data + ["Current network", "Actual bandwidth (Gain)"]
            for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length"]
        else:
            data=["Run no.", "Iteration", "User ID", "gamma"]
            for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
            for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
            data = data + ["Current network", "No. of users in current network", "Actual bandwidth - not utility", "Available bandwidth - not utility", "Actual bandwidth (utility)", "Gain", "Scaled gain", "Estimated gain", "Actual bandwidth (Gain - not utility)"]
            for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
            data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
            data += ["netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock"]

        myfile = open(filename,"a")
        out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()

part = 1
for i in range(2 * numUser // 3, numUser):
    filename = dir + "PHASE_" + str(part + 1) + "/" + "user" + str(i + 1) + ".csv"

    if SAVE_MINIMAL_DETAIL == True:
        data = ["Run no.", "Iteration"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "Actual bandwidth (Gain)"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Block length"]
    else:
        data = ["Run no.", "Iteration", "User ID", "gamma"]
        for j in range(numNetwork): data.append("Weight (net " + str(j + 1) + ")")
        for j in range(numNetwork): data.append("Probability (net " + str(j + 1) + ")")
        data = data + ["Current network", "No. of users in current network", "Actual bandwidth - not utility",
                       "Available bandwidth - not utility", "Actual bandwidth (utility)", "Gain", "Scaled gain",
                       "Estimated gain", "Actual bandwidth (Gain - not utility)"]
        for j in range(numNetwork): data.append("Bandwidth in network " + str(j + 1))
        data += ["Coin flip", "Choose greedily", "Switch to prev network", "Log"]
        data += ["netSelectedPrevBlock", "gainPerTimeStepCurrentBlock", "gainPerTimeStepPrevBlock"]

    myfile = open(filename, "a")
    out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
    out.writerow(data)
    myfile.close()

### end for dynamic env scenario
'''
