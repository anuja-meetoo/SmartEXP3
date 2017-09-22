#!/usr/bin/python3
import subprocess
from time import sleep, time
import csv
from termcolor import colored

wifiSSIDlist = ["dlink-C164-5GHz", "NUS"]
outputCSVfile = "wifi_delay.csv"

outfile = open(outputCSVfile, "a")
out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
out.writerow(["time slot", "delay (secs) - 3G"])
outfile.close()

process = subprocess.Popen("nmcli connection down id " + wifiSSIDlist[0], shell=True, stdout=subprocess.PIPE)
process.wait()
process = subprocess.Popen("nmcli connection up id " + wifiSSIDlist[1], shell=True, stdout=subprocess.PIPE)
process.wait()

currentNetwork = 2; previousNetwork = 1
for i in range(200):
    previousNetwork, currentNetwork = currentNetwork, previousNetwork

    startSwitchTime = time()

    ##### disconnect from previous WiFi network
    print("Disconnecting from " + wifiSSIDlist[previousNetwork - 1])
    process = subprocess.Popen("nmcli connection down id " + wifiSSIDlist[previousNetwork - 1], shell=True, stdout=subprocess.PIPE)
    process.wait()

    ##### connect to new wifi network
    print("Connecting to " + wifiSSIDlist[currentNetwork - 1])
    process = subprocess.Popen("nmcli connection up id " + wifiSSIDlist[currentNetwork - 1], shell=True, stdout=subprocess.PIPE)
    process.wait()

    startAdditionalTime = time()
    cmdOutput = subprocess.Popen("nmcli device status | grep " + wifiSSIDlist[currentNetwork - 1], shell="True", stdout=subprocess.PIPE)
    connectionStatus, err = cmdOutput.communicate()
    if " connected " not in str(connectionStatus):
        print("FAILED TO CONNECT...")
        outfile = open(outputCSVfile, "a")
        out = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        out.writerow([i + 1, -1])
    else:
        additionalTime = time() - startAdditionalTime
        ##### download
        err = "Network is unreachable"
        while "Network is unreachable" in str(err):
            cmdOutput = subprocess.Popen("curl 74.125.200.103", shell="True", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
