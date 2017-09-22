'''
@description: measures the delay incurred when switching from WiFi to 3G (3G connection via tethered mobile phone);
connection and disconnection involves enabling/disabling 3G on the phone by sending the appropriate adb shell command
'''

#!/usr/bin/python3
import subprocess
from time import sleep, time
import csv
from termcolor import colored

wifiSSID = "NUS"
gsmUUID = "9d93c7b8-3de9-372f-ae0e-6a98245d0521"
outputCSVfile = "delay.csv"

outfile = open(outputCSVfile, "a")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
out.writerow(["time slot", "delay (secs) - 3G"])
outfile.close()

for i in range(40):
    additionalTime = 0

    ##### disconnect from 3G (disable data)
    print("Disabling data on phone")
    cmdOutput = subprocess.Popen("time adb shell svc data disable", shell="True", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = cmdOutput.communicate()

    ##### connect to WiFi
    print("Connecting to WiFi")
    process = subprocess.Popen("nmcli connection up id " + wifiSSID, shell=True, stdout=subprocess.PIPE)
    process.wait()

    ##### switch to 3G
    # disconnect from WiFi
    print("Disconnecting from WiFi")
    startSwitchTime = time()
    process = subprocess.Popen("nmcli connection down id " + wifiSSID, shell=True, stdout=subprocess.PIPE)
    process.wait()

    # enable data
    print("Enabling data on phone")
    cmdOutput = subprocess.Popen("time adb shell svc data enable", shell="True", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = cmdOutput.communicate()
    timeTakenCommunicatePhone = str(err).rstrip()[2:].split()[2]
    timeTakenCommunicatePhone = float(timeTakenCommunicatePhone[2:len(timeTakenCommunicatePhone) - 7])
    additionalTime += timeTakenCommunicatePhone

    ##### download
    err = "Network is unreachable"
    while "Network is unreachable" in str(err):
        cmdOutput = subprocess.Popen("curl 74.125.200.103 --connect-timeout 16", shell="True", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, err = cmdOutput.communicate()
        print(err)
    delay = time() - startSwitchTime - additionalTime
    print(colored("switching delay: " + str(delay), "cyan"))

    outfile = open(outputCSVfile, "a")
    out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    out.writerow([i + 1, delay])
    sleep(10)

# www.google.com has address 74.125.200.103
# www.google.com has address 74.125.200.99
# www.google.com has address 74.125.200.147
# www.google.com has address 74.125.200.104
# www.google.com has address 74.125.200.106
# www.google.com has address 74.125.200.105
