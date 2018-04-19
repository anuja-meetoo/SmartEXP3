Evaluates the performance of Smart EXP3 and greedy through in-the-wild experiments, e.g. in a coffee shop. The number of devices and their selection approaches, and the bandwidth limit of available networks are unknown. The mobility of devices entering and leaving the service area are not controlled.

## Setup
A selection had to be made between 2 wireless networks, namely a public WiFi network and a cellular network. A laptop, equipped with a built-in WiFi interface and connected to the cellular network through a tethered phone, aims to download a [500MB file](http://www.speedtest.com.sg/), while connecting to the optimal network and optimizing on download time.

## Setting up the laptop
### Installing required libraries
```
pip3 install urllib3
apt-get install python3-pip
apt-get install python3-pycurl
```

## Running the experiment
Smart EXP3 and Greedy were run sequentially on a laptop.


The load of the 2 networks, monitored using Wireshark [10] and by capturing the EcIo values [7] from the mobile phone, varied during the experiments. 

## Brief description of files 
A brief description of the files is as follows:
* resumeDownload_periodic.py: Downloads a file from the internet, while selecting and connecting to the best network.
* getCellLoad.py: Type *#0011* on the tethered mobile phone's keypad to enter service menu where the cellular load is displayed on the screen. Then run this program to save the cellular load.
* wifiNetworkLoad: WiFi network load is obtained as follows: (1) sniff packets using Sniffer in MacBook (Wireless Diagnostics -> Window -> Sniffer; the channel and width information can be obtained from Wireless Diagnostics -> Window -> Scan), and (2) open the file in WireShark and filter out packets not for the WiFi AP being considered (wlan.addr=='mac of WiFi AP'), (3) from the resulting data, (a) extract the frame size and data rate from each packet, (b) compute the frame transfer duration, given its size and data rate, (c) estimate the load as the fraction of time the medium was busy, i.e. some packet was being transmitted. This program accomplishes (3).
* sniff.py: Sniff on two WiFi networks, periodically listening on one of each of them (was not used).
* extractDataForPlot.py: Gets the following for plotting: (1) bit rate, network selected and timestamp of start of each time slot and end of experiment, (2) computes the cellular load per time slot.
* wifiLoad_rollingAvg.py: Computes the rolling average of the WiFi load and saves it to a csv file.
