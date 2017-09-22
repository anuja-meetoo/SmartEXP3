import argparse
import csv
import numpy as np
import pandas
from math import ceil

rollingAvgWindow = 5

parser = argparse.ArgumentParser(description='computes the rolling average of the wifi load and saves it to a csv file.')
parser.add_argument('-i', dest="input_file", required=True, help='url of csv file containing wifi load per time slot')
parser.add_argument('-o', dest="output_file", required=True, help='url of output csv file that will store the rolling average')
args = parser.parse_args()
inputCSVfile = args.input_file
outputCSVfile = args.output_file

wifiLoadList = []

# read wifi load per time slot
with open(inputCSVfile, newline='') as inputCSVfile:
    rowReader = csv.reader(inputCSVfile)
    count = 0
    for row in rowReader:
        if count != 0:
            timeSlot = int(row[0])
            wifiLoadList.append(float(row[5]))
        count += 1
runDuration = len(wifiLoadList)

# compute the rolling average
wifiLoadList = np.array(wifiLoadList)
wifiLoadList = pandas.rolling_mean(wifiLoadList, rollingAvgWindow)
wifiLoadList = list(wifiLoadList[rollingAvgWindow-1:])

# save the result to a csv file
myfile = open(outputCSVfile, "w")
out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

out.writerow(["time slot", "load (%)"])
rowNumbering = [i for i in range(1 + int(ceil((rollingAvgWindow - 1) / 2)), runDuration - (rollingAvgWindow // 2) + 1)]
for numbering, load in zip(rowNumbering, wifiLoadList):
    out.writerow([numbering, load])
myfile.close()