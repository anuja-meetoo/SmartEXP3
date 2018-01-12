import subprocess
from time import sleep
import os
import traceback


algorithmNameList = ["EXP3", "blockEXP3", "hybridBlockEXP3", "stableHybridBlockEXP3", "stableHybridBlockExp3_reset", "greedy", "expWeightedAvgFullInfo", "centralized", "fixedRandom"]
algorithmIndexList = [(x + 1) for x in range(len(algorithmNameList))]

numUser=20
numNetwork=3
networkDataRate="4_7_22"
numRun=100
numParallelRun=5
timeStepDuration=15
maxNumIteration =1200
beta=0.1
gainScale=1
maxTimeStepPrevBlock=8
saveMinimalDetail=1

setup=2

epsilonEquilibriumListStr="0"
convergedProb=0.75
epsilon=7.5

for algorithmIndex in algorithmIndexList:
    algorithmName = algorithmNameList[algorithmIndex - 1]
    if os.path.exists(networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult") == False:
        subprocess.check_output("mkdir " + networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult", shell=True, universal_newlines=True)
    resultDirName = networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult/" + algorithmName
    if os.path.exists(resultDirName) == False:
        subprocess.check_output("mkdir " + resultDirName, shell=True, universal_newlines=True)
    resultDir = resultDirName + "/"

    if os.path.exists("nohup.out"): subprocess.check_output("rm nohup.out", shell=True, universal_newlines=True)
    if os.path.exists("nohup_process.out"): subprocess.check_output("rm nohup_process.out", shell=True,
                                                                    universal_newlines=True)

    # run the experiment
    subprocess.check_output("nohup bash experiments_parallel.sh " + str(numUser) + " " + str(numNetwork) + " " + networkDataRate + " " + str(numRun) + " " + str(numParallelRun) + " " + str(timeStepDuration) + " " + str(maxNumIteration) + " " + str(beta) + " " + str(gainScale) + " " + str(maxTimeStepPrevBlock) + " " + str(saveMinimalDetail) + " " + str(algorithmIndex) + " " + algorithmName + " " + str(setup) + " > nohup.out", shell=True, universal_newlines=True)

    # check if experiment is over
    sleep(5); result=0;
    try: result = int(subprocess.check_output("cat nohup.out | grep -c 'Run " + str(numRun) + " '", shell=True, universal_newlines=True))
    except: traceback.print_exc()
    while result != numParallelRun:
        sleep(60)
        try: result = int(subprocess.check_output("cat nohup.out | grep -c 'Run " + str(numRun) + " '", shell=True, universal_newlines=True))
        except: traceback.print_exc()

    # process the results
    subprocess.check_output("nohup bash processResults.sh " + str(numUser) + " " + str(numNetwork) + " " + networkDataRate + " " + str(maxNumIteration) + " " + str(numRun) + " " + str(numParallelRun) + " " + str(convergedProb) + " " + str(saveMinimalDetail) + " " + str(epsilon) + " " + resultDir + " " + algorithmName + " " + str(setup) + " > nohup_process.out", shell=True, universal_newlines=True)
    print("Done for algorithm index " + str(algorithmIndex) + "!!!")
