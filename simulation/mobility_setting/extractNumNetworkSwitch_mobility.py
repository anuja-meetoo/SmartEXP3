'''
@description: extracts per user number of network switches (considering only a set of users, e.g. those who are in the service area throughout the experiment)
'''

import csv
from sys import argv
from math import sqrt
import time
from multiprocessing import Process, Lock, Manager
import os
from numpy import std

numUser = 20
numNetwork = 5
algorithmList = ["EXP3", "blockEXP3", "hybridBlockEXP3", "stableHybridBlockEXP3", "stableHybridBlockExp3_reset", "greedy", "expWeightedAvgFullInfo", "centralized", "fixedRandom"]
numParallelRun = 5
numRun = 100    # number of runs in each parallel run
numPhase = 3    # setting 1
settingType = "mobility"
dataRate = [16,14,22,7,4]
rootDir = "/media/anuja/My Passport/simulationResults_final_20170602/" + settingType + "_setting_code/" + '_'.join(map(str, dataRate)) + "/"
outputDirName = "extractedData"

# mobile users
# userList = [x for x in range(1, 9)]
# numNetworkPerPhase = [3,4,3]
# userCategory = "mobileUser"

# stationary users
userList = [x for x in range(9, 21)]
userCategory = "stationaryUser"

def computeNumSwitch(userID, runDir):
    numNetworkSwitchPerRun = [0] * numRun
    previousNetworkPerRun = [-1] * numRun

    for phaseIndex in range(1, numPhase + 1):
        userCSVfile = runDir + "PHASE_" + str(phaseIndex) + "/user" + str(userID) + ".csv"
        with open(userCSVfile, newline='') as userCSVfile:
            reader = csv.reader(userCSVfile)
            count = 0
            for row in reader:
                if count > 0:
                    runNum = int(row[0])
                    iteration = int(row[1])
                    # numNetworkAvailable =numNetworkPerPhase[phaseIndex - 1]  # mobile users
                    if userID >= 11 and userID <= 15: numNetworkAvailable = 4    # stationary users
                    else: numNetworkAvailable = 3
                    # print("user ID: ", userID,", # network:", numNetworkAvailable)
                    currentNetwork = int(row[2 + (2 * numNetworkAvailable)])
                    # print("phase", phaseIndex, ", count", count, ", current network:", currentNetwork);
                    # if count == 1: print("row:", row, "current network:", currentNetwork)
                    if iteration != 1 and previousNetworkPerRun[runNum - 1] != currentNetwork: numNetworkSwitchPerRun[runNum - 1] += 1
                    previousNetworkPerRun[runNum - 1] = currentNetwork
                    # print("previousNetworkPerRun: ", previousNetworkPerRun, ", numNetworkSwitchPerRun:", numNetworkSwitchPerRun); #input()
                count += 1
        userCSVfile.close()
    return numNetworkSwitchPerRun

for algorithmName in algorithmList:
    numNetworkSwitchList_combined = []
    print("user list:", userList)
    algorithmDir = rootDir + algorithmName + "_" + str(numUser) + "users_" + str(numNetwork) + "networks/"
    print("algorithmDir:", algorithmDir)
    for runIndex in range(1, numParallelRun + 1):
        runDir = algorithmDir + "run_" + str(runIndex) + "/"
        for userID in userList:
            print("user", userID)
            numNetworkSwitchList_combined += computeNumSwitch(userID, runDir)
    # print("numNetworkSwitchList_combined: ", numNetworkSwitchList_combined)

    # save to csv file
    outputCSVfile = rootDir + "1_perClientNumNetworkSwitch_" + userCategory + "/perClientNumNetworkSwitch_" + algorithmName + ".csv"
    outfile = open(outputCSVfile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    for numSwitch in numNetworkSwitchList_combined: out.writerow([0, numSwitch])
    outfile.close()