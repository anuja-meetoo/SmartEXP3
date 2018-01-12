#!/bin/sh

numMobileUser=$1
numNetwork=$2
networkDataRate=$3
numRun=$4
numParallelSim=$5
timeStepDuration=$6
maxNumIteration=$7
beta=$8
gainScale=$9
maxTimeStepPrevBlock=${10}
saveMinimalDetail=${11}
algorithmIndex=${12}
algorithmName=${13}
setup=${14}

dir="${networkDataRate}"
if [ ! -d "$dir" ]; then
	mkdir $dir
fi

dir="$dir/${algorithmName}_${numMobileUser}users_${numNetwork}networks"
if [ ! -d "$dir" ]; then
	mkdir $dir
fi
for (( c=1; c<=$numParallelSim; c++ ))
do
   bash experiment.sh $numMobileUser $numNetwork $timeStepDuration $maxNumIteration $numRun $algorithmIndex $beta $gainScale $maxTimeStepPrevBlock $dir $saveMinimalDetail $c "$networkDataRate" $setup &
done

