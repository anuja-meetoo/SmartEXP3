'''
@description: Wireless network selection using the Exp3 (original Exp3 and block Exp3), greedy, or exponential weighted average (for full information model and adversarial MAB setting)
'''

DEBUG = 0#-2              # 1 - only output; 2 - more details; 3 - input() after each print statement to wait for user to press a key to continue

# import external libraries
import simpy
from random import randint, choice
from numpy import random
from math import exp, sqrt, log, ceil
from copy import deepcopy
import csv                          # to save output to file
from sys import argv, float_info    # to read command line argument; float_info to get the smallest float value
from termcolor import colored
import numpy as np
import os
from scipy.stats import t, johnsonsu
import pandas


# constants
NUM_MOBILE_USERS = int(argv[1])      # number of mobile users in the service area
NUM_NETWORK = int(argv[2])             # number of wireless networks in the service area
TIME_STEP_DURATION = float(argv[3])   # duration of a time step in seconds
# SWITCHING_COST = float(argv[4])          # delay incurred (in seconds) while switching network     # used 500 ms
MAX_NUM_ITERATION = int(argv[4])    # number of iterations (time horizon)
RUN_NUM = int(argv[5])          # current run number
ALGORITHM = int(argv[6])       # 1 - original EXP3, 2 - block EXP3, 3 - hybrid block EXP3, 4 - stable hybrid block EXP3, 5 - greedy, 6 - exponential weighted average - full info model
BETA = float(argv[7])               # beta is used in block length update rule
GAIN_SCALE = float(argv[8])    # range in which gain observed is scaled
MAX_TIME_STEP_CONSIDERED_PREV_BLOCK = int(argv[9])   # 10
OUTPUT_DIR = argv[10]
SAVE_MINIMAL_DETAIL = True if int(argv[11]) == 1 else False
NETWORK_BANDWIDTH = argv[12].split("_"); NETWORK_BANDWIDTH = [int(x) for x in NETWORK_BANDWIDTH] #[4, 8, 22]#[6,12,21] #[27, 49, 84, 19, 16, 26, 53, 28, 69, 51, 87, 99, 52, 27, 32, 20, 76, 49, 24, 22, 24, 26, 49, 27, 67, 54, 86, 98, 46, 28, 30, 23] # in Mbps - [LTE, 802.11n, 802.11ac, 3G, 802.11g]

EPSILON=0.75
CONVERGED_PROBABILITY = 0.75

# global variables for saving output files (common files for all mobile users - only one user must save detail for one iteration/run)
convergenceFileWritten = False
networkFileWritten = False

minBlockLengthPeriodicReset = 40 #90
numConsecutiveSlotForReset = 4
percentageDeclineForReset = 15
gainRollingAvgWindowSize = 12 #180

''' _______________________________________________________________________________________________________________________________________________________________________ '''
class Network(object):
    ''' class to represent network objects '''
    numNetwork = 0  # keeps track of number of networks to automatically assign an ID to network upon creation

    def __init__(self, dataRate):
        Network.numNetwork = Network.numNetwork + 1 # increment number of network objects created
        self.networkID = Network.numNetwork                 # ID of network
        self.dataRate = dataRate                                      # date rate of network
        self.numUser = 0                                                   # number of users currently connected to the network
        # end __init__

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def addMobileUser(self):
        '''
        description: increments the number of users connected to the network
        arg: self
        returns: None
        '''
        self.numUser = self.numUser + 1
        # end addMobileUser

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def removeMobileUser(self):
        '''
        description: decrements the number of users connected to the network
        arg: self
        returns: None
        '''
        self.numUser = self.numUser - 1
        # end removeMobileUser

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def getPerUserBandwidth(self, delay = 0): # default value of newlyJoined = False
        '''
        description: computes the amount of bandwidth obtained by a mobile user, while ignoring as well as taking into consideration switching cost and assuming linear capacity scaling law
        args: self, newlyJoined (a boolean variable; if set to True it means that the user has joined the network in the current time step and will incur a switching cost)
        returns: amount of bandwidth obtained/could have been obtained by a specific mobile user of the network, taking into consideration switching cost
        '''
        bandwidthIgnoringDelay = (self.dataRate/self.numUser) * TIME_STEP_DURATION   # amount of bandwidth available before taking into account switching cost
        bandwidthConsideringDelay = (self.dataRate/self.numUser) * (TIME_STEP_DURATION - delay)
        
        return bandwidthIgnoringDelay, bandwidthConsideringDelay    # in Mbits
        # end getPerUserBandwidth
# end class Network

''' _______________________________________________________________________________________________________________________________________________________________________ '''
class MobileUser(object):
    ''' class to represent mobile users '''
    numMobileUser = 0  # keeps track of number of mobile users to automatically assign an ID to user upon creation

    def __init__(self, networks):
        MobileUser.numMobileUser = MobileUser.numMobileUser + 1
        self.userID = MobileUser.numMobileUser     # ID of user
        self.availableNetwork = [networkList[i].networkID for i in range(len(networkList))]    # networkIDs of set of available networks
        self.weight = [1.0] * len(self.availableNetwork)                                                           # weight assigned to each network based on gains observed from it
        self.probability = [0] * len(self.availableNetwork)                                                       # probability distribution over available networks
        self.currentNetwork = -1                         # network currently connected to
        self.numMegaBitRecv = 0                            # amount of data downloaded (takes into account switching cost)
        self.gain = 0                                    # ignoring switching cost
        self.maxGain = max(NETWORK_BANDWIDTH[:len(self.availableNetwork)]) * TIME_STEP_DURATION   # max bandwidth initialized to maximum number of Mbits a client can expect to receive in one timeslot
        self.delay = 0

        # additional attributes for greedy algorithm
        self.networkToExplore = []                                                               # ID of networks that must be sampled
        self.totalBandwidthPerNetwork = [0] * len(self.availableNetwork)   # total bandwidth observed per network so far
        self.numTimeStepNetworkSelected = [0] * len(self.availableNetwork)
        self.blockLengthForGreedy = 0  # to enable use of greedy after reset

        # additional attributes for block Exp3 algorithm
        self.blockLength = 0
        self.blockLengthPerNetwork = [1] * len(self.availableNetwork)              # block length initially chosen for each network
        self.numBlockNetworkSelected = [0] * len(self.availableNetwork)                  # keeps track of number of blocks in which each network has been selected
#         self.totalBandwidthCurrentBlock = 0          # keep running total of bandwidth obtained in current block; to be used to get average at end of block
        self.beta = BETA # beta is used in the equation to compute block length
        self.probabilityCurrentBlock = 0

        # additional attributes for log
        self.gamma_gain_scaledGain_estGain=[0, 0, 0, 0]   # all ignoring delay; created only to be able to log the values in the csv files
        self.log = []                                                              # something to log to csv file, e.g. whether it's NE, why a type of strategy is chosen, ...
        self.coinFlip = 0               # whether or not coin is flipped in this iteration
        self.chooseGreedily = 0   # whether or not choose greedily in this iteration
        self.switchPrevNet = 0     # whether or not switch to previous network in this iteration
        self.explorationAfterReset = 0  # whether the algorithm is exploring a network after a reset in this iteration
        self.numNetHighestMaxAvg = 0  # number of network(s) with the highest max average gain

        # to allow user to switch back if current network is worse
        self.networkSelectedPrevBlock = -1           # network selected in the previous block
        self.gainPerTimeStepPrevBlock = []
        self.gainPerTimeStepCurrentBlock = []
        self.resetToPrevNetwork = False
        
        # for periodic reset
        self.resetBlockLength = 0  # whether the block length has been reset in the current iteration; for log
        self.totalNumResetPeriodic = 0  # number of times block length has been reset; without any reset to zero - tru total
        self.totalNumResetDrop = 0
        self.resetPeriodicTimeSlotList = []  # time slot at which the algorithm resets periodically
        self.resetDropTimeSlotList = []  # time slot at which the algorithm resets due to network quality drop
        self.preferredNetwork = -1
        self.numConsecutiveSlotPreferredNetwork = 0
        self.preferredNetworkGainList = []
        # end __init__

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def stableHybridBlockExp3_reset(self, env, startTime, endTime):
        global convergenceFileWritten, networkFileWritten  # refers to global variables shared by all mobile users
        global numConsecutiveSlotForReset, gainRollingAvgWindowSize
        t = 1  # initialize the time step (iteration number)
        b = 1  # initialize the block index (FOR BLOCK-BASED VERSION)

        gamma = MobileUser.computeGamma(self, b)  # initialize gamma based on block index rather than time step (FOR BLOCK-BASED VERSION)
        self.networkToExplore = deepcopy(self.availableNetwork)
        initialBlockLength = MobileUser.updateBlockLength(self, 0)  # 0 refers to the number of blocks the network has been selected
        self.blockLengthPerNetwork = [initialBlockLength] * len(self.availableNetwork)
        maxProbDiff = 1 / (len(self.availableNetwork) - 1)

        while t <= MAX_NUM_ITERATION:
            # if self.userID == 1: print("t = ", t)
            if self.userID == 1 and DEBUG == -1: print(colored("user " + str(self.userID) + ", time slot " + str(t) + ", b = " + str(b) + ", gamma = " + str(gamma), "red"))
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t, "network to explore: ", self.networkToExplore);# input()
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                # solely for the purpose of saving the data in the csv file
                networkFileWritten = False  # keeps track of whether any other mobile user has already written the number of users per network in the current time step to the network.csv file
                self.gamma_gain_scaledGain_estGain = [0, 0, 0, 0]  # reset
                self.gamma_gain_scaledGain_estGain[0] = gamma
                self.log = ["beta = " + str(self.beta) + " - "]
                prevWeight = deepcopy(self.weight)
                self.resetBlockLength = 0

                ##### update probability
                if self.blockLength == 0: MobileUser.updateProbability(self, gamma)  # (1) update probability
                else: MobileUser.updateProbability(self, MobileUser.computeGamma(self, b + 1))  # (1) update probability

                maxProbability = max(self.probability)
                convergedNetworkIndex = self.probability.index(maxProbability)

                ##### update blockLengthForGreedy is probability is not close to uniform as from this time slot
                if MobileUser.isProbNearUniform(self, maxProbDiff) == False and self.blockLengthForGreedy == 0:
                    self.blockLengthForGreedy = self.blockLengthPerNetwork[convergedNetworkIndex]
                    self.log.append("SETTING blockLengthForGreedy to " + str(self.blockLengthForGreedy))
                if self.userID == 1 and DEBUG == -2: print(colored("t = " + str(t) + ", prob:" + str(self.probability) + ", blockLengthPerNetwork:" + str(self.blockLengthPerNetwork) + ", num time slots selected:" + str(self.numTimeStepNetworkSelected) + ", block length for greedy:" + str(self.blockLengthForGreedy), "white", "on_blue")); input()

                ##### check if need for reset #####
                if self.userID == 1 and DEBUG == -1:
                    print("num consecutive slots:", self.numConsecutiveSlotPreferredNetwork, ", len gain list:", len(self.preferredNetworkGainList), ", rolling avg window size:", gainRollingAvgWindowSize)

                if maxProbability >= CONVERGED_PROBABILITY and self.blockLengthPerNetwork[convergedNetworkIndex] >= minBlockLengthPeriodicReset \
                        or (self.numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset and len(self.preferredNetworkGainList) >= (gainRollingAvgWindowSize + 1) and MobileUser.networkQualityDeclined(self)):
                    if (maxProbability >= CONVERGED_PROBABILITY and self.blockLengthPerNetwork[convergedNetworkIndex] >= minBlockLengthPeriodicReset):
                        if self.userID == 1 and DEBUG == -2: print(colored("user " + str(self.userID) + ", PERIODIC reset!!!!!" + ", prob: " + str(self.probability), "yellow"));  input()
                        self.totalNumResetPeriodic += 1
                        self.resetPeriodicTimeSlotList.append(t)
                        # elif (self.numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset and len(self.preferredNetworkGainList) >= (gainRollingAvgWindowSize + 1) and MobileUser.networkQualityDeclined(self)):
                    else:
                        if self.userID == 1 and DEBUG == -2: print(colored("user " + str(self.userID) + ", reset DUE TO NETWORK QUALITY DROP!!!!!", "magenta"));  # input()
                        self.totalNumResetDrop += 1
                        self.resetDropTimeSlotList.append(t)

                    ##### to handle updates that would have been made at end of block #####
                    if self.blockLength != 0:
                        b = b + 1; gamma = MobileUser.computeGamma(self, b);
                        if self.userID == 1 and DEBUG == -1: print(colored("b = " + str(b) + ", gamma = " + str(gamma), "blue"))
                    self.gainPerTimeStepPrevBlock = deepcopy(self.gainPerTimeStepCurrentBlock)
                    ##### end to handle updates that would have been made at end of block #####

                    MobileUser.resetNetworkBlockLength(self, initialBlockLength)

                    self.blockLength = 0
                    self.resetToPrevNetwork = False  # not sure it's needed
                    # if DEBUG == -1: print(colored("@ t = " + str(t) + ", user " + str(self.userID) + " will have a periodic reset of block length, block length: " + str(self.blockLengthPerNetwork) + ", num block network selected: " + str(self.numBlockNetworkSelected), "red", "on_white"))
                ##### end check if need for reset #####

                ##### select network and observe gain
                if self.blockLength == 0: prevNetworkSelected = MobileUser.selectWirelessNetwork_stableHybridBlock(self, b, maxProbDiff)  # prevNetworkSelected is also used to compute gain (whether cost is incurred...)
                else: prevNetworkSelected = self.currentNetwork; self.delay = 0
                networkIndex = MobileUser.getListIndex(self, self.currentNetwork)

                yield env.timeout(10)
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)  # (3) observe bandwidth obtained from the wireless network selected, and re-scale it to the range [0, 1]
                estimatedGain = MobileUser.computeEstimatedGain(self, scaledGain)  # (4) compute estimated gain

                self.gainPerTimeStepCurrentBlock.append(scaledGain)
                self.totalBandwidthPerNetwork[networkIndex] += scaledGain
                self.numTimeStepNetworkSelected[networkIndex] += 1  # for greedy part
                self.log.append("totalBandwidthPerNetwork: " + str(self.totalBandwidthPerNetwork))
                self.log.append("numTimeStepNetworkSelected: " + str(self.numTimeStepNetworkSelected))
                self.log.append("totalBandwidthCurrentBlock:" + str(self.totalBandwidthCurrentBlock))

                yield env.timeout(10)

                # saving details of current time step to user, network and rateOfConvergence files
                if isNashEquilibrium(): self.log.append("Nash equilibrium")  # if NE is reached, append Nash equilibrium to log column to be saved in user file
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)  # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)  # save network details to csv file
                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)  # if NE is reached, save a record in rateOfConvergence.csv file
                elif (t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1
                if DEBUG >= 1: MobileUser.printUserDetail(self, t, prevWeight)  # output user details...

                if self.userID == 1 and DEBUG == -1: print("self.blockLength: ", self.blockLength, ", self.blockLengthPerNetwork[networkIndex]:", self.blockLengthPerNetwork[networkIndex])

                if self.resetToPrevNetwork == False:
                    ''' performed only in first timestep of current block '''
                    if self.blockLength == self.blockLengthPerNetwork[networkIndex]:
                        if self.userID == 1 and DEBUG == -1: print(">>>>> explored network " + str(self.currentNetwork) + " for 1 slot ----- going to check if need to switch back to previous network!!!!! gain:", self.gain)
                        if MobileUser.isCurrentNetworkWorse(self, scaledGain) == True:
                            if self.userID == 1 and DEBUG == -1: print(colored("switching back", "yellow"))
                            self.resetToPrevNetwork = True
                            self.blockLength = 1
                else: self.resetToPrevNetwork = False

                yield env.timeout(10)
                MobileUser.updateWeight(self, MobileUser.computeGamma(self, b + 1), estimatedGain)  # (7) update weight for the next time step based on the new value of gamma

                t = t + 1  # (5) increment number of iterations
                if (self.blockLength == 1):  # last time step in the current block                                    (FOR BLOCK-BASED VERSION)
                    b = b + 1  # (FOR BLOCK-BASED VERSION)
                    gamma = MobileUser.computeGamma(self, b)  # (6) update the value of gamma                  (FOR BLOCK-BASED VERSION)
                    self.gainPerTimeStepPrevBlock = deepcopy(self.gainPerTimeStepCurrentBlock)

                self.blockLength -= 1  # decrement the number of time steps left in the current block                                 (FOR BLOCK-BASED VERSION)
                MobileUser.updatePreferredNetworkDetail(self, self.gain, self.currentNetwork)
                if self.userID == 1 and DEBUG == -1:
                    print(colored("user " + str(self.userID) + ", current network: " + str(self.currentNetwork) + "(" + str(networkList[self.currentNetwork - 1].numUser) + "), block length: " + str(self.blockLength) + ", preferred network: " + str(self.preferredNetwork) + ", # consecutive slots: " + str(self.numConsecutiveSlotPreferredNetwork) + ", gain list: " + str(self.preferredNetworkGainList), "cyan"));

            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t); #input()

                yield env.timeout(40)

                t = t + 1
            # if self.userID == 1 and DEBUG == -1: input()
        print("user", self.userID, ", no of resets:", (self.totalNumResetPeriodic + self.totalNumResetDrop), "(periodic: " + str(self.totalNumResetPeriodic) + ", drop: " + str(self.totalNumResetDrop) + ")",", time of reset (periodic: " + str(self.resetPeriodicTimeSlotList) + ", drop: " + str(self.resetDropTimeSlotList) + ")")
        # if DEBUG >= 1:print("user", self.userID, ", no of resets:", self.totalNumReset)
        # end stableHybridBlockExp3_reset

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def resetNetworkBlockLength(self, initialBlockLength):
        self.blockLengthPerNetwork = [initialBlockLength] * len(self.availableNetwork)
        self.numBlockNetworkSelected = [0] * len(self.availableNetwork)
        self.totalBandwidthPerNetwork = [0] * len(self.availableNetwork)  # total bandwidth observed per network so far
        self.numTimeStepNetworkSelected = [0] * len(self.availableNetwork)

        self.resetBlockLength = 1
        # self.totalNumReset += 1
        self.networkToExplore = deepcopy(self.availableNetwork)
        # self.log.append(">>> RESET OF BLOCK LENGTH!!! block length: " + str(self.blockLengthPerNetwork) + ", num block net selected: " + str(self.numBlockNetworkSelected) + ", nets to explore: " + str(self.networkToExplore))

        ##### reset details of "preferred network" used to monitor its quality for reset
        self.preferredNetwork = -1
        self.numConsecutiveSlotPreferredNetwork = 0
        self.preferredNetworkGainList = []
        # end resetNetworkBlockLength

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''

    def networkQualityDeclined(self):
        '''
        @description: determines if there has been a considerable decline in network quality and reset must be sonsidered
        '''
        global gainRollingAvgWindowSize, percentageDeclineForReset

        # initialGain = preferredNetworkGainList[0]   # initial gain of preferred network (from time it was considered preferred network)
        gainList = np.array(self.preferredNetworkGainList)
        gainList = pandas.rolling_mean(gainList, gainRollingAvgWindowSize)  # rolling average of gain
        gainList = gainList[~np.isnan(gainList)]  # remove nan from list
        gainList = list(gainList)
        initialGain = gainList[0]

        changeInGain = MobileUser.computeNetworkQualityChange(self, gainList)
        lastChangeInGain = self.preferredNetworkGainList[-1] - self.preferredNetworkGainList[-2]
        # if self.userID == 1: print("gain list (rolling avg): " + str(gainList) + ", changeInGain: " + str(changeInGain));  # input()
        if self.userID == 1 and DEBUG == -1: print("user ", self.userID, ", changeInGain: ", changeInGain, ", changeInGain < 0:", changeInGain < 0, ", (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100): ",
                                                   (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100), ", gain:", self.preferredNetworkGainList, ", gain rolling avg:", gainList)
        return True if ((changeInGain < 0) and (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100)) else False
        # return True if ((changeInGain < 0) and (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100) and MobileUser.strictlyNonIncreasingChangeInGain(self, self.preferredNetworkGainList[len(self.preferredNetworkGainList) - 4:])) else False
        # return True if ((changeInGain < 0) and (abs(changeInGain) >= (percentageDeclineForReset * initialGain) / 100) and (self.preferredNetworkGainList[0] > self.preferredNetworkGainList[-1])) else False
        # end networkQualityDeclined

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''

    def computeNetworkQualityChange(self, gainList):
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

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''

    def updatePreferredNetworkDetail(self, currentGain, currentNetwork):
        '''
        @description:   updates details pertaining to current preferred network
        @args:          None
        @return:        None
        '''
        # self.preferredNetwork = -1
        # self.numConsecutiveSlotPreferredNetwork = 0
        # self.preferredNetworkGainList = []

        highestCountTimeSlot = max(self.numTimeStepNetworkSelected)
        currentPreferredNetwork = self.numTimeStepNetworkSelected.index(highestCountTimeSlot) + 1
        if self.numTimeStepNetworkSelected.count(highestCountTimeSlot) > 1:  # several networks have same highest count of time slots
            # no preferred network
            self.preferredNetwork = -1
            self.numConsecutiveSlotPreferredNetwork = 0
            self.preferredNetworkGainList = []
            if self.userID == 1 and DEBUG == -1: print(colored("No preferred network", "green"))
        else:  # single network with highest count of time slots
            if self.preferredNetwork != currentPreferredNetwork:
                # change in preference
                self.preferredNetwork = currentPreferredNetwork
                self.numConsecutiveSlotPreferredNetwork = 1
                self.preferredNetworkGainList = [currentGain]
            else:
                # preferred network is same
                if currentNetwork == self.preferredNetwork:
                    self.numConsecutiveSlotPreferredNetwork += 1
                    self.preferredNetworkGainList.append(currentGain)
                else:
                    self.numConsecutiveSlotPreferredNetwork = 0
                    # if DEBUG >= 1: print(colored("numTimeSlotNetworkSelected: " + str(self.numTimeStepNetworkSelected) + ", current network: " + str(currentNetwork) + ", preferredNetwork: " + str(self.preferredNetwork) + ", numConsecutiveSlotPreferredNetwork: " + str(
                    #         self.numConsecutiveSlotPreferredNetwork) + ", preferredNetworkGainList: " + str(self.preferredNetworkGainList), "magenta"))
                    # input()
                    # end updatePreferredNetworkDetail
    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def stableHybridBlockExp3(self, env, startTime, endTime):
        global convergenceFileWritten, networkFileWritten                   # refers to global variables shared by all mobile users
        t = 1   # initialize the time step (iteration number)
        b = 1   # initialize the block index (FOR BLOCK-BASED VERSION)

        gamma = MobileUser.computeGamma(self, b)                            # initialize gamma based on block index rather than time step (FOR BLOCK-BASED VERSION)
        self.networkToExplore = deepcopy(self.availableNetwork)
        initialBlockLength = MobileUser.updateBlockLength(self, 0)       # 0 refers to the number of blocks the network has been selected
        self.blockLengthPerNetwork = [initialBlockLength] * len(self.availableNetwork)
        maxProbDiff = 1/(len(self.availableNetwork) - 1)

        while t <= MAX_NUM_ITERATION:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                # solely for the purpose of saving the data in the csv file
                networkFileWritten = False  # keeps track of whether any other mobile user has already written the number of users per network in the current time step to the network.csv file
                self.gamma_gain_scaledGain_estGain=[0, 0, 0, 0] # reset
                self.gamma_gain_scaledGain_estGain[0] = gamma
    #             self.coinFlip = self.chooseGreedily = self.switchPrevNet = 0
                self.log = ["beta = " + str(self.beta)+ " - "]
                prevWeight = deepcopy(self.weight)

                ##### update probability
                if self.blockLength ==0: MobileUser.updateProbability(self, gamma)                                                                   # (1) update probability
                else: MobileUser.updateProbability(self, MobileUser.computeGamma(self, b + 1))                                                                   # (1) update probability

                if self.userID == 1 and DEBUG == -2: print(colored("t = " + str(t) + ", prob:" + str(self.probability) + ", blockLengthPerNetwork:" + str(self.blockLengthPerNetwork) + ", num time slots selected:" + str(self.numTimeStepNetworkSelected) + ", block length for greedy:" + str(self.blockLengthForGreedy), "white", "on_blue")); input()

                ##### select network and observe gain
                if self.blockLength == 0: prevNetworkSelected = MobileUser.selectWirelessNetwork_stableHybridBlock(self, b, maxProbDiff) # prevNetworkSelected is also used to compute gain (whether cost is incurred...)
                else: prevNetworkSelected = self.currentNetwork; self.delay = 0

                networkIndex = MobileUser.getListIndex(self, self.currentNetwork)

                yield env.timeout(10)
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)                 # (3) observe bandwidth obtained from the wireless network selected, and re-scale it to the range [0, 1]
                estimatedGain = MobileUser.computeEstimatedGain(self, scaledGain)                           # (4) compute estimated gain

                self.gainPerTimeStepCurrentBlock.append(scaledGain)
                self.totalBandwidthPerNetwork[networkIndex] += scaledGain
                self.numTimeStepNetworkSelected[networkIndex] += 1                  # for greedy part
                self.log.append("totalBandwidthPerNetwork: " + str(self.totalBandwidthPerNetwork))
                self.log.append("numTimeStepNetworkSelected: " + str(self.numTimeStepNetworkSelected))
                self.log.append("totalBandwidthCurrentBlock:" + str(self.totalBandwidthCurrentBlock))

                yield env.timeout(10)

                # saving details of current time step to user, network and rateOfConvergence files
                if isNashEquilibrium(): self.log.append("Nash equilibrium")                             # if NE is reached, append Nash equilibrium to log column to be saved in user file
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)             # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                                                              # save network details to csv file
                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)                   # if NE is reached, save a record in rateOfConvergence.csv file
                elif (t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1
                if DEBUG >=1: MobileUser.printUserDetail(self, t, prevWeight)     # output user details...

                ##### check if need to switch back to previous network #####
                if self.resetToPrevNetwork == False:
                    ''' performed only in first timestep of current block '''
                    if self.blockLength == self.blockLengthPerNetwork[networkIndex]:
                        if MobileUser.isCurrentNetworkWorse(self, scaledGain) == True:
                            self.resetToPrevNetwork = True
                            self.blockLength = 1
                else:self.resetToPrevNetwork = False
                ##### end check if need to switch back to previous network #####

                yield env.timeout(10)
                MobileUser.updateWeight(self, MobileUser.computeGamma(self, b + 1), estimatedGain)       # (7) update weight for the next time step based on the new value of gamma

                t = t + 1                                                                                   # (5) increment number of iterations
                if (self.blockLength == 1):     # last time step in the current block                                    (FOR BLOCK-BASED VERSION)
                    b = b + 1                                                                                                                                               # (FOR BLOCK-BASED VERSION)
                    gamma = MobileUser.computeGamma(self, b)                      # (6) update the value of gamma                  (FOR BLOCK-BASED VERSION)
                    self.gainPerTimeStepPrevBlock = deepcopy(self.gainPerTimeStepCurrentBlock)

                self.blockLength -= 1 # decrement the number of time steps left in the current block                                 (FOR BLOCK-BASED VERSION)
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(40)

                t = t + 1
            # end stableHybridBlockExp3

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''

    def selectGreedy(self):
        averagePerNet = list(totalBandwidth / numBlock for totalBandwidth, numBlock in
                             zip(self.totalBandwidthPerNetwork, self.numTimeStepNetworkSelected))
        maxAvgBandwidth = max(averagePerNet)
        ### select the (or one of the) network(s) with the highest average bandwidth
        # a single network with the highest max average bandwidth
        self.numNetHighestMaxAvg = averagePerNet.count(maxAvgBandwidth)
        self.log.append("averagePerNet:" + str(averagePerNet) + ", numNetHighestMaxAvg: " + str(self.numNetHighestMaxAvg))

        if self.numNetHighestMaxAvg == 1:
            bestNetIndex = averagePerNet.index(maxAvgBandwidth)
        else:  # several networks with the same highest average bandwidth; choose one at random
            indices = [i for i, x in enumerate(averagePerNet) if x == maxAvgBandwidth]
            bestNetIndex = choice(indices)
            # print("user", self.userID, ", numNetHighestMaxAvg:", self.numNetHighestMaxAvg, ", averagePerNet:", averagePerNet, ", total bandwidth: ", self.totalBandwidthPerNetwork, ", # time selected:", self.numTimeStepNetworkSelected, " selected:", self.availableNetwork[bestNetIndex]); #input()
        # bestNetIndex = averagePerNet.index(maxAvgBandwidth)
        networkSelected = self.availableNetwork[bestNetIndex]  # bestNetIndex + 1 ### for mobility scenario

        return networkSelected
    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def selectWirelessNetwork_stableHybridBlock(self, b, maxProbDiff):
        self.coinFlip = self.chooseGreedily = self.switchPrevNet = self.explorationAfterReset = self.numNetHighestMaxAvg = 0

        prevNetworkSelected = self.currentNetwork

        # for exploration after a reset
        # if self.totalNumReset > 0 and self.networkToExplore != []:
        if self.networkToExplore != []:
            self.networkSelectedPrevBlock = self.currentNetwork
            networkSelected = choice(self.networkToExplore)
            self.log.append("Exploring network" + str(networkSelected) + " from list " + str(self.networkToExplore))
            self.networkToExplore.remove(networkSelected)
            self.explorationAfterReset = 1

        # for a switch back
        elif self.resetToPrevNetwork == True:
            networkSelected = self.networkSelectedPrevBlock  # self.netIDofNetworkToResetTo       # reset network choice to previous; because prev
            self.networkSelectedPrevBlock = prevNetworkSelected
            if self.userID == 1 and DEBUG == -2: print(colored("This network seems to be worse than previous one, returning to previous network...", "yellow"))
            self.log.append("This network seems to be worse than previous one, returning to previous network...")
            self.switchPrevNet = 1

        # for greedy or random selection
        else:
            self.networkSelectedPrevBlock = self.currentNetwork
            triedAllNet = (0 not in self.numBlockNetworkSelected)
            probNearUniform = MobileUser.isProbNearUniform(self, maxProbDiff)
            maxProb = max(self.probability)
            maxProbIndex = self.probability.index(maxProb)

            if triedAllNet == False: self.log.append("not all networks have been tried...")
            if triedAllNet == True and probNearUniform != True:
                self.log.append("Prob not near uniform...")
            if self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy:
                self.log.append("block length of favored network still low...")

            # if triedAllNet == True and (probNearUniform == True or self.blockLengthPerNetwork[maxProbIndex] <= maxBlockLengthForGreedy):
            if self.userID == 1 and DEBUG == -2:
                print(colored("triedAllNet == True: " + str(triedAllNet == True) + ", probNearUniform: " + str(probNearUniform) + ", self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy: " + str(self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy), "blue", "on_white"))
            if triedAllNet == True and (probNearUniform == True or self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy):
                if self.userID == 1 and DEBUG == -2: print("in greedy loop...")
                coinFlip = randint(1,2)  # coinFlip = 1 # always choose network with highest probability if distribution is near uniform

                if coinFlip == 1:  # use deterministic approach ''' UPDATED THIS '''
                    # averagePerNet = list(totalBandwidth / numBlock for totalBandwidth, numBlock in zip(self.totalBandwidthPerNetwork, self.numTimeStepNetworkSelected))
                    # maxAvgBandwidth = max(averagePerNet)
                    # bestNetIndex = averagePerNet.index(maxAvgBandwidth)
                    # networkSelected = self.availableNetwork[bestNetIndex]  # bestNetIndex + 1 ### mor mobility scenario
                    networkSelected = MobileUser.selectGreedy(self)
                    self.log.append("coin flipped... choose network " + str(networkSelected) + " with prob 1...")
                    self.chooseGreedily = 1
                else:
                    networkSelected = random.choice(self.availableNetwork, p=self.probability)
                    self.log.append("coin flipped... but will not use deterministic version...use randomized Exp3")  # ''' UPDATED THIS '''
                self.coinFlip = 1

            else:
                networkSelected = random.choice(self.availableNetwork, p=self.probability)
                self.log.append("use randomized Exp3")

        networkIndex = MobileUser.getListIndex(self, networkSelected)

        self.blockLengthPerNetwork[networkIndex] = MobileUser.updateBlockLength(self, self.numBlockNetworkSelected[networkIndex])  # get the block length for the network selected
        self.blockLength = self.blockLengthPerNetwork[networkIndex]
        self.log.append("block length:" + str(self.blockLength))
        self.numBlockNetworkSelected[networkIndex] += 1  # increment no of block in which network has been selected

        # reset some values
        self.totalBandwidthCurrentBlock = 0  # reset total bandwidth in current block                                                     (FOR BLOCK-BASED VERSION)
        self.gainPerTimeStepCurrentBlock = []

        if prevNetworkSelected != networkSelected:  # mobile user is switching wireless network
            if prevNetworkSelected != -1: MobileUser.leaveNetwork(self, prevNetworkSelected)  # it's not the first time step where the user was not connected to any network in the previous time step
            MobileUser.joinNetwork(self, networkSelected)
            # compute delay
            self.delay = MobileUser.computeDelay(self)
        else:
            self.delay = 0

        self.currentNetwork = networkSelected
        self.probabilityCurrentBlock = self.probability[MobileUser.getListIndex(self, self.currentNetwork)]  # probability that will be used in computing estimated gain

        return prevNetworkSelected
        # end selectWirelessNetwork_stableHybridBlock
    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def hybridBlockExp3(self, env, startTime, endTime):
        global convergenceFileWritten, networkFileWritten                   # refers to global variables shared by all mobile users
        t = 1   # initialize the time step (iteration number)
        b = 1   # initialize the block index (FOR BLOCK-BASED VERSION)

        gamma = MobileUser.computeGamma(self, b)                            # initialize gamma based on block index rather than time step (FOR BLOCK-BASED VERSION)
        initialBlockLength = MobileUser.updateBlockLength(self, 0)
        self.blockLengthPerNetwork = [initialBlockLength] * len(self.availableNetwork)
        maxProbDiff = 1/(len(self.availableNetwork) - 1)

        while t <= MAX_NUM_ITERATION:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                # solely for the purpose of saving the data in the csv file
                networkFileWritten = False  # keeps track of whether any other mobile user has already written the number of users per network in the current time step to the network.csv file
                self.gamma_gain_scaledGain_estGain=[0, 0, 0, 0] # reset
                self.gamma_gain_scaledGain_estGain[0] = gamma
    #             self.coinFlip = self.chooseGreedily = 0
                self.log = ["beta = " + str(self.beta)+ " - "]
                prevWeight = deepcopy(self.weight)

                ##### update probability
                if self.blockLength ==0: MobileUser.updateProbability(self, gamma)                                                                   # (1) update probability
                else: MobileUser.updateProbability(self, MobileUser.computeGamma(self, b + 1))                                                                   # (1) update probability

                if self.userID == 1 and DEBUG == -2: print(colored("t = " + str(t) + ", prob:" + str(self.probability) + ", blockLengthPerNetwork:" + str(self.blockLengthPerNetwork) + ", num time slots selected:" + str(self.numTimeStepNetworkSelected) + ", block length for greedy:" + str(self.blockLengthForGreedy), "white", "on_blue")); input()

                ##### select network and observe gain
                if self.blockLength == 0: prevNetworkSelected = MobileUser.selectWirelessNetwork_hybridBlock(self, b, maxProbDiff)  # prevNetworkSelected is also used to compute gain (whether cost is incurred...)
                else: prevNetworkSelected = self.currentNetwork; self.delay = 0

                networkIndex = MobileUser.getListIndex(self, self.currentNetwork)

                yield env.timeout(10)
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)                 # (3) observe bandwidth obtained from the wireless network selected, and re-scale it to the range [0, 1]
                estimatedGain = MobileUser.computeEstimatedGain(self, scaledGain)                           # (4) compute estimated gain

                self.totalBandwidthPerNetwork[networkIndex] += scaledGain # for greedy part
                self.numTimeStepNetworkSelected[networkIndex] += 1                  # for greedy part
                self.log.append("totalBandwidthPerNetwork:"+ str(self.totalBandwidthPerNetwork))
                self.log.append("numTimeStepNetworkSelected:" + str(self.numTimeStepNetworkSelected))

                yield env.timeout(10)

                # saving details of current time step to user, network and rateOfConvergence files
                if isNashEquilibrium(): self.log.append("Nash equilibrium")                             # if NE is reached, append Nash equilibrium to log column to be saved in user file
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)             # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                                                              # save network details to csv file
                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)                   # if NE is reached, save a record in rateOfConvergence.csv file
                elif (t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1
                if DEBUG >=1: MobileUser.printUserDetail(self, t, prevWeight)     # output user details...

                yield env.timeout(10)

                MobileUser.updateWeight(self, MobileUser.computeGamma(self, b + 1), estimatedGain)       # (7) update weight for the next time step based on the new value of gamma

                t = t + 1                                                                                   # (5) increment number of iterations
                if (self.blockLength == 1):     # last time step in the current block                                    (FOR BLOCK-BASED VERSION)
                    b = b + 1                                                                                                                                               # (FOR BLOCK-BASED VERSION)
                    gamma = MobileUser.computeGamma(self, b)                      # (6) update the value of gamma                  (FOR BLOCK-BASED VERSION)
                self.blockLength -= 1 # decrement the number of time steps left in the current block                                 (FOR BLOCK-BASED VERSION)
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(40)

                t = t + 1
            # end hybridBlockExp3

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def selectWirelessNetwork_hybridBlock(self, b, maxProbDiff):
        self.coinFlip = self.chooseGreedily = self.numNetHighestMaxAvg = 0

        prevNetworkSelected = self.currentNetwork
        triedAllNet = (0 not in self.numBlockNetworkSelected)
        probNearUniform = MobileUser.isProbNearUniform(self, maxProbDiff)

        maxProb = max(self.probability)
        maxProbIndex = self.probability.index(maxProb)
        if triedAllNet == False: self.log.append("not all networks have been tried...")
        if triedAllNet == True and not (probNearUniform == True or self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy): self.log.append("Prob not near uniform... no need to consider deterministic approach...")

        if self.userID == 1 and DEBUG == -2:
            print(colored("triedAllNet == True: " + str(triedAllNet == True) + ", probNearUniform: " + str(probNearUniform) + ", self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy: " + str(self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy), "blue", "on_white"))
        # if triedAllNet == True and (probNearUniform == True or self.blockLengthPerNetwork[maxProbIndex] <= maxBlockLengthForGreedy):
        if triedAllNet == True and (probNearUniform == True or self.blockLengthPerNetwork[maxProbIndex] <= self.blockLengthForGreedy):
            if self.userID == 1 and DEBUG == -2: print("in greedy loop...")

            coinFlip = randint(1, 2)  # coinFlip = 1 # always choose network with highest probability if distribution is near uniform

            if coinFlip == 1:  # use deterministic approach ''' UPDATED THIS '''
                # averagePerNet = list(totalBandwidth / numBlock for totalBandwidth, numBlock in zip(self.totalBandwidthPerNetwork, self.numTimeStepNetworkSelected))
                # maxAvgBandwidth = max(averagePerNet)
                # bestNetIndex = averagePerNet.index(maxAvgBandwidth)
                # networkSelected = self.availableNetwork[bestNetIndex]  # bestNetIndex + 1 ### mor mobility scenario
                networkSelected = MobileUser.selectGreedy(self)
                self.log.append("coin flipped... choose network " + str(networkSelected) + " with prob 1...")
                self.chooseGreedily = 1
            else:
                networkSelected = random.choice(self.availableNetwork, p=self.probability)
                self.log.append("coin flipped... but will not use deterministic version...use randomized Exp3")  # ''' UPDATED THIS '''
            self.coinFlip = 1

        else:
            networkSelected = random.choice(self.availableNetwork, p=self.probability)
            self.log.append("use randomized Exp3")

        networkIndex = MobileUser.getListIndex(self, networkSelected)
        if b == 1:
            self.blockLength = self.blockLengthPerNetwork[networkIndex]
        else:
            self.blockLengthPerNetwork[networkIndex] = MobileUser.updateBlockLength(self, self.numBlockNetworkSelected[networkIndex])  # get the block length for the network selected
            self.blockLength = self.blockLengthPerNetwork[networkIndex]
        self.log.append("block length:" + str(self.blockLength))
        self.numBlockNetworkSelected[networkIndex] += 1  # increment no of block in which network has been selected

        # reset some values
        if prevNetworkSelected != networkSelected:  # mobile user is switching wireless network
            if prevNetworkSelected != -1: MobileUser.leaveNetwork(self, prevNetworkSelected)  # it's not the first time step where the user was not connected to any network in the previous time step
            MobileUser.joinNetwork(self, networkSelected)
            self.delay = MobileUser.computeDelay(self)
        else:
            self.delay = 0

        self.currentNetwork = networkSelected
        self.probabilityCurrentBlock = self.probability[MobileUser.getListIndex(self, self.currentNetwork)]  # probability that will be used in computing estimated gain
        return prevNetworkSelected
        # end selectWirelessNetwork_hybridBlock

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def blockExp3(self, env, startTime, endTime):
        '''
        description: Instead of performing network selection at every time step, it is done once per block, where a block consists of a number of time steps
        args: self, env
        returns: None
        '''
        global convergenceFileWritten, networkFileWritten                   # refers to global variables shared by all mobile users
        t = 1   # initialize the time step (iteration number)
        b = 1   # initialize the block index (FOR BLOCK-BASED VERSION)

        gamma = MobileUser.computeGamma(self, b)                            # initialize gamma based on block index rather than time step (FOR BLOCK-BASED VERSION)
        initialBlockLength = MobileUser.updateBlockLength(self, 0)
        self.blockLengthPerNetwork = [initialBlockLength] * len(self.availableNetwork)

        while t <= MAX_NUM_ITERATION:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                # solely for the purpose of saving the data in the csv file
                networkFileWritten = False  # keeps track of whether any other mobile user has already written the number of users per network in the current time step to the network.csv file
                self.gamma_gain_scaledGain_estGain=[0, 0, 0, 0] # reset
                self.gamma_gain_scaledGain_estGain[0] = gamma
                self.log = ["beta = " + str(self.beta)+ " - "]
                prevWeight = deepcopy(self.weight)

                if self.blockLength == 0: # if at the beginning of a new block    (FOR BLOCK-BASED VERSION)
                    MobileUser.updateProbability(self, gamma)                                                                   # (1) update probability
                    prevNetworkSelected = MobileUser.selectWirelessNetwork(self)   # (2) select a wireless network and connect to it

                    networkIndex = MobileUser.getListIndex(self, self.currentNetwork)                                                                                     # (FOR BLOCK-BASED VERSION)
                    self.blockLengthPerNetwork[networkIndex] = MobileUser.updateBlockLength(self, self.numBlockNetworkSelected[networkIndex]) # get the block length for the network selected
                    self.blockLength = self.blockLengthPerNetwork[networkIndex]

                    self.numBlockNetworkSelected[networkIndex] += 1     # increment number of block in which the network has been selected         (FOR BLOCK-BASED VERSION)
    #                 self.totalBandwidthCurrentBlock = 0                    # reset total bandwidth in current block                                                     (FOR BLOCK-BASED VERSION)
                    self.log.append("block length:" + str(self.blockLength))
                else:
                    MobileUser.updateProbability(self, MobileUser.computeGamma(self, b + 1))                                                                   # (1) update probability
                    prevNetworkSelected = self.currentNetwork    # not reached start of a new block yet                                                        (FOR BLOCK-BASED VERSION)
                    self.delay = 0

                yield env.timeout(10)
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)                 # (3) observe bandwidth obtained from the wireless network selected, and re-scale it to the range [0, 1]
                estimatedGain = MobileUser.computeEstimatedGain(self, scaledGain)                           # (4) compute estimated gain
    #             self.totalBandwidthCurrentBlock += scaledGain #  keep a running total of the amount of bandwidth (scaled) obtained from the selected network over time steps in the current block

                yield env.timeout(10)

                # saving details of current time step to user, network and rateOfConvergence files
                if isNashEquilibrium(): self.log.append("Nash equilibrium")                             # if NE is reached, append Nash equilibrium to log column to be saved in user file
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)             # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                                                              # save network details to csv file
                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)                   # if NE is reached, save a record in rateOfConvergence.csv file
                elif (t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1

                if DEBUG >=1: MobileUser.printUserDetail(self, t, prevWeight)     # output user details...

                yield env.timeout(10)

                MobileUser.updateWeight(self, MobileUser.computeGamma(self, b + 1), estimatedGain)       # (7) update weight for the next time step based on the new value of gamma

                t = t + 1                                                                                   # (5) increment number of iterations
                if (self.blockLength == 1):     # last time step in the current block                                                               (FOR BLOCK-BASED VERSION)
                    b = b + 1                                                                                                                                               # (FOR BLOCK-BASED VERSION)
                    gamma = MobileUser.computeGamma(self, b)                      # (6) update the value of gamma                  (FOR BLOCK-BASED VERSION)
                self.blockLength -= 1 # decrement the number of time steps left in the current block                                 (FOR BLOCK-BASED VERSION)
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(40)

                t = t + 1
            # end blockExp3

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def exp3(self, env, startTime, endTime):
        '''
        description: Performs all the steps involved in a wireless network selection using Exp3
            At each time step a users selects a wireless network at random using a probability distribution
        args: self, env
        returns: None
        '''
        global convergenceFileWritten, networkFileWritten   # refers to global variables shared by all mobile users
        t = 1   # initialize the time step (iteration number)
        gamma = MobileUser.computeGamma(self, t)             # initialize gamma

        while t <= MAX_NUM_ITERATION:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                # solely for the purpose of saving the data in the csv file
                networkFileWritten = False  # keeps track of whether any other mobile user has already written the number of users per network in the current time step to the network.csv file
                self.gamma_gain_scaledGain_estGain[0] = gamma
                self.log = []
                prevWeight = deepcopy(self.weight)

                MobileUser.updateProbability(self, gamma)                                                                   # (1) update probability
                prevNetworkSelected = MobileUser.selectWirelessNetwork(self)   # (2) select a wireless network and connect to it
                yield env.timeout(10)
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)                 # (3) observe bandwidth obtained from the wireless network selected, and re-scale it to the range [0, 1]
                estimatedGain = MobileUser.computeEstimatedGain(self, scaledGain)                           # (4) compute estimated gain
                yield env.timeout(10)

                # saving details of current time step to user, network and rateOfConvergence files
                if isNashEquilibrium(): self.log.append("Nash equilibrium")                             # if NE is reached, append Nash equilibrium to log column to be saved in user file
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)             # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                                                              # save network details to csv file
                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)                   # if NE is reached, save a record in rateOfConvergence.csv file
                elif (t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1

                if DEBUG >=1: MobileUser.printUserDetail(self, t, prevWeight)     # output user details...

                yield env.timeout(10)

                t = t + 1                                                                               # (5) increment number of iterations
                gamma = MobileUser.computeGamma(self, t)                      # (6) update the value of gamma
                MobileUser.updateWeight(self, gamma, estimatedGain)      # (7) update weight for the next time step based on the new value of gamma

            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(40)

                t = t + 1
            # end exp3

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def selectWirelessNetwork(self):
        '''
        description: selects a wireless network based on the probability distribution of the mobile user
        args: self
        returns: wireless network selected in the previous time step and the one selected in the current time step
        '''
        prevNetworkSelected = self.currentNetwork
        networkSelected = random.choice(self.availableNetwork, p=self.probability)

        # update number of users in networks; as users leave a network and join another
        if prevNetworkSelected != networkSelected: # mobile user is switching wireless network
            if prevNetworkSelected != -1: MobileUser.leaveNetwork(self, prevNetworkSelected) # it's not the first time step where the user was not connected to any network in the previous time step
            MobileUser.joinNetwork(self, networkSelected)
            self.delay = MobileUser.computeDelay(self)
        else: self.delay = 0

        self.currentNetwork = networkSelected
        self.probabilityCurrentBlock = self.probability[networkSelected - 1]    # probability that will be used in computing estimated gain
        
        return prevNetworkSelected
        # end selectWirelessNetwork

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def greedy(self, env, startTime, endTime):
        '''
        description: Performs all the steps involved in a wireless network selection using greedy algorithm
        selects each algorithm once during the first K time steps, where K is the number of networks available; then from time steps k+1 onwards, chose the network
         in which the highest amount of bandwidth was observed... (switching cost is incurred...)
        args: self, env
        return: None
        '''
        global convergenceFileWritten, networkFileWritten # global variables
        t = 1   # initialize the iteration number
        self.networkToExplore = deepcopy(self.availableNetwork)
        prevWeight = [0] * len(self.availableNetwork) # not required; only for calling saveUserDetails

        while t <= MAX_NUM_ITERATION: #True:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                networkFileWritten = False
                prevNetworkSelected = self.currentNetwork
                self.log = ["GREEDY ALGO..."]                                                           # solely for the purpose of saving the data in the csv file
                prevWeight = deepcopy(self.weight)      # make a copy of the weights since it will be required to save in cvs file later in the current iteration
                averageBandwidthPerNet = []

                # select network
                if self.networkToExplore != []:      # haven't yet tried all networks
                    self.currentNetwork = choice(self.networkToExplore)
                    self.networkToExplore.remove(self.currentNetwork)
                else: # choose greedily; the network with the highest average amount of bandwidth
                    averageBandwidthPerNet = list(totalBandwidth/numTimeStep for totalBandwidth, numTimeStep in zip(self.totalBandwidthPerNetwork, self.numTimeStepNetworkSelected))
                    highestAverageBandwidth = max(averageBandwidthPerNet)
                    self.currentNetwork = self.availableNetwork[averageBandwidthPerNet.index(highestAverageBandwidth)]

                # update number of users in networks; as users leave a network and join another
                if prevNetworkSelected != self.currentNetwork:
                    if prevNetworkSelected != -1: MobileUser.leaveNetwork(self, prevNetworkSelected)
                    MobileUser.joinNetwork(self, self.currentNetwork)
                    self.delay = MobileUser.computeDelay(self)
                else: self.delay = 0

                yield env.timeout(10)

                networkIndex = MobileUser.getListIndex(self, self.currentNetwork)       # get the index in lists where details of the specific network is saved
                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)

                #  update total bandwidth observed from the network so far
                self.totalBandwidthPerNetwork[networkIndex] += scaledGain

                #self.totalBandwidthPerNetwork[networkIndex] += scaledGain #self.actualBandwidth
                self.numTimeStepNetworkSelected[networkIndex] += 1

                self.log.append("totalBandwidthPerNetwork:" + str(self.totalBandwidthPerNetwork))
                self.log.append("numTimeStepNetworkSelected:" + str(self.numTimeStepNetworkSelected))
                self.log.append("averageBandwidthPerNet: " + str(averageBandwidthPerNet))

                yield env.timeout(10)
                if isNashEquilibrium(): # if NE is reached
                    self.log.append("Nash equilibrium")
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)                            # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                           # save network details to csv file

                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)  # save rate of convergence to csv file
                elif(t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir) # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1

                if DEBUG >=1: MobileUser.displayOutput(self, t, prevWeight)

                t = t + 1   # increment number of iterations
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(30)

                t = t + 1
                # end greedy

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def expWeightedAvgFullInfo(self, env, startTime, endTime):
        '''
        description: Performs all the steps involved in a wireless network selection using exponential weighted average in full information model
        args: self, env
        return: None
        '''
        global convergenceFileWritten, networkFileWritten # global variables
        t = 1   # initialize the iteration number
        eta = sqrt(8 * log(len(self.availableNetwork)) / t)  # value of eta without the need to know the horizon; log to base e (ln)
        while t <= MAX_NUM_ITERATION: #True:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                networkFileWritten = False
                self.gamma_gain_scaledGain_estGain[0] = eta    # solely for the purpose of saving the data in the csv file
                self.log = []                                                           # solely for the purpose of saving the data in the csv file
                prevWeight = deepcopy(self.weight)      # make a copy of the weights since it will be required to save in cvs file later in the current iteration

                self.probability = list((weight/sum(self.weight)) for weight in self.weight) # update probability
                prevNetworkSelected = self.currentNetwork
                self.currentNetwork = random.choice(self.availableNetwork, p=self.probability)          # select a wireless network

                # update number of users in networks; as users leave a network and join another
                if prevNetworkSelected != self.currentNetwork:
                    if prevNetworkSelected != -1: MobileUser.leaveNetwork(self, prevNetworkSelected)
                    MobileUser.joinNetwork(self, self.currentNetwork)
                    self.delay = MobileUser.computeDelay(self)
                else: self.delay = 0

                yield env.timeout(10)

                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)

                # store bandwidth obtained/obtainable in each network
                scaledGainPerNetwork = [0] * len(self.availableNetwork)
                scaledGainPerNetwork[self.currentNetwork - 1] = scaledGain
                for i in range(len(self.availableNetwork)):
                    if(self.currentNetwork != (i + 1)):  # already set for current network
                        scaledGainPerNetwork[i] = ((networkList[i].dataRate/(networkList[i].numUser + 1)) * TIME_STEP_DURATION)/self.maxGain

                # compute loss
                scaledLossPerNetwork = list((max(scaledGainPerNetwork) - bandwidth) for bandwidth in scaledGainPerNetwork)


                yield env.timeout(10)

                self.log.append("eta: " + str(eta) + "; ")
                self.log.append("scaledGainPerNetwork: " + str(scaledGainPerNetwork) + "; ")
                self.log.append("scaledLossPerNetwork: " + str(scaledLossPerNetwork) + "; ")


                if isNashEquilibrium(): self.log.append("Nash equilibrium")
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)             # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)                           # save network details to csv file

                if DEBUG >=1: MobileUser.displayOutput(self, t, prevWeight)

                if isNashEquilibrium(): MobileUser.saveRateOfConvergence(self, t, dir)  # save rate of convergence to csv file
                elif(t == MAX_NUM_ITERATION): MobileUser.saveRateOfConvergence(self, -1, dir)  # save rate of convergence to csv file

                t = t + 1   # increment number of iterations
                eta = sqrt(8 * log(len(self.availableNetwork)) / t)  # value of eta without the need to know the horizon; log to base e (ln)

                # update weight
                self.weight = list((w * exp(-1 * eta * scaledLoss)) for w, scaledLoss in zip(self.weight, scaledLossPerNetwork))
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(30)

                t = t + 1
            # end expWeightedAvgFullInfo

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def centralized(self, env, networkAssigned, startTime, endTime):
        global convergenceFileWritten, networkFileWritten  # global variables
        t = 1  # initialize the iteration number
        prevWeight = [0] * len(self.availableNetwork)  # not required; only for calling saveUserDetails

        while t <= MAX_NUM_ITERATION:  # True:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 3) + 1) or t == ((2 * MAX_NUM_ITERATION // 3) + 1): dir = createDir(t)

                yield env.timeout(10)

                networkFileWritten = False
                prevNetworkSelected = self.currentNetwork
                prevWeight = deepcopy(
                    self.weight)  # make a copy of the weights since it will be required to save in cvs file later in the current iteration

                # select network
                self.currentNetwork = networkAssigned
                if t == startTime:
                    MobileUser.joinNetwork(self, self.currentNetwork)
                    # compute delay
                    self.delay = MobileUser.computeDelay(self)
                else:
                    self.delay = 0

                yield env.timeout(10)

                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)

                yield env.timeout(10)
                if isNashEquilibrium():  # if NE is reached
                    self.log.append("Nash equilibrium")
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)  # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)  # save network details to csv file

                if isNashEquilibrium():
                    MobileUser.saveRateOfConvergence(self, t, dir)  # save rate of convergence to csv file
                elif (t == MAX_NUM_ITERATION):
                    MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1

                if DEBUG >= 1: MobileUser.displayOutput(self, t, prevWeight)

                t = t + 1  # increment number of iterations
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(30)

                t = t + 1
            # end centralized
    
    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def fixedRandom(self, env, startTime, endTime):
        global convergenceFileWritten, networkFileWritten  # global variables
        t = 1  # initialize the iteration number
        prevWeight = [0] * len(self.availableNetwork)  # not required; only for calling saveUserDetails

        while t <= MAX_NUM_ITERATION:  # True:
            if t >= startTime and t <= endTime:
                if t == startTime: print("user", self.userID, "is active at t =", t)
                # dynamic environment case; each time changes in the environment, save in different folder
                if t == 1 or t == ((MAX_NUM_ITERATION // 2) + 1): dir = createDir(t)

                yield env.timeout(10)

                networkFileWritten = False
                prevNetworkSelected = self.currentNetwork
                prevWeight = deepcopy(
                    self.weight)  # make a copy of the weights since it will be required to save in cvs file later in the current iteration

                # select network
                if t == startTime:
                    self.currentNetwork = randint(1, len(networkList))
                    MobileUser.joinNetwork(self, self.currentNetwork)
                    # compute delay
                    self.delay = MobileUser.computeDelay(self)
                else:
                    self.delay = 0; prevNetworkSelected = self.currentNetwork

                yield env.timeout(10)

                scaledGain = MobileUser.observeGain(self, prevNetworkSelected)

                yield env.timeout(10)
                if isNashEquilibrium():  # if NE is reached
                    self.log.append("Nash equilibrium")
                MobileUser.saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir)  # save user details to csv file
                MobileUser.saveNetworkDetail(self, t, dir)  # save network details to csv file

                if isNashEquilibrium():
                    MobileUser.saveRateOfConvergence(self, t, dir)  # save rate of convergence to csv file
                elif (t == MAX_NUM_ITERATION):
                    MobileUser.saveRateOfConvergence(self, -1, dir)  # if algorithm did not converge, still save an entry in rateOfConvergence csv file with rate of convergence set to -1

                if DEBUG >= 1: MobileUser.displayOutput(self, t, prevWeight)

                t = t + 1  # increment number of iterations
            else:
                if t == (endTime + 1):
                    MobileUser.leaveNetwork(self, self.currentNetwork)
                    self.currentNetwork = -1
                    print("user", self.userID, "is not active as from t =", t)

                yield env.timeout(30)

                t = t + 1
            # end fixedRandom
    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def computeDelay(self):
        ''' using a truncated generalized extreme value '''
        # parameters for generalized extreme value distribution
#         shape = 0.2661
#         location = 0.5890
#         scale = 0.1361
#
#         minDelay = 0.3650882794
#         maxDelay = 0.977544271
# #         minDelay = 0.1
# #         maxDelay = TIME_STEP_DURATION - 0.1
#
#         return max(minDelay, min(maxDelay, genextreme.rvs(shape, location, scale)))
        wifiDelay = [3.0659475327, 14.6918344498]  # min and max delay observed for wifi
        # timeSlotDurationInExperiment = 15     # duration of time slot in experiment done to measure delay

        # johnson su in python (fitter.Fitter.fit()) and t location-scale in matlab (allfitdist)
        # in python, error is higher for t compared to johnson su
        delay = min(max(johnsonsu.rvs(0.29822254217554717, 0.71688524931466857, loc=6.6093350624107909, scale=0.5595970482712973), wifiDelay[0]), wifiDelay[1])
        # delay /= timeSlotDurationInExperiment       # scale to (0, 1)
        if DEBUG >= 1: print(">>>>> Delay: " + str(delay))
        return delay

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def computeGamma(self, t):
        '''
        description: Computes the value of gamma based on t, without the need to know the horizon
        args: self, current time step t
        returns: value of gamma for the current time step
        '''
        return t ** (-1/3)
        # end computeGamma

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def updateProbability(self, gamma):
        '''
        description: updates the probability distribution
        args: self, the value of gamma for the current time step
        returns: None
        '''
        totalWeight = sum(self.weight)
        self.probability = list(((1 - gamma) * (weight/totalWeight)) + (gamma/len(self.availableNetwork)) for weight in self.weight)
        # end updateProbability

        ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def observeGain(self, prevNetworkSelected):
        '''
        description: return the amount of bandwidth observed by the user from the current wireless network and scale the gain to the range [0, 1]
        args: self
        returns: amount of bandwidth observed by the user
        '''
        networkIndex = MobileUser.getListIndex(self, self.currentNetwork)       # get the index in lists where details of the specific network is saved
        self.gain, self.numMegaBitRecv = networkList[networkIndex].getPerUserBandwidth(self.delay)  # in Mbits
        scaledGain = self.gain/self.maxGain          # scale gain in range [0, 1]; scaling in range [0, GAIN_SCALE] is performed after calling exp in updateWeight to avoid overflow from exp...
        
        # saving values for the purpose of logging in csv file        
        self.gamma_gain_scaledGain_estGain[1] = self.gain        
        self.gamma_gain_scaledGain_estGain[2] = scaledGain
        
        return scaledGain
        # end observeGain

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def computeEstimatedGain(self, scaledGain):
        '''
        description: calculate the estimated gain from the current network, based on the average amount of bandwidth observed and switching cost incurred
        args: self, average amount of bandwidth observed
        returns: estimated gain
        '''
        # networkIndex = MobileUser.getListIndex(self, self.currentNetwork)       # get the index in lists where details of the specific network is saved
        #
        # if self.chooseGreedily == 1: estimatedGain = scaledGain/(1/2)
        # elif self.switchPrevNet ==1 : estimatedGain = scaledGain                      # choice was deterministic
        # else: estimatedGain = scaledGain/self.probabilityCurrentBlock
        #
        # self.gamma_gain_scaledGain_estGain[3] = estimatedGain                      # saving value for the purpose of logging in csv file
        # return estimatedGain
        networkIndex = MobileUser.getListIndex(self, self.currentNetwork)  # get the index in lists where details of the specific network is saved

        if self.explorationAfterReset == 1:
            prob = 1 / (len(self.networkToExplore) + 1);  # prob = 1 / len(self.availableNetwork)  # exploration following a periodic reset
            if self.userID == 1 and DEBUG == -1: print("EXPLORATION:- user", self.userID, ", net:", self.currentNetwork, ", current block prob: ", prob)  # exploration following a periodic reset
        elif self.switchPrevNet == 1: prob = 1  # switch back to previous network; choice was deterministic
        elif self.chooseGreedily == 1: prob = (1 / 2) * (1 / self.numNetHighestMaxAvg)  # greedy choice was made; might be that many networks have same highest avg
        else:  # random choice
            if self.coinFlip == 1: prob = (1 / 2) * self.probabilityCurrentBlock  # if coin was flipped multiply by 1/2
            else: prob = self.probabilityCurrentBlock

        estimatedGain = scaledGain / prob

        self.gamma_gain_scaledGain_estGain[3] = estimatedGain  # saving value for the purpose of logging in csv file
        return estimatedGain
        # end estimateGain

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def updateWeight(self, gamma, estimatedGain):
        '''
        description: update the weight of the network selected
        args: self, gamma used in the update equation, estimated gain obtained from the current network
        returns: None
        '''
        networkIndex = MobileUser.getListIndex(self, self.currentNetwork)
        try:
#             if self.resetToPrevNetwork == True:
            self.weight[networkIndex] = self.weight[networkIndex] * (exp((gamma * estimatedGain)/len(self.availableNetwork)) ** GAIN_SCALE) # single slot...
#             else:
#                 self.weight[networkIndex] = self.weight[networkIndex] * (exp((gamma * estimatedGain)/len(self.availableNetwork)) ** (GAIN_SCALE * self.blockLengthPerNetwork[networkIndex]))
        except OverflowError:
            self.weight[networkIndex] = 1   # in case of overflow, set to 1
#         print("user", self.userID, ", gamma = ", gamma, ", estimated gain = ", estimatedGain, ", weight before normalization: ", self.weight)
        # normalize the weights; (float_info.min * float_info.epsilon) is the smallest subnormal float
        self.weight = [w/max(self.weight) if w/max(self.weight) > 0 else (float_info.min * float_info.epsilon) for w in self.weight]
        # end updateWeight

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def joinNetwork(self, networkSelected):
        '''
        description: adds user to a specified network, by incrementing the number of users in that network by 1
        arg: self, ID of network to join
        returns: None
        '''
        networkIndex = MobileUser.getListIndex(self, networkSelected)
        networkList[networkIndex].addMobileUser()
        # end joinNetwork

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def leaveNetwork(self, prevNetworkSelected):
        '''
        description: removes user from a specified network, by decrementing the number of users in that network by 1
        arg: self, ID of network to leave
        returns: None
        '''
        networkIndex = MobileUser.getListIndex(self, prevNetworkSelected)
        networkList[networkIndex].removeMobileUser()
        # end leaveNetwork

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    # given a networkID, return the index in the list where details of the network is stored (e.g. in networkList, weight, or probability...
    def getListIndex(self, networkID):
        '''
         description: returns the index of arrays at which details of the network with ID networkID is stored
         args: self, ID of the network whose details is being sought
         returns: index of array at which details of the network is stored
        '''
        return networkID - 1

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    '''
    description: checks if differences among the probability values are less than or equal to maxGap
    '''
    def isProbNearUniform(self, maxGap):
        if (max(self.probability) - min(self.probability)) > maxGap: return False
        else: return True

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def percentageElemGreaterOrEqual(self, alist, val):
        count = 0
        for num in alist:
            if num > val: count += 1
        return count*100/len(alist)

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def isCurrentNetworkWorse(self, scaledGain):    # scaled gain does not include switching cost
        triedAllNet = (0 not in self.numBlockNetworkSelected)
        if (triedAllNet == True and self.currentNetwork != self.networkSelectedPrevBlock):
            if len(self.gainPerTimeStepPrevBlock) < MAX_TIME_STEP_CONSIDERED_PREV_BLOCK: gainPerTimeStep = self.gainPerTimeStepPrevBlock
            else: gainPerTimeStep = self.gainPerTimeStepPrevBlock[len(self.gainPerTimeStepPrevBlock) - MAX_TIME_STEP_CONSIDERED_PREV_BLOCK:]
            averageGainPrevBlock = sum(gainPerTimeStep)/len(gainPerTimeStep)
            gainLastTimestepPrevBlock = gainPerTimeStep[-1]

            self.log.append("averageGainPrevBlock:" + str(averageGainPrevBlock) + "; gainLastTimestepPrevBlock:" + str(gainLastTimestepPrevBlock))

            if self.userID == 1 and DEBUG == -1: print("averageGainPrevBlock:" + str(averageGainPrevBlock) + "; gainLastTimestepPrevBlock:" + str(gainLastTimestepPrevBlock), "; scaled gain:", scaledGain)
            if ((averageGainPrevBlock > scaledGain) or (MobileUser.percentageElemGreaterOrEqual(self, gainPerTimeStep, scaledGain) > 50) or (gainLastTimestepPrevBlock > scaledGain)):
                if self.userID == 1 and DEBUG == -1: print(colored("YES", "red"))
                return True
            if self.userID == 1 and DEBUG == -1: print(colored("NO", "red"))
            return False

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    # returns two values, because for exponential rules the prevBlockLength will always be the initial length and exponential computed at each step...
    def updateBlockLength(self, numBlockNetworkSelected):
        return ceil((1 + self.beta) ** numBlockNetworkSelected)
        # end updateBlockLength

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def printUserDetail(self, t, prevWeight):
        '''
        description: prints details
        args: self, current time step t, weights of each network in the previous time step
        returns: None
        '''
        print("t:", t, ", user ", self.userID, ", prob:", self.probability, ", network selected:", self.currentNetwork, ", bandwidth:", self.actualBandwidth, ", weight:", self.weight);

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def saveUserDetail(self, t, prevWeight, prevNetworkSelected, dir = OUTPUT_DIR):
        '''
        description: save each user details
        args: self, iteration t, weight used in the previous iteration to compute the probability
        returns: None
        '''
        filename = dir+"user" + str(self.userID) + ".csv"
        networkIndex = MobileUser.getListIndex(self, self.currentNetwork)

        # build the data to be saved to the user csv file
        if SAVE_MINIMAL_DETAIL == True:
            data=[RUN_NUM, t]
            for index in range(len(prevWeight)): data.append(prevWeight[index])      # weight of networks used in this time step to calculate the probability distribution
            for index in range(len(self.probability)): data.append(self.probability[index])
            data += [self.currentNetwork, self.delay, self.numMegaBitRecv/8, self.gain/8]   # save in MB
            # append bandwidth available from other networks; each of the experts' gain
            for netIndex in range(len(networkList)):
                # print(">>>>>>>>>> in saveUserDetail:- t = ", t, ", user", self.userID, ", self.currentNetwork: ",self.currentNetwork, ", networkList[netIndex].numUser:", networkList[netIndex].numUser)

                if(networkList[netIndex].networkID == self.currentNetwork): availableBandwidth = (networkList[netIndex].dataRate/networkList[netIndex].numUser) * TIME_STEP_DURATION
                else: availableBandwidth = (networkList[netIndex].dataRate/(networkList[netIndex].numUser + 1)) * TIME_STEP_DURATION
                data.append(availableBandwidth/8)   # save in MB
            data.append(self.coinFlip)
            data.append(self.chooseGreedily)
            data.append(self.switchPrevNet)
            currentNetIndex = MobileUser.getListIndex(self, self.currentNetwork)
            data.append(self.blockLengthPerNetwork[currentNetIndex])
            data.append(self.resetBlockLength)
        else:
            data=[RUN_NUM, t, self.userID, self.gamma_gain_scaledGain_estGain[0]]
            for index in range(len(prevWeight)): data.append(prevWeight[index])      # weight of networks used in this time step to calculate the probability distribution
            for index in range(len(self.probability)): data.append(self.probability[index])
            data += [self.currentNetwork, networkList[networkIndex].numUser, self.delay, self.numMegaBitRecv/8, self.gain/8, self.gamma_gain_scaledGain_estGain[1], self.gamma_gain_scaledGain_estGain[2], self.gamma_gain_scaledGain_estGain[3]]
            # append bandwidth available from other networks; each of the experts' gain
            for netIndex in range(len(networkList)):
                if(networkList[netIndex].networkID == self.currentNetwork): availableBandwidth = (networkList[netIndex].dataRate/networkList[netIndex].numUser) * TIME_STEP_DURATION
                else: availableBandwidth = (networkList[netIndex].dataRate/(networkList[netIndex].numUser + 1)) * TIME_STEP_DURATION
                data.append(availableBandwidth/8)
            data.append(self.coinFlip)
            data.append(self.chooseGreedily)
            data.append(self.switchPrevNet)
            data.append(self.log)
            currentNetIndex = MobileUser.getListIndex(self, self.currentNetwork)
            data.append(self.blockLengthPerNetwork[currentNetIndex])
            data.append(self.networkSelectedPrevBlock)
            data.append(self.gainPerTimeStepCurrentBlock)
            data.append(self.gainPerTimeStepPrevBlock)
            data.append(self.resetBlockLength)
            data.append(self.totalNumResetPeriodic + self.totalNumResetDrop)
        # open the csv file, write the data to it and close it
        myfile = open(filename,"a")
        out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(data)
        myfile.close()
        # end saveUserDetail

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def saveNetworkDetail(self, t, dir = OUTPUT_DIR):
        '''
        description: save each network details
        args: self, iteration t
        returns: None
        '''
        global networkFileWritten

        if networkFileWritten == False:
            networkFileWritten = True
            filename = dir+"network.csv"
            data = [RUN_NUM, t, self.userID]
            for i in range(NUM_NETWORK):
                data.append(networkList[i].numUser)
            if isNashEquilibrium(): data.append("Nash equilibrium") # if NE is reached
            else: data.append("")
            if isEpsilonEquilibrium(): data.append("Epsilon equilibrium") # if epsilon equilibrium is reached
            # open the csv file, write the data to it and close it
            myfile = open(filename,"a")
            out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_ALL)
            out.writerow(data)
            myfile.close()
            # end saveNetworkDetail

    ''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
    def saveRateOfConvergence(self, t, dir = OUTPUT_DIR):
        '''
        description: save rate of convergence to file rateOfConvergence.csv
        arg: self
        returns: None
        '''
        global convergenceFileWritten

        if convergenceFileWritten == False:
            convergenceFileWritten = True
            filename = dir+"rateOfConvergence.csv"
            data=[RUN_NUM, t, self.userID]
            for i in range(NUM_NETWORK):
                data.append(networkList[i].numUser)

            # open the csv file, write the data to it and close it
            myfile = open(filename,"a")
            out = csv.writer(myfile, delimiter=',',quoting=csv.QUOTE_ALL)
            out.writerow(data)
            myfile.close()
            # end saveRateOfConvergence
# end MobileUser class

''' _______________________________________________________________________________________________________________________________________________________________________ '''
def isNashEquilibrium():
    '''
    description: checks if Nash equilibrium has been reached
    arg: None
    returns: Boolean value depending on whether it is a Nash equilibrium or not
    '''
    for i in range(len(mobileUserList)):
        selectedNetwork = mobileUserList[i].currentNetwork
        selectedNetworkIndex = mobileUserList[i].getListIndex(selectedNetwork)
        if selectedNetwork != -1:
            for j in range(len(networkList)):
                if ((networkList[j].networkID != selectedNetwork) and ((networkList[j].dataRate/(networkList[j].numUser + 1)) > (networkList[selectedNetworkIndex].dataRate/networkList[selectedNetworkIndex].numUser))):
                    return False
    return True
    # end NashEquilibrium

''' _______________________________________________________________________________________________________________________________________________________________________ '''
def isEpsilonEquilibrium():
    '''
    description: checks if Nash equilibrium has been reached
    arg: None
    returns: Boolean value depending on whether it is a Nash equilibrium or not
    '''
    for i in range(len(mobileUserList)):
        selectedNetwork = mobileUserList[i].currentNetwork
        selectedNetworkIndex = selectedNetwork - 1
        if selectedNetwork != -1:
            for j in range(len(networkList)):
                if ((networkList[j].networkID != selectedNetwork) and ((networkList[j].dataRate/(networkList[j].numUser + 1)) - (networkList[selectedNetworkIndex].dataRate/networkList[selectedNetworkIndex].numUser)) > ((networkList[selectedNetworkIndex].dataRate/networkList[selectedNetworkIndex].numUser) * EPSILON/100)):
                    return False
    return True
    # end isEpsilonEquilibrium

''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
def computeMovingAverage(values, window):
    ''' source: https://gordoncluster.wordpress.com/2014/02/13/python-numpy-how-to-generate-moving-averages-efficiently-part-2/ '''
    weights = np.repeat(1.0, window) / window
    sma = np.convolve(values, weights, 'valid')
    return sma
    # end computeMovingAverage

''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
def computeChangeInGain(gainList):
    changeInGain = 0

    prevGain = gainList[0]
    for gain in gainList[1:]: changeInGain += (gain - prevGain); prevGain = gain
    return changeInGain
    # end computeChangeInGain

''' ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- '''
def createDir(timeSlot):
    if timeSlot == 1: dir = OUTPUT_DIR + "PHASE_1/"
    elif timeSlot == ((MAX_NUM_ITERATION // 2) + 1): dir = OUTPUT_DIR + "PHASE_2/"
    # elif timeSlot == ((2 * MAX_NUM_ITERATION // 3) + 1): dir = OUTPUT_DIR + "PHASE_3/"

    if os.path.exists(dir) == False: os.makedirs(dir)

    return dir

''' _______________________________________________________________________________________________________________________________________________________________________ '''
'''
 Setup and start the simulation
'''
env = simpy.Environment()
#env = simpy.rt.RealtimeEnvironment(initial_time=0, factor=0.1, strict=True)

networkList = [Network(NETWORK_BANDWIDTH[i]) for i  in range(NUM_NETWORK)]   # create network objects and store in networkList
'''
networkList = []
for i  in range(NUM_NETWORK): #network objects and store in networkList
    networkList.append(Network(NETWORK_BANDWIDTH[i] + randint(1, 9))) # create a random number between 1 and 10, and add it to the bandwidth
for i  in range(NUM_NETWORK): print(networkList[i].dataRate, end =" ")
print()
'''
mobileUserList = [MobileUser(networkList) for i in range(NUM_MOBILE_USERS)]                                             # create mobile user objects and store in mobileUserList
# 9 users join late and leave early
numDynamicUsers = 16
for i in range(NUM_MOBILE_USERS - numDynamicUsers):
    if ALGORITHM == 1: proc=env.process(mobileUserList[i].exp3(env, 1, MAX_NUM_ITERATION))                                                            # each mobile user object calls the method exp3
    elif ALGORITHM == 2: proc=env.process(mobileUserList[i].blockExp3(env, 1, MAX_NUM_ITERATION))                                                 # each mobile user object calls the method blockExp3
    elif ALGORITHM == 3: proc=env.process(mobileUserList[i].hybridBlockExp3(env, 1, MAX_NUM_ITERATION))                                       # each mobile user object calls the method hybridBlockExp3
    elif ALGORITHM == 4: proc=env.process(mobileUserList[i].stableHybridBlockExp3(env, 1, MAX_NUM_ITERATION))                             # each mobile user object calls the method epochBlockExp3
    elif ALGORITHM == 5: proc=env.process(mobileUserList[i].stableHybridBlockExp3_reset(env, 1, MAX_NUM_ITERATION))      # each mobile user object calls the method epochBlockExp3
    elif ALGORITHM == 6: proc=env.process(mobileUserList[i].greedy(env, 1, MAX_NUM_ITERATION))                                                      # each mobile user object calls the method greedy
    elif ALGORITHM == 7: proc=env.process(mobileUserList[i].expWeightedAvgFullInfo(env, 1, MAX_NUM_ITERATION))                            # each mobile user object calls the method expWeightedAvgFullInfo
    elif ALGORITHM == 8: # each mobile user object calls the method expWeightedAvgFullInfo
        if i < 2: proc=env.process(mobileUserList[i].centralized(env, 1, 1, MAX_NUM_ITERATION))
        elif i >= 2 and i < 6: proc=env.process(mobileUserList[i].centralized(env, 2, 1, MAX_NUM_ITERATION))
        else: proc=env.process(mobileUserList[i].centralized(env, 3, 1, MAX_NUM_ITERATION))
    elif ALGORITHM == 9: proc=env.process(mobileUserList[i].fixedRandom(env, 1, MAX_NUM_ITERATION))                                             # each mobile user object calls the method fixedRandom

for i in range(NUM_MOBILE_USERS - numDynamicUsers, NUM_MOBILE_USERS):
    if ALGORITHM == 1: proc=env.process(mobileUserList[i].exp3(env, 1, MAX_NUM_ITERATION//2))                                                            # each mobile user object calls the method exp3
    elif ALGORITHM == 2: proc=env.process(mobileUserList[i].blockExp3(env, 1, MAX_NUM_ITERATION//2))                                                 # each mobile user object calls the method blockExp3
    elif ALGORITHM == 3: proc=env.process(mobileUserList[i].hybridBlockExp3(env, 1, MAX_NUM_ITERATION//2))                                       # each mobile user object calls the method hybridBlockExp3
    elif ALGORITHM == 4: proc=env.process(mobileUserList[i].stableHybridBlockExp3(env, 1, MAX_NUM_ITERATION//2))                             # each mobile user object calls the method epochBlockExp3
    elif ALGORITHM == 5: proc=env.process(mobileUserList[i].stableHybridBlockExp3_reset(env, 1, MAX_NUM_ITERATION//2))      # each mobile user object calls the method epochBlockExp3
    elif ALGORITHM == 6: proc=env.process(mobileUserList[i].greedy(env, 1, MAX_NUM_ITERATION//2))                                                      # each mobile user object calls the method greedy
    elif ALGORITHM == 7: proc=env.process(mobileUserList[i].expWeightedAvgFullInfo(env, 1, MAX_NUM_ITERATION//2))                            # each mobile user object calls the method expWeightedAvgFullInfo
    elif ALGORITHM == 8: # each mobile user object calls the method expWeightedAvgFullInfo
        if i < 2: proc=env.process(mobileUserList[i].centralized(env, 1, 1, MAX_NUM_ITERATION//2))
        elif i >= 2 and i < 6: proc=env.process(mobileUserList[i].centralized(env, 2, 1, MAX_NUM_ITERATION//2))
        else: proc=env.process(mobileUserList[i].centralized(env, 3, 1, MAX_NUM_ITERATION//2))
    elif ALGORITHM == 9: proc=env.process(mobileUserList[i].fixedRandom(env, 1, MAX_NUM_ITERATION//2))                                             # each mobile user object calls the method fixedRandom

env.run(until=proc)#SIM_TIME)
''' _______________________________________________________________________________________________________________________________________________________________________ '''

