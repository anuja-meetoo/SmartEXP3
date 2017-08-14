#!/bin/sh

: '
Run as bash ./experiment.sh instead of sh experiment.sh since sh has less extensive syntax
else if statement will not execute properly
'
numMobileUser=$1
numNetwork=$2
timeStepDuration=$3
maxNumIteration=$4
numRun=$5
algorithmIndex=$6
beta=$7
gainScale=$8
maxTimeStepPrevBlock=$9
dir=${10}
saveMinimalDetail=${11}
parallelRunNum=${12}
networkDataRate=${13}

dir="$dir/run_${parallelRunNum}"
mkdir $dir
dir="$dir/"

python3 createCSVfile.py $numMobileUser $numNetwork "$dir" $saveMinimalDetail

COUNTER=1
prevTime=$(date +%s)
echo "simulation starts @ $(date +"%r")"
while [  $COUNTER -lt $((numRun+1)) ]; do
   python3 wns_greedyDevices.py $numMobileUser $numNetwork $timeStepDuration $maxNumIteration $COUNTER $algorithmIndex $beta $gainScale $maxTimeStepPrevBlock $dir $saveMinimalDetail $networkDataRate
   now=$(date +%s)
   diff=$(($now-$prevTime))
   prevTime=$now
   if [ $diff -ge 60 ]
   then
   	echo "Run $COUNTER is completed in $((diff/60)) minutes @$(date +"%r")"
   else
   	echo "Run $COUNTER is completed in $diff seconds @$(date +"%r")"
   fi
   COUNTER=$((COUNTER + 1 ))
done

