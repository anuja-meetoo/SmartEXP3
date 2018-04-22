'''
@description: Computes the average gain of all mobile users for each iteration in a specific run
'''

import csv
from sys import argv
from os import system
import os

numUser = int(argv[1]) #20
numNetwork = int(argv[2]) #3
dir=argv[3]
numIteration = int(argv[4])           # number of iterations in the run to be considered
numRun = int(argv[5])                   # number of runs  per parallel run
numParallelRun = int(argv[6])       # number of parallel runs


SAVE_MINIMAL_DETAIL = True if int(argv[7]) == 1 else 0

outputGainCSVfileParallel = dir + "extractedData/averageGainPerIterationParallel.xls"
outputRegretCSVfileParallel = dir + "extractedData/averageRegretPerIterationParallel.xls"

highestRegret = 0; highestRegretUser = 0; highestRegretRunNum = 0; highestRegretParallelRunNum = 0; regretList=[]


def computeAverageGainRegretPerIteration(parallelRunDir, parallelRunNum): # compute average user gains per iteration in a single folder
    ''' 
    description: Computes the average gain of all users per iteration in a single folder (not considering parallel run)
    arg: Directory for the runs (parallel runs saved in different directories
    return: List of average gain of all users per iteration
    '''
    global highestRegret, highestRegretUser, highestRegretRunNum, highestRegretParallelRunNum, regretList # to keep track of the worst case regret
    
    totalGainPerIteration, avgGainPerIteration, totalRegretPerIteration, avgRegretPerIteration = [0] * numIteration, [0] * numIteration, [0] * (numIteration - 1), [0] * (numIteration - 1)
    for i in range(numUser):
        bestExpertPerRunPerUser = [] # best expert ID per run for one user
        userCSVfile = parallelRunDir + "user" + str(i + 1) + ".csv"

        # open the file to compute average gain per iteration for one user;
        # and find the best expert for the user in each run
        with open(userCSVfile, newline='') as userCSVfile:
            userFileReader = csv.reader(userCSVfile)
            count = 0 # no of rows processed so far; to skip header
            totalExpertGain = [0] *  numNetwork # save total gain of each expert for one user
            totalUserGain = 0
            for rowUser in userFileReader:
                if count != 0:
                    currentRunNum = int(rowUser[0])                
                    currentIterationNum = int(rowUser[1])

                    if SAVE_MINIMAL_DETAIL == True: userGain = float(rowUser[4 + (2 * numNetwork)]) #userGain = float(rowUser[3 + (2 * numNetwork)])
                    else: userGain = float(rowUser[7 + (2 * numNetwork)]) #userGain = float(rowUser[11 + (2 * numNetwork)])
                    
                    # if start of a new run reached
                    if currentRunNum != 1 and currentIterationNum == 1:
                        bestExpertID = totalExpertGain.index(max(totalExpertGain)) + 1
                        bestExpertPerRunPerUser.append(bestExpertID)
                        
                        # to keep track of worst regret
                        bestExpertGain = max(totalExpertGain)
                        totalRegret = bestExpertGain - totalUserGain
                        #print("total regret = ", totalRegret)
                        if totalRegret > highestRegret: highestRegret = totalRegret; highestRegretUser = (i+1); highestRegretRunNum = currentRunNum - 1; highestRegretParallelRunNum = parallelRunNum
                        
                        totalExpertGain = [0] *  numNetwork # reset the total gain of each expert for one user
                        totalUserGain = 0
                    
                    elif currentIterationNum > 1:                        
                        totalUserGain += userGain
                        for net in range(numNetwork):
                            if SAVE_MINIMAL_DETAIL == True: totalExpertGain[net] += float(rowUser[6 + (2 * numNetwork) + net])
                            else: totalExpertGain[net] += float(rowUser[12 + (2 * numNetwork) + net])
                    totalGainPerIteration[currentIterationNum - 1] += userGain

                count += 1
            # best expert for last run
            bestExpertID = totalExpertGain.index(max(totalExpertGain)) + 1
            bestExpertPerRunPerUser.append(bestExpertID)
            
            # to keep track of worst regret
            bestExpertGain = max(totalExpertGain)
            totalRegret = bestExpertGain - totalUserGain
            #print("total regret: ", totalRegret)
            if totalRegret > highestRegret: highestRegret = totalRegret; highestRegretUser = (i+1); highestRegretRunNum = currentRunNum; highestRegretParallelRunNum = parallelRunNum
            
        #print("user ID =", (i + 1), "; bestExpertID: ", bestExpertPerRunPerUser)
        userCSVfile.close()
        # end compute average gain per iteration for one user - close the file
        
        # open the file to compute average regret per iteration
        userCSVfile = parallelRunDir + "user" + str(i + 1) + ".csv"
        with open(userCSVfile, newline='') as userCSVfile:
            userFileReader = csv.reader(userCSVfile)
            count = 0 # no of rows processed so far; to skip header
            for rowUser in userFileReader:
                if count != 0:
                    currentRunNum = int(rowUser[0])
                    currentIterationNum = int(rowUser[1])
                    if currentIterationNum > 1:
                        if SAVE_MINIMAL_DETAIL == True: userGain = float(rowUser[4 + (2 * numNetwork)])
                        else: userGain = float(rowUser[7 + (2 * numNetwork)]) #userGain = float(rowUser[11 + (2 * numNetwork)])
                        #print("user", (1 + i), ", going to subtract gain ", userGain,"from", rowUser[11 + (2 * numNetwork) + bestExpertPerRunPerUser[currentRunNum - 1]])
                        if SAVE_MINIMAL_DETAIL == True: gainBestExpert = float(rowUser[6 + (2 * numNetwork) + bestExpertPerRunPerUser[currentRunNum - 1] - 1])
                        else: gainBestExpert = float(rowUser[12 + (2 * numNetwork) + bestExpertPerRunPerUser[currentRunNum - 1] - 1])

                        userRegret = gainBestExpert - userGain

                        #print("user: ", (i + 1), "; iteration: ", currentIterationNum,"; regret: ", userRegret)
                        totalRegretPerIteration[currentIterationNum - 2] += userRegret

                count += 1
        #print("totalGainPerIteration",totalGainPerIteration)
        #print("gain... done for user", (i + 1))
        #print("bestExpertPerRunPerUser", bestExpertPerRunPerUser)

        #print("totalRegretPerIteration",totalRegretPerIteration)
        print("done for user", (i + 1));
        userCSVfile.close()
        # end compute average regret per iteration - close the file

    for i in range(numIteration):
        avgGainPerIteration[i] = totalGainPerIteration[i]/(numUser * numRun) # compute average for each iteration
    for i in range(numIteration - 1): # ignore first iteration as the delay to join the networks is unknown (except the one the user joined)
        avgRegretPerIteration[i] = totalRegretPerIteration[i]/(numUser * numRun) # compute average for each iteration
    #print("totalGainPerIteration: ", totalGainPerIteration)
    #print("avgGainPerIteration: ", avgGainPerIteration)
    #print("totalRegretPerIteration: ", totalRegretPerIteration)
    #print("@@@ avgRegretPerIteration: ", avgRegretPerIteration)
    return avgGainPerIteration, avgRegretPerIteration
    # end compute average user gains per iteration when user makes use of greedy algorithm

def combineParallelRunAveragePerIteration(fileName, numRows): # combine average gain per iteration computed for each folder into a single file
    '''
    description: Saves the average gain of all users per iteration passed as argument in a csv file
    arg: List of average gain of all users per iteration, address of csv file in which to save the average user gains per iteration
    return: None
    '''
    totalPerIteration, avgPerIteration = [0] * numRows, [0] * numRows
    for i in range(numParallelRun): 
        parallelRunDir = dir + "run_" + str(i + 1) + "/extractedData/"
        if os.path.exists(parallelRunDir) == False: os.makedirs(parallelRunDir)
        inputCSVfile = parallelRunDir + fileName #"averageGainPerIteration.xls"
        with open(inputCSVfile, newline='') as inputCSVfile:
            inputFileReader = csv.reader(inputCSVfile)
            count = 0 # no of rows processed so far; to skip header and to determine index of element in list totalGainPerIteration to which value must be added
            for row in inputFileReader:
                if count != 0:
                    currentVal = float(row[0])
                    totalPerIteration[count - 1] += currentVal
                count += 1
        print("done for parallel run ", (i + 1))
        inputCSVfile.close()
    for i in range(numRows): avgPerIteration[i] = totalPerIteration[i]/numParallelRun # compute average for each iteration
    return avgPerIteration
        
def writeCSVfile(avgPerIteration, outputCSVfile):
    '''
    description: Saves the average gain of all users per iteration passed as argument in a csv file
    arg: List of average gain of all users per iteration, address of csv file in which to save the average user gains per iteration
    return: None
    '''
    outfile = open(outputCSVfile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
    out.writerow(["Average per iteration"])    
    for i in range(len(avgPerIteration)): out.writerow([avgPerIteration[i]])
    outfile.close()

def computeAverageGainPerIterationParallel():
    '''
    description: Calculates average gain of all users per iteration across all runs
    arg: None
    return: None 
    ''' 
    for i in range(numParallelRun): # compute average user gains per iteration for every parallel run
        parallelRunDir = dir + "run_" + str(i + 1) + "/"
        if os.path.exists(parallelRunDir+ "extractedData") == False: os.makedirs(parallelRunDir + "extractedData")
        outputGainCSVfile = parallelRunDir + "extractedData/averageGainPerIteration.xls"
        outputRegretCSVfile = parallelRunDir + "extractedData/averageRegretPerIteration.xls"
        avgGainPerIteration, avgRegretPerIteration = computeAverageGainRegretPerIteration(parallelRunDir, (i + 1))
        writeCSVfile(avgGainPerIteration, outputGainCSVfile)
        writeCSVfile(avgRegretPerIteration, outputRegretCSVfile)
        print("done for parallel run", (i + 1))
    avgGainPerIteration = combineParallelRunAveragePerIteration("averageGainPerIteration.xls", numIteration) # combine result for all parallel runs
    writeCSVfile(avgGainPerIteration, outputGainCSVfileParallel)    # save the result in a csv file
    avgRegretPerIteration = combineParallelRunAveragePerIteration("averageRegretPerIteration.xls", numIteration - 1)
    writeCSVfile(avgRegretPerIteration, outputRegretCSVfileParallel)
    
    print("highestRegret: " + str(highestRegret) + "; highestRegretUser: " + str(highestRegretUser) + "; highestRegretRunNum: " + str(highestRegretRunNum) + "; highestRegretParallelRunNum: " + str(highestRegretParallelRunNum))
    shellCommand = "echo highestRegret is " + str(highestRegret) + ", highestRegretUser is " + str(highestRegretUser) + ", highestRegretRunNum is " + str(highestRegretRunNum) + ", highestRegretParallelRunNum is " + str(highestRegretParallelRunNum) + " > " + dir + "extractedData/worstCaseRegret.txt"
    system(shellCommand)
computeAverageGainPerIterationParallel()
