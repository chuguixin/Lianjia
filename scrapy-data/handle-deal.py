import datetime
import sys
import scrapy
import json
import re
import time
import math
import os

with open('./raw/2017-05-19.qd.deal.json') as json_file:
    houseDealData = json.load(json_file)

monthData = {}
for key,value in houseDealData['areaDealData']['huangdao'].items():
    month = key[0:7]
    if (not monthData.has_key(month)):
        monthData[month] = {
            'houseAreaCount': 0.0,
            'priceCount': 0.0,
            'houseCount': 0,
            'unitPriceCount': 0.0
        }
    for dealValue in value:
        monthData[month]['houseAreaCount'] = monthData[month]['houseAreaCount'] + dealValue['houseAreaCount'];
        monthData[month]['priceCount'] = monthData[month]['priceCount'] + dealValue['price'];
        monthData[month]['houseCount'] = monthData[month]['houseCount'] + 1;
        monthData[month]['unitPriceCount'] = monthData[month]['unitPriceCount'] + dealValue['unitPrice'];

resultData = {}
for key,value in monthData.items():
    if (int(key[0:4]) < 2015):
        continue
    resultData[key] = round(value['unitPriceCount']/(value['houseCount']*10000), 2)


resultDataItems = resultData.items()
resultDataItems.sort()
resultKey = []
resultValue = []
houseCountValue = []
for key,value in resultDataItems:
   resultKey.append(key)
   resultValue.append(value)


jsonData = {}
jsonData['resultKey'] = resultKey
jsonData['resultValue'] = resultValue
jsonData['resultData'] = resultData
# jsonData['monthData'] = monthData


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
    json_file.write(json.dumps(jsonData, indent=4, sort_keys=False, ensure_ascii=False))
