'''
@description: Identify the best distribution that fits the delay values measured, using Python's Fitter tool
'''

from fitter import Fitter
import csv
delayCSVfile = "/Users/anuja/wns/_____delayMeasurements/delay_combined_scaled.csv"

data = []
with open(delayCSVfile, newline='') as delayCSVfile:
    delayFileReader = csv.reader(delayCSVfile)
    count = 0

    for row in delayFileReader:
        delay = float(row[0])
        data.append(delay)
f = Fitter(data)
f.fit()
# may take some time since by default, all distributions are tried
# but you call manually provide a smaller set of distributions
f.summary()

# f.fitted_param['dweibull']
