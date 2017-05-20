import datetime
import sys
import scrapy
import json
import re
import time
import math
import os

def get_yestday(day):
    oneday = datetime.timedelta(days=1)
    return day - oneday

with open(str(get_yestday(datetime.datetime.now()))[0:10] + '.qd.json') as json_file:
    houseDataYestday = json.load(json_file)
# with open('2017-04-27.qd.json') as json_file:
#     houseDataYestday = json.load(json_file)

with open(time.strftime("%Y-%m-%d", time.localtime()) + '.qd.json') as json_file:
    houseDataToday = json.load(json_file)
# with open('2017-05-08.qd.json') as json_file:
#     houseDataToday = json.load(json_file)

declineCount = 0
riseCount = 0
declinePriceCount = 0
risePriceCount = 0
noExitCount = 0
for key,value in houseDataToday['houseDict'].items():
    if (key in houseDataYestday['houseDict']):
        todyPrice = float(value['price'])
        yestdayPrice = float(houseDataYestday['houseDict'][key]['price'])
        if todyPrice < yestdayPrice:
            declineCount += 1
            declinePriceCount += (yestdayPrice - todyPrice)
            print("Decline", todyPrice, yestdayPrice, value['record7Days'], value['url'].decode('utf-8'))
        elif todyPrice > yestdayPrice:
            riseCount += 1
            risePriceCount += (todyPrice - yestdayPrice)
            print("Rise", todyPrice, yestdayPrice, value['record7Days'], value['url'].decode('utf-8'))
    else:
        noExitCount += 1

houseData = {}
houseData['declineCount'] = declineCount
houseData['riseCount'] = riseCount
houseData['declinePriceCount'] = declinePriceCount
houseData['risePriceCount'] = risePriceCount
houseData['houseCount'] = len(houseDataToday['houseDict'])


path = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(path):
    jsonFileWiriteDir = path
elif os.path.isfile(path):
    jsonFileWiriteDir = os.path.dirname(path)

jsonFileWiriteDir = jsonFileWiriteDir + '/dist/'
if (not os.path.isdir(jsonFileWiriteDir)):
    os.mkdir(jsonFileWiriteDir)
os.chdir(jsonFileWiriteDir)
with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + 'qd.json', 'wb') as json_file:
    json_file.write(json.dumps(houseData, indent=4, sort_keys=False, ensure_ascii=False))
