'''
source: https://diogomonica.com/2011/04/10/sniffing-in-monitor-mode-with-airport/
'''

import subprocess
from time import sleep
import os
from datetime import datetime

sniffDuration = 60
wifiChannelList = [36, "64-1"]   # list of WiFi channels on which to sniff
outputDir = os.path.expanduser('~') + "/Desktop/experiment_" + datetime.now().strftime('%Y%m%d_%H%M%S') + "/"
# logFile = outputDir + "logFile.txt"

if not os.path.exists(outputDir): os.makedirs(outputDir)

count = 1
try:
    while(True):
        for wifiChannel in wifiChannelList:
            print("Going to sniff on channel " + str(wifiChannel) + " for " + str(sniffDuration) + " seconds...")
            sniffStartTime = datetime.now().strftime('%Y%m%d_%H%M%S')
            sniffProcess = subprocess.Popen("airport en0 sniff " + str(wifiChannel), shell=True)
            sleep(sniffDuration)
            sniffStopTime = datetime.now().strftime('%Y%m%d_%H%M%S')
            subprocess.Popen("kill -HUP %s" % sniffProcess.pid, shell=True)

            # get the .cap file and save it to desktop
            outputFile = subprocess.Popen("ls /tmp/ | grep airport", shell=True, stdout=subprocess.PIPE).communicate()[0]
            print(outputFile)
            outputFile = str(outputFile,'utf-8').rstrip()
            # outputFile = str(outputFile).rstrip()
            subprocess.Popen("mv /tmp/" + outputFile + " " + outputDir + str(count) + "_channel_" + str(wifiChannel) + "_" + sniffStartTime + "_" + sniffStopTime + ".cap", shell=True)
        count += 1
except KeyboardInterrupt:
    subprocess.Popen("kill -HUP %s" % sniffProcess.pid, shell=True)

    # get the .cap file and save it to desktop
    outputFile = subprocess.Popen("ls /tmp/ | grep airport", shell=True, stdout=subprocess.PIPE).communicate()[0]
    print(outputFile)
    # outputFile = str(outputFile,'utf-8').rstrip()
    outputFile = str(outputFile).rstrip()
    subprocess.Popen("mv /tmp/" + outputFile + " " + outputDir + str(count) + "_channel_" + str(wifiChannel) + "_" + sniffStartTime + "_" + sniffStopTime + ".cap", shell=True)