## Setup
The setup consists of:
  * 3 WiFi routers (TP-Link TL-WR841N) running OpenWRT (Designated driver - Bleeding Edge, 50140) and operating on 2.4GHz with bandwidth limits set to 4, 7 and 22 Mbps and channels 11, 6 and 1.
  * 2 laptops, each running a TCP server that continuously sends data to its clients (a request is sent to an alternate server when one fails to respond). Although they download data over WiFi, the clients are also conected to the servers through cables to enable us to ssh to them and run the commands without interfering with the wireless networks.
  * 14 raspberry pis (versions 2 and 3; those of version 2 had a WiFi USB dongle as they do not have an in-built WiFi inetrface) that act as clients.
  * A main router (Linksys WRT54GL) running OpenWRT that connects the servers and 3 WiFi APs through LAN cables. 
Devices run Smart EXP3 or Greedy and receive data from the server. They are synchronized, with drift of less than one second. Switching networks is implemented by closing and establishing new network and TCP connections. Gain is estimated based on the download during the time spent in a network. 

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

## Setting up the servers 


## Setting up the clients

## Running the experiment
1. Start the servers by running the following command on them:
   ?
2. Start clients by executing the following command on them:
   ?

Note: The use of [Terminator](https://linux.die.net/man/1/terminator) or [iTerm2](https://www.iterm2.com/) helps to send the same command to multiple devices at the same time. You can split the terminal window into multiple panes, use each pane to ssh into a particular device (server/client), and send the same command to all of them simultaneously.


https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
