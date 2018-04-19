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
* Set the following parameters in file resumeDownload_periodic.py program:
  * value of the parameter lteUUID to the UUID of the tethered phone, obtained using the command 'nmcli con list' (line 56).
  * If you want to download another file, set the value of the parameter 'url' accordingly (line 66).
* Start the experiment by running the resumeDownload_periodic.py program:
  ```
  ./resumeDownload_periodic.py -a <algorithm_name> -l <physical_location> -w <SSID_WiFi_network>
  ```
  For example, given that we want to evaluate Smart EXP3 by selecting the optimal network between the WiFi network with SSID 'coffee' and the cellular network and the experiment is being carried out at a coffee shop:
  ```
  ./resumeDownload_periodic.py -a "smartEXP3" -l "coffee_shop" -w "coffee"
  ```
  It saves details of the experiment run to a text file, e.g. .
  
  outputTxtFileName + "_" + algorithmName + "_" + timestamp + "_" + location + ".csv"
  
  
## Monitoring the load of the WiFi network during experiment
* Sniff packets using Sniffer in MacBook (Wireless Diagnostics -> Window -> Sniffer; the channel and width information can be obtained from Wireless Diagnostics -> Window -> Scan).
* Open the file in WireShark and filter out packets not for the WiFi AP being considered (wlan.addr=='mac of WiFi AP')
* Execute wifiNetworkLoad.py.
  ```
  ./wifiNetworkLoad.py -a <algorithm_index> -c <cap_file> -o <output_file_url>
  ```
  It performs the following operations on the data resulting from the above 2 steps:
   * Extract the frame size and data rate from each packet.
   * Compute the frame transfer duration, given its size and data rate.
   * Estimate the load as the fraction of time the medium was busy, i.e. some packet was being transmitted.
* wifiLoad_rollingAvg.py computes the rolling average of the WiFi load and saves it to a csv file.
* extractDataForPlot.py: Gets the following for plotting: (1) bit rate, network selected and timestamp of start of each time slot and end of experiment, (2) computes the cellular load per time slot.

* sniff.py: Sniff on two WiFi networks, periodically listening on one of each of them (was not used).

## Monitoring the load of the cellular network during experiment
* Type *#0011* on the tethered mobile phone's keypad to enter service menu where the cellular load is displayed on the screen.
* Run getCellLoad.py to continuously save the cellular load:
 ```
 ./getCellLoad.py
 ```
* Press Ctrl + C to stop the program.

The load of the 2 networks, monitored using Wireshark [10] and by capturing the EcIo values [7] from the mobile phone, varied during the experiments. 
