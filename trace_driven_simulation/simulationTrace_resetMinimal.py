'''
@ changes made: (1) monitor preferred network, (2) ?????maxProbDiff is a max of 1/2
'''
'''
@description:   evaluate the algorithms using traces of WiFi and cellular bit rates, to show that smartEXP3 discovers
                and connects to the "best" network (learns and adapts), while greedy is naive and cannot adapt
'''

from time import time, sleep
import csv
import argparse
from random import randint, choice, random
from copy import deepcopy
import numpy #import random
from math import ceil, exp
from termcolor import colored
import numpy as np
import pandas
from scipy.stats import t, johnsonsu
from statistics import median
from math import sqrt
import matplotlib.pyplot as plt

# global parameters
actualSlotDuration = 15     # in seconds
rootDir = "/Users/anuja/Desktop/WNS_EXPERIMENT_WILD_BACKUP/networkTrace_yih/"
z = 2.576   # 99% confidence

DEBUG = 0

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def wns(timeSlot, algorithmName, cellularBitRatePerTimeSlot, wifiBitRatePerTimeSlot):
    global currentNetwork, previousNetwork, totalBytePerNetwork, numTimeSlotNetworkSelected, gainPerTimeSlotCurrentBlock, bitRateObservedPerTimeSlot
    global totalNumMegaBytesDownloaded, actualSlotDuration, monitoredGainList, monitoringSlotDuration, networkSelectedPerTimeSlot, totalSwitchingCost

    if DEBUG >= 1:  print(colored("time slot:" + str(timeSlot), "blue", "on_white"))
    # previousNetwork = currentNetwork
    if algorithmName == "smartEXP3": currentNetwork = smartEXP3(timeSlot)
    elif algorithmName == "epsilon_greedy": currentNetwork = epsilonGreedy()
    else: currentNetwork = greedy()

    if currentNetwork == 1:
        totalBytePerNetwork[0] += wifiBitRatePerTimeSlot[timeSlot - 1];
        numTimeSlotNetworkSelected[0] += 1
        bitRateObservedPerTimeSlot.append(wifiBitRatePerTimeSlot[timeSlot - 1])
        gainPerTimeSlotCurrentBlock.append(wifiBitRatePerTimeSlot[timeSlot - 1])
    else:
        totalBytePerNetwork[1] += cellularBitRatePerTimeSlot[timeSlot - 1];
        numTimeSlotNetworkSelected[1] += 1
        bitRateObservedPerTimeSlot.append(cellularBitRatePerTimeSlot[timeSlot - 1])
        gainPerTimeSlotCurrentBlock.append(cellularBitRatePerTimeSlot[timeSlot - 1])

    ##### cater for switching cost - delay
    if timeSlot != 1 and currentNetwork != networkSelectedPerTimeSlot[-1]:
        delay = simulateDelay(currentNetwork)
        totalSwitchingCost += (bitRateObservedPerTimeSlot[-1] * delay)/8
        totalNumMegaBytesDownloaded += (bitRateObservedPerTimeSlot[-1] * (actualSlotDuration - delay))/8
    else: totalNumMegaBytesDownloaded += (bitRateObservedPerTimeSlot[-1] * actualSlotDuration)/8
    if DEBUG >= 1: print("adding (", bitRateObservedPerTimeSlot[-1], " * ", actualSlotDuration, ")/8 ----- totalNumMegaBytesDownloaded:", totalNumMegaBytesDownloaded)
    # print("delay: ", delay, ", bit rate: ", bitRateObservedPerTimeSlot[-1], ", switching cost:", totalSwitchingCost); input()
    updatePreferredNetworkDetail(bitRateObservedPerTimeSlot[-1], currentNetwork)    # update details of preferred network
    return currentNetwork
    # end wns

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def smartEXP3(timeSlot):
    global currentNetwork, previousNetwork, availableNetworkID, numNetwork, maxGain, beta, networkToExplore, weight, probability
    global blockLength, blockIndex, blockLengthPerNetwork, numBlockNetworkSelected, probabilityCurrentBlock, switchBack, maxProbDiff
    global totalBytePerNetwork, numTimeSlotNetworkSelected, gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, highProbability, largeBlock
    global bitRateObservedPerTimeSlot
    global numConsecutiveSlotPreferredNetwork, numConsecutiveSlotForReset, preferredNetworkGainList, gainRollingAvgWindowSize, totalNumReset
    global resetTime

    if blockLength == 0: blockIndex += 1  # at beginning of a new block
    gamma = blockIndex ** (-1 / 3)  # compute gamma, based on  block index

    if timeSlot == 1:  # first time slot
        # networkSelected = numpy.random.choice(availableNetworkID, p=probability)  # random choice
        networkSelected = choice(networkToExplore);
        if DEBUG >= 1: print("start of new block --- will explore network " + str(networkSelected))
        probabilityCurrentBlock = 1 / len(networkToExplore);
        networkToExplore.remove(networkSelected)

        switchBack = False
        networkSelectedIndex = availableNetworkID.index(networkSelected)
        blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
        numBlockNetworkSelected[networkSelectedIndex] += 1

    else:  # subsequent time slots; timeSlot > 1
        currentNetworkIndex = availableNetworkID.index(currentNetwork)  # list index where details of current network are stored

        # check if need for reset of algorithm and reset accordingly in the next time slot
        maxProbability = max(probability)  # highest probability
        convergedNetworkIndex = probability.index(maxProbability)  # list index where details of network with highest probability are stored

        minProbDiff = 0
        if preferredNetwork != -1:
            probabilityCpy = deepcopy(probability)
            preferredNetworkIndex = availableNetworkID.index(preferredNetwork)
            probabilityCpy.remove(probability[preferredNetworkIndex])
            minProbDiff = maxProbability - max(probabilityCpy)
        if DEBUG >= 1: print(colored("preferred net:" + str(preferredNetwork) + ",prob:" + str(probability) + ", min prob diff:" + str(minProbDiff), "yellow")); #input()
        # if maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= largeBlock:
        if DEBUG >= 1: print(colored("numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset:" + str(numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset) + ", len(preferredNetworkGainList) >= gainRollingAvgWindowSize:" + str(len(preferredNetworkGainList) >= gainRollingAvgWindowSize), "red"))
        if (maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= largeBlock) or \
                (numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset and len(preferredNetworkGainList) >= (gainRollingAvgWindowSize + 1) and networkQualityDeclined()):
            reset()
            totalNumReset += 1
            if blockLength != 0: blockIndex += 1  # else already incremented above
            blockLength = 0
            gamma = blockIndex ** (-1 / 3)  # compute gamma, based on  block index
            switchBack = False
            resetTime.append(timeSlot)
            if DEBUG >= 1: print("ALGORITHM RESET"); #input()

        # update and normalize weight
        estimatedGain = computeEstimatedGain(bitRateObservedPerTimeSlot[-1])
        gammaForUpdate = ((blockIndex + 1) ** (-1 / 3)) if blockLength != 0 else gamma  # to use correct value given that update is supposed to be made once per block
        weight[currentNetworkIndex] *= exp(gammaForUpdate * estimatedGain / numNetwork);  # print("before normalization, weight: ", weight)
        weight = list(w / max(weight) for w in weight);  # print("after normalization, weight: ", weight)  # normalize the weights

        # update probability
        probability = list((((1 - gammaForUpdate) * w) / sum(weight)) + (gammaForUpdate / numNetwork) for w in weight);  # print("probability: ", probability)
        if DEBUG >= 1:print("weight: ", weight, ", probability: ", probability)

        # if second time slot of block, check if need to switch back
        if DEBUG >= 1:
            print(colored("going to check if need to switch back...", "red", "on_white"))
            print("0 not in numBlockNetworkSelected:", 0 not in numBlockNetworkSelected)
            print("switchBack == False:", switchBack == False)
            print("current network:", currentNetwork, ", previous network:", previousNetwork, ", currentNetwork != previousNetwork:", currentNetwork != previousNetwork)
            print("blockLength == (blockLengthPerNetwork[currentNetworkIndex] - 1): ", blockLength == (blockLengthPerNetwork[currentNetworkIndex] - 1))
        if 0 not in numBlockNetworkSelected and switchBack == False and currentNetwork != previousNetwork and \
                        blockLength == (blockLengthPerNetwork[currentNetworkIndex] - 1) and mustSwitchBack(bitRateObservedPerTimeSlot[-1], timeSlot) == True:
            if DEBUG >= 1:print(colored(">>> will switch back to network " + str(previousNetwork), "red", "on_white"))
            previousNetwork, networkSelected = currentNetwork, previousNetwork
            if blockLength != 0: blockIndex += 1  # if blockLength = 0, update has already been made @line 398
            probabilityCurrentBlock = 1;
            switchBack = True;
            networkSelectedIndex = availableNetworkID.index(networkSelected)
            blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
            numBlockNetworkSelected[networkSelectedIndex] += 1
            gainPerTimeSlotPreviousBlock, gainPerTimeSlotCurrentBlock = gainPerTimeSlotCurrentBlock, []

        elif blockLength == 0:  # start of a new block
            previousNetwork = currentNetwork
            if networkToExplore != []:
                networkSelected = choice(networkToExplore);
                if DEBUG >= 1:print("start of new block --- will explore network " + str(networkSelected))
                # probabilityCurrentBlock = 1 / numNetwork;
                probabilityCurrentBlock = 1 / len(networkToExplore);
                networkToExplore.remove(networkSelected)
            else:
                if DEBUG >= 1:print(">>>>> no network to explore!")
                if mustSelectGreedily(timeSlot) == True:  # greedy
                    networkSelected, numNetworkHighestAverageByte = selectGreedily()
                    if DEBUG >= 1:print("start of new block --- will choose greedily network " + str(networkSelected))
                    if numNetworkHighestAverageByte > 1 and networkSelected == previousNetwork:
                        probabilityCurrentBlock = 1 / 2
                        if DEBUG >= 1: print("GREEDY STAYING IN SAME NETWORK")
                    else:
                        probabilityCurrentBlock = (1 / 2) * (1 / numNetworkHighestAverageByte)
                else:  # random based on probability distribution
                    networkSelected = numpy.random.choice(availableNetworkID, p=probability)  # random choice
                    if DEBUG >= 1:print("start of new block --- will choose randomly network " + str(networkSelected))
                    probabilityCurrentBlock = probability[availableNetworkID.index(networkSelected)];

            switchBack = False
            networkSelectedIndex = availableNetworkID.index(networkSelected)
            blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
            numBlockNetworkSelected[networkSelectedIndex] += 1
            gainPerTimeSlotPreviousBlock, gainPerTimeSlotCurrentBlock = gainPerTimeSlotCurrentBlock, []
        else:  # in the middle of a block
            if DEBUG >= 1: print("in the middle of a block")
            networkSelected = currentNetwork; previousNetwork = currentNetwork;
            networkSelectedIndex = availableNetworkID.index(networkSelected)
            switchBack = False
    if DEBUG >= 1: print("probability current block: ", probabilityCurrentBlock, ", block lenght:", blockLength)

    return networkSelected
    # end smartEXP3
''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def greedy():
    global networkToExplore, previousNetwork, currentNetwork

    previousNetwork = currentNetwork
    if networkToExplore != []: # explore a network at random
        if DEBUG >= 1: print("not yet explored all networks")
        networkSelected = choice(networkToExplore)
        networkToExplore.remove(networkSelected)
    else:
        if DEBUG >= 1: print("explored all networks ----- going to choose greedily...")
        networkSelected, numNetworkHighestAverageByte = selectGreedily("greedy")

    return networkSelected

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def epsilonGreedy():
    global networkToExplore, previousNetwork, currentNetwork, availableNetworkID
    epsilon = 0.1

    previousNetwork = currentNetwork
    if networkToExplore != []: # explore a network at random
        if DEBUG >= 1: print("not yet explored all networks")
        networkSelected = choice(networkToExplore)
        networkToExplore.remove(networkSelected)
    else:
        num = random()
        if num > epsilon:
            if DEBUG >= 1: print("explored all networks ----- going to choose greedily...")
            networkSelected, numNetworkHighestAverageByte = selectGreedily("greedy")
        else:
            if DEBUG >= 1: print("explored all networks ----- going to choose at random...")
            networkSelected = choice(availableNetworkID)

    return networkSelected

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def selectGreedily(algorithmName = "smartEXP3"):
    global networkToExplore, totalBytePerNetwork, numTimeSlotNetworkSelected, availableNetworkID, previousNetwork

    averageBytePerNet = list(totalByte / numTimeSlot for totalByte, numTimeSlot in zip(totalBytePerNetwork, numTimeSlotNetworkSelected))
    highestAverageByte = max(averageBytePerNet)

    if DEBUG >= 1: print("totalBytePerNetwork:", totalBytePerNetwork, ", numTimeSlotNetworkSelected:", numTimeSlotNetworkSelected, ", averageBytePerNet:", averageBytePerNet)

    ### select the (or one of the) network(s) with the highest average bandwidth
    numNetworkHighestAverageByte = averageBytePerNet.count(highestAverageByte)

    if numNetworkHighestAverageByte == 1:
        # a single network with the highest max average bandwidth
        bestNetIndex = averageBytePerNet.index(highestAverageByte)
        networkSelected = availableNetworkID[bestNetIndex]
    else:
        # several networks with the same highest average bandwidth; choose one at random
        indices = [i for i, x in enumerate(averageBytePerNet) if x == highestAverageByte]
        bestNetworkIDList = [availableNetworkID[x] for x in indices]
        if algorithmName == "smartEXP3" and previousNetwork in bestNetworkIDList: networkSelected = previousNetwork
        else: networkSelected = choice(bestNetworkIDList)
        if DEBUG >= 1: print("numNetworkHighestAverageByte:", numNetworkHighestAverageByte)

    return networkSelected, numNetworkHighestAverageByte

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def computeEstimatedGain(gain):
    '''
    @description: compute the estimated gain, the probability value used in the computation depends on the type of selection used
    '''
    global maxGain, probabilityCurrentBlock

    scaledGain = gain/maxGain
    estimatedGain = scaledGain/probabilityCurrentBlock
    if DEBUG >= 1: print("gain: ", gain, ", scaled gain: ", scaledGain, ", estimated gain: ", estimatedGain)
    return estimatedGain
    # end computeEstimatedGain

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def mustSwitchBack(gain, timeSlot):
    '''
    @description: determines whether there is a need to switch back to the previous network
    '''
    global gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, numBlockNetworkSelected, maxTimeSlotConsideredPrevBlock
    global probability, numNetwork, blockLengthPerNetwork, switchBack, currentNetwork, previousNetwork

    if DEBUG >= 1: print(colored("IN mustSwitchBack", "green", "on_white"))
    if len(gainPerTimeSlotPreviousBlock) <= maxTimeSlotConsideredPrevBlock: gainList = gainPerTimeSlotPreviousBlock
    else: gainList = gainPerTimeSlotPreviousBlock[(len(gainPerTimeSlotPreviousBlock) - maxTimeSlotConsideredPrevBlock):]

    if DEBUG >= 1: print("gainList:", gainList, ", gainPerTimeSlotPreviousBlock: ", gainPerTimeSlotPreviousBlock)
    averageGainPreviousBlock = sum(gainList) / len(gainList)
    gainLastTimeStepPreviousBlock = gainList[-1]

    # if total gain of last block is equal to zero, no need to switch back
    if (averageGainPreviousBlock > gain or gainLastTimeStepPreviousBlock > gain or
            ((((sum(i >= gain for i in gainList) * 100) / (len(gainList))) > 50) and sum(gainList) != 0)):
        return True
    return False
    # end mustSwitchBack

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def mustSelectGreedily(timeSlot):
    '''
    @description: determines whether greedy selection must be leveraged
    '''
    global probability, numNetwork, blockLengthPerNetwork, numBlockNetworkSelected, maxBlock

    highestProbabilityIndex = probability.index(max(probability))
    if 0 not in numBlockNetworkSelected and (((max(probability) - min(probability)) <= (1 / (numNetwork - 1)))
                                             or blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock):
        coinFlip = randint(1, 2)
        if coinFlip == 1:
            if DEBUG >= 1: print("flipped coin and will select greedily...")
            return True
        else:
            if DEBUG >= 1:print("flipped coin but will not select greedily...")
    else:
        if DEBUG >= 1: print("no need to flip coin ----- will not select greedily...; 0 not in numBlockNetworkSelected: "
                    + str(0 not in numBlockNetworkSelected) + ", diff between prob: " + str((max(probability) - min(probability))
                    <= (1 / (numNetwork - 1))) + ", blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock:"
                    + str(blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock))
    return False
    # end mustSelectGreedily

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def reset():
    '''
    @description: periodic reset of the algorithm
    '''
    global numNetwork, numBlockNetworkSelected, blockLengthPerNetwork
    global networkToExplore, totalBytePerNetwork, numTimeSlotNetworkSelected
    global preferredNetwork, numConsecutiveSlotPreferredNetwork, preferredNetworkGainList

    if DEBUG >= 1: print("RESET IS CALLED!!!")
    networkToExplore = deepcopy(availableNetworkID)
    numBlockNetworkSelected = [0] * numNetwork
    blockLengthPerNetwork = [0] * numNetwork
    totalBytePerNetwork = [0] * numNetwork
    numTimeSlotNetworkSelected = [0] * numNetwork

    # details of preferred network
    preferredNetwork = -1
    numConsecutiveSlotPreferredNetwork = 0
    preferredNetworkGainList = []
    # end reset

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def networkQualityDeclined():
    '''
    @description: determines if there has been a considerable decline in network quality and reset must be sonsidered
    '''
    global preferredNetworkGainList, gainRollingAvgWindowSize, percentageDeclineForReset

    # initialGain = preferredNetworkGainList[0]   # initial gain of preferred network (from time it was considered preferred network)
    gainList = np.array(preferredNetworkGainList)
    gainList = pandas.rolling_mean(gainList, gainRollingAvgWindowSize)    # rolling average of gain
    gainList = gainList[~np.isnan(gainList)]                              # remove nan from list
    gainList = list(gainList)
    initialGain = gainList[0]

    changeInGain = computeNetworkQualityChange(gainList)
    if DEBUG >= 1: print(colored("gain list (rolling avg): " + str(gainList) + ", changeInGain: " + str(changeInGain), "green"));  # input()

    return True if ((changeInGain < 0) and (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100)) else False
    # end networkQualityDeclined

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def computeNetworkQualityChange(gainList):
    '''
    @description:   computes change in quality of preferred network (as sum of differences of consecutive gains observed)
    @arg:           rolling average of gain observed from preferred network
    @return:        change in gain of preferred network
    '''
    changeInGain = 0

    prevGain = gainList[0]
    for gain in gainList[1:]: changeInGain += (gain - prevGain); prevGain = gain
    return changeInGain
    # end computeChangeInGain

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def updatePreferredNetworkDetail(currentGain, currentNetwork):
    '''
    @description:   updates details pertaining to current preferred network
    @args:          None
    @return:        None
    '''
    global preferredNetwork, numConsecutiveSlotPreferredNetwork, preferredNetworkGainList, numTimeSlotNetworkSelected

    highestCountTimeSlot = max(numTimeSlotNetworkSelected)
    currentPreferredNetwork = numTimeSlotNetworkSelected.index(highestCountTimeSlot) + 1
    if numTimeSlotNetworkSelected.count(highestCountTimeSlot) > 1:   # several networks have same highest count of time slots
        # no preferred network
        preferredNetwork = -1
        numConsecutiveSlotPreferredNetwork = 0
        preferredNetworkGainList = []
        if DEBUG >= 1: print(colored("No preferred network", "green"))
    else: # single network with highest count of time slots
        if preferredNetwork != currentPreferredNetwork:
            # change in preference
            preferredNetwork = currentPreferredNetwork
            numConsecutiveSlotPreferredNetwork = 1
            preferredNetworkGainList = [currentGain]
        else:
            # preferred network is same
            if currentNetwork == preferredNetwork:
                numConsecutiveSlotPreferredNetwork += 1
                preferredNetworkGainList.append(currentGain)
            else:
                numConsecutiveSlotPreferredNetwork = 0
        if DEBUG >= 1: print(colored("numTimeSlotNetworkSelected: " + str(numTimeSlotNetworkSelected) + ", current network: " + str(currentNetwork) + ", preferredNetwork: " + str(preferredNetwork) + ", numConsecutiveSlotPreferredNetwork: " + str(numConsecutiveSlotPreferredNetwork) + ", preferredNetworkGainList: " + str(preferredNetworkGainList), "magenta"))
    # input()
    # end updatePreferredNetworkDetail

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def simulateDelay(currentNetwork):
    '''
    @description: generates a delay based on the appropriate distribution
    '''
    wifiDelay = [3.0659475327, 14.6918344498]       # min and max delay observed for wifi
    cellularDelay = [4.2531193161, 14.3172883892]   # min and max delay observed for 3G

    if currentNetwork == 1: # wifi
        # johnson su in python (fitter.Fitter.fit()) and t location-scale in matlab (allfitdist)
        # in python, error is higher for t compared to johnson su
        delay = min(max(johnsonsu.rvs(0.29822254217554717, 0.71688524931466857, loc=6.6093350624107909, scale=0.5595970482712973), wifiDelay[0]), wifiDelay[1])
    else:
        # t in python (fitter.Fitter.fit()) and t location-scale in matlab (allfitdist)
        delay = min(max(t.rvs(0.43925241212097499, loc=4.4877772816533934, scale=0.024357324434644639), cellularDelay[0]), cellularDelay[1])
    if DEBUG >= 1: print(colored("Delay for " + str(availableNetworkName[currentNetwork - 1]) + ": " + str(delay), "cyan"))
    # input()
    return delay
    # end simulateDelay

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def getBitRate(inputCSVfile, numValue, columnIndex):
    '''
    @description:   returns tht top numValue number of bit rates from inputCSVfile as a list
    @arg:           CSV file containing the bit rates and the number of bit rates to return
    @return:        list of bit rates
    '''
    global algorithmName
    # columnIndex = 1 if algorithmName == "smartEXP3" else 2 #8
    bitRateList = []

    with open(inputCSVfile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        for row in rowReader:
            if count > numValue: break
            if count != 0: bitRateList.append(float(row[columnIndex]))
            count += 1
    inputCSVfile.close()

    return bitRateList
    # end getBitRate

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def saveTxtFile(outputTxtFile, data):
    '''
    @description:   saves data to the text file with the specified name
    @arg:           url of output text file and data to be written to the file
    @return:        None
    '''
    outfile = open(outputTxtFile, "a")
    outfile.write(data + "\n\n")
    outfile.close()
    # end saveTxtFile

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
algorithmName = ""#"smartEXP3"#
numRun = 1
maxBandwidth = 8 # MBps
timeSlotDuration = 2        # duration in the simulation

# smartEXP3
availableNetworkName = ["WiFi", "cellular"]
numNetwork = len(availableNetworkName)
availableNetworkID = [i for i in range(1, numNetwork + 1)]
networkToExplore = [] # if algorithmName == "smartEXP3" else [i for i in range(1, numNetwork + 1)]
previousNetwork = currentNetwork = -1
maxGain = maxBandwidth * 8  # Mbps
gainPerTimeSlotCurrentBlock = []
gainPerTimeSlotPreviousBlock = []
highProbability = 0.75
largeBlock = 40         # for periodic reset
maxBlock = 6            # for greedy
maxTimeSlotConsideredPrevBlock = 8 # for switch back
beta = 0.1
weight = [1] * numNetwork
probability = [1/numNetwork] * numNetwork
blockLength = 0
blockLengthPerNetwork = [0] * numNetwork
switchBack = False
numBlockNetworkSelected = [0] * numNetwork
probabilityCurrentBlock = 1/numNetwork
blockIndex = 0
maxProbDiff = 1/(numNetwork - 1)

# greedy
totalBytePerNetwork = [0] * numNetwork
numTimeSlotNetworkSelected = [0] * numNetwork

# to monitor quality of preferred network
preferredNetwork = -1                       # ID of network with highest time slot count
numConsecutiveSlotPreferredNetwork = 0      # number of consecutive time slots spent in current network till current time slot
preferredNetworkGainList = []               # list of gain observed in preferred network from the time it was identified as the preferred network
numConsecutiveSlotForReset = 4              # no. of consecutive time slots spent in preferred network to consider a reset
percentageDeclineForReset = 15              # minimum percentage decline (from initial gain) in preferred network to consider a reset
gainRollingAvgWindowSize = 12                # window size for rolling average of gain

# log
networkSelectedPerTimeSlot = []
bitRateObservedPerTimeSlot = []
totalNumMegaBytesDownloaded = 0
totalNumMegaBytesDownloadedPerRun = []
totalNumNetworkSwitchPerRun = []
totalSwitchingCostPerRun = []
totalNumResetPerRun = []
totalSwitchingCost = 0
totalNumReset = 0
resetTime = []

def main():
    global algorithmName, numRun, actualSlotDuration, availableNetworkName, numNetwork, availableNetworkID, networkToExplore, previousNetwork
    global currentNetwork, maxGain, gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, highProbability, largeBlock, maxBlock
    global maxTimeSlotConsideredPrevBlock, beta, weight, probability, blockLength, blockLengthPerNetwork, switchBack, numBlockNetworkSelected
    global probabilityCurrentBlock, blockIndex, maxProbDiff, totalBytePerNetwork, numTimeSlotNetworkSelected, networkSelectedPerTimeSlot
    global bitRateObservedPerTimeSlot, totalNumMegaBytesDownloaded, totalNumMegaBytesDownloadedPerRun, totalNumNetworkSwitchPerRun, totalNumReset
    global totalSwitchingCost, rootDir, totalSwitchingCostPerRun
    global resetTime

    parser = argparse.ArgumentParser(description='Simulates wireless network selection using traces of WiFi and cellular load.')
    parser.add_argument('-a', dest="algorithm_name", required=True, help='name of wireless network selection algorithm (smartEXP3/greedy)')
    parser.add_argument('-n', dest="num_run", required=True, help='number of simulation run')
    parser.add_argument('-s', dest="scenario_index", required=True, help='scenario index')

    args = parser.parse_args()
    algorithmName = args.algorithm_name
    numRun = int(args.num_run)
    scenario = args.scenario_index
    if algorithmName != "smartEXP3" and algorithmName != "greedy" and algorithmName != "epsilon_greedy": print("Invalid algorithm name!"); return

    scenarioList = ["1", "2", "3a", "3b", "4", "5", "6"]
    # numIterationList = [110, 100, 110, 105, 90, 100, 118]
    numIterationList = [100, 100, 100, 100, 100, 100, 100]
    numIteration = numIterationList[scenarioList.index(scenario)]
    inputFileNameList = ["scenario" + str(scenario) + ".csv", "scenario" + str(scenario) + ".csv"]

    outputFileName = str(scenario) + "_" + algorithmName + "_output_details.txt"

    wifiBitRatePerTimeSlot = getBitRate(rootDir + inputFileNameList[0], numIteration, 1)  # load list of bit rates from csv file
    cellularBitRatePerTimeSlot = getBitRate(rootDir + inputFileNameList[1], numIteration, 2)   # load list of bit rates from csv file

    for run in range(numRun):
        networkToExplore = [i for i in range(1, numNetwork + 1)]
        previousNetwork = currentNetwork = -1
        gainPerTimeSlotCurrentBlock = []
        gainPerTimeSlotPreviousBlock = []
        weight = [1] * numNetwork
        probability = [1 / numNetwork] * numNetwork
        blockLength = 0
        blockLengthPerNetwork = [0] * numNetwork
        switchBack = False
        numBlockNetworkSelected = [0] * numNetwork
        probabilityCurrentBlock = 1 / numNetwork
        blockIndex = 0
        totalBytePerNetwork = [0] * numNetwork
        numTimeSlotNetworkSelected = [0] * numNetwork
        networkSelectedPerTimeSlot = []
        bitRateObservedPerTimeSlot = []
        totalNumMegaBytesDownloaded = 0
        totalSwitchingCost = 0
        totalNumNetworkSwitch = 0
        totalNumReset = 0
        resetTime = []

        for i in range(numIteration):
            if DEBUG >= 1: print("WiFi bit rate:", wifiBitRatePerTimeSlot[i], ", cellular bit rate:", cellularBitRatePerTimeSlot[i])
            if DEBUG >= 1: print("prob:", probability)
            # start = time()
            currentNetwork = wns(i + 1, algorithmName, cellularBitRatePerTimeSlot, wifiBitRatePerTimeSlot)
            if networkSelectedPerTimeSlot != [] and networkSelectedPerTimeSlot[-1] != currentNetwork: totalNumNetworkSwitch += 1
            networkSelectedPerTimeSlot.append(currentNetwork)
            if DEBUG >= 1: print()
            if algorithmName == "smartEXP3": blockLength -= 1
            # input();
            # sleep(timeSlotDuration - (time() - start))
        totalNumMegaBytesDownloadedPerRun.append(totalNumMegaBytesDownloaded)
        totalNumNetworkSwitchPerRun.append(totalNumNetworkSwitch)
        totalNumResetPerRun.append(totalNumReset)
        totalSwitchingCostPerRun.append(totalSwitchingCost)
        if DEBUG >= 1:
            print("network selected: ", networkSelectedPerTimeSlot)
            print("bit rate observed: ", bitRateObservedPerTimeSlot)
            print("total # megabytes downloaded: ", totalNumMegaBytesDownloaded)
            print("switching cost: ", totalSwitchingCost)
        print("Simulation run", run + 1 ,"completed")
        saveTxtFile(rootDir + outputFileName, "***** RUN " + str(run + 1) + " *****\nnetwork selected: " + str(networkSelectedPerTimeSlot) + "\n" + "bit rate observed: " + str(bitRateObservedPerTimeSlot) + "\n" + "total # megabytes downloaded: " + str(totalNumMegaBytesDownloaded) + "\nreset time slot:" + str(resetTime) + "\n" + "-" * 150)

        ##### plot in matplotlib
        # print(">>> reset time:", resetTime)
        # plt.style.use('classic')
        # MARKER_SIZE = 5
        # MARKER_INTERVAL = 250
        # LINE_WIDTH = 2.0
        # # xAxisTicks = [x * 100 for x in range(27)]
        # plt.xlim(xmin=1, xmax=numIteration)
        # # plt.xticks(xAxisTicks, xAxisTicks)
        # plt.xlabel("Time step")
        # plt.ylabel("Bit rate observed")
        # plt.plot(wifiBitRatePerTimeSlot, color='#01DFD7', linestyle='-', marker='H', markersize=MARKER_SIZE, markevery=MARKER_INTERVAL, linewidth=LINE_WIDTH, label='wifi')
        # plt.plot(cellularBitRatePerTimeSlot, color='blue', linestyle='-', marker='H', markersize=MARKER_SIZE, markevery=MARKER_INTERVAL, linewidth=LINE_WIDTH, label='wifi')
        #
        # x = 1
        # for network, bitRate in zip(networkSelectedPerTimeSlot, bitRateObservedPerTimeSlot):
        #     plt.scatter(x, bitRate, color='r', s=10, marker='o')#, alpha=.4)
        #     x += 1
        # for t in resetTime: plt.axvline(x=t, color="pink")
        # grd = plt.grid(True)
        # plt.legend(['WiFi', '3G'], loc='upper right', numpoints=1)
        # plt.show()

        ##### output in format to use in the plot
        # x = 1
        # print("x \ty \tlabel")
        # for network, bitRate in zip(networkSelectedPerTimeSlot, bitRateObservedPerTimeSlot):
        #     label = "a" if network == 1 else "b"
        #     print(str(x) + "\t" + str(bitRate) + "\t" + label)
        #     x += 1

    print("total # megabytes download per run:", totalNumMegaBytesDownloadedPerRun)
    print("avg=", sum(totalNumMegaBytesDownloadedPerRun)/len(totalNumMegaBytesDownloadedPerRun))
    print("min=", min(totalNumMegaBytesDownloadedPerRun))
    print("max=", max(totalNumMegaBytesDownloadedPerRun))
    print("median=", median(totalNumMegaBytesDownloadedPerRun))
    numValue = len(totalNumMegaBytesDownloadedPerRun)
    totalNumMegaBytesDownloadedPerRun = np.array(totalNumMegaBytesDownloadedPerRun)
    stdNumMegaBytesDownloaded = np.std(totalNumMegaBytesDownloadedPerRun)
    offsetNumMegaBytesDownloaded = z * stdNumMegaBytesDownloaded / sqrt(numValue)

    print("total number of network switches per run:", totalNumNetworkSwitchPerRun)
    print("avg=", sum(totalNumNetworkSwitchPerRun) / len(totalNumNetworkSwitchPerRun))
    print("min=", min(totalNumNetworkSwitchPerRun))
    print("max=", max(totalNumNetworkSwitchPerRun))
    print("median=", median(totalNumNetworkSwitchPerRun))

    print("switching cost per run:", totalSwitchingCostPerRun)
    print("avg=", sum(totalSwitchingCostPerRun) / len(totalSwitchingCostPerRun))
    print("min=", min(totalSwitchingCostPerRun))
    print("max=", max(totalSwitchingCostPerRun))
    print("median=", median(totalSwitchingCostPerRun))
    numValue = len(totalSwitchingCostPerRun)
    totalSwitchingCostPerRun = np.array(totalSwitchingCostPerRun)
    stdSwitchingCost = np.std(totalSwitchingCostPerRun)
    offsetSwitchingCost = z * stdSwitchingCost / sqrt(numValue)

    print("total number of reset:", totalNumResetPerRun)
    print("avg=", sum(totalNumResetPerRun) / len(totalNumResetPerRun))
    print("min=", min(totalNumResetPerRun))
    print("max=", max(totalNumResetPerRun))
    print("median=", median(totalNumResetPerRun))


    print("total number of reset per run:", totalNumResetPerRun)
    saveTxtFile(rootDir + outputFileName, "total # megabytes download per run:" + str(totalNumMegaBytesDownloadedPerRun) + "\n\tavg=" +
                str(sum(totalNumMegaBytesDownloadedPerRun)/len(totalNumMegaBytesDownloadedPerRun)) + "\n\tmin=" + str(min(totalNumMegaBytesDownloadedPerRun)) +
                "\n\tmax=" + str(max(totalNumMegaBytesDownloadedPerRun)) + "\n\t median=" + str(median(totalNumMegaBytesDownloadedPerRun)) +
                "\n\tstd = " + str(stdNumMegaBytesDownloaded) + "\t 'offset' = " + str(offsetNumMegaBytesDownloaded) +
                "\ntotal number of network switches per run:" + str(totalNumNetworkSwitchPerRun) +
                "\n\tavg=" + str(sum(totalNumNetworkSwitchPerRun)/len(totalNumNetworkSwitchPerRun)) + "\n\tmin=" + str(min(totalNumNetworkSwitchPerRun)) +
                "\n\tmax=" + str(max(totalNumNetworkSwitchPerRun)) + "\n\tmedian=" + str(median(totalNumNetworkSwitchPerRun)) +
                "\ntotal switching cost per run:" + str(totalSwitchingCostPerRun) + "\n\tavg=" + str(sum(totalSwitchingCostPerRun)/len(totalSwitchingCostPerRun)) +
                "\n\tmin=" + str(min(totalSwitchingCostPerRun)) + "\n\tmax=" + str(max(totalSwitchingCostPerRun)) + "\n\tmedian=" + str(median(totalSwitchingCostPerRun)) +
                "\n\tstd = " + str(stdSwitchingCost) + "\t 'offset' = " + str(offsetSwitchingCost) +
                "\ntotal number of reset per run:" + str(totalNumResetPerRun) + "\n\tavg:" + str(sum(totalNumResetPerRun)/len(totalNumResetPerRun)) +
                "\n\tmin=" + str(min(totalNumResetPerRun)) + "\n\tmax=" + str(max(totalNumResetPerRun)) + "\n\tmedian:" + str(median(totalNumResetPerRun)))

    # save per run download and number of network switches in csv file
    outputCSVfile = rootDir + "perRunGain_" + str(scenario) + "_" + algorithmName + ".csv"
    outfile = open(outputCSVfile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    for data in totalNumMegaBytesDownloadedPerRun: out.writerow([0, data])
    outfile.close()

    outputCSVfile = rootDir + "perRunSwitchingCost_ " + str(scenario) + "_" + algorithmName + ".csv"
    outfile = open(outputCSVfile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    for data in totalSwitchingCostPerRun: out.writerow([0, data])
    outfile.close()

print("Simulation completed")

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
main()