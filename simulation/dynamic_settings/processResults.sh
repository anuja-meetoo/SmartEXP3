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
setup=${12}

dir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/"
copyFromDir="${dataRate}/${algoName}_${numUser}users_${numNetwork}networks/extractedData/"
zipFileName="${algoName}_${numUser}users_${numNetwork}network_dynamicEnv.zip"

if [ $setup -eq 1 ]
then
    echo ">>> 1. going to compute distance to NE for phase 1"
    python3 computeDistanceToNE_dynamicEnv.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun $dataRate "1,2,8" 7.5 1

    echo ">>> 2. going to compute distance to NE for phase 2"
    python3 computeDistanceToNE_dynamicEnv.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun $dataRate "2,4,14" 7.5 2

    echo ">>> 3. going to compute distance to NE for phase 3"
    python3 computeDistanceToNE_dynamicEnv.py $numUser $numNetwork $dir $((maxNumIteration/3)) $numRun $numParallelRun $dataRate "1,2,8" 7.5 3
    echo ">>> DONE!!!"
    echo ""
else
    echo ">>> 1. going to compute distance to NE for phase 1"
    python3 computeDistanceToNE_dynamicEnv.py $numUser $numNetwork $dir $((maxNumIteration/2)) $numRun $numParallelRun $dataRate "2,4,14" 7.5 1

    echo ">>> 2. going to compute distance to NE for phase 2"
    python3 computeDistanceToNE_dynamicEnv.py $numUser $numNetwork $dir $((maxNumIteration/2)) $numRun $numParallelRun $dataRate "0,1,3" 7.5 2
    echo ">>> DONE!!!"
    echo ""
fi

cp -r ${copyFromDir} ${resultDir}
cp nohup* ${resultDir}

cd ${dataRate}
zip -r $zipFileName "${algoName}_${numUser}users_${numNetwork}networks/"
cd ..
