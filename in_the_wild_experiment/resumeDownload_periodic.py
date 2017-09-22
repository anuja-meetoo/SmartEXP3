#!/usr/bin/python3

'''
@description: Downloads a file, using a selection algorithm to select the "best" network to use
@date: 3 March 2017
@version: 1.1
'''

'''
test download files' URL:
[http://scholar.princeton.edu/angelab/publications/super-Large-Pdf-100Mb]
http://scholar.princeton.edu/sites/default/files/oversize_pdf_test_0.pdf

[http://speedtest-sgp1.digitalocean.com/]
http://speedtest-sgp1.digitalocean.com/10mb.test	# 10 MB file
http://speedtest-sgp1.digitalocean.com/100mb.test	# 100 MB file
http://speedtest-sgp1.digitalocean.com/test_checksums.txt

[http://www.speedtest.com.sg/]
http://www.speedtest.com.sg/test_random_10mb.zip
http://www.speedtest.com.sg/test_random_100mb.zip
http://www.speedtest.com.sg/test_random_500mb.zip
http://www.speedtest.com.sg/test_random_1000mb.zip

MD5 Checksum
test_random_10mb.zip : a7689ef31a2e3e180dac9ae8ae27e247
test_random_100mb.zip : 0170b4ad3c993ae0d77be0cc5c5b0142
test_random_500mb.zip : 01378eacd669e4e46a3ef3e99d8e2e25
test_random_1000mb.zip : ffd134f78a288f8ec7a3839b6faddb83

[http://speedtest.ftp.otenet.gr/]
ftp://speedtest:speedtest@ftp.otenet.gr/test5Gb-a.db
'''

import os
import pycurl
import sys
from numpy import random
from random import randint, choice
from multiprocessing import Process, Manager
import subprocess
import argparse
import datetime
from copy import deepcopy
from math import ceil, exp
import signal
from time import sleep, time
from datetime import datetime
import traceback
import csv
from termcolor import colored
import numpy as np
import pandas

### global parameters
lteUUID = "8922ff30-83f5-33da-818d-2bfc3383fabf"    # USB tethered phone
# lteUUID = "199a3d51-1f6f-4422-adf5-c4f682f15270" # M1 dongle
timeSlotDuration = 15
maxBandwidth = 8 		# MBps
highProbability = 0.75
largeBlock = 40         # for periodic reset
maxBlock = 6            # for greedy
maxTimeSlotConsideredPrevBlock = 8 # for switch back
beta = 0.1
totalFileSize = 0			 # size of file to be downloaded

# url = "http://128.199.90.252/100mb.test"
# url="http://www.hostdime.com.br/2gbfile.tgz"
url = "http://202.150.221.170//test_random_500mb.zip" # "ftp://speedtest:speedtest@ftp.otenet.gr/test100Mb.db"
# url = "ftp://speedtest:speedtest@ftp.otenet.gr/test5Gb-a.db"
filename = url.split("/")[-1].strip()
outputTxtFileName = "experiment_data"
rootDir = os.getcwd() + "/"		# get the current working directory; the downloaded file will be saved there

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def progress(total, existing, upload_t, upload_d):
    '''
    @source: http://stackoverflow.com/questions/13775892/pause-and-resume-downloading-with-pycurl
    @description: dynamically displays the progress of the download (% downloaded so far) - updated to set delay
    '''
    global filename, totalFileSize, prevPercentDownload, startSwitch, delayPerTimeSlot, timeSlot, timeSlotDuration, delayCarriedToNextTimeSlot
    existing = os.path.getsize(filename)
    if totalFileSize == 0 and total > 0: totalFileSize = total + existing # total is only what is left to download

    #  compute percentage download complete - used for display of download progress
    try: percentDownload = (float(existing)*100)/float(totalFileSize)
    except:	percentDownload = 0

    # if change in percentage download and delay not yet set, then compute the delay and store it
    if percentDownload > prevPercentDownload and len(delayPerTimeSlot) < timeSlot:
        currentTime = time()
        if (currentTime - startSwitch) > timeSlotDuration:
            delayPerTimeSlot.append(timeSlotDuration)
            delayCarriedToNextTimeSlot = currentTime - startSwitch - timeSlotDuration
            print(colored("delay carried forward being saved..." + str(delayCarriedToNextTimeSlot), "magenta"))
        else: delayPerTimeSlot.append(currentTime - startSwitch)
        prevPercentDownload = percentDownload
    sys.stdout.write("\r%s %3i%%" % ("File downloaded - ", percentDownload))
    sys.stdout.flush()
    # end progress

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def debugHandler(debug_type, debug_msg):
    '''
    @source: http://stackoverflow.com/questions/13775892/pause-and-resume-downloading-with-pycurl
    '''
    print("debug(%d): %s" % (debug_type, debug_msg))
    # end debugHandler

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def fileDownload(url, filename):
    '''
    @source: http://stackoverflow.com/questions/13775892/pause-and-resume-downloading-with-pycurl
    @description: resume download of file
    '''
    # create a pycurl.Curl instance
    c = pycurl.Curl()

    # use setopt to set options
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.FOLLOWLOCATION, 1)	# allow libcurl to follow redirects
    c.setopt(pycurl.MAXREDIRS, 5)

    # Setup writing
    if os.path.exists(filename):
        # file already exists - open in append and binary (then response body can be written bytewise without decoding or encoding steps) mode
        f = open(filename, "ab")
        c.setopt(pycurl.RESUME_FROM, os.path.getsize(filename))
    else:
        # file does not exist - open in write and binary (then response body can be written bytewise without decoding or encoding steps) mode
        f = open(filename, "wb")

    c.setopt(pycurl.WRITEDATA, f)	# write to the file f

    # #c.setopt(pycurl.VERBOSE, 1)
    c.setopt(pycurl.DEBUGFUNCTION, debugHandler)		# callback for debug
    c.setopt(pycurl.NOPROGRESS, 0)			# switch on the progress meter; to allow the callback for progress meter to be called
    c.setopt(pycurl.PROGRESSFUNCTION, progress)	# callback for progress meter

    try:
        # perform the operation
        print(colored("going to download the file...", "green"))
        c.perform()
        c.close()
    except KeyboardInterrupt:
        # traceback.print_exc()
        print("ctrl+c pressed... stopping process readBytes...")
        c.close()
        sys.exit(-1)
    except:
        # traceback.print_exc()
        c.close()
        sys.exit(-1)
    print()
    # end fileDownload

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def timeoutHandler(signum, frame):
    '''
    @description: handler called upon a timeout, it sets the delay in case of unsuccessful network connection, and the bytes received
    '''
    global filename, algorithmName, timeSlot, timeSlotDuration, maxGain, blockLength, currentNetwork, availableNetworkID
    global delayPerTimeSlot, numByteDownloadedPerTimeSlot, numByteWithoutDelayPerTimeSlot, gainPerTimeSlotCurrentBlock, totalBytePerNetwork
    global connectDownloadDurationPerTimeSlot, selectionDurationPerTimeSlot, numByteDownloadedDuringSelectionPerTimeSlot
    global startSelectionTime, prevStartSelectionTime, bitRatePerTimeSlot, dateTime

    try:
        print(colored("timeout being handled...","red"))

        numByteDownloaded = os.path.getsize(filename) if os.path.exists(filename) else 0    # get the number of bytes downloaded so far

        # ##### all download from this point onwards is excluded from details of the previous time slot
        # compute the duration of time spent disconnecting from previous network, connecting to the network selected and downloading the file
        prevStartSelectionTime, startSelectionTime, dateTime = startSelectionTime, time(), datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        connectDownloadDurationPerTimeSlot.append(startSelectionTime - prevStartSelectionTime - selectionDurationPerTimeSlot[-1])
        print(colored("startSelectionTime being set to " + str(startSelectionTime) + ", #bytes read:" + str(numByteDownloaded), "blue"))
        if algorithmName == "smartEXP3": blockLength -= 1

        # set the delay if it hasn't been set, implying that no data could be downloaded in the previous time slot
        if len(delayPerTimeSlot) < timeSlot: delayPerTimeSlot.append(timeSlotDuration)

        # compute and store number of bytes downloaded in last time slot
        if delayPerTimeSlot[-1] == timeSlotDuration: numByteDownloadedLastTimeSlot = 0
        else: numByteDownloadedLastTimeSlot = numByteDownloaded - sum(numByteDownloadedPerTimeSlot) - sum(numByteDownloadedDuringSelectionPerTimeSlot)
        numByteDownloadedPerTimeSlot.append(numByteDownloadedLastTimeSlot)

        # compute and store gain that could be observed in the absence of switching cost
        if numByteDownloadedLastTimeSlot == 0: numByteWithoutDelay = 0
        else: numByteWithoutDelay = (numByteDownloadedLastTimeSlot * timeSlotDuration) / (connectDownloadDurationPerTimeSlot[-1] - delayPerTimeSlot[-1])
        numByteWithoutDelayPerTimeSlot.append(numByteWithoutDelay)
        print(">>> numByteDownloadedLastTimeSlot:", numByteDownloadedLastTimeSlot, ", numByteWithoutDelay:", numByteWithoutDelay)
        # update maxGain if required
        if numByteWithoutDelay > maxGain: maxGain = numByteWithoutDelay; print(colored("updating maxGain", "red"))

        # keep track of gain per time slot for current block
        gainPerTimeSlotCurrentBlock.append(numByteWithoutDelay)
        totalBytePerNetwork[availableNetworkID.index(currentNetwork)] += numByteWithoutDelayPerTimeSlot[-1] # update total bytes

        bitRate = (numByteWithoutDelay * 8)/((1000**2) * timeSlotDuration)
        bitRatePerTimeSlot.append(bitRate)
        print(colored("Bit rate observed: %.2f Mbps" %(bitRate), "red", "on_white"))

        updatePreferredNetworkDetail(numByteWithoutDelayPerTimeSlot[-1], currentNetwork)  # update details of preferred network
        saveCurrentTimeslotToFile(timeSlot)
    except: print("exception occurred in timeoutHandler"); traceback.print_exc()
    raise Exception("end of time")
    # end timeoutHandler

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def disconnect(previousNetwork):
    '''
    @description: from disconnect previousNetwork
    '''
    global wifiSSID, lteUUID

    try:
        # The subprocess module allows you to spawn new processes, connect to their input/output/error pipes, and obtain their return codes.
        # source: http://stackoverflow.com/questions/325463/launch-a-shell-command-with-in-a-python-script-wait-for-the-termination-and-ret
        if previousNetwork == 1:
            process = subprocess.Popen("nmcli connection down id " + wifiSSID, shell=True, stdout=subprocess.PIPE)
        elif previousNetwork == 2:
            process = subprocess.Popen("nmcli con down uuid " + lteUUID, shell=True, stdout=subprocess.PIPE) # singtel
        status = process.wait()
    except: print("exception occurred in disconnect")#traceback.print_exc()
    # end disconnect

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def connect(currentNetwork, startTime):
    '''
    @description: connect to currentNetwork, setting a timeout of the time left in the current time slot so as the
    connection is not established later in another time slot when another network is selected and being used
    '''
    global timeSlotDuration, wifiSSID, lteUUID
    wifiAP = ""

    try:
        timeLapsedCurrentTimeSlot = (time() - startTime)
        timeoutInterval = int(ceil(timeSlotDuration - timeLapsedCurrentTimeSlot))
        # print(colored("timeoutInterval:" + str(timeoutInterval) + ", time lapsed:" + str(timeLapsedCurrentTimeSlot),"red", "on_white"))
        if currentNetwork == 1:
            # process = subprocess.Popen("sudo ip link set dev wlp2s0 down && sudo ifconfig wlp2s0 hw ether 10:0b:a9:ba:9f:5e && sudo ip link set dev wlp2s0 up", shell=True, stdout=subprocess.PIPE)
            process = subprocess.Popen("nmcli -w " + str(timeoutInterval) + " connection up id " + wifiSSID, shell=True, stdout=subprocess.PIPE)
            status = process.wait()
            if isConnected(1):wifiAP = saveWiFiAPdetail()
        else:
            process = subprocess.Popen("nmcli -w " + str(timeoutInterval) + " con up uuid " + lteUUID, shell=True, stdout=subprocess.PIPE)
            status = process.wait()
        return wifiAP
    except: print("exception occurred in connect")#traceback.print_exc()
    # end connect

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def isConnected(network):
    try:
        if network == 1:
            cmdOutput = subprocess.Popen("nmcli device status | grep wifi", shell="True", stdout=subprocess.PIPE)
            connectionStatus, err = cmdOutput.communicate()
            if " connected " in str(connectionStatus): return True
        else:
            # cmdOutput = subprocess.Popen("nmcli device status | grep gsm", shell="True", stdout=subprocess.PIPE)
            cmdOutput = subprocess.Popen("nmcli device status | grep USBtetheredPhone", shell="True", stdout=subprocess.PIPE)
            connectionStatus, err = cmdOutput.communicate()
            if " connected " in str(connectionStatus): return True
        return False
    except: print("exception occured in isConnected"); return "" #traceback.print_exc()
    # end isConnected

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def wns(url): #, timeSlot, delayPerTimeSlot, algorithmName): # 1 - wifi, 2 - lte
    '''
    @description: performs network selection, changes network if required and resumes file download
    '''
    global algorithmName, timeSlot, timeSlotDuration, startSelectionTime, startSwitch, currentNetwork, previousNetwork, p
    global availableNetworkID, availableNetworkName, filename, blockLength
    global delayPerTimeSlot, networkSelectedPerTimeSlot, numTimeSlotNetworkSelected, delayCarriedToNextTimeSlot
    global numByteDownloadedDuringSelectionPerTimeSlot, selectionDurationPerTimeSlot

    try:
        logPerTimeSlot.append([])

        additionalDelay = 0
        # select network
        if algorithmName == "smartEXP3": currentNetwork = smartEXP3()
        elif algorithmName == "greedy": currentNetwork = greedy()
        elif algorithmName == "wifi": previousNetwork = currentNetwork; currentNetwork = 1  # only wifi
        else: previousNetwork = currentNetwork; currentNetwork = 2  # only cellular

        print("\n")
        print(colored("@time slot:" + str(timeSlot) + ", network selected = " + availableNetworkName[availableNetworkID.index(currentNetwork)] \
                      + " for " + str(blockLength) + " time slots...", "white", "on_blue"))
        print("prob:", probability)
        networkSelectedPerTimeSlot.append(availableNetworkName[availableNetworkID.index(currentNetwork)])
        numTimeSlotNetworkSelected[availableNetworkID.index(currentNetwork)] += 1  # increment no of times network selected

        if timeSlot == 1 or previousNetwork != currentNetwork:  # first time slot or change in network
            if timeSlot == 1:
                print("initial start of download")
                endSelectionTime = time()
                selectionDurationPerTimeSlot.append(endSelectionTime - startSelectionTime)
                numByteDownloadedDuringSelectionPerTimeSlot.append(0)
                # print("selectionDurationPerTimeSlot:", selectionDurationPerTimeSlot, ", numByteDownloadedDuringSelectionPerTimeSlot:", numByteDownloadedDuringSelectionPerTimeSlot)

            else: # timeSlot > 1
                print("change in network... will change network and resume download...")
                startSwitch = time()
                # print("p==None?", p == None)
                if p != None and delayPerTimeSlot[-1] != timeSlotDuration:
                    print(">>>>> going to terminate p"); p.terminate(); p = None
                else: print(">>>>> no need to terminate p - p = None")
                endSelectionTime = time()
                selectionDurationPerTimeSlot.append(endSelectionTime - startSelectionTime);
                # if os.path.exists(filename): numByteDownloadedDuringSelection = os.path.getsize(filename) - sum(numByteDownloadedPerTimeSlot) - sum(numByteDownloadedDuringSelectionPerTimeSlot)
                # else: numByteDownloadedDuringSelection = 0

                # if os.path.exists(filename): print(colored("in if ----- timeslot " + str(timeSlot) + ", end selection at " + str(endSelectionTime) + ", #bytes downloaded: " + str(os.path.getsize(filename)), "red"))
                # else: print(colored("in if ----- timeslot " + str(timeSlot) + ", end selection at " + str(endSelectionTime) + ", #bytes downloaded: 0", "red"))
                #
                # numByteDownloadedDuringSelectionPerTimeSlot.append(numByteDownloadedDuringSelection)
                # print("selectionDurationPerTimeSlot:", selectionDurationPerTimeSlot, ", numByteDownloadedDuringSelectionPerTimeSlot:", numByteDownloadedDuringSelectionPerTimeSlot)

                p = Process(target=fileDownload, args=(url, filename,))

                # close current network connection
                # if isConnected(previousNetwork):
                print(colored("going to disconnect from network " + str(availableNetworkName[availableNetworkID.index(previousNetwork)]), "green"))
                disconnect(previousNetwork)

                if os.path.exists(filename): numByteDownloadedDuringSelection = os.path.getsize(filename) - sum(numByteDownloadedPerTimeSlot) - sum(numByteDownloadedDuringSelectionPerTimeSlot)
                else: numByteDownloadedDuringSelection = 0
                numByteDownloadedDuringSelectionPerTimeSlot.append(numByteDownloadedDuringSelection)

            # create a new connection to network selected
            print(colored("going to connect to network " + str(availableNetworkName[availableNetworkID.index(currentNetwork)]), "green"))
            # wifiAP = connect(currentNetwork, wnsStartTime); logPerTimeSlot[timeSlot - 1].append(wifiAP)
            # if isConnected(currentNetwork): print(colored("going to start download process, time left in slot:" + str(timeSlotDuration - (time() - wnsStartTime)), "green")); p.start()
            wifiAP = connect(currentNetwork, startSelectionTime); logPerTimeSlot[timeSlot - 1].append(wifiAP)
            if isConnected(currentNetwork): print(colored("going to start download process, time left in slot:" + str(timeSlotDuration - (time() - startSelectionTime)), "green")); p.start()

        elif delayPerTimeSlot[-1] == timeSlotDuration: # connection not established or download not started in previous time slot
            selectionDurationPerTimeSlot.append(0)
            if os.path.exists(filename): numByteDownloadedDuringSelection = os.path.getsize(filename) - sum(numByteDownloadedPerTimeSlot) - sum(numByteDownloadedDuringSelectionPerTimeSlot)
            else: numByteDownloadedDuringSelection = 0

            # if os.path.exists(filename): print(colored("in elif ----- timeslot " + str(timeSlot) + ", selection duration: 0, # bytes downloaded: " + str(os.path.getsize(filename)), "red"))
            # else: print(colored("in elif ----- " + str(timeSlot) + ", selection duration: 0, # bytes downloaded: 0", "red"))

            numByteDownloadedDuringSelectionPerTimeSlot.append(numByteDownloadedDuringSelection)
            print(colored("in elif selectionDurationPerTimeSlot:" + str(selectionDurationPerTimeSlot) \
                  +", numByteDownloadedDuringSelectionPerTimeSlot:" + str(numByteDownloadedDuringSelectionPerTimeSlot), "magenta"))

            print(colored("numByteDownloadedDuringSelection: " + str(numByteDownloadedDuringSelection)+ ", isConnected(previousNetwork)? " + str(isConnected(previousNetwork)) + ", p == None? " + str(p == None), "green"))
            if numByteDownloadedDuringSelection != 0:
                # some bytes were downloaded during the selection
                delayPerTimeSlot.append(delayCarriedToNextTimeSlot); delayCarriedToNextTimeSlot = 0
                print(colored("no need to reconnect, delay carried forward" + str(delayCarriedToNextTimeSlot) + ", p == None>? " + str(p == None), "magenta"))
            elif isConnected(previousNetwork) == True and p == None:
                # connection was established but process not started
                print(colored("connection was already established last time step ----- going to start download process", "green"))
                startSwitch = time()
                p = Process(target=fileDownload, args=(url, filename,))
                print(colored("going to start download process, time left in slot:" + str(timeSlotDuration - (time() - wnsStartTime)), "green"))
                p.start()
            else:
                # no connection  was established/no download was made
                print(colored("connection was not established last time step ----- going to connect and start download process", "green"))
                startSwitch = time()
                # wifiAP = connect(currentNetwork, wnsStartTime); logPerTimeSlot[timeSlot - 1].append(wifiAP)
                # if isConnected(currentNetwork): print(colored("going to start download process, time left in slot:" + str(timeSlotDuration - (time() - wnsStartTime)), "green")); p.start()
                wifiAP = connect(currentNetwork, startSelectionTime); logPerTimeSlot[timeSlot - 1].append(wifiAP)
                if isConnected(currentNetwork): print(colored("going to start download process, time left in slot:" + str(timeSlotDuration - (time() - startSelectionTime)), "green")); p.start()

        else: # no change in network, download continues
            print("no change in network... will continue download...")
            delayPerTimeSlot.append(0)
            selectionDurationPerTimeSlot.append(0)
            numByteDownloadedDuringSelectionPerTimeSlot.append(0)

            # print(colored("in else ----- " + str(timeSlot) + ", selection duration: 0, # bytes downloaded: " + str(os.path.getsize(filename)), "white", "on_red"))

            # print("in else selectionDurationPerTimeSlot:", selectionDurationPerTimeSlot,", numByteDownloadedDuringSelectionPerTimeSlot:", numByteDownloadedDuringSelectionPerTimeSlot)

        currentSleepTime = time()
        # print(">>>>> wnsStartTime:" + str(wnsStartTime) + ", (currentTime - wnsStartTime): " + str(currentSleepTime - wnsStartTime))
        # while p.is_alive() and ((currentSleepTime - wnsStartTime) < (timeSlotDuration)):
        while p.is_alive() and ((currentSleepTime - startSelectionTime) < (timeSlotDuration)):
            # print("going to sleep, time spent", (currentSleepTime - wnsStartTime))
            sleep(1); currentSleepTime = time() # sleep as long as time slot not over

    except: print("exception");traceback.print_exc()
    # end wns

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def saveWiFiAPdetail():
    global wifiConnectedAPset
    try:
        wifiAP = subprocess.Popen("iwconfig wlp2s0 | grep 'Access Point' | awk -F'[ ]+' '{ print $7 }'", shell=True, stdout=subprocess.PIPE).communicate()[0]
        wifiAP = str(wifiAP, 'utf-8').rstrip()
        print(">>>>> wifiAP: ", wifiAP)
        wifiConnectedAPset.add(wifiAP)
        return wifiAP
    except: print("exception occurred in saveWiFiAPdetail"); return "" # traceback.print_exc()
    # end saveWiFiAPdetail

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def smartEXP3():
    '''
    @description: implements smart EXP3
    '''
    global currentNetwork, previousNetwork, availableNetworkID, numNetwork, maxGain, beta, networkToExplore, weight, probability
    global blockLength, blockIndex, blockLengthPerNetwork, numBlockNetworkSelected, probabilityCurrentBlock, switchBack, maxProbDiff
    global totalBytePerNetwork, numTimeSlotNetworkSelected, gainPerTimeSlotCurrentBlock, gainPerTimeSlotPreviousBlock, highProbability, largeBlock
    global numByteWithoutDelayPerTimeSlot, selectionTypePerTimeSlot, logPerTimeSlot
    global numConsecutiveSlotPreferredNetwork, numConsecutiveSlotForReset, preferredNetworkGainList, gainRollingAvgWindowSize, totalNumReset

    # print("at beginning in smartEXP3, block index: ", blockIndex, ", blockLength:", blockLength)
    if blockLength == 0: blockIndex += 1    # at beginning of a new block
    gamma = blockIndex ** (-1 / 3)          # compute gamma, based on  block index
    # print("logPerTimeSlot:logPerTimeSlot ", logPerTimeSlot)
    if timeSlot == 1: # first time slot
        # networkSelected = random.choice(availableNetworkID, p=probability)  # random choice
        networkSelected = choice(networkToExplore);
        print(colored("start of new block --- will explore network " + str(networkSelected), "green"))
        probabilityCurrentBlock = 1 / len(networkToExplore); selectionTypePerTimeSlot.append(2); logPerTimeSlot[timeSlot - 1].append("exploring after a reset")
        networkToExplore.remove(networkSelected)

        switchBack = False
        networkSelectedIndex = availableNetworkID.index(networkSelected)
        blockLengthPerNetwork[networkSelectedIndex] = blockLength = ceil((1 + beta) ** numBlockNetworkSelected[networkSelectedIndex])
        numBlockNetworkSelected[networkSelectedIndex] += 1
        # selectionTypePerTimeSlot.append(2)  # random selection
        logPerTimeSlot[timeSlot - 1].append("prob current block:" + str(probabilityCurrentBlock))
    else: # subsequent time slots; timeSlot > 1
        currentNetworkIndex = availableNetworkID.index(currentNetwork)  # list index where details of current network are stored

        # update and normalize weight
        estimatedGain = computeEstimatedGain(numByteWithoutDelayPerTimeSlot[-1])
        gammaForUpdate = ((blockIndex + 1) ** (-1 / 3)) if blockLength != 0 else gamma  # to use correct value given that update is supposed to be made once per block
        logPerTimeSlot[timeSlot - 1].append("; gamma used= " + str(gammaForUpdate))
        weight[currentNetworkIndex] *= exp(gammaForUpdate * estimatedGain / numNetwork);  # print("before normalization, weight: ", weight)
        weight = list(w / max(weight) for w in weight);  # print("after normalization, weight: ", weight)  # normalize the weights

        # update probability
        probability = list((((1 - gammaForUpdate) * w) / sum(weight)) + (gammaForUpdate / numNetwork) for w in weight);  # print("probability: ", probability)

        # check if need for reset of algorithm and reset accordingly in the next time slot
        maxProbability = max(probability)                           # highest probability
        convergedNetworkIndex = probability.index(maxProbability)   # list index where details of network with highest probability are stored
        # if maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= largeBlock:
        if (maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= largeBlock) or \
                (numConsecutiveSlotPreferredNetwork > numConsecutiveSlotForReset and len(preferredNetworkGainList) >= (gainRollingAvgWindowSize + 1) and networkQualityDeclined()):
            if (maxProbability >= highProbability and blockLengthPerNetwork[convergedNetworkIndex] >= largeBlock):logPerTimeSlot[timeSlot - 1].append("PERIODIC ALGORITHM RESET"); print("PERIODIC ALGORITHM RESET")
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
                    if numNetworkHighestAverageByte > 1 and networkSelected == previousNetwork: probabilityCurrentBlock = 1/2; print(colored("GREEDY STAYING IN SAME NETWORK", "red"))
                    else: probabilityCurrentBlock = (1/2) * (1/numNetworkHighestAverageByte); selectionTypePerTimeSlot.append(1); logPerTimeSlot[timeSlot - 1].append("choosing greedily")
                else:  # random based on probability distribution
                    networkSelected = random.choice(availableNetworkID, p=probability)  # random choice
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
            # print("logPerTimeSlot[timeSlot - 1]: ", logPerTimeSlot[timeSlot - 1])
            logPerTimeSlot[timeSlot - 1].append("no selection ----- in the middle of a block")
    print("probability current block: ", probabilityCurrentBlock)

    # for log
    blockIndexPerTimeSlot.append(blockIndex); weightPerTimeSlot.append(str(weight)); probabilityPerTimeSlot.append(str(probability))
    gammaPerTimeSlot.append(gamma); maxGainPerTimeSlot.append(maxGain); blockLengthPerTimeSlot.append(blockLengthPerNetwork[networkSelectedIndex])

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
    # print("gain: ", gain, ", scaled gain: ", scaledGain, ", estimated gain: ", estimatedGain)
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

    # if total gain of last block is equal to zero, no need to switch back
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
    global probability, numNetwork, blockLengthPerNetwork, numBlockNetworkSelected, maxBlock, logPerTimeSlot, timeSlot

    # print("logPerTimeSlot:", logPerTimeSlot, " ----- type: ", type(logPerTimeSlot))
    highestProbabilityIndex = probability.index(max(probability))
    if 0 not in numBlockNetworkSelected and (((max(probability) - min(probability)) <= (1 / (numNetwork - 1)))
                                             or blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock):
        coinFlip = randint(1, 2)
        if coinFlip == 1:
            logPerTimeSlot[timeSlot - 1].append("flipped coin and will select greedily...")
            return True
        else: logPerTimeSlot[timeSlot - 1].append("flipped coin but will not select greedily...")
    else:
        logPerTimeSlot[timeSlot - 1].append("no need to flip coin ----- will not select greedily...; 0 not in numBlockNetworkSelected: "
                    + str(0 not in numBlockNetworkSelected) + ", diff between prob: " + str((max(probability) - min(probability))
                    <= (1 / (numNetwork - 1))) + ", blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock:"
                    + str(blockLengthPerNetwork[highestProbabilityIndex] <= maxBlock))
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
    print(colored("gain list (rolling avg): " + str(gainList) + ", changeInGain: " + str(changeInGain), "green"));  # input()

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
        print(colored("No preferred network", "green"))
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
        print(colored("numTimeSlotNetworkSelected: " + str(numTimeSlotNetworkSelected) + ", current network: " + str(currentNetwork) + ", preferredNetwork: " + str(preferredNetwork) + ", numConsecutiveSlotPreferredNetwork: " + str(numConsecutiveSlotPreferredNetwork) + ", preferredNetworkGainList: " + str(preferredNetworkGainList), "magenta"))
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
        print("numNetworkHighestAverageByte:", numNetworkHighestAverageByte)

    return networkSelected, numNetworkHighestAverageByte
    # end selectGreedily

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def greedy():
    '''
    @description: implements greedy selection
    '''
    global networkToExplore, totalBytePerNetwork, numTimeSlotNetworkSelected, availableNetworkID, previousNetwork, maxGainPerTimeSlot

    previousNetwork = currentNetwork
    if networkToExplore != []:  # not yet explored all networks, pick one of those not yet explored at random
        print("not yet explored all networks")
        networkSelected = choice(networkToExplore)
        networkToExplore.remove(networkSelected)
    else:  # select the one from which the highest average gain has been observed
        print("explored all networks ----- going to choose greedily...")
        # averageBytePerNet = list(totalByte / numTimeSlot for totalByte, numTimeSlot in zip(totalBytePerNetwork, numTimeSlotNetworkSelected))
        # highestAverageByte = max(averageBytePerNet)
        # networkSelected = availableNetworkID[averageBytePerNet.index(highestAverageByte)]
        networkSelected, numNetworkHighestAverageByte = selectGreedily()
    maxGainPerTimeSlot.append(maxGain)
    return networkSelected
    # end greedy

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def displayOutput(downloadTotalTime, timeMetric):
    global algorithmName, networkSelectedPerTimeSlot, numByteDownloadedPerTimeSlot, delayPerTimeSlot, numTimeSlotNetworkSelected, maxGain
    global wifiConnectedAPset, bitRatePerTimeSlot

    print("\n\n ----- Download complete in " + str(downloadTotalTime) + " " + timeMetric + " -----")
    print("Algorithm:", algorithmName)
    print("network selected:", networkSelectedPerTimeSlot)
    print("#bytes:", numByteDownloadedPerTimeSlot, "-----", numByteDownloadedDuringSelectionPerTimeSlot, "-----", sum(numByteDownloadedPerTimeSlot) + sum(numByteDownloadedDuringSelectionPerTimeSlot))
    print("bit rate:", bitRatePerTimeSlot)
    print("delay:", delayPerTimeSlot)
    print("# time slot network selected:", numTimeSlotNetworkSelected)
    print("Max gain: " + str(maxGain))
    print("wifi AP: ", wifiConnectedAPset, " ----- ", len(wifiConnectedAPset))
    # end displayOutput

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def saveToFile(downloadTotalTime, timeMetric, currentTime, success):
    '''
    save details to text file (2 files, 1 with minimal details, another with all details)
    '''
    global outputTxtFileName, filename, location, algorithmName, maxGain, timestampPerTimeSlot
    global gammaPerTimeSlot, networkSelectedPerTimeSlot, delayPerTimeSlot, numByteDownloadedPerTimeSlot, numByteWithoutDelayPerTimeSlot, logPerTimeSlot
    global numTimeSlotNetworkSelected, maxGainPerTimeSlot, blockIndexPerTimeSlot, blockLengthPerTimeSlot, weightPerTimeSlot, probabilityPerTimeSlot
    global selectionTypePerTimeSlot, selectionDurationPerTimeSlot, connectDownloadDurationPerTimeSlot, numByteDownloadedDuringSelectionPerTimeSlot
    global bitRatePerTimeSlot, dateTimePerTimeSlot

    fileopen = open(outputTxtFileName + ".txt", "a")

    fileopen.write(currentTime + " ----- Download complete in " + str(downloadTotalTime) + " " + timeMetric + " ----- " + filename + " ----- @" + location + "\n")
    fileopen.write("Algorithm: " + algorithmName + "\n")
    fileopen.write("network selected: " + str(networkSelectedPerTimeSlot) + "\n")
    fileopen.write("#bytes: " + str(numByteDownloadedPerTimeSlot) + "-----" + str(numByteDownloadedDuringSelectionPerTimeSlot) + "-----" + str(sum(numByteDownloadedPerTimeSlot) + sum(numByteDownloadedDuringSelectionPerTimeSlot)) + "\n")
    fileopen.write("delay: " + str(delayPerTimeSlot) + "\n")
    fileopen.write("bit rate (Mbps): " + str(bitRatePerTimeSlot) + "\n")
    fileopen.write("# time slot network selected: " + str(numTimeSlotNetworkSelected) + "\n")
    fileopen.write("Max gain: " + str(maxGain) + "\n")
    fileopen.write("wifi AP: " + str(wifiConnectedAPset) + " ----- " + str(len(wifiConnectedAPset)) + "\n")
    fileopen.write("Download successful: " + str(success) + "\n")
    fileopen.write("--------------------------------------------------------------------------------------------------------------\n")

    fileopen.close()

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def saveCurrentTimeslotToFile(timeSlot):
    global outputCSVfile, filename, location, algorithmName, maxGain, timestampPerTimeSlot
    global gammaPerTimeSlot, networkSelectedPerTimeSlot, delayPerTimeSlot, numByteDownloadedPerTimeSlot, numByteWithoutDelayPerTimeSlot, logPerTimeSlot
    global numTimeSlotNetworkSelected, maxGainPerTimeSlot, blockIndexPerTimeSlot, blockLengthPerTimeSlot, weightPerTimeSlot, probabilityPerTimeSlot
    global selectionTypePerTimeSlot, selectionDurationPerTimeSlot, connectDownloadDurationPerTimeSlot, numByteDownloadedDuringSelectionPerTimeSlot
    global bitRatePerTimeSlot, dateTimePerTimeSlot

    outfile = open(outputCSVfile, "a")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    # save details to csv file
    if algorithmName == "smartEXP3":  # save more details in a csv file
        print(len(timestampPerTimeSlot), len(dateTimePerTimeSlot), len(blockIndexPerTimeSlot), len(blockLengthPerTimeSlot), len(gammaPerTimeSlot),
              len(maxGainPerTimeSlot), len(weightPerTimeSlot), len(probabilityPerTimeSlot), len(selectionTypePerTimeSlot),
              len(networkSelectedPerTimeSlot), len(delayPerTimeSlot), len(numByteDownloadedPerTimeSlot), len(numByteWithoutDelayPerTimeSlot),
              len(bitRatePerTimeSlot), len(selectionDurationPerTimeSlot), len(connectDownloadDurationPerTimeSlot),
              len(numByteDownloadedDuringSelectionPerTimeSlot), len(logPerTimeSlot))
        out.writerow([timeSlot, timestampPerTimeSlot[timeSlot - 1], dateTimePerTimeSlot[timeSlot - 1],
                      blockIndexPerTimeSlot[timeSlot - 1], blockLengthPerTimeSlot[timeSlot - 1],
                      gammaPerTimeSlot[timeSlot - 1], maxGainPerTimeSlot[timeSlot - 1],
                      weightPerTimeSlot[timeSlot - 1], probabilityPerTimeSlot[timeSlot - 1],
                      selectionTypePerTimeSlot[timeSlot - 1], networkSelectedPerTimeSlot[timeSlot - 1],
                      delayPerTimeSlot[timeSlot - 1], numByteDownloadedPerTimeSlot[timeSlot - 1],
                      numByteWithoutDelayPerTimeSlot[timeSlot - 1], bitRatePerTimeSlot[timeSlot - 1],
                      selectionDurationPerTimeSlot[timeSlot - 1],
                      connectDownloadDurationPerTimeSlot[timeSlot - 1],
                      numByteDownloadedDuringSelectionPerTimeSlot[timeSlot - 1], logPerTimeSlot[timeSlot - 1]])
    else:
        if len(maxGainPerTimeSlot) < timeSlot: maxGainPerTimeSlot.append(maxGain)
        print(len(timestampPerTimeSlot), len(dateTimePerTimeSlot), len(maxGainPerTimeSlot), len(networkSelectedPerTimeSlot),
              len(delayPerTimeSlot), len(numByteDownloadedPerTimeSlot), len(numByteWithoutDelayPerTimeSlot), len(bitRatePerTimeSlot),
              len(selectionDurationPerTimeSlot), len(connectDownloadDurationPerTimeSlot), len(numByteDownloadedDuringSelectionPerTimeSlot),
              len(logPerTimeSlot), len(numByteDownloadedDuringSelectionPerTimeSlot), len(logPerTimeSlot))
        out.writerow([timeSlot, timestampPerTimeSlot[timeSlot - 1], dateTimePerTimeSlot[timeSlot - 1],
                      maxGainPerTimeSlot[timeSlot - 1], networkSelectedPerTimeSlot[timeSlot - 1],
                      delayPerTimeSlot[timeSlot - 1], numByteDownloadedPerTimeSlot[timeSlot - 1],
                      numByteWithoutDelayPerTimeSlot[timeSlot - 1], bitRatePerTimeSlot[timeSlot - 1],
                      selectionDurationPerTimeSlot[timeSlot - 1],
                      connectDownloadDurationPerTimeSlot[timeSlot - 1],
                      numByteDownloadedDuringSelectionPerTimeSlot[timeSlot - 1], logPerTimeSlot[timeSlot - 1]])
    outfile.close()

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
def successfulDownload():
    '''
    @description:   identifies whether file has been properly downloaded
    @return:        True if the checksum of the downloaded file is correct and False otherwise
    '''
    global url

    md5checksum = "01378eacd669e4e46a3ef3e99d8e2e25"
    filename = url.split("/")[-1].strip()
    rootDir = os.getcwd() + "/"

    cmdOutput = subprocess.Popen("md5sum " + rootDir + filename, shell="True", stdout=subprocess.PIPE)
    checksum, err = cmdOutput.communicate()
    checksum = str(checksum, 'utf-8').rstrip().split()[0]
    print("computed checksum:", checksum, ", file properly downloaded?", md5checksum == checksum)
    return md5checksum == checksum

''' ------------------------------------------------------------------------------------------------------------------------------------------ '''
##### command line arguments
parser = argparse.ArgumentParser(description='Selects the optimal network to improve file download experience (download speed).')
parser.add_argument('-a', dest = "algorithm_name", required = True, help = 'name of wireless network selection algorithm (smartEXP3/greedy/wifi/cellular)')
parser.add_argument('-l', dest = "location", required = True, help = 'physical location where the experiment is carried out')
parser.add_argument('-w', dest = "wifiSSID", required = True, help = 'SSID of WiFi network available')

args = parser.parse_args()

# read command-line arguments
algorithmName = args.algorithm_name	# algorithm name
location = args.location		# physical location where the experiment is run
wifiSSID = args.wifiSSID		# SSID of WiFi network available

##### global variables
# remove numByteDownloaded as global variable
if algorithmName != "smartEXP3" and algorithmName != "greedy" and algorithmName != "wifi" and algorithmName != "cellular":
    print("Invalid algorithm name ----- must be either smartEXP3 or greedy or wifi"); sys.exit(-1)
timeSlot = 0			# index of time step
availableNetworkName = ["WiFi", "Cellular"]; numNetwork = len(availableNetworkName); availableNetworkID = [i for i in range(1, numNetwork + 1)]
currentNetwork = previousNetwork = -1
prevPercentDownload = 0		        # to detect resuming download to set delay
delayCarriedToNextTimeSlot = 0      # delay if download starts after one time slot and before the next selection, where the same network is selected
maxGain = maxBandwidth * timeSlotDuration * (1000 ** 2) 	# max bytes obtainable per time slot in bytes
# for greedy
totalBytePerNetwork = [0] * numNetwork
numTimeSlotNetworkSelected = [0] * numNetwork
networkToExplore = deepcopy(availableNetworkID) # if algorithmName == "greedy" else []
# for smart EXP3
weight = [1] * numNetwork			# weight per network
probability = [1/numNetwork] * numNetwork	# probability distribution
# for block
numBlockNetworkSelected = [0] * numNetwork	# no of blocks in which each network has been selected
blockLengthPerNetwork = [0] * numNetwork	# block length for each network
blockLength = 0  				# number of time slots left in current block
blockIndex = 0					# index of current block - for computation of gamma
probabilityCurrentBlock = 1/numNetwork		# probability with which the network in the current block was selected (to compute estimated gain)
# for hybrid (greedy)
maxProbDiff = 1/(numNetwork - 1)	# max difference in probability distribution to consider use of greedy
# for switch back
gainPerTimeSlotCurrentBlock = []  	# gain observed per time slot in current block
gainPerTimeSlotPreviousBlock = []  	# gain observed per time slot in previous block
switchBack = False				    # to prevent switch backs in 2 consecutive blocks leading to ping pong between 2 networks
# to monitor quality of preferred network
preferredNetwork = -1                       # ID of network with highest time slot count
numConsecutiveSlotPreferredNetwork = 0      # number of consecutive time slots spent in current network till current time slot
preferredNetworkGainList = []               # list of gain observed in preferred network from the time it was identified as the preferred network
numConsecutiveSlotForReset = 4              # no. of consecutive time slots spent in preferred network to consider a reset
percentageDeclineForReset = 15              # minimum percentage decline (from initial gain) in preferred network to consider a reset
gainRollingAvgWindowSize = 12                # window size for rolling average of gain
# for log
networkSelectedPerTimeSlot = []	    # network selected per time slot
manager = Manager(); delayPerTimeSlot = manager.list([])	# delay incurred per time slot; to be shared among processes
numByteDownloadedPerTimeSlot = []	# number of bytes downloaded per time slot
numByteWithoutDelayPerTimeSlot = []	# gain without delay per time slot
selectionTypePerTimeSlot = []		# type of selection per time slot; -1 - switch back, 0 - random, 1 - greedy, 2 - explore
weightPerTimeSlot = []				# per network weight per time slot
probabilityPerTimeSlot = []			# probability distribution per time slot
gammaPerTimeSlot = []				# gamma per time slot
maxGainPerTimeSlot = []				# max gain observable/observed per time slot
blockIndexPerTimeSlot = []			# index of block per time slot
blockLengthPerTimeSlot = []			# length of current block per time slot
logPerTimeSlot = []					# any additional useful data per time slot
wifiConnectedAPset = set()          # mac address of wifi APs to which device connects during the experiment
selectionDurationPerTimeSlot = []   # time taken to make a network selection per time slot
connectDownloadDurationPerTimeSlot = [] # time taken to create a connection, start the download process and receive bytes per time slot
numByteDownloadedDuringSelectionPerTimeSlot = [] # number of bytes downloaded by the previous network during selection in current time slot
timestampPerTimeSlot = []           # timestamp at start of each time slot
dateTimePerTimeSlot = []
bitRatePerTimeSlot = []


# disconnect from all networks
for networkID in availableNetworkID:
    if isConnected(networkID): print(colored("going to disconnect from network " + str(availableNetworkName[availableNetworkID.index(networkID)]), "green")); disconnect(networkID)

startSwitch = time()		        # starting time for switch; used to compute delay
downloadStartTime = time()          # start time of the file download; initial start of program

# for saving to file
timestamp = datetime.now().strftime("%I:%M%p on %B %d %Y")      # for file name
outputCSVfile = outputTxtFileName + "_" + algorithmName + "_" + timestamp + "_" + location + ".csv"
##### main program
outfile = open(outputCSVfile, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
if algorithmName == "smartEXP3":  # save more details in a csv file
    out.writerow(["time slot", "timestamp", "date time", "block index", "block length", "gamma", "max gain", "weight", "probability", "selection type", "network selected", "delay", "#bytes", "#bytes w/o delay", "bit rate (Mbps)", "selection duration", "connect and download duration", "#bytes downloaded during selection by previous network", "log"])
else:
    if len(maxGainPerTimeSlot) == 0: maxGainPerTimeSlot = [maxGain] * len(timestampPerTimeSlot)
    out.writerow(["time slot", "timestamp", "date time", "max gain", "network selected", "delay", "#bytes", "#bytes w/o delay", "bit rate (Mbps)", "selection duration", "connect and download duration", "#bytes downloaded during selection by previous network", "log"])
outfile.close()

# create a process that will download the file; but it's not started yet
p = Process(target=fileDownload, args=(url, filename,))

while timeSlot == 0 or p.is_alive() or delayPerTimeSlot[-1] == timeSlotDuration:	# as long as the file has not been downloaded
    try:
        timeSlot += 1	# increment time step index
        if timeSlot == 1: startSelectionTime, dateTime = time(), datetime.now().strftime("%d/%m/%Y %H:%M:%S"); prevStartSelectionTime = startSelectionTime	# get the current time
        else:
            # update the current time and get the duration of the previous slot
            # currentSlotStartTime, timeLapsed = time(), time() - startSelectionTime
            print(colored("\n@time slot " + str(timeSlot) + ", duration of previous time slot: " + str(startSelectionTime- prevStartSelectionTime) + ", #bytes downloaded: " \
                          + str(sum(numByteDownloadedPerTimeSlot) + sum(numByteDownloadedDuringSelectionPerTimeSlot)) + ", delay: " + str(delayPerTimeSlot) + ", #byte: " + str(numByteDownloadedPerTimeSlot) + \
                          ", numTimeSlotNetworkSelected: " + str(numTimeSlotNetworkSelected), "blue"))
        signal.signal(signal.SIGALRM, timeoutHandler)   # register the signal function handler, a handler for the timeout
        signal.alarm(timeSlotDuration)                  # define a timeout for the wns function

        # if timeSlot == 1: startSelectionTime = time()
        timestampPerTimeSlot.append(startSelectionTime)
        dateTimePerTimeSlot.append(dateTime)

        # call wns that will perform network selection and continue the file download
        wns(url) #, timeSlot, delayPerTimeSlot, algorithmName)
    except KeyboardInterrupt:
        # traceback.print_exc()
        print("ctrl+c pressed... stopping program...")
        sys.exit(-1)
    except:
        # traceback.print_exc()
        print("\n")
        print(colored("Function time out", "red", "on_white")) ###

# save number of bytes downloaded and connect and download time for last time slot; which is not saved as timeoutHandler is not called
downloadCompleteTime = time()
connectDownloadDurationPerTimeSlot.append(downloadCompleteTime - startSelectionTime - selectionDurationPerTimeSlot[-1])
totalNumByteDownloaded = os.path.getsize(filename)
numByteDownloadedLastTimeSlot = totalNumByteDownloaded - sum(numByteDownloadedPerTimeSlot) - sum(numByteDownloadedDuringSelectionPerTimeSlot)
numByteDownloadedPerTimeSlot.append(numByteDownloadedLastTimeSlot)	# number of bytes downloaded
lastTimeSlotDuration = downloadCompleteTime - timestampPerTimeSlot[-1]
numByteWithoutDelayPerTimeSlot.append((numByteDownloadedLastTimeSlot * lastTimeSlotDuration) / (connectDownloadDurationPerTimeSlot[-1] - delayPerTimeSlot[-1]))
bitRate = (numByteWithoutDelayPerTimeSlot[-1] * 8)/((1000**2) * lastTimeSlotDuration); bitRatePerTimeSlot.append(bitRate)
print("duration of last time slot:", lastTimeSlotDuration)

##### check if file properly downloaded - as per checksum
success = successfulDownload()
if success: print("File properly downloaded")
else: print("File not properly downloaded")
##### save details to text file
downloadTotalTime = downloadCompleteTime - downloadStartTime  # total time taken to complete the download
if downloadTotalTime > 60: downloadTotalTime /= 60; timeMetric = "mins"
else: timeMetric = "secs"
displayOutput(downloadTotalTime, timeMetric)    # display the output
saveToFile(downloadTotalTime, timeMetric, timestamp, success)       # save details to file
print("#bytes downloaded:", os.path.getsize(filename))
''' ------------------------------------------------------------------------------------------------------------------------------------------ '''