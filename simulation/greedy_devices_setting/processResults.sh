#!/bin/sh

: '
process simulation results...
'

numUser=$1
numNetwork=$2
dataRate=$3
maxNumIteration=$4
numRun=$5
numParallelRun=$6
NElistStr=$7
epsilonEquilibriumListStr=$8
convergedProb=$9
saveMinimalDetail=${10}
epsilon=${11}
resultDir=${12}
algoName=${13}

dir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/"
copyFromDir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/extractedData/"
zipFileName="${algoName}_${numUser}users_${numNetwork}network.zip"
:'
echo ">>> 1. going to process result for convergence, stability, and per user data"
python3 processCSVfile_mean_sd_convergence_multiprocessing.py $numUser $numNetwork $dir $maxNumIteration $numRun $numParallelRun ${NElistStr} ${epsilonEquilibriumListStr} $convergedProb $saveMinimalDetail
echo ">>> DONE!!!"
echo ""


echo ">>> 2. going to extract number of network switches per time slot"
python3 computeNumNetworkSwitchPerTimeStep.py $numUser $numNetwork $numRun $numParallelRun $maxNumIteration $dir $saveMinimalDetail
echo ">>> DONE!!!"
echo ""

echo ">>> 3. going to compute distance to NE"
python3 computeDistanceToNE.py $numUser $numNetwork $dir $maxNumIteration $numRun $numParallelRun $dataRate $NElistStr $epsilon
echo ">>> DONE!!!"
echo ""

echo ">>> 4. gong to compute average gain and average regret per time slot"
python3 computeAverageGainRegretParallel.py $numUser $numNetwork $dir $maxNumIteration $numRun $numParallelRun $saveMinimalDetail
echo ">>> DONE!!!"
'
echo ">>>>> going to extract stability and convergence data"
python3 convergence_stability.py $numUser $numNetwork $numRun $numParallelRun $maxNumIteration $dataRate $dir $NElistStr
cp -r ${copyFromDir} ${resultDir}
cp nohup* ${resultDir}

cd ${dataRate}
zip -r $zipFileName "${algoName}_${numUser}users_${numNetwork}networks/"
scp $zipFileName anuja@"172.26.191.129:/media/anuja/Data/wns_simulationResults/${dataRate}_${numUser}users_${numNetwork}networks/"
rm $zipFileName
cd ..
rm -r $dir
