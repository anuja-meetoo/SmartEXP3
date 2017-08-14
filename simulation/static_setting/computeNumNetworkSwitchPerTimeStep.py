'''
@description: Computes number of network switch per time step for every run; and on average over all runs
@author: Anuja
@data: 10 February 2016
'''

import csv
from sys import argv

numUser = int(argv[1])
numNetwork = int(argv[2])
numRun = int(argv[3])
numParallelRun = int(argv[4])
MAX_NUM_ITERATION = int(argv[5])
dir = argv[6]
SAVE_MINIMAL_DETAIL = True if int(argv[7]) == 1 else 0


totalNumNetSwitchAllRunsCSVfile = dir + "extractedData/numNetSwitchPerIteration_allRuns.csv"

def computeNumNetSwitchPerTimeStep():
    totalNumNetSwitchAllRuns = [0] * MAX_NUM_ITERATION

    for j in range(numParallelRun):
        totalNumNetSwitchPerRun = []
        for l in range(numRun): totalNumNetSwitchPerRun.append([0] * MAX_NUM_ITERATION)

        for i in range(numUser):
            userCSVfile = dir + "run_" + str(j + 1) + "/user" + str(i + 1) + ".csv"
            with open(userCSVfile, newline='') as userCSVfile:
                userReader = csv.reader(userCSVfile)
                count = 0
                prevNetwork = -1
                for rowUser in userReader:  # compute total gain of user and that of each expert
                    if count != 0:
                        runNum = int(rowUser[0])
                        iterationNum = int(rowUser[1])

                        if SAVE_MINIMAL_DETAIL == True: currentNetwork = int(rowUser[2 + (2 * numNetwork)])
                        else: currentNetwork = int(rowUser[4 + (2 * numNetwork)])

                        if prevNetwork != -1 and currentNetwork != prevNetwork: # there has been a change in network in the current time step
                            totalNumNetSwitchAllRuns[iterationNum - 1] += 1
                            totalNumNetSwitchPerRun[runNum - 1][iterationNum - 1] += 1

                        if iterationNum == MAX_NUM_ITERATION: # last iteration
                            prevNetwork = -1
                        else: prevNetwork = currentNetwork
                    count = count + 1

            print("done for user", (i + 1))

            userCSVfile.close()
        print("done for 1 parallel run", (j + 1))

    return totalNumNetSwitchAllRuns

def savePerRunData(totalNumNetSwitchPerRun, j):
    for r in range(len(totalNumNetSwitchPerRun)): # i = 0 to 49
        fileRunNum = numRun * j + (r + 1)
        totalNumNetSwitchSingleRunCSVfile = dir + "/extractedData/numNetSwitchPerIteration_run" + str(fileRunNum) + ".csv"
        outfile = open(totalNumNetSwitchSingleRunCSVfile, "w")
        out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
        out.writerow(["Parallel run", "Run no", "No of network switch"])
        for i in range(MAX_NUM_ITERATION):
            out.writerow([(j + 1), (i + 1), totalNumNetSwitchPerRun[r][i]])
        outfile.close()

# main program
totalNumNetSwitchAllRuns = computeNumNetSwitchPerTimeStep()

outfile = open(totalNumNetSwitchAllRunsCSVfile, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
out.writerow(["Run no", "Total no of network switch", "Average number of network switch per run"])
for i in range(len(totalNumNetSwitchAllRuns)):
    out.writerow([(i + 1), totalNumNetSwitchAllRuns[i], totalNumNetSwitchAllRuns[i]/(numRun * numParallelRun)])
outfile.close()
