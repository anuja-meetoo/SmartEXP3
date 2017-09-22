'''
@description:   Extract the following form the logs: (1) per time slot data rate over wifi and cellular, (2) per time slot cell load
@date: Monday   24 April 2017
@version:       1.0
'''

import csv
import dateutil.parser
import argparse

rootDir = "/Users/anuja/Desktop/WNS_EXPERIMENT_WILD_BACKUP/experiments@yih_20170428/"
slotDuration = 15

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def extractWiFiBitRate(inputCSVfile, startTimestamp, endTimestamp):
    '''
    @description:   extracts bit rate, and timestamp of start of each time slot
    @arg:           CSV file containing details of experiment run (inputCSVfile)
    @return:        list of bit rates observed per time slot (bitRateList), timestamp of start of each time slot + end timestamp of last time slot
                    (slotStartTimestampList)
    '''
    global slotDuration

    wifiBitRateList = []
    slotStartTimestampList = []

    print("going to extract trace from file", inputCSVfile)
    with open(inputCSVfile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        for row in rowReader:
            if count != 0:
                if count == 1: print(row)
                slotStartTimestamp = float(row[1])
                if int(slotStartTimestamp) > int(endTimestamp): break
                if int(slotStartTimestamp) >= int(startTimestamp):
                    slotStartTimestampList.append(slotStartTimestamp)
                    wifiBitRateList.append(float(row[8]))
                    slotDuration = float(row[9]) + float(row[10])
                # print("count:", count, ", slotStartTimestamp:", slotStartTimestamp, ", row:", row, ", slotStartTimestampList:", slotStartTimestampList); input()
            count += 1
    print(">>>>>b4 adding last:", len(slotStartTimestampList))
    slotStartTimestampList.append(slotStartTimestampList[-1] + slotDuration)
    # print("slotStartTimestampList:", slotStartTimestampList, "-----", len(slotStartTimestampList))
    # print("wifi bit rate:", wifiBitRateList, "----- len:", len(wifiBitRateList))
    inputCSVfile.close()
    return wifiBitRateList, slotStartTimestampList
    # end extractBitRate

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def extractCellularBitRate(inputCSVfile, slotStartTimestampList):
    cellularBitRateList = []
    p = dateutil.parser.parser()    # to parse date and time as string to datetime format
    index = 0; startTimeSlot = slotStartTimestampList[index]; endTimeSlot = slotStartTimestampList[index + 1] # current time slot start and end timestamps

    with open(inputCSVfile, newline='') as inputCSVfile:
        rowReader = csv.reader(inputCSVfile)
        count = 0
        bitRateCurrentTimeSlotList = []
        for row in rowReader:
            if count > 5:
                # print("----- startTimeSlot:", startTimeSlot)
                timestamp = p.parse(row[0]).timestamp() # convert date as string to datetime, then to timestamp
                bitRate = float(row[16])/(1000**2)
                if int(timestamp) > int(slotStartTimestampList[-1]):
                    # print("bitRateCurrentTimeSlotList:", bitRateCurrentTimeSlotList);input()
                    cellularBitRateList.append(sum(bitRateCurrentTimeSlotList) / len(bitRateCurrentTimeSlotList))
                    break    # data if not within time range of network trace considered
                if int(timestamp) >= int(endTimeSlot):    # data for the next time slot
                    # print("bitRateCurrentTimeSlotList:", bitRateCurrentTimeSlotList);input()
                    cellularBitRateList.append(sum(bitRateCurrentTimeSlotList)/len(bitRateCurrentTimeSlotList))
                    bitRateCurrentTimeSlotList = [bitRate]
                    index += 1
                    if index == len(slotStartTimestampList) - 1: break
                    else: startTimeSlot = slotStartTimestampList[index]; endTimeSlot = slotStartTimestampList[index + 1]
                elif int(timestamp) >= int(startTimeSlot) and int(timestamp) < int(endTimeSlot):
                    # add bit rate to current slot details
                    bitRateCurrentTimeSlotList.append(bitRate)   # convert to Mbps
                # else: print("discarding ", bitRate, "for timestamp", timestamp, "-----", row[0])
            count += 1
    inputCSVfile.close()

    # print("cellular bit rate:", cellularBitRateList, "----- len:", len(cellularBitRateList))

    return cellularBitRateList
    # end extractCellularBitRate

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def saveCSVfile(outputCSVfile, wifiBitRateList, cellularBitRateList):
    '''
    @description:   saves details in a csv file with the specified name
    @arg:           url of output CSV file
    @return:        None
    '''
    myfile = open(outputCSVfile, "w")
    out = csv.writer(myfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    # output csv file format: time slot	WiFi bit rate (Mbps)	Cellular bit rate (Mbps)

    out.writerow(["time slot", "WiFi bit rate (Mbps)", "Cellular bit rate (Mbps)"])
    for i in range(len(wifiBitRateList)):
        out.writerow([i + 1, wifiBitRateList[i], cellularBitRateList[i]])
    myfile.close()
    # end saveCSVfile

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def saveTxtFile(outputTxtFile, data):
    '''
    @description:   saves data to the text file with the specified name
    @arg:           url of output text file and data to be written to the file
    @return:        None
    '''
    outfile = open(outputTxtFile, "a")
    outfile.write(data + "\n\n")
    outfile.close()
    # end saveTxtFile

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
def main():
    parser = argparse.ArgumentParser(description='Extracts details from network trace.')
    parser.add_argument('-i', dest="scenario_index", required=True, help='scenario being processed')
    parser.add_argument('-s', dest="start_timestamp", required=True, help='start timestamp to be considered for trace')
    parser.add_argument('-e', dest="end_timestamp", required=True, help='end timestamp to be considered for trace (including the slot starting at that timestamp)')
    args = parser.parse_args()
    scenarioIndex = int(args.scenario_index)
    startTimestamp = float(args.start_timestamp)
    endTimestamp = float(args.end_timestamp)
    wifiInputCSVfile = rootDir + "scenario" + str(scenarioIndex) + "_wifiTrace.csv"
    cellularInputCSVfile = rootDir + "scenario" + str(scenarioIndex) + "_cellularTrace.csv"

    outputCSVfile = rootDir + "networkTrace/scenario" + str(scenarioIndex) + ".csv"

    # extract details for wifi network trace
    wifiBitRateList, slotStartTimestampList = extractWiFiBitRate(wifiInputCSVfile, startTimestamp, endTimestamp)
    cellularBitRate = extractCellularBitRate(cellularInputCSVfile, slotStartTimestampList)

    saveCSVfile(outputCSVfile, wifiBitRateList, cellularBitRate)

''' ------------------------------------------------------------------------------------------------------------------------------------- '''
main()

# convert from dtaetime to timestamp
# currentTime = time()
# >> > currentTime, datetime.fromtimestamp(currentTime).timestamp()

# convert from string to datetime
# endTime = str(float(row[1]) + slotDuration) + "; " + str(p.parse(row[2]) + timedelta(seconds=slotDuration))
