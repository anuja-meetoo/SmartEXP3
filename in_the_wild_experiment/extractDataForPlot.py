# possible values of EcIo - ftp://hazards.cr.usgs.gov/Eq_Effects/GeekPack/Procedures-Configs-Info/2_Radios/Raven-X_XE/What-is-%20EcIo_Explanation.pdf
'''
@description: get per time slot bit rate and cell load
'''
import numpy as np
from math import sqrt, ceil
import matplotlib.pyplot as plt
import pandas
import csv
from copy import deepcopy
import os
import dateutil.parser
from datetime import datetime, timedelta

# parameter
algorithmNameIndex = 1  # 1 - smartEXP3, 2 - greedy
rollingAvgWindow = 5

algorithmNameList = ["smartEXP3", "greedy"]
rootDir = "/Users/anuja/Desktop/WNS_EXPERIMENT_WILD_BACKUP/experiments@vivocity_20170522/"
inputFileNameList =[["smartEXP3_run1_experiment_data_smartEXP3_03_33PM_on_May_22_2017_vivocity.csv", "smartEXP3_run2_experiment_data_smartEXP3_03_49PM_on_May_22_2017_vivocity.csv", "smartEXP3_run3_experiment_data_smartEXP3_04_23PM_on_May_22_2017_vivocity.csv", "smartEXP3_run4_experiment_data_smartEXP3_05_58PM_on_May_22_2017_vivocity.csv", "smartEXP3_run5_experiment_data_smartEXP3_06_49PM_on_May_22_2017_vivocity.csv"], ["greedy_run1_experiment_data_greedy_04_05PM_on_May_22_2017_vivocity.csv", "greedy_run2_experiment_data_greedy_04_38PM_on_May_22_2017_vivocity.csv", "greedy_run3_experiment_data_greedy_05_11PM_on_May_22_2017_vivocity.csv", "greedy_run4_experiment_data_greedy_06_17PM_on_May_22_2017_vivocity.csv", "greedy_run5_experiment_data_greedy_07_23PM_on_May_22_2017_vivocity.csv"]]
cellLoadFileNameList = [["smartEXP3_run1_cellLoad_smartEXP3_15_33_25_22May2017.csv", "smartEXP3_run2_cellLoad_smartEXP3_15_49_41_22May2017.csv", "smartEXP3_run3_cellLoad_smartEXP3_16_23_12_22May2017.csv", "smartEXP3_run4_cellLoad_smartEXP3_17_58_11_22May2017.csv", "smartEXP3_run5_cellLoad_smartEXP3_18_49_12_22May2017.csv"], ["greedy_run1_cellLoad_greedy_16_05_23_22May2017.csv", "greedy_run2_cellLoad_greedy_16_38_42_22May2017.csv", "greedy_run3_cellLoad_greedy_17_10_23_22May2017.csv", "greedy_run4_cellLoad_greedy_18_17_29_22May2017.csv", "greedy_run5_cellLoad_greedy_19_22_17_22May2017.csv"]]
numRun = len(inputFileNameList[algorithmNameIndex - 1])
networkToHighlight = ["WiFi", "WiFi"]      # network type to be highlighted by a dot bit rate on plot
indexPrefix = int(ceil((rollingAvgWindow-1)/2)) + 1 # due to rolling average
outputDir = rootDir + "dataForPlot/"
if not os.path.exists(outputDir): os.makedirs(outputDir)

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def extractBitRate(inputCSVfile):
    '''
    @description:   extracts bit rate, network selected, and timestamp of start of each time slot and end of experiment, and prints
                    start and end time of the experiment run
    @arg:           CSV file containing details of experiment run (inputCSVfile)
    @return:        list of bit rates observed per time slot (bitRateList), network selected per time slot (networkSelectedList),
                    timestamp of start of each time slot (slotStartTimestampList) and end of experiment (slotStartTimestampList)
    '''
    global algorithmNameIndex, networkToHighlight, outputDir

    bitRateList = []
    networkSelectedList = []
    timeSlotToHighlightList = []
    slotStartTimestampList = []
    startTime = endTime = 0

    with open(inputCSVfile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        for row in rowReader:
            if count != 0:
                timeSlot = int(row[0])
                slotStartTimestampList.append(float(row[1]))
                if algorithmNameIndex == 1:
                    bitRateList.append(float(row[14]))
                    networkSelectedList.append(row[10])
                    slotDuration = float(row[15]) + float(row[16])
                else:
                    bitRateList.append(float(row[8]))
                    networkSelectedList.append(row[4])
                    slotDuration = float(row[9]) + float(row[10])
                if networkSelectedList[-1] == networkToHighlight[algorithmNameIndex - 1]: timeSlotToHighlightList.append(timeSlot)
                if count == 1:
                    startTime = row[1] + "; " + row[2]
                else:
                    p = dateutil.parser.parser()
                    endTime = str(float(row[1]) + slotDuration) + "; " + str(p.parse(row[2]) + timedelta(seconds=slotDuration))

            count += 1
    slotStartTimestampList.append(slotStartTimestampList[-1] + slotDuration)  # add timestamp of end time of algorithm
    print("slotStartTimestampList:", slotStartTimestampList)
    inputCSVfile.close()
    print("start time:", startTime, "; end time:", endTime)
    saveTxtFile(outputDir + algorithmNameList[algorithmNameIndex - 1] + "_start_end_timestamps.txt", "start time:" + str(startTime) + "\nend time:" + str(endTime))
    return bitRateList, networkSelectedList, timeSlotToHighlightList, slotStartTimestampList
    # end extractBitRate

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def getHighlightCoordinates(timeSlotToHighlightList, bitRateListOriginal, bitRateList, runIndex):
    '''
    @description:   constructs a list of coordinates to highlight in the plot to show the bit rate obtained each time a particular network was selected
    @arg:           list of time slots requiring highlight (as a particular network was selected at that time slot), bit rate obtained at each time
                    slot (before and after applying rolling average)
    @return:        list of coordinates to be highlighted in plot as bit rate obtained when a particular network is selected (dotCoordinatesList)
    '''
    global indexPrefix, rollingAvgWindow
    labelList = ['a', 'b', 'c', 'd', 'e']
    dotCoordinatesList = "" #[]

    # details for timeSlot x is obtained at index (x - indexPrefix) in list bitRateList (rolling average); index range from 0 to (prevLen - rollingAverage)
    for timeSlot in timeSlotToHighlightList:
        index = timeSlot - indexPrefix
        if index >= 0 and index <= (len(bitRateListOriginal) - rollingAvgWindow):
            dotCoordinatesList += str(timeSlot) + "\t" + str(bitRateList[index]) + "\t" + labelList[runIndex] + "\n"
            # dotCoordinatesList.append("(" + str(timeSlot) + "," + str(bitRateList[index]) + ")")
        else:
            dotCoordinatesList += str(timeSlot) + "\t" + str(bitRateListOriginal[timeSlot - 1]) + "\t" + labelList[runIndex] + "\n"
            # dotCoordinatesList.append("(" + str(timeSlot) + "," + str(bitRateListOriginal[timeSlot - 1]) + ")")
    return dotCoordinatesList

    # x    y    label
    # 1    1.2345098953833116    a
    # 3    2.24657679375    a
    # 4    2.94334546906    a

    # end getHighlightCoordinates

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def extractCellLoad(inputCSVfile, slotStartTimestampList):
    '''
    @description:   computes cell load per time slot (load might have been captured for every seconds...)
    @arg:           CSV file containing cell load details captured during experiment (inputCSVfile), timestamps od start of time slots and
                    the timestamp of the end of the experiment
    @return:        cell load per time step (cellLoadList)
    '''
    cellLoadList = []

    currentSlotIndex = 0
    currentSlotStartTimestamp = slotStartTimestampList[currentSlotIndex]
    currentSlotEndTimestamp = slotStartTimestampList[currentSlotIndex + 1]
    currentSlotCellLoadList = []

    with open(inputCSVfile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        for row in rowReader:
            if count != 0:  # not the header row in csv file
                currRowTimestamp = float(row[0])
                if currRowTimestamp > slotStartTimestampList[-1]: break     # already processed all rows for ecio captured during experiment
                elif currRowTimestamp >= currentSlotStartTimestamp and currRowTimestamp < currentSlotEndTimestamp:
                    # cell load correspond to current slot details
                    currentSlotCellLoadList.append(int(row[3]))
                elif currRowTimestamp >=  currentSlotEndTimestamp:
                    # cell load correspond to next slot details
                    if currentSlotCellLoadList == []: avgCellLoad = 0 # in case no cell load captured for the slot
                    else: avgCellLoad = sum(currentSlotCellLoadList)/len(currentSlotCellLoadList)
                    # print(currRowTimestamp, "-----", currentSlotCellLoadList, "-----", avgCellLoad)
                    cellLoadList.append(avgCellLoad)
                    currentSlotIndex += 1
                    currentSlotStartTimestamp = slotStartTimestampList[currentSlotIndex]
                    currentSlotEndTimestamp = slotStartTimestampList[currentSlotIndex + 1]
                    currentSlotCellLoadList = [int(row[3])]
            count += 1
        avgCellLoad = sum(currentSlotCellLoadList) / len(currentSlotCellLoadList)
        cellLoadList.append(avgCellLoad)
        # print(currRowTimestamp, "-----", currentSlotCellLoadList, "-----", avgCellLoad)
    inputCSVfile.close()

    # # interpolate missing cell load
    # for i in range(len(cellLoadList)):
    #     if cellLoadList[i] == 0: cellLoadList = interpolate(cellLoadList, i)
    if 0 in cellLoadList: print(">>>>> MISSING CELL LOAD DATA")
    return cellLoadList
    # end extractCellLoad

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def saveCSVfile(outputCSVfile, header, data, rowNumbering):
    '''
    @description:   saves details in a csv file with the specified name
    @arg:           url of output CSV file
    @return:        None
    '''
    global numRun

    myfile = open(outputCSVfile, "w")
    out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

    out.writerow(header)
    for i in range(len(rowNumbering)):
        row = [rowNumbering[i]]
        for j in range(numRun):
            if i < len(data[j]): row.append(data[j][i])
            else: row.append("")
        out.writerow(row)
    myfile.close()
    # end saveCSVfile


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
def main():
    # list to store details of all runs
    bitRateListOriginalPerRun = []  # before applying rolling average
    bitRateListPerRun = []          # after applying rolling average
    networkSelectedListPerRun = []  # network selected in every time slot
    dotCoordinatesListPerRow = []   # coordinates denoting selection of a particular network (timeSlot, bitRate)
    cellLoadListPerRun = []         # cell load per time slot
    maxRunDuration = 0              # in number of slots

    for runIndex in range(numRun):
        # get the bit rate, network selected and timestamp of start of every time slot
        inputCSVfile = rootDir + inputFileNameList[algorithmNameIndex - 1][runIndex]
        bitRateList, networkSelectedList, timeSlotToHighlightList, slotStartTimestampList = extractBitRate(inputCSVfile)
        if len(bitRateList) > maxRunDuration: maxRunDuration = len(bitRateList)

        # save to combined list for all runs
        bitRateListOriginal = deepcopy(bitRateList); bitRateListOriginalPerRun.append(bitRateListOriginal)
        bitRateList = np.array(bitRateList); bitRateList = pandas.rolling_mean(bitRateList, 5); bitRateList = list(bitRateList[rollingAvgWindow-1:])
        bitRateListPerRun.append(bitRateList)
        networkSelectedListPerRun.append(networkSelectedList)
        print(len(bitRateListOriginal), "-----", len(bitRateList))

        # get the coordinates to highlight in plot
        dotCoordinatesList = getHighlightCoordinates(timeSlotToHighlightList, bitRateListOriginal, bitRateList, runIndex)
        dotCoordinatesListPerRow.append(dotCoordinatesList)
        # print("Coordinates to highlight:", dotCoordinatesListPerRow)
        # saveTxtFile(outputDir + algorithmNameList[algorithmNameIndex - 1] + "_coordinates.txt", "Coordinates to highlight: \n" + str(dotCoordinatesList))
        saveTxtFile(outputDir + algorithmNameList[algorithmNameIndex - 1] + "_coordinates.txt", "Run " + str(runIndex + 1) + "\nx\ty\tlabel\n" + str(dotCoordinatesList))

        # compute cell load per time slot; from cell load file
        inputCSVfile = rootDir + cellLoadFileNameList[algorithmNameIndex - 1][runIndex]
        cellLoadList = extractCellLoad(inputCSVfile, slotStartTimestampList)
        cellLoadList = np.array(cellLoadList); cellLoadList = pandas.rolling_mean(cellLoadList, 5); cellLoadList = list(cellLoadList[rollingAvgWindow - 1:])
        cellLoadListPerRun.append(cellLoadList)

    header = ["time slot"]
    for i in range(1, numRun + 1): header += ["Run " + str(i)]
    # save consolidated per time slot bit rate file
    outputCSVfile = outputDir + algorithmNameList[algorithmNameIndex - 1] + "_bitRate.csv"
    rowNumbering = [i for i in range(1 + int(ceil((rollingAvgWindow - 1)/2)), maxRunDuration - (rollingAvgWindow//2) + 1)]
    saveCSVfile(outputCSVfile, header, bitRateListPerRun, rowNumbering)

    # save consolidated per time slot cell load
    outputCSVfile = outputDir + algorithmNameList[algorithmNameIndex - 1] + "_cellLoad.csv"
    # rowNumbering = [i for i in range(1, maxRunDuration + 1)]
    rowNumbering = [i for i in range(1 + int(ceil((rollingAvgWindow - 1) / 2)), maxRunDuration - (rollingAvgWindow // 2) + 1)]
    saveCSVfile(outputCSVfile, header, cellLoadListPerRun, rowNumbering)

    # plot the graphs
    # plt.style.use('classic')
    # colorList = ["blue", "pink", "green", "magenta", "red", "orange"]
    # xLabel = range(1, maxRunDuration + 1)
    # plt.xlim(1, len(xLabel))
    # for i in range(numRun):
    #     xLabel_local = list(range(1, len(bitRateListOriginalPerRun[i]) + 1))
    #     plt.plot(xLabel_local, bitRateListOriginalPerRun[i], linestyle="--", color=colorList[i])
    #     plt.plot(xLabel_local[int(ceil((rollingAvgWindow-1)/2)) : len(bitRateListOriginalPerRun[i])-((rollingAvgWindow-1)//2)], bitRateListPerRun[i], linestyle="-", color=colorList[i+ (numRun * 1)])
    # plt.show()
    # end main

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
main()