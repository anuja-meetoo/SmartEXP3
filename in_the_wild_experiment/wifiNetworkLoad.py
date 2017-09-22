#!/usr/bin/python3

import argparse
import pyshark
from datetime import datetime, timedelta
import csv
import datetime
import dateutil.parser
import time
import numpy as np
import pandas
from math import ceil

''' global variable declaration '''
monitoringSlotDuration = 15 # in seconds
rollingAvgWindow = 5

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def computeFrameTransferTime(size, dataRate, arrivalTime):
    '''
    @description:   computes the frame transfer duration, given its size and data rate, and the time the frame was sent
    @args:          frame size (bytes), data rate (Mbps), frame arrival time
    @returns:       frame transfer duration, time frame was sent
    '''
    size = (size * 8)/(1000 ** 2)       # convert frame size to Mb
    transferDuration = size/dataRate
    transferStartTime = arrivalTime - timedelta(seconds=transferDuration)

    return transferDuration, transferStartTime
    # end computeFrameTransferTime

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def computeNetworkLoad(totalTransmissionTime, slotDuration=monitoringSlotDuration):
    '''
    @description:   computes the load of the network for the slot duration
    @args:          total packet transmission time during the time slot
    @return:        network load during that time slot
    '''
    return (totalTransmissionTime * 1.0)/slotDuration
    # end computeNetworkLoad

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def getDateTimeObject(timeStr):
    '''
    @description:   converts date as a string to datetime object
    @arg:           date as a string in format m dd, yyyy hh:mm:ss.s SGT, e.g. Apr 16, 2017 16:19:15.244577000 SGT
    @return:        date as a datetime object
    '''
    monthList = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    timeSplit = timeStr.split()
    time_month = monthList.index(timeSplit[0]) + 1
    time_month = "0" + str(time_month) if time_month < 10 else str(time_month)
    time_day = timeSplit[1][:-1]
    time_year = timeSplit[2]
    time_time = timeSplit[3]
    timeStr = time_month + "/" + time_day + "/" + time_year + " " + time_time
    p = dateutil.parser.parser()
    timeObj = p.parse(timeStr)
    return timeObj
    # end getDateTimeObject

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def loadMonitoringSlotStartTime(algorithmIndex, experimentFile): # 1 - smartEXP3, 2 - greedy
    '''
    @description:   extracts the start time and duration of each time slot during the experiment run, and computes the experiment end time
    @args:          index of algorithm being considered
    @returns:       list of slot start time and duration, and experiment end time
    '''
    monitoringSlotStartTimeList = []
    monitoringSlotDurationList = []

    with open(experimentFile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        for row in rowReader:
            if count != 0:
                monitoringSlotStartTimeList.append(datetime.datetime.fromtimestamp(float(row[1])))
                if algorithmIndex == 1: print(">>>>> IN IF algorithmIndex = ", algorithmIndex, ", ", row[15], ", ", row[16]); duration = float(row[15]) + float(row[16])
                else: print(">>>>> IN ELSE algorithmIndex = ", algorithmIndex, ", ", row[9], ", ", row[10]); duration = float(row[9]) + float(row[10])
                monitoringSlotDurationList.append(duration)
            count += 1
    inputCSVfile.close()

    return monitoringSlotStartTimeList, monitoringSlotDurationList, monitoringSlotStartTimeList[-1] + timedelta(seconds=duration)
    # end loadMonitoringSlotStartTime

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def main():
    global monitoringSlotDuration

    # get the name of the cap file containing details of frames captured
    parser = argparse.ArgumentParser(description='Estimates WiFi network load.')
    parser.add_argument('-a', dest="algorithm_index", required=True, help='index of algorithm (1 - smartEXP3; 2 - greedy)')
    parser.add_argument('-c', dest="cap_file", required=True, help='file name containing details of frames captured')
    parser.add_argument('-x', dest="experiment_file", required=True, help='file name containing details of data during experiment')
    parser.add_argument('-o', dest="output_file_url", required=True, help='url of output file to store load per monitoring time slot')

    args = parser.parse_args()
    algorithmIndex = int(args.algorithm_index)
    capFile = args.cap_file                                             # location of cap file
    experimentFile = args.experiment_file
    outputCSVfile = args.output_file_url                                # url of output file to save load per monitoring slot

    # load time slot start time, slot duration and experiment end time from file containing details from experiment run
    monitoringSlotStartTimeList, monitoringSlotDurationList, endTime = loadMonitoringSlotStartTime(algorithmIndex, experimentFile)
    startTime = monitoringSlotStartTimeList[0]

    # initialization
    monitoringSlotStartTime = monitoringSlotStartTimeList[0]            # monitoring start time
    monitoringSlotEndTime = monitoringSlotStartTimeList[1]              # monitoring end time
    totalTransmissionTime = 0                                           # total time during a monitoring slot that there was some transmission
    totalTransmissionTimeList = []                                      # total time during each monitoring slot that there was some transmission
    networkLoadList = []                                                # list to store network load in each network monitoring slot
    numPkt = 0
    timeSlotIndex = 1                                                   # index of time slot being processed, starting from 1

    print("start time:", startTime, ", end time:", endTime)#; input()
    print(">>>>> monitoringSlotStartTime: ", str(monitoringSlotStartTime), ", monitoringSlotEndTime: ", monitoringSlotEndTime)
    print("start time list: ", monitoringSlotStartTimeList, "-----", len(monitoringSlotStartTimeList))
    print("slot duration list:", monitoringSlotDurationList, "-----", len(monitoringSlotDurationList))

    cap = pyshark.FileCapture(capFile)  # load the capFile

    for pkt in cap:
        frameSize = int(pkt.length)                             # packet size in bytes
        dataRate = float(pkt.layers[1].data_rate)               # data rate in Mbps from radiotap header
        frameArrivalTime = pkt.frame_info.time                  # packet arrival time, e.g. Apr 16, 2017 16:19:15.244577000 SGT
        frameArrivalTime = getDateTimeObject(frameArrivalTime)  # convert frame arrival time to a datetime object

        if frameArrivalTime > (endTime + timedelta(seconds=monitoringSlotDuration)): break  # stop processing as already exceeded monitoring time

        if frameArrivalTime > startTime: # frame to be considered as it arrived after startTime of monitoring duration
            # get transfer duration and transfer start time of packet
            transferDuration, transferStartTime = computeFrameTransferTime(frameSize, dataRate, frameArrivalTime)

            if transferStartTime < endTime:                     # the the packet was sent after the experiment end time, no need to consider
                if frameArrivalTime > monitoringSlotEndTime:    # frame is for the the next time slot
                    # reset monitoringSlotStartTime, monitoringSlotEndTime, totalTransmissionTime and numPkt, and update totalTransmissionTimeList
                    print(">>>>> frameArrivalTime: ", str(frameArrivalTime))
                    monitoringSlotStartTime = monitoringSlotEndTime
                    timeSlotIndex += 1
                    if timeSlotIndex < len(monitoringSlotStartTimeList): monitoringSlotEndTime = monitoringSlotStartTimeList[timeSlotIndex]
                    else: monitoringSlotEndTime = endTime
                    totalTransmissionTimeList.append(totalTransmissionTime)
                    print(">>>>> monitoringSlotStartTime: ", str(monitoringSlotStartTime), ", monitoringSlotEndTime: ", monitoringSlotEndTime, ", total transmission time prev slot: ", totalTransmissionTime, ", numPkt:", numPkt)
                    totalTransmissionTime = 0  # reset total transmission time
                    numPkt = 0

                # performed in all cases - update total transmission time
                transferDuration, transferStartTime = computeFrameTransferTime(frameSize, dataRate, frameArrivalTime)
                if transferStartTime >= monitoringSlotStartTime: totalTransmissionTime += transferDuration
                else: # the frame transfer overlaps over two monitoring slots
                    totalTransmissionTime += (frameArrivalTime - monitoringSlotStartTime).total_seconds()
                    if totalTransmissionTimeList != []: totalTransmissionTimeList[-1] += (monitoringSlotStartTime - transferStartTime).total_seconds()
                numPkt += 1

    # update for last time slot
    totalTransmissionTimeList.append(totalTransmissionTime)

    # compute network load from total transmission of each time slot
    for totalTime, duration in zip(totalTransmissionTimeList, monitoringSlotDurationList): networkLoadList.append(computeNetworkLoad(totalTime, duration))

    # save load to CSV file
    myfile = open(outputCSVfile, "w")
    out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    out.writerow(["Time slot", "Timestamp of time slot start time", "Time slot start time", "Time slot duration", "Load", "Load (%)"])
    for i in range(len(networkLoadList)):
        out.writerow([i + 1, ((time.mktime(monitoringSlotStartTimeList[i].timetuple()) * 1000000) + (monitoringSlotStartTimeList[i].microsecond)) / 1000000, monitoringSlotStartTimeList[i], monitoringSlotDurationList[i], networkLoadList[i], networkLoadList[i]*100])
    myfile.close()

    # compute and save network load rolling average
    networkLoadList = [num * 100 for num in networkLoadList]
    runDuration = len(networkLoadList)
    networkLoadList = np.array(networkLoadList)
    networkLoadList = pandas.rolling_mean(networkLoadList, rollingAvgWindow)
    networkLoadList = list(networkLoadList[rollingAvgWindow - 1:])

    myfile = open(outputCSVfile.split(".csv")[0]+"_rollingAvg.csv", "w")
    out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

    out.writerow(["time slot", "load (%)"])
    rowNumbering = [i for i in range(1 + int(ceil((rollingAvgWindow - 1) / 2)), runDuration - (rollingAvgWindow // 2) + 1)]
    for numbering, load in zip(rowNumbering, networkLoadList):
        out.writerow([numbering, load])
    myfile.close()
    # end main

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
main()

# ----- convert from datetime to seconds
# >>> time.mktime(datetime.datetime(2017, 4, 16, 16, 19, 12, 320644).timetuple()) * 1000
# 1492330752000.0