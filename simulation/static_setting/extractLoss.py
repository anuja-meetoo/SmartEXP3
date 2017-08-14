#!/usr/bin/python3

import csv
import os

numUser = 20 
numNetwork = 3
dataRate = [4, 7, 22]
numRun = 100 
numParallelRun = 5 
numIteration = 1200 
rootDir = "/wns/4_7_22/stableHybridBlockExp3_reset_20users_3networks/"
outputDir = rootDir + "extractedData/"

timeSlotDuration = 15

def extractLossDueToSwitching():
    '''
    @description: identifies the smallest delay observed by clients in each network per time slot, based on that computes the
                  loss due to switching (as smallest delay * network bit rate)
    '''
    megaByteLostPerRun = [0] * (numRun * numParallelRun) # total MB lost due to switching by all users in each run

    for i in range(1, numParallelRun + 1):
        # initialise list to store minimum delay observed by clients in each network in every time slot
        smallestDelayPerNetworkPerTimeSlot = []
        for j in range(numRun):
            smallestDelayPerNetworkPerTimeSlotPerRun = []
            for k in range(numIteration): smallestDelayPerNetworkPerTimeSlotPerRun.append([-1] * numNetwork)
            smallestDelayPerNetworkPerTimeSlot.append(smallestDelayPerNetworkPerTimeSlotPerRun)
        # print("smallestDelayPerNetworkPerTimeSlot: ", smallestDelayPerNetworkPerTimeSlot)
        # extract the minimum delay
        for j in range(1, numUser + 1):
            inputCSVfile = rootDir + "run_" + str(i) + "/user" + str(j) + ".csv"

            with open(inputCSVfile, newline='') as inputCSVfile:
                fileReader = csv.reader(inputCSVfile)
                count = 0
                for row in fileReader:
                    delay = 0
                    if count > 0:
                        runIndex = int(row[0])
                        iteration = int(row[1])
                        currentNetwork = int(row[2 + 2 * numNetwork])
                        if iteration > 1: delay = float(row[3 + 2 * numNetwork])
                        if smallestDelayPerNetworkPerTimeSlot[runIndex - 1][iteration - 1][currentNetwork - 1] == -1 or delay < smallestDelayPerNetworkPerTimeSlot[runIndex - 1][iteration - 1][currentNetwork - 1]: smallestDelayPerNetworkPerTimeSlot[runIndex - 1][iteration - 1][currentNetwork - 1] = delay
                    count += 1
            inputCSVfile.close()


        # print("smallestDelayPerNetworkPerTimeSlot: ", smallestDelayPerNetworkPerTimeSlot)
        # compute the total loss due to switching for each run
        for j in range(numRun):
            totalLossSwitching = 0
            for k in range(1, numIteration):
                for l in range(numNetwork):
                    # print("i = ", i, ", j = ", j, ", k = ", k, ", l = ", l)
                    if smallestDelayPerNetworkPerTimeSlot[j][k][l] != -1: totalLossSwitching += smallestDelayPerNetworkPerTimeSlot[j][k][l] * dataRate[l]
            megaByteLostPerRun[(j) + (numRun * (i - 1))] += totalLossSwitching
            # print("parallel run index:", i, ", run index:", j, ", data stored at index:", (j) + (numRun * (i - 1))); #input()
    print("megaByteLostPerRun - switching:", megaByteLostPerRun)
    return megaByteLostPerRun
    # end extractLossDueToSwitching

def extractLossDueToUnusedResource():
    megaByteLostPerRun = [0] * (numRun * numParallelRun) # total MB lost due to unused resource in each run
    for i in range(1, numParallelRun + 1):
            inputCSVfile = rootDir + "run_" + str(i) + "/network.csv"
            with open(inputCSVfile, newline='') as inputCSVfile:
                fileReader = csv.reader(inputCSVfile)
                count = 0
                for row in fileReader:
                    if count > 0:
                        # print("row:", row, end="")
                        runIndex = int(row[0])
                        for j in range(numNetwork):
                            if int(row[3 + j]) == 0: # no user in that network j + 1
                                megaByteLost = dataRate[j] * timeSlotDuration
                                megaByteLostPerRun[(runIndex - 1) + (numRun * (i - 1))] += megaByteLost
                        # print("megaByteLostPerRun: ", megaByteLostPerRun); input()
                    count += 1

    print("megaByteLostPerRun - unused resource: ", megaByteLostPerRun)
    return megaByteLostPerRun
    # end extractLossDueToUnusedResource

def saveToTxtFile(megabyteLost, outputTxtFileName):
    fileopen = open(outputTxtFileName, "w")
    for loss in megabyteLost:
        fileopen.write(str(loss) + "\n")
    fileopen.close()
    # end saveToTxtFile

def main():
    if not os.path.exists(outputDir): os.makedirs(outputDir)  # create the output directory if it does not exist

    lossDueToSwitchingPerRun = extractLossDueToSwitching()
    lossDueToUnusedResourcePerRun = extractLossDueToUnusedResource()

    saveToTxtFile(lossDueToSwitchingPerRun, outputDir + "lossDueToSwitchingPerRun.csv")
    saveToTxtFile(lossDueToUnusedResourcePerRun, outputDir + "lossDueToUnusedResourcePerRun.csv")

    avgLossDueToSwitching = sum(lossDueToSwitchingPerRun) / len(lossDueToSwitchingPerRun)
    avgLossDueToUnusedResource = sum(lossDueToUnusedResourcePerRun) / len(lossDueToUnusedResourcePerRun)
    fileopen = open(outputDir + "averageLoss.txt", "w")
    fileopen.write("Average loss due to switching (MB): " + str(avgLossDueToSwitching) + "\n")
    fileopen.write("Average loss due to unused resource (MB): " + str(avgLossDueToUnusedResource) + "\n")
    fileopen.close()

main()
