'''
@description: computes the average number of resets and extracts and outputs (in the proper format for plot) the time slot at which there was a reset
'''

import numpy as np
inputTxtFile = "/Users/anuja/Desktop/simulationResult/4_7_22_20users_3networks_processedResult_static/stableHybridBlockExp3_reset/nohup.out"

def convertStringToList(alist):
    '''
    converts a list given as a string to list of integers
    '''
    if alist == "[]": return []

    alist = alist[1:-1].split(", ")
    result = [int(x) for x in alist]
    return result
    # end convertStringToList

def getNumReset(line):
    line = line.split("no of resets: ")
    return int(line[1].split(" ")[0])
    # end getNumReset

def main():
    resetPeriodicTimeSlotList = []
    resetDropTimeSlotList = []
    numResetList = []
    file = open(inputTxtFile, "r")
    for line in file:
        if "time of reset" in line:
            line = line.rstrip()
            # print(line)
            num = getNumReset(line)
            numResetList.append(num)
            # print("totalNumReset:", totalNumReset)
            line = line.split("time of reset")
            line = line[1][2:-1]
            line = line.split(", drop: ")
            # print(line)
            resetPeriodicTimeSlotList += convertStringToList(line[0].split("periodic: ")[1])
            resetDropTimeSlotList += convertStringToList(line[1])

    resetPeriodicTimeSlotSet = set(resetPeriodicTimeSlotList)
    resetPeriodicTimeSlotList = []
    for val in resetPeriodicTimeSlotSet: resetPeriodicTimeSlotList.append(val)

    resetDropTimeSlotSet = set(resetDropTimeSlotList)
    resetDropTimeSlotList = []
    for val in resetDropTimeSlotSet: resetDropTimeSlotList.append(val)
    # print("resetPeriodicTimeSlotList:", resetPeriodicTimeSlotList)
    # print("resetDropTimeSlotList:", resetDropTimeSlotList)
    # print("totalNumReset:", totalNumReset)
    # print("count:", count)
    print("avg number of reset: ", sum(numResetList)/len(numResetList), ", min: ", min(numResetList), ", max: ", max(numResetList), ", median:", np.median(numResetList))

    # for timeSlot in resetPeriodicTimeSlotList:
    #     print("\\addplot [cyan, dashed, no markers] coordinates {(" + str(timeSlot) + ",0) (" + str(timeSlot) + ",250)};")
    # for timeSlot in resetDropTimeSlotList:
    #     print("\\addplot [magenta, dashed, no markers] coordinates {(" + str(timeSlot) + ",0) (" + str(timeSlot) + ",250)};")
    # end main

main()