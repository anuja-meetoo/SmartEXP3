Delay observed when switching between networks are measured and Python's Fitter tool is applied to the values to identify the probability distribution that best fits the values.

A brief description of the files is as follows:
* measure3Gdelay.py: Measures delay incurred when switching from a WiFi network to 3G (via a tethered phone - by sending the correct adb shell command to enable/disable 3G on the phone).
* measureWiFiDelay.py: Measures delay values when switching between 2 WiFi networks.
* 3G_delay_combined.csv: 500 delay values measured when switching from WiFi to 3G.
* wifi_delay_combined.csv: 500 delay values measured when switching between 2 WiFi networks.
* model.py: Identifies the probability distibution that best fits the delay values measured (using Python's Fitter tool). 
