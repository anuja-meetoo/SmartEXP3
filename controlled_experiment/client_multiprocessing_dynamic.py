#!/usr/bin/python3

import socket, sys
import subprocess
from math import ceil, exp
import os
import argparse
from time import time, sleep
import signal
from termcolor import colored
import traceback
from random import randint, choice
from multiprocessing import Process, Manager, Value, Lock
from copy import deepcopy
import csv
from datetime import datetime
import numpy as np
import pandas

DEBUG = 0

timeSlotDuration = 15
hostIP1 = "<IP_address_of_primary_TCP_server>"
hostIP2 = "<IP_address_of_secondary_TCP_server>"
hostPort = 8000
fileDestinationIP = hostIP1
bufferSize = 1480

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def timeoutHandler(signum, frame):
    global timeSlot, timeSlotDuration, startSelectionTime, startSelectionDateTime, prevStartSelectionTime, numByteRecv
    global blockLength, maxGain, algorithmName, globalTimeSlot, startIteration, endIteration
    global delayPerTimeSlot, numByteDownloadedPerTimeSlot, numByteWithoutDelayPerTimeSlot, connectDownloadDurationPerTimeSlot
    # updatePreferredNetwork
    global preferredNetwork, numConsecutiveSlotPreferredNetwork, preferredNetworkGainList, numTimeSlotNetworkSelected
    # save details at every time slot
    global outputCSVfile, timestampPerTimeSlot, dateTimePerTimeSlot, networkSelectedPerTimeSlot, bitRatePerTimeSlot, selectionDurationPerTimeSlot
    global numByteDownloadedDuringSelectionPerTimeSlot, logPerTimeSlot, totalBytePerNetwork, numTimeSlotNetworkSelected, gainPerTimeSlotPreviousBlock
    global blockIndexPerTimeSlot, blockLengthPerTimeSlot, gammaPerTimeSlot, weightPerTimeSlot, probabilityPerTimeSlot, selectionTypePerTimeSlot

    try:
        if DEBUG >= 1: print(colored("in timeout handler for time slot" + str(timeSlot), "green"))
        if globalTimeSlot >= startIteration and globalTimeSlot <= endIteration:
            # print(colored("will perform operations in timeout handler", "red"))
            prevStartSelectionTime, startSelectionTime, startSelectionDateTime = startSelectionTime, time(), datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            # compute and store number of bytes downloaded during previous time slot
            numByteDownloadedPerTimeSlot.append(numByteRecv[0] - (sum(numByteDownloadedPerTimeSlot) + sum(numByteDownloadedDuringSelectionPerTimeSlot)))

            # compute the duration of time spent disconnecting from previous network, connecting to the network selected and downloading the file
            connectDownloadDurationPerTimeSlot.append(startSelectionTime - prevStartSelectionTime - selectionDurationPerTimeSlot[-1])

            if algorithmName == "smartEXP3": blockLength -= 1

            if len(delayPerTimeSlot) < timeSlot: delayPerTimeSlot.append(startSelectionTime - prevStartSelectionTime) #timeSlotDuration)

            # compute and store number of bytes that could have been obtained without delay in the previous time slot
            if numByteDownloadedPerTimeSlot[-1] == 0: numByteWithoutDelayPerTimeSlot.append(0)
            else: numByteWithoutDelayPerTimeSlot.append((numByteDownloadedPerTimeSlot[-1] * connectDownloadDurationPerTimeSlot[-1]) / (connectDownloadDurationPerTimeSlot[-1] - delayPerTimeSlot[-1]))
            if numByteWithoutDelayPerTimeSlot[-1] > maxGain: maxGain = numByteWithoutDelayPerTimeSlot[-1];

            # keep track of gain per time slot for current block
            gainPerTimeSlotCurrentBlock.append(numByteWithoutDelayPerTimeSlot[-1])
            totalBytePerNetwork[availableNetworkID.index(currentNetwork)] += numByteWithoutDelayPerTimeSlot[-1]  # update total bytes
            if DEBUG >= 1: print("numByteWithoutDelayPerTimeSlot: ", numByteWithoutDelayPerTimeSlot[-1], "-----", len(numByteDownloadedPerTimeSlot), ", connectDownloadDurationPerTimeSlot: ", connectDownloadDurationPerTimeSlot[-1], "-----", len(connectDownloadDurationPerTimeSlot))
            bitRate = (numByteWithoutDelayPerTimeSlot[-1] * 8) / ((1000 ** 2) * connectDownloadDurationPerTimeSlot[-1])     # in Mbps
            bitRatePerTimeSlot.append(bitRate)

            # updatePreferredNetworkDetail(numByteWithoutDelayPerTimeSlot[-1], currentNetwork)  # update details of preferred network
            highestCountTimeSlot = max(numTimeSlotNetworkSelected)
            currentPreferredNetwork = numTimeSlotNetworkSelected.index(highestCountTimeSlot) + 1
            if numTimeSlotNetworkSelected.count(highestCountTimeSlot) > 1:  # several networks have same highest count of time slots
                # no preferred network
                preferredNetwork = -1
                numConsecutiveSlotPreferredNetwork = 0
                preferredNetworkGainList = []
            else:  # single network with highest count of time slots
                if preferredNetwork != currentPreferredNetwork:
                    # change in preference
                    preferredNetwork = currentPreferredNetwork
                    numConsecutiveSlotPreferredNetwork = 1
                    preferredNetworkGainList = [numByteWithoutDelayPerTimeSlot[-1]]
                else:
                    # preferred network is same
                    if currentNetwork == preferredNetwork:
                        numConsecutiveSlotPreferredNetwork += 1
                        preferredNetworkGainList.append(numByteWithoutDelayPerTimeSlot[-1])
                    else:
                        numConsecutiveSlotPreferredNetwork = 0

            # saveCurrentTimeSlotToFile(timeSlot)
            outfile = open(outputCSVfile, "a")
            out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
            if algorithmName == "smartEXP3":
                if DEBUG >= 1: print(len(timestampPerTimeSlot), len(dateTimePerTimeSlot), len(blockIndexPerTimeSlot), len(blockLengthPerTimeSlot), len(gammaPerTimeSlot),
                      len(weightPerTimeSlot), len(probabilityPerTimeSlot), len(selectionTypePerTimeSlot), len(networkSelectedPerTimeSlot), len(delayPerTimeSlot),
                      len(numByteDownloadedPerTimeSlot), len(numByteWithoutDelayPerTimeSlot), len(bitRatePerTimeSlot), len(selectionDurationPerTimeSlot),
                      len(connectDownloadDurationPerTimeSlot), len(numByteDownloadedDuringSelectionPerTimeSlot), len(logPerTimeSlot))
                out.writerow([timeSlot, timestampPerTimeSlot[timeSlot - 1], dateTimePerTimeSlot[timeSlot - 1], blockIndexPerTimeSlot[timeSlot - 1],
                              blockLengthPerTimeSlot[timeSlot - 1], gammaPerTimeSlot[timeSlot - 1], maxGain, weightPerTimeSlot[timeSlot - 1],
                              probabilityPerTimeSlot[timeSlot - 1], selectionTypePerTimeSlot[timeSlot - 1], networkSelectedPerTimeSlot[timeSlot - 1],
                              delayPerTimeSlot[timeSlot - 1], numByteDownloadedPerTimeSlot[timeSlot - 1], numByteWithoutDelayPerTimeSlot[timeSlot - 1],
                              bitRatePerTimeSlot[timeSlot - 1], selectionDurationPerTimeSlot[timeSlot - 1], connectDownloadDurationPerTimeSlot[timeSlot - 1],
                              numByteDownloadedDuringSelectionPerTimeSlot[timeSlot - 1], totalBytePerNetwork, numTimeSlotNetworkSelected,
                              gainPerTimeSlotPreviousBlock, logPerTimeSlot[timeSlot - 1]])
            elif algorithmName == "greedy":
                out.writerow([timeSlot, timestampPerTimeSlot[timeSlot - 1], dateTimePerTimeSlot[timeSlot - 1], maxGain, networkSelectedPerTimeSlot[timeSlot - 1],
                              delayPerTimeSlot[timeSlot - 1], numByteDownloadedPerTimeSlot[timeSlot - 1], numByteWithoutDelayPerTimeSlot[timeSlot - 1],
                              bitRatePerTimeSlot[timeSlot - 1], selectionDurationPerTimeSlot[timeSlot - 1], connectDownloadDurationPerTimeSlot[timeSlot - 1],
                              numByteDownloadedDuringSelectionPerTimeSlot[timeSlot - 1], totalBytePerNetwork, numTimeSlotNetworkSelected, logPerTimeSlot[timeSlot - 1]])
        else: pass
    except IndexError:
        print("IndexError exception occurred in timeoutHandler");
        if DEBUG >= 1: traceback.print_exc()
    # except: print("exception occurred in timeoutHandler"); traceback.print_exc()
    raise Exception("end of time")  # is raised to cause the wns function to halt; else it continues execution although this function is called at specified time
    # end timeoutHandler

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def disconnect(previousNetwork):
    '''
    @description: from disconnect previousNetwork
    '''
    global availableNetworkSSID, availableNetworkID, startSelectionTime, x, startWnsTime

    try:
        if DEBUG >= 1: print(">>>>> in disconnect.....")
        # recommended to use disconnect because disconnection places the interface into a "manual" mode, in which no automatic connection will
        # start until an external event like carrier change, hibernate or sleep occurs
        # (source: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/Networking_Guide/sec-Using_the_NetworkManager_Command_Line_Tool_nmcli.html)
        timeLapsedCurrentTimeSlot = (time() - startWnsTime)
        timeoutInterval = int(round(x - timeLapsedCurrentTimeSlot))
        if timeoutInterval > 0: process = subprocess.check_output("sudo nmcli dev disconnect wlan0", timeout=timeoutInterval, stderr=subprocess.STDOUT, shell=True)

    except subprocess.CalledProcessError as e: print("exception occurred in disconnect...", e.output)#traceback.print_exc()
    except subprocess.TimeoutExpired as e: print("TimeoutExpired exception occurred in disconnect... time lapsed " + str(time() - startSelectionTime), e.output);  # traceback.print_exc()
    # end disconnect

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def connect(currentNetwork):
    '''
    @description: connect to currentNetwork, setting a timeout of the time left in the current time slot so as the
    connection is not established later in another time slot when another network is selected and being used
    '''
    global timeSlotDuration, availableNetworkSSID, startSelectionTime, x, startWnsTime

    try:
        timeLapsedCurrentTimeSlot = (time() - startWnsTime)
        timeoutInterval = int(round(x - timeLapsedCurrentTimeSlot))
        if timeoutInterval > 0:
            process = subprocess.check_output("sudo nmcli -w " + str(timeoutInterval) + " connection up id " + availableNetworkSSID[availableNetworkID.index(currentNetwork)], timeout=timeoutInterval, stderr=subprocess.STDOUT, shell=True)#, stderr=subprocess.STDOUT) #, shell=True)
    except subprocess.CalledProcessError as e: print("CalledProcessError exception occurred in connect... time lapsed " + str(time() - startSelectionTime), e.output); #traceback.print_exc()
    except subprocess.TimeoutExpired as e: print("TimeoutExpired exception occurred in connect... time lapsed " + str(time() - startSelectionTime), e.output); #traceback.print_exc()
    # except: traceback.print_exc()
    # end connect

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def isConnected(network):
    global availableNetworkSSID, availableNetworkID

    try:
        cmdOutput = subprocess.Popen("sudo nmcli device status | grep wifi", shell="True", stdout=subprocess.PIPE)
        connectionStatus, err = cmdOutput.communicate()
        # print("connection status: ", connectionStatus)
        if " connected " in str(connectionStatus) and availableNetworkSSID[availableNetworkID.index(network)] in str(connectionStatus): return True
        return False
    except subprocess.CalledProcessError as e: print("CalledProcessError exception occurred in isConnected... time lapsed " + str(time() - startSelectionTime), e.output); #traceback.print_exc()
    except TimeoutError as e: print("TimeoutError exception occured in isConnected... time lapsed " + str(time() - startSelectionTime), e.output); return ""  # traceback.print_exc()
    # end isConnected

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def downloadByte(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, startSwitchTime, hostIP1, hostIP2, hostPort):
    global numByteRecv, delayPerTimeSlot, delayCarriedToNextTimeSlot
    clientSocket = None
    try:
        if DEBUG >= 1: print(colored("in downloadByte", "blue"))
        timeLapsedCurrentTimeSlot = (time() - startWnsTime)
        timeoutInterval = int(x - timeLapsedCurrentTimeSlot)
        if timeoutInterval < 0: return

        sourceIP = subprocess.check_output("ifconfig wlan0 | grep 'inet ' | awk -F'[: ]+' '{ print $4 }'", timeout=timeoutInterval, stderr=subprocess.STDOUT, shell=True) # shell=True, universal_newlines=True)
        sourceIP = str(sourceIP).rstrip('\n')[2:-3]
        if DEBUG >= 1: print("sourceIP: ", sourceIP)

        # set the static routes accordingly so that traffic uses the appropriate interface and wireless network
        if DEBUG >= 1: print("going to set static routes..... time lapsed " + str(time() - startSelectionTime))
        os.system("sudo ip route add " + str(currentNetwork) + "0.0.0.0/24 dev wlan0 src " + str(sourceIP) + " table admin_wlan0")
        os.system("sudo ip route add default via " + str(currentNetwork) + "0.0.0.1 dev wlan0 table admin_wlan0")
        os.system("sudo ip rule add from " + str(sourceIP) + "/24 table admin_wlan0")
        os.system("sudo ip rule add to " + str(sourceIP) + "/24 table admin_wlan0")
        os.system("sudo ip route flush cache")

        if DEBUG >= 1: print("going to create client socket and connect to tcp server..... time lapsed " + str(time() - startSelectionTime))
        hostIP = hostIP2; count = 0; tcpConnection = False
        numByteBeforeConnection = numByteRecv[0] #.value
        if DEBUG >= 1: print("numByteBeforeConnection: " + str(numByteBeforeConnection))
        while numByteRecv[0] == numByteBeforeConnection:
            try:
                count += 1
                if DEBUG >= 1: print("count: ", count)
                if DEBUG >= 1: print("going to create client socket..... time lapsed " + str(time() - startSelectionTime))
                if tcpConnection == True: clientSocket.shutdown(socket.SHUT_RDWR); tcpConnection = False
                # create a TCP/IP socket object
                clientSocket = socket.socket(socket.AF_INET,  # constant implies that the socket can communicate with IPv4 addresses
                                             socket.SOCK_STREAM)  # transport protocol is TCP

                # set socket option to allow immediate reuse of local addresses after a close so that I can restart server soon after it is stopped
                # after close, a socket waits for WAIT_TIME to handle packets still on the way in the network
                clientSocket.setsockopt(socket.SOL_SOCKET,  # level at which the option is defined
                                        socket.SO_REUSEADDR,  # socket option for which the value is to be set
                                        1)  # value for the socket option; flag set to prevent socket to stay in WAIT_TIME after a close

                # bind the socket to the IP address and any available port (specified by zero)
                clientSocket.bind((sourceIP, 0))

                clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)

                # connect to the server
                timeoutInterval = x - (time() - startWnsTime)
                if timeoutInterval > 0: clientSocket.settimeout(2) #timeoutInterval)
                else: return
                hostIP = hostIP1 if hostIP == hostIP2 else hostIP2
                if DEBUG >= 1:
                    if count > 1: print(colored("trying another server..... lapsedTime:" + str(time() - startSelectionTime), "white", "on_red"))
                    print("going to connect to tcp server..... time lapsed " + str(time() - startSelectionTime))
                clientSocket.connect((hostIP, hostPort))
                tcpConnection = True
                if DEBUG >= 1:
                    print("done creating tcp connection..... time lapsed " + str(time() - startSelectionTime))
                    print("going to read bytes..... time lapsed " + str(time() - startSelectionTime))
                timeoutInterval = x - (time() - startWnsTime)
                if timeoutInterval > 0: clientSocket.settimeout(2)  # timeoutInterval)
                else: return
                msg = clientSocket.recv(1)
                delay = time() - startSwitchTime;
                if delay > timeSlotDuration: delayCarriedToNextTimeSlot[0] = delay - timeSlotDuration
                else: delayPerTimeSlot.append(delay)
                numByteRecv[0] += len(msg)  # number of bytes received

            except: print("exception in inner loop of download process....."); #traceback.print_exc()
        clientSocket.settimeout(None)  # reset the timeout after a connection =====> actually makes it blocking

        # print(colored("numByteRecv in downloadByte: " + str(numByteRecv.value), "red"))
        if DEBUG >= 1: print(colored("numByteRecv in downloadByte: " + str(numByteRecv[0]) + "..... lapsedTime:" + str(time() - startSelectionTime), "red"))
        while True:
            msg = clientSocket.recv(bufferSize)
            numByteRecv[0] += len(msg)  # number of bytes received

    except socket.error as error:
        # traceback.print_exc()
        print("SOCKET.ERROR occurred in createTCPconnection:", error, " ... time lapsed " + str(time() - startSelectionTime))
    except socket.timeout as error:
        # traceback.print_exc()
        print("SOCKET.TIMEOUT occurred in createTCPconnection:", error, " ... time lapsed " + str(time() - startSelectionTime))
    except IndexError as error:
        print("IndexError occurred in createTCPconnection:", error, " ... time lapsed " + str(time() - startSelectionTime))
    # except: traceback.print_exc(); return
    # end downloadByte

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def closeTCPconnection():
    global clientSocket

    try:
        clientSocket.shutdown(socket.SHUT_RDWR)
        clientSocket.close()
    except OSError as error:
        print(colored("OSError ----- " + str(error) + " ... time lapsed " + str(time() - startSelectionTime), "red"))
    # end closeTCPconnection

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def smartEXP3():
    '''
    @description: implements smart EXP3
    '''
    global currentNetwork, previousNetwork, availableNetworkID, numNetwork, maxGain, beta, networkToExplore, weight, probability
    global blockLength, blockIndex, blockLengthPerNetwork, numBlockNetworkSelected, probabilityCurrentBlock, switchBack, maxProbDiff
    global totalBytePerNetwork, numTimeSlotNetworkSelected, gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, highProbability, minBlockLengthPeriodicReset
    global numByteWithoutDelayPerTimeSlot, selectionTypePerTimeSlot, logPerTimeSlot, blockLengthForGreedy
    global numConsecutiveSlotPreferredNetwork, numConsecutiveSlotForReset, preferredNetworkGainList, gainRollingAvgWindowSize, totalNumReset
    global blockIndexPerTimeSlot, weightPerTimeSlot, probabilityPerTimeSlot, gammaPerTimeSlot, blockLengthPerTimeSlot

    if blockLength == 0: blockIndex += 1    # at beginning of a new block
    gamma = blockIndex ** (-1 / 3)          # compute gamma, based on  block index

    if timeSlot == 1: # first time slot
        networkSelected = choice(networkToExplore);
        print(colored("start of new block --- will explore network " + str(networkSelected), "green"))
        probabilityCurrentBlock = 1 / len(networkToExplore); selectionTypePerTimeSlot.append(2); logPerTimeSlot[timeSlot - 1].append("exploring after a reset")
        networkToExplore.remove(networkSelected)

        switchBack = False
        networkSelectedIndex = availableNetworkID.index(networkSelected)
        blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
        numBlockNetworkSelected[networkSelectedIndex] += 1
        logPerTimeSlot[timeSlot - 1].append("prob current block:" + str(probabilityCurrentBlock))
    else: # subsequent time slots; timeSlot > 1
        currentNetworkIndex = availableNetworkID.index(currentNetwork)  # list index where details of current network are stored

        # update and normalize weight
        estimatedGain = computeEstimatedGain(numByteWithoutDelayPerTimeSlot[-1])
        gammaForUpdate = ((blockIndex + 1) ** (-1 / 3)) if blockLength != 0 else gamma  # to use correct value given that update is supposed to be made once per block
        if DEBUG >= 1: print("len(logPerTimeSlot): ", len(logPerTimeSlot))
        logPerTimeSlot[timeSlot - 1].append("; gamma used= " + str(gammaForUpdate))
        weight[currentNetworkIndex] *= exp(gammaForUpdate * estimatedGain / numNetwork);  # print("before normalization, weight: ", weight)
        weight = list(w / max(weight) for w in weight);  # print("after normalization, weight: ", weight)  # normalize the weights

        # update probability
        probability = list((((1 - gammaForUpdate) * w) / sum(weight)) + (gammaForUpdate / numNetwork) for w in weight);  # print("probability: ", probability)

        maxProbability = max(probability)                           # highest probability
        convergedNetworkIndex = probability.index(maxProbability)   # list index where details of network with highest probability are stored

        ##### update blockLengthForGreedy if probability is not close to uniform as from this time slot
        if (max(probability) - min(probability)) > (1 / (numNetwork - 1)) and blockLengthForGreedy == 0:
            blockLengthForGreedy = max(2, blockLengthPerNetwork[convergedNetworkIndex])
            logPerTimeSlot[timeSlot - 1].append("SETTING blockLengthForGreedy to " + str(blockLengthForGreedy))
        print(colored("prob:" + str(probability) + ", blockLengthPerNetwork:" + str(blockLengthPerNetwork) + ", num time slots selected:" +
                      str(numTimeSlotNetworkSelected) + ", block length for greedy:" + str(blockLengthForGreedy), "white", "on_blue"));

        # check if need for reset of algorithm and reset accordingly in the next time slot
        if (maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= minBlockLengthPeriodicReset) or \
                (numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset and len(preferredNetworkGainList) >= (gainRollingAvgWindowSize + 1) and networkQualityDeclined()):
            if (maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= minBlockLengthPeriodicReset):logPerTimeSlot[timeSlot - 1].append("PERIODIC ALGORITHM RESET"); print("PERIODIC ALGORITHM RESET")
            else:logPerTimeSlot[timeSlot - 1].append("ALGORITHM RESET DUE TO NETWORK QUALITY DROP"); print("ALGORITHM RESET DUE TO NETWORK QUALITY DROP")
            reset()
            if blockLength != 0: blockIndex += 1 # else already incremented above
            blockLength = 0
            gamma = blockIndex ** (-1 / 3)  # compute gamma, based on  block index
            switchBack = False
            print(colored("@@@t = " + str(timeSlot) + " ----- algorithm has been reset", "red", "on_yellow"))
            print(colored("network to explore: " + str(networkToExplore) + "\nnumBlockNetworkSelected: " + str(numBlockNetworkSelected)
                          + "\ntotalBytePerNetwork: " + str(totalBytePerNetwork) + "\nnumTimeSlotNetworkSelected: " + str(numTimeSlotNetworkSelected)
                          + "\nblockLength: " + str(blockLength), "white", "on_blue"))

        # if second time slot of block, check if need to switch back
        if 0 not in numBlockNetworkSelected and switchBack == False and currentNetwork != previousNetwork and \
                        blockLength == (blockLengthPerNetwork[currentNetworkIndex] - 1) and mustSwitchBack(numByteWithoutDelayPerTimeSlot[-1]) == True:
            print(colored("will switch back to network " + str(previousNetwork), "blue"))
            previousNetwork, networkSelected = currentNetwork, previousNetwork
            if blockLength != 0: blockIndex += 1  # if blockLength = 0, update has already been made @line 398
            probabilityCurrentBlock = 1; switchBack = True; selectionTypePerTimeSlot.append(-1); logPerTimeSlot[timeSlot - 1].append(" ----- switch back")
            # print(colored("setting selection type to -1", "yellow"))
            networkSelectedIndex = availableNetworkID.index(networkSelected)
            blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
            numBlockNetworkSelected[networkSelectedIndex] += 1
            gainPerTimeSlotPreviousBlock, gainPerTimeSlotCurrentBlock = gainPerTimeSlotCurrentBlock, []

        elif blockLength == 0:  # start of a new block
            previousNetwork = currentNetwork
            if networkToExplore != []:
                networkSelected = choice(networkToExplore);
                print(colored("start of new block --- will explore network " + str(networkSelected), "green"))
                probabilityCurrentBlock = 1 / len(networkToExplore); selectionTypePerTimeSlot.append(2); logPerTimeSlot[timeSlot - 1].append("exploring after a reset")
                networkToExplore.remove(networkSelected)
                logPerTimeSlot[timeSlot - 1].append("prob current block:" + str(probabilityCurrentBlock))
            else:
                print(colored("no network to explore!", "green"))
                if mustSelectGreedily() == True:  # greedy
                    networkSelected, numNetworkHighestAverageByte = selectGreedily("smart", previousNetwork)
                    print(colored("start of new block --- will choose greedily network " + str(networkSelected), "green"))
                    if numNetworkHighestAverageByte > 1 and networkSelected == previousNetwork: probabilityCurrentBlock = 1/2; print(colored("GREEDY STAYING IN SAME NETWORK", "red")); selectionTypePerTimeSlot.append(1); #print(colored("setting selection type to 1", "yellow"))
                    else: probabilityCurrentBlock = (1/2) * (1/numNetworkHighestAverageByte); logPerTimeSlot[timeSlot - 1].append("choosing greedily"); selectionTypePerTimeSlot.append(1); #print(colored("setting selection type to 1", "yellow"))

                else:  # random based on probability distribution
                    networkSelected =  np.random.choice(availableNetworkID, p=probability)  # random choice
                    print(colored("start of new block --- will choose randomly network " + str(networkSelected), "green"))
                    probabilityCurrentBlock = probability[availableNetworkID.index(networkSelected)]; selectionTypePerTimeSlot.append(0); logPerTimeSlot[timeSlot - 1].append("choosing randomly")
            switchBack = False
            networkSelectedIndex = availableNetworkID.index(networkSelected)
            blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
            numBlockNetworkSelected[networkSelectedIndex] += 1
            gainPerTimeSlotPreviousBlock, gainPerTimeSlotCurrentBlock = gainPerTimeSlotCurrentBlock, []

        else:  # in the middle of a block
            print(colored("in the middle of a block", "green"))
            networkSelected = currentNetwork; previousNetwork = currentNetwork; networkSelectedIndex = availableNetworkID.index(networkSelected)
            switchBack = False
            selectionTypePerTimeSlot.append(selectionTypePerTimeSlot[-1])
            logPerTimeSlot[timeSlot - 1].append("no selection ----- in the middle of a block")
    print(colored("probability current block: " + str(probabilityCurrentBlock) + "; selection type list len: " +str(len(selectionTypePerTimeSlot)), "yellow"))

    # for log
    blockIndexPerTimeSlot.append(blockIndex); weightPerTimeSlot.append(str(weight)); probabilityPerTimeSlot.append(str(probability))
    gammaPerTimeSlot.append(gamma); blockLengthPerTimeSlot.append(blockLengthPerNetwork[networkSelectedIndex])

    return networkSelected
    # end smartEXP3

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def computeEstimatedGain(gain):
    '''
    @description: compute the estimated gain, the probability value used in the computation depends on the type of selection used
    '''
    global maxGain, probabilityCurrentBlock

    scaledGain = gain/maxGain
    estimatedGain = scaledGain/probabilityCurrentBlock
    return estimatedGain
    # end computeEstimatedGain

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def mustSwitchBack(gain):
    '''
    @description: determines whether there is a need to switch back to the previous network
    '''
    global gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, numBlockNetworkSelected, maxTimeSlotConsideredPrevBlock
    global probability, numNetwork, blockLengthPerNetwork, switchBack, currentNetwork, previousNetwork, logPerTimeSlot, timeSlot

    if len(gainPerTimeSlotPreviousBlock) <= maxTimeSlotConsideredPrevBlock: gainList = gainPerTimeSlotPreviousBlock
    else: gainList = gainPerTimeSlotPreviousBlock[(len(gainPerTimeSlotPreviousBlock) - maxTimeSlotConsideredPrevBlock):]

    averageGainPreviousBlock = sum(gainList) / len(gainList)
    gainLastTimeStepPreviousBlock = gainList[-1]

    logPerTimeSlot[timeSlot - 1].append("current gain: " + str(gain) + ", prev block gain: " + str(gainList))

    if (averageGainPreviousBlock > gain or gainLastTimeStepPreviousBlock > gain or
            ((((sum(i > gain for i in gainList) * 100) / (len(gainList))) > 50) and sum(gainList) != 0)):
        return True
    return False
    # end mustSwitchBack

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def mustSelectGreedily():
    '''
    @description: determines whether greedy selection must be leveraged
    '''
    global probability, numNetwork, blockLengthPerNetwork, numBlockNetworkSelected, blockLengthForGreedy, logPerTimeSlot, timeSlot

    highestProbabilityIndex = probability.index(max(probability))
    if 0 not in numBlockNetworkSelected and (((max(probability) - min(probability)) <= (1 / (numNetwork - 1)))
                                             or blockLengthPerNetwork[highestProbabilityIndex] <= blockLengthForGreedy):
        coinFlip = randint(1, 2)
        if coinFlip == 1:
            logPerTimeSlot[timeSlot - 1].append("flipped coin and will select greedily...")
            return True
        else: logPerTimeSlot[timeSlot - 1].append("flipped coin but will not select greedily...")
    else:
        logPerTimeSlot[timeSlot - 1].append("no need to flip coin ----- will not select greedily...; 0 not in numBlockNetworkSelected: "
                    + str(0 not in numBlockNetworkSelected) + ", diff between prob: " + str((max(probability) - min(probability))
                    <= (1 / (numNetwork - 1))) + ", blockLengthPerNetwork[highestProbabilityIndex] <= blockLengthForGreedy:"
                    + str(blockLengthPerNetwork[highestProbabilityIndex] <= blockLengthForGreedy))
    return False
    # end mustSelectGreedily

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def reset():
    '''
    @description: periodic reset of the algorithm
    '''
    global numNetwork, numBlockNetworkSelected, blockLengthPerNetwork
    global networkToExplore, totalBytePerNetwork, numTimeSlotNetworkSelected
    global preferredNetwork, numConsecutiveSlotPreferredNetwork, preferredNetworkGainList

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
    if DEBUG >= 1: print(colored("changeInGain: " + str(changeInGain), "green"));  # input()

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
    global preferredNetwork, numConsecutiveSlotPreferredNetwork, preferredNetworkGainList, numTimeSlotNetworkSelected, startSelectionTime

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
        if DEBUG >= 1: print(colored("numTimeSlotNetworkSelected: " + str(numTimeSlotNetworkSelected) + ", current network: " + str(currentNetwork) + ", preferredNetwork: " + str(preferredNetwork) + ", numConsecutiveSlotPreferredNetwork: " + str(numConsecutiveSlotPreferredNetwork) + "-----" + str(time() - startSelectionTime), "magenta"))
    # input()
    # end updatePreferredNetworkDetail

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def selectGreedily(type="naive", previousNetwork = -1):
    global totalBytePerNetwork, numTimeSlotNetworkSelected, availableNetworkID, logPerTimeSlot, timeSlot

    averageBytePerNet = list(totalByte / numTimeSlot for totalByte, numTimeSlot in zip(totalBytePerNetwork, numTimeSlotNetworkSelected))
    highestAverageByte = max(averageBytePerNet)

    ### select the (or one of the) network(s) with the highest average bandwidth
    numNetworkHighestAverageByte = averageBytePerNet.count(highestAverageByte)
    logPerTimeSlot[timeSlot - 1].append("averageBytePerNet:" + str(averageBytePerNet) + ", numNetworkHighestAverageByte: " + str(numNetworkHighestAverageByte))

    if numNetworkHighestAverageByte == 1:
        # a single network with the highest max average bandwidth
        bestNetIndex = averageBytePerNet.index(highestAverageByte)
        networkSelected = availableNetworkID[bestNetIndex]
    else:
        # several networks with the same highest average bandwidth; choose one at random
        indices = [i for i, x in enumerate(averageBytePerNet) if x == highestAverageByte]
        bestNetworkIDList = [availableNetworkID[x] for x in indices]
        if type != "naive" and previousNetwork in bestNetworkIDList: networkSelected = previousNetwork; logPerTimeSlot[timeSlot - 1].append("STAYING IN PREVIOUS NETWORK")
        else: networkSelected = choice(bestNetworkIDList)
        if DEBUG >= 1: print("numNetworkHighestAverageByte:", numNetworkHighestAverageByte)

    return networkSelected, numNetworkHighestAverageByte
    # end selectGreedily

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def greedy():
    '''
    @description: implements greedy selection
    '''
    global networkToExplore, totalBytePerNetwork, numTimeSlotNetworkSelected, availableNetworkID, previousNetwork

    previousNetwork = currentNetwork
    if networkToExplore != []:  # not yet explored all networks, pick one of those not yet explored at random
        print("not yet explored all networks")
        networkSelected = choice(networkToExplore)
        networkToExplore.remove(networkSelected)
    else:  # select the one from which the highest average gain has been observed
        print("explored all networks ----- going to choose greedily...")
        networkSelected, numNetworkHighestAverageByte = selectGreedily()
    return networkSelected
    # end greedy

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def wns():
    global algorithmName, startSwitchTime, availableNetworkSSID, timeSlot, previousNetwork, currentNetwork, timeSlotDuration, numByteRecv
    global startSelectionTime, downloadProcess, BUFFER_SIZE, x, startWnsTime, lock, delayCarriedToNextTimeSlot, globalTimeSlot
    global delayPerTimeSlot, numByteDownloadedPerTimeSlot, numByteDownloadedDuringSelectionPerTimeSlot, logPerTimeSlot, startIteration, endIteration
    global selectionDurationPerTimeSlot, connectDownloadDurationPerTimeSlot, networkSelectedPerTimeSlot, numTimeSlotNetworkSelected

    try:
        logPerTimeSlot.append([])
        if DEBUG >= 1: print("@t = ", globalTimeSlot, ", in wns..... len(logPerTimeSlot): ", len(logPerTimeSlot), ", lapsedTime:", time() - startSelectionTime)

        if globalTimeSlot < startIteration or globalTimeSlot > endIteration:
            ''' client not in the service area and not using the network '''
            if globalTimeSlot < startIteration: print(">>> client not yet joined")
            if globalTimeSlot > endIteration:
                if downloadProcess.is_alive():
                    if DEBUG >= 1: print("going to terminate download process..... lapsedTime:", time() - startSelectionTime)
                    while downloadProcess.is_alive(): downloadProcess.terminate(); downloadProcess.join();
                if DEBUG >= 1: print("done terminating download process..... lapsedTime:", time() - startSelectionTime)
                if isConnected(previousNetwork):
                    if DEBUG >= 1: print("going to disconnect from previous network, downloadProcess.is_alive(): ", downloadProcess.is_alive(), ", downloadProcess.exitcode: ", downloadProcess.exitcode, "..... lapsedTime:",time() - startSelectionTime);
                    disconnect(previousNetwork)
                if DEBUG >= 1: print("done disconnection!!!!!..... lapsedTime:", time() - startSelectionTime)
                print(">>> client already left")
            sleep(timeSlotDuration - (time() - startWnsTime) + 1)
        else:
            ''' client in the service area and using the network '''
            timeSlot = globalTimeSlot - startIteration + 1

            # select a wireless network
            if algorithmName == "smartEXP3": currentNetwork = smartEXP3()
            elif algorithmName == "greedy": currentNetwork = greedy()
            print("network selected: ", currentNetwork)

            networkSelectedPerTimeSlot.append(currentNetwork)
            numTimeSlotNetworkSelected[availableNetworkID.index(currentNetwork)] += 1  # increment no of times network selected

            if timeSlot == 1 or previousNetwork != currentNetwork:
                # first time slot or change in network
                startSwitchTime = endSelectionTime = time()
                if timeSlot == 1: print("initial start of download..... lapsedTime:", time() - startSelectionTime); numByteDownloadedDuringSelectionPerTimeSlot.append(0)
                else:
                    print("change in network... will change network and resume download..... lapsedTime:", time() - startSelectionTime)
                    if downloadProcess.is_alive():
                        if DEBUG >= 1: print("going to terminate download process..... lapsedTime:", time() - startSelectionTime)
                        while downloadProcess.is_alive(): downloadProcess.terminate(); downloadProcess.join();
                    if DEBUG >= 1: print("done terminating download process..... lapsedTime:", time() - startSelectionTime)
                    if isConnected(previousNetwork):
                        if DEBUG >= 1: print("going to disconnect from previous network, downloadProcess.is_alive(): ", downloadProcess.is_alive(), ", downloadProcess.exitcode: ", downloadProcess.exitcode, "..... lapsedTime:", time() - startSelectionTime);
                        disconnect(previousNetwork)
                    if DEBUG >= 1: print("done disconnection!!!!!..... lapsedTime:", time() - startSelectionTime)
                    numByteRecvCopy = numByteRecv[0]  # read the value before terminating the process; else get program occasionally hangs while trying to read the value :(
                    numByteRecvCopy = numByteRecvCopy - (sum(numByteDownloadedPerTimeSlot) + sum(numByteDownloadedDuringSelectionPerTimeSlot))
                    numByteDownloadedDuringSelectionPerTimeSlot.append(numByteRecvCopy)
                selectionDurationPerTimeSlot.append(endSelectionTime - startSelectionTime)
                if DEBUG >= 1:
                    print("done setting selectionDurationPerTimeSlot..... ", selectionDurationPerTimeSlot[-1], "..... lapsedTime:", time() - startSelectionTime)
                    print("going to connect to network..... lapsedTime:", time() - startSelectionTime)
                connect(currentNetwork)
                if isConnected(currentNetwork):
                    if DEBUG >= 1: print("going to start download process..... lapsedTime:", time() - startSelectionTime)
                    downloadProcess = Process(target=downloadByte, args=(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, startSwitchTime, hostIP1, hostIP2, hostPort,))
                    downloadProcess.start()
                else:
                    if DEBUG >= 1: print("could not connect to network..... lapsedTime:", time() - startSelectionTime)
            else:
                # no change in network
                selectionDurationPerTimeSlot.append(0)
                numByteDownloadedDuringSelectionPerTimeSlot.append(0)

                if isConnected(currentNetwork):
                    print("already connected to network..... lapsedTime:", time() - startSelectionTime)
                    if DEBUG >= 1: print("downloadProcess.is_alive(): ", downloadProcess.is_alive(), "..... lapsedTime:", time() - startSelectionTime)
                    if downloadProcess.is_alive():
                        if (numByteDownloadedPerTimeSlot[-1] != 0) or (numByteDownloadedPerTimeSlot[-1] == 0 and delayCarriedToNextTimeSlot[0] != 0):
                            # network and tcp connection was established and bytes were received
                            print("download process already started..... lapsedTime:", time() - startSelectionTime)
                            if DEBUG >= 1: print("setting delay to delayCarriedToNextTimeSlot " + str(delayCarriedToNextTimeSlot[0]), "..... lapsedTime:", time() - startSelectionTime)
                            delayPerTimeSlot.append(delayCarriedToNextTimeSlot[0]); delayCarriedToNextTimeSlot[0] = 0
                        else:
                            # network and tcp connection was established but no byte was received
                            print("download process already started - but no byte received - will restart it..... lapsedTime:", time() - startSelectionTime)
                            startSwitchTime = time()
                            if DEBUG >= 1: print("going to restart download process..... lapsedTime:", time() - startSelectionTime)
                            while downloadProcess.is_alive(): downloadProcess.terminate(); downloadProcess.join(); print("downloadProcess.exitcode: ", downloadProcess.exitcode,"..... lapsedTime:", time() - startSelectionTime)
                            downloadProcess = Process(target=downloadByte, args=(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, startSwitchTime, hostIP1, hostIP2, hostPort,))
                            downloadProcess.start()
                    else:
                        # network connection was established but download process was not started
                        startSwitchTime = time()
                        print("going to start download process..... lapsedTime:", time() - startSelectionTime)
                        downloadProcess = Process(target=downloadByte, args=(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, startSwitchTime, hostIP1, hostIP2, hostPort,))
                        downloadProcess.start()
                else:
                    # network connection was not established
                    startSwitchTime = time()
                    print("going to connect to network..... lapsedTime:", time() - startSelectionTime)
                    connect(currentNetwork)
                    print("going to start download process..... lapsedTime:", time() - startSelectionTime)
                    downloadProcess = Process(target=downloadByte, args=(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, startSwitchTime, hostIP1, hostIP2, hostPort,))
                    downloadProcess.start()

            sleep(timeSlotDuration - (time() - startWnsTime) + 1)   # 1 added as sometimes, wns ends before timeout and timslot incremented by 1 before timeout occurs..... appears as if 1 time slot skipped
    except:
        print("Caught exception in wns");
        if DEBUG >= 1: traceback.print_exc()
   # end wns

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
parser = argparse.ArgumentParser(description='Performs wireless network selection.')
parser.add_argument('-a', dest = "algorithm_name", required = True, help = 'name of network selection algorithm to use')
parser.add_argument('-b', dest = 'network_bandwidth', required=True, help = 'data rate of each network')
parser.add_argument('-r', dest = 'run_number', required=True, help = 'an integer to denote the current run number')
parser.add_argument('-m', dest = 'max_iteration', required=True, help = 'an integer to denote the number of iterations')
parser.add_argument('-t', dest = 'start_time', required=True, help='time at which to start the program')
parser.add_argument('-s', dest = 'start_iteration', required=True, help = 'an integer to denote the iteration number at which the client joins the service area')
parser.add_argument('-e', dest = 'end_iteration', required=True, help = 'an integer to denote the iteration number at which the client leaves the service area')

args = parser.parse_args()

### read command-line arguments
algorithmName = args.algorithm_name
bandwidth = args.network_bandwidth; bandwidth = bandwidth.split("_"); bandwidth=[int(x) for x in bandwidth]
maxGain = (timeSlotDuration * max(bandwidth) * (1000 ** 2))/8 # maximum amount of gain that is expected in one time slot in bytes
runNum = int(args.run_number)
numIteration = int(args.max_iteration)
programStartTime = float(args.start_time)
startIteration = int(args.start_iteration); startIteration = 1 if startIteration == -1 else startIteration
endIteration = int(args.end_iteration); endIteration = numIteration if endIteration == -1 else endIteration

timeSlot = 0; globalTimeSlot = 0
availableNetworkSSID = ["pink", "green", "orange"]; numNetwork = len(availableNetworkSSID); availableNetworkID = [i for i in range(1, numNetwork + 1)]
previousNetwork = currentNetwork = -1

# for EXP3
weight = [1] * numNetwork			# weight per network
probability = [1/numNetwork] * numNetwork	# probability distribution

# for block
beta = 0.1
numBlockNetworkSelected = [0] * numNetwork	# no of blocks in which each network has been selected
blockLengthPerNetwork = [0] * numNetwork	# block length for each network
blockLength = 0  				# number of time slots left in current block
blockIndex = 0					# index of current block - for computation of gamma
probabilityCurrentBlock = 1/numNetwork		# probability with which the network in the current block was selected (to compute estimated gain)

# for greedy / hybrid
totalBytePerNetwork = [0] * numNetwork
numTimeSlotNetworkSelected = [0] * numNetwork
networkToExplore = deepcopy(availableNetworkID) if algorithmName != "EXP3" else []
maxProbDiff = 1/(numNetwork - 1)	# max difference in probability distribution to consider use of greedy
blockLengthForGreedy = 0

# for switch back
maxTimeSlotConsideredPrevBlock = 8 # for switch back
gainPerTimeSlotCurrentBlock = []  	# gain observed per time slot in current block
gainPerTimeSlotPreviousBlock = []  	# gain observed per time slot in previous block
switchBack = False				    # to prevent switch backs in 2 consecutive blocks leading to ping pong between 2 networks

# for reset
highProbability = 0.75
minBlockLengthPeriodicReset = 40         # for periodic reset
preferredNetwork = -1                       # ID of network with highest time slot count
numConsecutiveSlotPreferredNetwork = 0      # number of consecutive time slots spent in current network till current time slot
preferredNetworkGainList = []               # list of gain observed in preferred network from the time it was identified as the preferred network
numConsecutiveSlotForReset = 4              # no. of consecutive time slots spent in preferred network to consider a reset
percentageDeclineForReset = 15              # minimum percentage decline (from initial gain) in preferred network to consider a reset
gainRollingAvgWindowSize = 12                # window size for rolling average of gain

# for log
manager = Manager();
delayPerTimeSlot = manager.list([])	# delay incurred per time slot; to be shared among processes
numByteRecv = manager.list([]); numByteRecv.append(0)
delayCarriedToNextTimeSlot = manager.list([]); delayCarriedToNextTimeSlot.append(0)
gammaPerTimeSlot = []				# gamma per time slot
weightPerTimeSlot = []				# per network weight per time slot
probabilityPerTimeSlot = []			# probability distribution per time slot
selectionTypePerTimeSlot = []		# type of selection per time slot; -1 - switch back, 0 - random, 1 - greedy, 2 - explore
blockIndexPerTimeSlot = []			# index of block per time slot
blockLengthPerTimeSlot = []			# length of current block per time slot
networkSelectedPerTimeSlot = []
numByteDownloadedPerTimeSlot = []
numByteWithoutDelayPerTimeSlot = []
numByteDownloadedDuringSelectionPerTimeSlot = []
selectionDurationPerTimeSlot = []
connectDownloadDurationPerTimeSlot = []
logPerTimeSlot = []
timestampPerTimeSlot = []           # timestamp at start of each time slot
dateTimePerTimeSlot = []
bitRatePerTimeSlot = []

countExceedTimeSlotDuration = 0
countZeroByte = 0
timeSlotZeroByte = []
countDelayCarriedToNextTimeSlot = 0

# get client hostname - used for filename
cmdOutput = subprocess.Popen("hostname", shell="True", stdout=subprocess.PIPE)
hostname, err = cmdOutput.communicate()
hostname = str(hostname).rstrip()[2:-3]
outputCSVfile = hostname + "_" + algorithmName + "_run" + str(runNum) + ".csv"   # e.g. rpi_1.csv

clientID = int(hostname.split("_")[1])

x = 0; startSwitchTime = startSelectionTime = startSelectionDateTime = prevStartSelectionTime = startWnsTime = time()

# disconnect from all networks
for networkID in availableNetworkID:
    if isConnected(networkID): print(colored("going to disconnect from network " + str(availableNetworkSSID[availableNetworkID.index(networkID)]), "green")); disconnect(networkID)

# save header to CSV file
outfile = open(outputCSVfile, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
if algorithmName == "smartEXP3":
    out.writerow(["time slot", "timestamp", "date time", "block index", "block length", "gamma", "max gain", "weight", "probability", "selection type", "network selected", "delay", "#bytes", "#bytes w/o delay", "bit rate (Mbps)", "selection duration", "connect and download duration", "#bytes downloaded during selection by previous network", "#bytes per network", "#time network selected", "gain prev block", "log"])
elif algorithmName == "greedy":
    out.writerow(["time slot", "timestamp", "date time", "max gain", "network selected", "delay", "#bytes", "#bytes w/o delay", "bit rate (Mbps)", "selection duration", "connect and download duration", "#bytes downloaded during selection by previous network", "#bytes per network", "#time network selected", "log"])
outfile.close()

downloadProcess = Process(target=downloadByte, args=(currentNetwork, timeSlotDuration, x, startWnsTime, bufferSize, numByteDownloadedPerTimeSlot, hostIP1, hostIP2, hostPort,))# created for global... not started yet
downloadProcess.daemon = True # when main completes, the process will also stop; source: https://stackoverflow.com/questions/25391025/what-exactly-is-python-multiprocessing-modules-join-method-doing

# wait for right time to start
tmpTime = time()
while tmpTime < programStartTime: tmpTime = time()

while globalTimeSlot < numIteration:
    try:
        if DEBUG >= 1: print(colored("going to increment globalTimeSlot to " + str(globalTimeSlot), "green", "on_white"));
        globalTimeSlot += 1
        if DEBUG >= 1: print(colored("incremented globalTimeSlot to " + str(globalTimeSlot) + "@ " + str(time()), "green", "on_white"))  # increment time step index

        # register the signal function handler
        signal.signal(signal.SIGALRM, timeoutHandler)     # for function timeout

        # define a timeout for your function
        if DEBUG >= 1: print("globalTimeSlot: ", globalTimeSlot, "downloadProcess.is_alive()?", downloadProcess.is_alive())
        if globalTimeSlot == 1:
            startSelectionTime, startSelectionDateTime = time(), datetime.now().strftime("%d/%m/%Y %H:%M:%S"); prevStartSelectionTime = startSelectionTime
        else:
            print(colored("globalTimeSlot = " + str(globalTimeSlot) + ", previous time slot:- duration = " + str(startSelectionTime - prevStartSelectionTime) + ", delay = " + str(delayPerTimeSlot[-1]) + ", #bytes recv = " + str(numByteDownloadedPerTimeSlot[-1]) + ", bit rate: " + str(bitRatePerTimeSlot[-1]), "red", "on_white"))
            if startSelectionTime - prevStartSelectionTime > (timeSlotDuration + 1): countExceedTimeSlotDuration += 1

            if globalTimeSlot >= startIteration and globalTimeSlot <= (endIteration + 1):
                if numByteDownloadedPerTimeSlot[-1] == 0: countZeroByte += 1; timeSlotZeroByte.append(globalTimeSlot - 1)
                if delayCarriedToNextTimeSlot[0] != 0: countDelayCarriedToNextTimeSlot += 1
                if bitRatePerTimeSlot[-1] < 0: break

        startWnsTime = time()
        x = timeSlotDuration - (round(startWnsTime) % timeSlotDuration) #- offset # time left to the next multiple of timeStepDuration
        if x <= 0: x = timeSlotDuration

        if DEBUG >= 1: print(colored("time slot = " + str(globalTimeSlot) + ", x = " + str(x), "yellow"))
        signal.alarm(int(x))

        timestampPerTimeSlot.append(startSelectionTime)
        dateTimePerTimeSlot.append(startSelectionDateTime)

        wns()

    except KeyboardInterrupt:
        # traceback.print_exc()
        if downloadProcess.is_alive(): downloadProcess.terminate(); downloadProcess.join()
        sys.exit(-1)

    except:
        # traceback.print_exc()
        print("Function time out")
if downloadProcess.is_alive(): downloadProcess.terminate(); downloadProcess.join()
os.system("scp " + outputCSVfile + " anuja@" + fileDestinationIP + ":/Users/anuja/Desktop/experiment_controlled/" + algorithmName + "_run" + str(runNum) + "/")
print(">>>>> countExceedTimeSlotDuration: ", countExceedTimeSlotDuration, ", countZeroByte: ", countZeroByte, " at ", timeSlotZeroByte, ", countDelayCarriedToNextTimeSlot: ", countDelayCarriedToNextTimeSlot)
os.system("echo " + "'" + algorithmName + ", run: " + str(runNum) + ", countExceedTimeSlotDuration: " + str(countExceedTimeSlotDuration) + ", countZeroByte: " + str(countZeroByte) + " at " + str(timeSlotZeroByte) + ", countDelayCarriedToNextTimeSlot: " + str(countDelayCarriedToNextTimeSlot) + "' >> runDetails.txt")