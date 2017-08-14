import csv
import numpy as np
import pandas

rootDir = "/media/anuja/Data/"
numScenario = 3
rollingAvgWindowSize = 5
userCategory = ["smartEXP3", "greedy"]
distancePerTimeSlot_combined = []

for scenarioIndex in range(1, numScenario+1):
    scenarioDir = rootDir + "4_7_22_dishonestUsers_scenario" + str(scenarioIndex) + "/stableHybridBlockExp3_reset_20users_3networks/extractedData/"

    # read distance for each category of user
    for category in userCategory:
        distancePerTimeSlot = []
        inputCSVfile = scenarioDir + "distanceToNE_allRuns_" + category + ".csv"
        with open(inputCSVfile, newline='') as inputCSVfile:
            fileReader = csv.reader(inputCSVfile)
            count = 0
            for row in fileReader:
                if count > 0: distancePerTimeSlot.append(float(row[1]));
                count += 1
        inputCSVfile.close()
        print(distancePerTimeSlot, "-----", len(distancePerTimeSlot), "-----", distancePerTimeSlot[0], "-----", distancePerTimeSlot[1190:])
        distancePerTimeSlot = np.array(distancePerTimeSlot)
        distancePerTimeSlot = pandas.rolling_mean(distancePerTimeSlot, rollingAvgWindowSize)
        distancePerTimeSlot = distancePerTimeSlot[~np.isnan(distancePerTimeSlot)]  # remove nan from list
        distancePerTimeSlot = list(distancePerTimeSlot)
        distancePerTimeSlot_combined.append(distancePerTimeSlot)

# save combined file
outputCSVfile = rootDir + "distanceToNE_dishonestUsers.csv"
outfile = open(outputCSVfile, "w")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
header = ["Time slot"]
for scenarioIndex in range(1, numScenario + 1):
    for category in userCategory:
        header.append("Scenario " + str(scenarioIndex) + " - " + category)
out.writerow(header)
for i in range(len(distancePerTimeSlot_combined[0])):
    out.writerow([i + 1 + (rollingAvgWindowSize//2)] + [distancePerTimeSlot_combined[j][i] for j in range(len(distancePerTimeSlot_combined))])
outfile.close()