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
epsilonEquilibriumListStr=${7}
convergedProb=${8}
saveMinimalDetail=${9}
resultDir=${10}
algoName=${11}

dir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/"
copyFromDir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/extractedData/"
zipFileName="${algoName}_${numUser}users_${numNetwork}network_mobility.zip"

echo ">>> 1. going to compute distance to NE for phase 1"
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 1 "5,5,7,2,1" "1,2,3,4,5,6,7,8" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 1 "5,5,7,2,1" "9,10" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 1 "5,5,7,2,1" "11,12,13,14,15" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 1 "5,5,7,2,1" "16,17,18,19,20" $dataRate

echo ">>> 2. going to compute distance to NE for phase 2"
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 2 "6,2,9,2,1" "1,2,3,4,5,6,7,8" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 2 "6,2,9,2,1" "9,10" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 2 "6,2,9,2,1" "11,12,13,14,15" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 2 "6,2,9,2,1" "16,17,18,19,20" $dataRate

echo ">>> 3. going to compute distance to NE for phase 3"
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 3 "8,2,5,3,2" "1,2,3,4,5,6,7,8" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 3 "8,2,5,3,2" "9,10" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 3 "8,2,5,3,2" "11,12,13,14,15" $dataRate
python3 computeDistanceToNE_mobility.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun 3 "8,2,5,3,2" "16,17,18,19,20" $dataRate
echo ">>> DONE!!!"
echo ""

cp -r ${copyFromDir} ${resultDir}
cp nohup* ${resultDir}

cd ${dataRate}
zip -r $zipFileName "${algoName}_${numUser}users_${numNetwork}networks/"
cd ..
