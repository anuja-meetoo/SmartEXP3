Smart EXP3 is evaluated in a 'controlled setting' where we set the bandwidth limit of each AP and we have control over the number of active wireless devices in the environment.

## Setup
The setup consists of:
  * A main router (Linksys WRT54GL) running OpenWRT (connected to the Internet to download files/packages for setup).
  * 3 WiFi routers (TP-Link TL-WR841N) running OpenWRT (Designated driver - Bleeding Edge, 50140) and operating on 2.4GHz with bandwidth limits set to 4, 7 and 22 Mbps and channels 11, 6 and 1; they are connected to the main router through LAN cables.
  * 2 laptops (primary and secondary), each running a TCP server that continuously sends data to its clients (a request is sent to an alternate server when one fails to respond); they are connected to the main router through cables (using an Ethernet hub as there are not enough ports on the router).
  * 14 raspberry pis (rpis), versions 2 and 3, that act as clients; rpis 2 were equipped with a LB-Link WiFi USB dongle as they do not have an in-built WiFi interface. Although they download data over WiFi, the clients are also conected to the servers through cables to enable us to ssh to them and run the commands without interfering with the wireless networks.  
  
Devices run Smart EXP3 or Greedy and receive data from the server. They are synchronized, with drift of less than one second. Switching networks is implemented by closing and establishing new network and TCP connections. Gain is estimated based on the download during the time spent in a network. 

We ssh to the devices from one of the laptop running the secondary server. Results from the clients are also sent to this laptop at the end of the experiment.


## Setting up the WiFi APs
The APs are setup as follows.
### Allow ssh from wan <br> 
  First of all, enable ssh on the router, by adding the following lines in /etc/config/firewall:
  ```
  config rule                     
    option src              wan   
    option dest_port        22    
    option target           ACCEPT
    option proto            tcp   
  ``` 
  After 'reboot', it will accept port 22 request (in this case ,ssh request) from WAN. <br>
  
### Change the LAN IP  
  Edit the file /etc/config/network to set the LAN IP. We set the LAN IPs of the 3 routers to 10.0.0.1, 20.0.0.1 and 30.0.0.1.
  
### Enable WiFi and set the channel, SSID and password for the network 
  Edit the file /etc/config/wireless with the right SSID (option ssid \<ssid>), password (option key \<password>) and WiFi channel (option channel \<wifi_channel>), and enable WiFi. We set the SSIDs of the the 3 routers to 'pink', 'green' and 'orange', and their channels to 11, 6 and 1, respectively. An example of the /etc/config/wireless file is as follows:
  ```
  config wifi-device      radio0
        option type       mac80211
        option channel    <wifi_channel>
        option hwmode     11bgn
        option path       'platform/qca953x_wmac'
        option htmode     HT20
        # COMMENT THE FOLLOWING LINE TO ENABLE WIFI
        #option disabled  1

  config wifi-iface
        option device     radio0
        option network    lan
        option mode       ap
        option ssid       <ssid>
        option encryption psk
        option key        <password>
```

### Set bandwidth limit
Install the following [packages](https://wiki.openwrt.org/doc/howto/packet.scheduler/packet.scheduler) and insert the specified module in kernel. 
```
opkg update
opkg install tc iptables-mod-ipopt
opkg install kmod-sched
insmod sch_tbf
```
Notes: 
 * You might need to update the nameserver in the file /etc/resolv.conf for Internet connection.
 * If you encounter [problems installing the packages due to insufficient memory](https://stackoverflow.com/questions/34112053/openwrt-cant-install-packages-memory-issue), comment out everything but base and luci (first two) in file /etc/opkg/distfeeds.conf.

Run the following command to set the bandwidth limit (must be run everytime you power up the AP or you might set the command in the appropriate file for execution at startup):
```
tc qdisc add dev br-lan root tbf rate <bandwidth>mbit burst 30kb latency 50ms
```
We set the bandwidth limit of the networks 'pink', 'green', and 'orange' to 4, 7 and 22 Mbps, respectively. For example, the following command sets the bandwidth limit of 4 Mbps:
```
tc qdisc add dev br-lan root tbf rate 4mbit burst 30kb latency 50ms
```
To disable the rate limit, you run the following command:
```
tc qdisc del dev br-lan root
```

## Setting up the raspberry pis
### Set the hostname
Edit sudo nano /etc/hostname and set the name of each client as rpi_\<client_ID>.

### Add WiFi connections
Add new WiFi connections for each of the 3 WiFi networks using the following command:
```
sudo nmcli device wifi connect <SSID> password <password>
```

The following commands might be useful:
```
sudo nmcli con up <SSID>              % to connect to the network with SSID <SSID>
sudo nmcli con down <SSID>            % to disconnect from the network with SSID <SSID>
sudo con remove <uuid-of-connection>  % to remove the specified connection; to lookup the uuid, type 'sudo con show'
```

### Turn power management off
Add the following to the file /etc/rc.local:
```
sudo ifup <wlan_interface>
sudo iw dev <wlan_interface> set power_save off 
```

### Disable bluetooth
Run the following to check if bluetooth is on: 
```
hciconfig 
```
If it is on, turn it off using the following command: 
```
hciconfig hci0 down 
```

### Allow ssh without login to the server
At the end of the experiment, results (stored in a file) are sent to a remote machine (the laptop running the secondary) for processing. To enable the clients to send the file without the need to login to the server, follow the [steps](https://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id) below:
```
ssh-keygen
```
Copy the public key to remote-host using ssh-copy-id
```
anuja@anuja$ ssh-copy-id -i ~/.ssh/id_rsa.pub remote-host
```
Now, you should be able to logging into the remote machine from the rpi, with "ssh 'remote-host'", without the need to provide any password.

### Synchronize time using network time protocol (ntp)
Execute the following commands:
```
sudo /etc/init.d/ntp stop
sudo ntpd -q -g
sudo /etc/init.d/ntp start
```

## Running the experiment
The use of [Terminator](https://linux.die.net/man/1/terminator) or [iTerm2](https://www.iterm2.com/) helps to send the same command to multiple devices at the same time. You can split the terminal window into multiple panes, use each pane to ssh into a particular device (server/client), and send the same command to all of them simultaneously.

* On the servers:
  * Copy the file server_multiprocessing.py to each of the servers.
  * Start ther TCP servers by executing the command: 
```
./server_multiprocessing.py
```

* On the clients:
  * Copy the files client_multiprocessing.py and client_multiprocessing_dynamic.py to the clients.
  * Ensure that power management is turned off, Bluetooth is turned off and their time is synchronized (type command *date*).
  * Set the following in the files client_multiprocessing.py and client_multiprocessing_dynamic.py:
    * IP addresses of the TCP servers (lines 23 - 24).
    * username to access the remote machine and location in the remote machine where the experiment data will be saved (line 831/850 depending on which of the above 2 files is being used).
 * Disconnect from all wireless neworks.
 * Execute the client program.
   For the static setting, execute the program client_multiprocessing.py as follows:
   ```
   python3 client_multiprocessing.py -a <algorithm_name> -m <max_iteration> -b "<network_bandwidth>" -r <run_index> -t <start_time>
   ```
   For example:
   ```
   python3 client_multiprocessing.py -a smartEXP3 -m 480 -b "4_7_22" -r 1 -t 1499804700
   ```
   
   For a dynamic setting, execute the program client_multiprocessing_dynamic.py as follows:
   ```
   python3 client_multiprocessing_dynamic.py -a smartEXP3 -m 480 -b "4_7_22" -r 1 -t 1499804700 -s <start_iteration> -e <end_iteration>
   ```
   
   Per time slot data will be saved in the file \<hostname>_\<algorithmName>_run\<run_index>.csv (e.g. rpi_1_SmartEXP3_run1.csv) and sent to the remote machine (running the secondary server) at the end of the experiment).
