import subprocess
from time import sleep
import os
import traceback


algorithmNameList = ["EXP3", "blockEXP3", "hybridBlockEXP3", "stableHybridBlockEXP3", "stableHybridBlockExp3_reset", "greedy", "expWeightedAvgFullInfo", "centralized", "fixedRandom"]
algorithmIndexList = [5]#(x + 1) for x in range(len(algorithmNameList))]

numUser=20
numNetwork=3
networkDataRate="4_7_22"	#"11_11_11"
numRun=100 #25
numParallelRun=5 #20
timeStepDuration=15
maxNumIteration =1200
beta=0.1
gainScale=1
maxTimeStepPrevBlock=8
saveMinimalDetail=1

#NElistStr="1,2,7,5,5"
#NElistStr="1,1,5,4,3,2,4"
NElistStr="2,4,14" #"6,7,7;7,6,7;7,7,6"
epsilonEquilibriumListStr="0"#"9,16,55;9,18,53;10,16,54;10,17,53;10,18,52"#"0" #"1,2,7,6,4;1,2,8,5,4" #"0"
convergedProb=0.75
epsilon=7.5
# 20 users 
# 5 networks [4,7,22,16,14]
# NE = [1, 2, 7, 5, 5]
# epsilonEquilibrium = [[1, 2, 7, 6, 4], [1, 2, 8, 5, 4]]
# 7 networks [4,7,22,16,14,11,17]
#NE=[1, 1, 5, 4, 3, 2, 4]
#no epsilon equilibrium

#python3 computeDistanceToNE.py 20 3 ~/testSimulation/tmp/ 1200 1 5 "4_7_22" "2,4,14" 7.5
#rootDir = "/media/anuja/myDrive/"
for algorithmIndex in algorithmIndexList:
    algorithmName = algorithmNameList[algorithmIndex - 1]
    if os.path.exists(networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult") == False:
        subprocess.check_output("mkdir " +networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult", shell=True, universal_newlines=True)
    resultDirName = networkDataRate + "_" + str(numUser) + "users_" + str(numNetwork) + "networks_processedResult/" + algorithmName
    if os.path.exists(resultDirName) == False:
        subprocess.check_output("mkdir " + resultDirName, shell=True, universal_newlines=True)
    resultDir = resultDirName + "/"

    if os.path.exists("nohup.out"): subprocess.check_output("rm nohup.out", shell=True, universal_newlines=True)
    if os.path.exists("nohup_process.out"): subprocess.check_output("rm nohup_process.out", shell=True,
                                                                    universal_newlines=True)

    # run the experiment
    subprocess.check_output("nohup bash experiments_parallel.sh " + str(numUser) + " " + str(numNetwork) + " " + networkDataRate + " " + str(numRun) + " " + str(numParallelRun) + " " + str(timeStepDuration) + " " + str(maxNumIteration) + " " + str(beta) + " " + str(gainScale) + " " + str(maxTimeStepPrevBlock) + " " + str(saveMinimalDetail) + " " + str(algorithmIndex) + " " + algorithmName + " > nohup.out", shell=True, universal_newlines=True)

    # check if experiment is over
    sleep(240); result=0;
    try: result = int(subprocess.check_output("cat nohup.out | grep -c 'Run " + str(numRun) + " '", shell=True, universal_newlines=True))
    except: traceback.print_exc()
    while result != numParallelRun:
        sleep(60)
        try: result = int(subprocess.check_output("cat nohup.out | grep -c 'Run " + str(numRun) + " '", shell=True, universal_newlines=True))
        except: traceback.print_exc()

    # process the results
    #subprocess.check_output("nohup bash processResults.sh " + str(numUser) + " " + str(numNetwork) + " " + networkDataRate + " " + str(maxNumIteration) + " " + str(numRun) + " " + str(numParallelRun) + " '" + NElistStr + "' '" + epsilonEquilibriumListStr + "' " + str(convergedProb) + " " + str(saveMinimalDetail) + " " + str(epsilon) + " " + resultDir + " " + algorithmName + " > nohup_process.out", shell=True, universal_newlines=True) 
    print("Done for algorithm index " + str(algorithmIndex) + "!!!")
