'''
@description: reads the distance to NE of each algorithm, compute their rolling average and save the later into a single CSV file
'''

import csv
import numpy as np
import pandas

algorithmList = ["EXP3", "blockEXP3", "hybridBlockEXP3", "stableHybridBlockEXP3", "stableHybridBlockExp3_reset", "greedy", "expWeightedAvgFullInfo", "centralized", "fixedRandom"]
rootDir = "/Users/anuja/Desktop/simulationResult/4_7_22_20users_3networks_processedResult_static/"
rollingAverageWindowSize = 5

distanceRollingAvgPerAlgorithm = []

# read the distance and compute the rolling average
for algorithm in algorithmList:
    inputCSVfile = rootDir + algorithm + "/extractedData/distanceToNE_allRuns.csv"

    # read the distance to NE per time slot into a list
    distanceRollingAvg = []
    with open(inputCSVfile, newline='') as inputCSVfile:
        fileReader = csv.reader(inputCSVfile)
        count = 0
        for row in fileReader:
            if count != 0: distanceRollingAvg.append(float(row[1]))
            count += 1

    # compute the rolling average
    distanceRollingAvg = np.array(distanceRollingAvg)
    distanceRollingAvg = pandas.rolling_mean(distanceRollingAvg, rollingAverageWindowSize)  # rolling average of gain
    distanceRollingAvg = distanceRollingAvg[~np.isnan(distanceRollingAvg)]  # remove nan from list
    distanceRollingAvg = list(distanceRollingAvg)

    distanceRollingAvgPerAlgorithm.append(distanceRollingAvg)

# save into a combined file
outputCSVfile = rootDir + "distanceToNE.csv"
outfile = open(outputCSVfile, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
out.writerow(["Time slot"] + algorithmList)
for i in range(len(distanceRollingAvgPerAlgorithm[0])):
    rowData = [(rollingAverageWindowSize//2) + 1 + i]
    for j in range(len(algorithmList)): rowData.append(distanceRollingAvgPerAlgorithm[j][i])
    out.writerow(rowData)
outfile.close()