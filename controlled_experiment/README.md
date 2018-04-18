# Setup

3 WiFi routers (ref?) running OpenWRT (version?) and ? raspberry pis (versions 2 and 3).


# Setting up the WiFi APs
The routers did not have a web interface (GUI) due to lack of space on the device. Hence, the following commands were used to set up the AP.
### Allow ssh from wan <br> 
  Add the following lines in /etc/config/firewall:
  ```
  config rule                     
    option src              wan   
    option dest_port        22    
    option target           ACCEPT
    option proto            tcp   
  ```
  After 'reboot', it will accept port 22 request (in this case ,ssh request) from wan. <br>
  
  * Change its IP on lan
  
  Edit the file /etc/config/network
  
  * Set the SSID and password
  
  Edit the file /etc/config/wireless with the right SSID (option ssid <ssid>) and password (option key <password>) and enable   WiFi An example of the file is as follows:
  
  config wifi-device  radio0
        option type     mac80211
        option channel  1
        option hwmode   11bgn
        option path     'platform/qca953x_wmac'
        option htmode   HT20
        # REMOVE THIS LINE TO ENABLE WIFI:
        #option disabled 1

config wifi-iface
        option device   radio0
        option network  lan
        option mode     ap
        option ssid     pink
        option encryption psk
        option key flower123

To be able to run opkg update, update the /etc/resolv.conf file with the ip of the main router
nameserver ***.***.***.***

Set bandwidth limit
opkg update
opkg install tc iptables-mod-ipopt
opkg install kmod-sched
insmod sch_tbf

If problem installing due to insufficient memory:
Go into /etc/opkg/distfeeds.conf and comment out everything but base and luci, the first two. (Source:https://stackoverflow.com/questions/34112053/openwrt-cant-install-packages-memory-issue)

tc qdisc add dev br-lan root tbf rate 16mbit burst 30kb latency 50ms

To disable the rate limit later, you can do the following.
tc qdisc del dev br-lan root



commands

# Setting up the servers 


# Setting up the clients

# Running the experiment
1. Start the servers by running the following command on them:
   ?
2. Start clients by executing the following command on them:
   ?

Note: The use of [Terminator](https://linux.die.net/man/1/terminator) or [iTerm2](https://www.iterm2.com/) helps to send the same command to multiple devices at the same time. You can split the terminal window into multiple panes, use each pane to ssh into a particular device (server/client), and send the same command to all of them simultaneously.


https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
