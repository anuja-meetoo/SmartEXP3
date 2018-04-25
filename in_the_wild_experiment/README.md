Evaluates the performance of Smart EXP3 and greedy through in-the-wild experiments, e.g. in a coffee shop. The number of devices and their selection approaches, and the bandwidth limit of available networks are unknown. The mobility of devices entering and leaving the service area are not controlled.

## Hardware required
A selection had to be made between 2 wireless networks, namely a public WiFi network and a cellular network. The following are required for the experiment:
* A laptop (equipped with a WiFi interface).
* A mobile phone (Android phone) to provide connection to the cellular network through USB tethering.

The aim is to download a [500MB file](http://www.speedtest.com.sg/), while connecting to the optimal network and optimizing on download time.

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
* Set the value of the following parameters in file resumeDownload_periodic.py program:
  * lteUUID to the UUID of the tethered phone, obtained using the command 'nmcli con list' (line 56).
  * If you want to download another file, set the value of the parameter 'url' accordingly (line 66).
* Create a connection for the public WiFi.
* Disconnect from all wireless networks.
* Start the experiment by running the resumeDownload_periodic.py program:
  ```
  ./resumeDownload_periodic.py -a <algorithm_name> -l <physical_location> -w <SSID_WiFi_network>
  ```
  For example, given that we want to evaluate Smart EXP3 by selecting the optimal network between the WiFi network with SSID 'coffee' and the cellular network and the experiment is being carried out at a coffee shop:
  ```
  ./resumeDownload_periodic.py -a "smartEXP3" -l "coffee_shop" -w "coffee"
  ```
It saves per time slot details of the run in a csv file 'experiment_data_<algorithmName>_<timestamp>_<physical_location>.csv' and some other details in a text file 'experiment_data.txt'.
 
## Monitoring the load of the WiFi network during experiment
* Sniff packets using Sniffer in MacBook (Wireless Diagnostics -> Window -> Sniffer; the channel and width information can be obtained from Wireless Diagnostics -> Window -> Scan).
* Open the file in [WireShark](http://www.wireshark.org/) and filter out packets not for the WiFi AP being considered (wlan.addr=='mac of WiFi AP').
* Save the resulting data as a .cap file.
* Execute wifiNetworkLoad.py to perform the following operations on the data resulting from the above 2 steps:
  * Extract the frame size and data rate from each packet.
  * Compute the frame transfer duration, given its size and data rate.
  * Estimate the load as the fraction of time the medium was busy, i.e. some packet was being transmitted.
  ```
  ./wifiNetworkLoad.py - a <algorithm_index> -c <cap_file> -x experiment_file> -o <output_file_url>
  ```
  Use algorithm index 1 for 'SmartEXP3' and 2 for 'greedy'.  
* wifiLoad_rollingAvg.py can be executed to compute the rolling average of the WiFi load and save the result to a csv file.
* extractDataForPlot.py extracts required details for plotting:
  * Gets the bit rate, network selected and timestamp of start of each time slot and end of experiment.
  * Computes the cellular load per time slot.

## Monitoring the load of the cellular network during experiment
* Type *#0011* on the tethered mobile phone's keypad to enter service menu where the cellular load, [EcIo values](https://dl.acm.org/citation.cfm?id=2500447), is displayed on the screen. 
* Execute getCellLoad.py to save the cellular load.
  ```
  ./getCellLoad.py -a <algorithm_name> -n <cellular_network_type>
  ```
  For example,
  ```
  ./getCellLoad.py -a "smartEXP3" -n "3G"
  ```

## Experiment data
Data from 12 runs of the experiment using Smart EXP3 and Greedy is provided in the directory '*experiment_data*'.
