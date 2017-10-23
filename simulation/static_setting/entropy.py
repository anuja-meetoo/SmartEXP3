import csv
from math import log

numUser = 20
numNetwork = 3
numTimeSlot = 1200
numRun = 100
numParallelRun = 5
algorithmNameList = ["stableHybridBlockEXP3"] #["EXP3", "stableHybridBlockExp3_reset"]
rootDir = "/media/anuja/My Passport/simulationResults_final_20170602/static_setting_code/4_7_22/"
# rootDir = "/Users/anuja/testSimulation/static_setting_code/4_7_22/"

def computeEntropyPerTimeSlot(dir):
    '''
    @description:   computes the entropy per time slot for each user, add the entropy of all users per time slot; compute the average over all runs
    @arg:           root directory where the user files are stored
    $return:        average (over all runs) aggregate (for all users) entropy per time slot
    '''
    global numUser, numNetwork, numTimeSlot, numParallelRun

    entropyPerTimeSlot = [0] * numTimeSlot

    for parallelRunIndex in range(1, numParallelRun + 1):
        for userID in range(1, numUser + 1):
            userCSVfile = dir + "run_" + str(parallelRunIndex) + "/user" + str(userID) + ".csv"

            with open(userCSVfile, newline='') as userCSVfile:
                rowReader = csv.reader(userCSVfile)
                count = 0

                for row in rowReader:
                    if count != 0:
                        timeSlot = int(row[1])
                        probability = row[2 + numNetwork : 2 + 2*numNetwork]
                        probability = [float(x) for x in probability]
                        entropy = computeEntropy(probability)
                        # print("user:", userID, ", time slot: ", timeSlot, ", prob:", probability, ", entropy:", entropy); input()
                        entropyPerTimeSlot[timeSlot - 1] += entropy
                    count += 1
    print("Done parallel run", parallelRunIndex)
    entropyPerTimeSlot = [x/(numParallelRun*numRun*numUser) for x in entropyPerTimeSlot]
    return entropyPerTimeSlot
    # end computeEntropyPerTimeSlot

def computeEntropy(probability):
    '''
    @description:   computes the entropy of a probability distribution
    @arg:           probability distribution of a user at a particular time slot
    @return:        the entropy value
    '''
    entropy = 0
    for prob in probability: entropy += (prob * log(prob, 2))
    entropy *= (-1)
    return entropy
    # end computeEntropy

def saveToCSVfile(outputCSVfile, data):
    outfile = open(outputCSVfile, "w")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    out.writerow(["Time slot", "entropy (aggregate for all users; average over all runs)"])
    for i in range(len(data)): out.writerow([i + 1, data[i]])
    outfile.close()
    # end saveToCSVfile

def main():
    global rootDir

    for algorithmName in algorithmNameList:
        dir = rootDir + algorithmName + "_20users_3networks/"
        entropyPerTimeSlot = computeEntropyPerTimeSlot(dir)
        print(entropyPerTimeSlot)
        saveToCSVfile(dir + "extractedData/entropy.csv", entropyPerTimeSlot)
        print("Done algorithm", algorithmName)
    # end main
main()
