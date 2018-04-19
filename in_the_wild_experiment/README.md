Evaluates the performance of Smart EXP3 and greedy through in-the-wild experiments, e.g. in a coffee shop. The number of devices and their selection approaches, and the bandwidth limit of available networks are unknown. The mobility of devices entering and leaving the service area are not controlled.

## Setup
A selection had to be made between 2 wireless networks, namely a public WiFi network and a cellular network. A laptop, equipped with a built-in WiFi interface and connected to the cellular network through a tethered phone, aims to download a [500MB file](http://www.speedtest.com.sg/), while connecting to the optimal network and optimizing on download time.

## Setting up the laptop
### Installing required libraries
```
apt-get install python3-pip
pip3 install urllib3
apt-get install python3-pycurl
```

### Setting up cellular connection
Share the cellular data connection of a mobile phone with the laptop by following these steps:
1. Connect a mobile phone (Android phone) with data connection to the laptop using a USB cable.
2. Go to Settings; choose Connections, Mobile Hotspot and tethering, and USB tethering.

## Running the experiment
* Set the value of the parameter lteUUID to the UUID of the tethered phone, obtained using the command 'nmcli con list'.
* If you want to download another file, set the value of the parameter 'url' accordingly.
* Start the experiment by running the resumeDownload_periodic.py program:
```
./resumeDownload_periodic.py -a <algorithm_name> -l <physical_location> -w <SSID_WiFi_network>
```
For example, given that we want to evaluate Smart EXP3 by selecting the optimal network between the WiFi network with SSID 'coffee' and the cellular network and the experiment is being carried out at a coffee shop:
```
./resumeDownload_periodic.py -a "smartEXP3" -l "coffee_shop" -w "coffee"
```

## Monitoring the load of the WiFi network during experiment

## Monitoring the load of the cellular network during experiment

The load of the 2 networks, monitored using Wireshark [10] and by capturing the EcIo values [7] from the mobile phone, varied during the experiments. 

## Brief description of files 
A brief description of the files is as follows:
* resumeDownload_periodic.py: Downloads a file from the internet, while selecting and connecting to the best network.
* getCellLoad.py: Type *#0011* on the tethered mobile phone's keypad to enter service menu where the cellular load is displayed on the screen. Then run this program to save the cellular load.
* wifiNetworkLoad: WiFi network load is obtained as follows: (1) sniff packets using Sniffer in MacBook (Wireless Diagnostics -> Window -> Sniffer; the channel and width information can be obtained from Wireless Diagnostics -> Window -> Scan), and (2) open the file in WireShark and filter out packets not for the WiFi AP being considered (wlan.addr=='mac of WiFi AP'), (3) from the resulting data, (a) extract the frame size and data rate from each packet, (b) compute the frame transfer duration, given its size and data rate, (c) estimate the load as the fraction of time the medium was busy, i.e. some packet was being transmitted. This program accomplishes (3).
* sniff.py: Sniff on two WiFi networks, periodically listening on one of each of them (was not used).
* extractDataForPlot.py: Gets the following for plotting: (1) bit rate, network selected and timestamp of start of each time slot and end of experiment, (2) computes the cellular load per time slot.
* wifiLoad_rollingAvg.py: Computes the rolling average of the WiFi load and saves it to a csv file.
