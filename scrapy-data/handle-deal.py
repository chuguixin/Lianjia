# -- coding: utf-8 --
import datetime
import sys  
reload(sys)  
sys.setdefaultencoding('utf-8')  
import scrapy
import json
import re
import time
import math
import os

with open('./raw/2017-06-04.qd.deal.json') as json_file:
    houseDealData = json.load(json_file)
with open('./raw/2017-06-15.qd.deal.json') as json_file:
    houseDealData2 = json.load(json_file)

# x = 0;
# obj = {}
# for dateKey, dateValue in houseDealData['allDealData'].items():
#     for subValue in dateValue:
#         if (obj.has_key(subValue['url'])):
#             print subValue['url']
#         obj[subValue['url']] = 1
#         x = x + 1
# print x;

# exit()

houseExistDict = {}

areaNameList = []
echarsMonthDict = {}
echartsJson = {
    'unitPrice': [],
    'dealCount': [],
    'unitAreaPrice': [],
    'areaCount': []
}

areaDealDataItems = houseDealData['areaDealData'].items()
# 区域循环
for areaKey,areaValue in areaDealDataItems:
    areaName = ''
    areaMonthData = {}
    echartsSeriesDataUnitPrice = []
    echartsSeriesDataHouseCount = []
    echartsSeriesDataAreaUnitPrice = []
    echartsSeriesDataAreaCount = []

    thisMonthAreaDateDealItems = houseDealData2['areaDealData'][areaKey].items()

    for thisMonthDateKey, thisMonthDateValue in thisMonthAreaDateDealItems:
        areaValue[thisMonthDateKey] = thisMonthDateValue

    areaDateDealItems = areaValue.items()
    if (len(areaDateDealItems) < 1):
        continue
    # 单个区循环，每次为每天
    for dateKey, dateValue in areaDateDealItems:
        month = dateKey[0:7]
        # 以月为维度
        if (len(dateValue) < 1):
            continue
        if (not areaMonthData.has_key(month)):
            areaMonthData[month] = {
                'priceCount': 0.0,
                'houseCount': 0,
                'unitPriceCount': 0.0,
                'areaCount': 0.0
            }
            echarsMonthDict[month] = 1
        # 循环每天所有的成交，并记录到当天所在的月
        for dealItem in dateValue:
            reMatchObj = re.search( r'[\D]*(\d+).*', dealItem['url'], re.M|re.I)
            houseId = int(reMatchObj.group(1))
            if (not houseExistDict.has_key(houseId)):
                houseExistDict[houseId] = 1
            else:
                continue
            areaMonthData[month]['priceCount'] = areaMonthData[month]['priceCount'] + dealItem['price'];
            areaMonthData[month]['houseCount'] = areaMonthData[month]['houseCount'] + 1;
            areaMonthData[month]['unitPriceCount'] = areaMonthData[month]['unitPriceCount'] + dealItem['unitPrice'];
            areaMonthData[month]['areaCount'] = areaMonthData[month]['areaCount'] + dealItem['houseAreaCount'];
            if (areaName != dealItem['areaHanzi']):
                areaName = areaName + dealItem['areaHanzi']
                areaNameList.append(dealItem['areaHanzi'])

    areaMonthDataItems = areaMonthData.items()
    for monthKey, monthValue in areaMonthDataItems:
        calcUnitPrice = round(monthValue['unitPriceCount']/(monthValue['houseCount']*10000), 2)
        calcAreaUnitPrice = round(monthValue['priceCount']/monthValue['areaCount'], 2)
        monthValue['calcUnitPrice'] = calcUnitPrice
        monthValue['calcAreaUnitPrice'] = calcAreaUnitPrice
        # 为echarts data添加数据
        echartsSeriesDataUnitPrice.append([monthKey, calcUnitPrice])
        echartsSeriesDataHouseCount.append([monthKey, round(monthValue['houseCount'], 2)])
        echartsSeriesDataAreaCount.append([monthKey, round(monthValue['areaCount'], 2)])
        echartsSeriesDataAreaUnitPrice.append([monthKey, calcAreaUnitPrice])
    # 
    echartsJson['unitAreaPrice'].append({
        'name': areaName,
        'data': echartsSeriesDataAreaUnitPrice,
        'type': 'line',
        'smooth': True,
        'stack': areaKey
    })
    echartsJson['unitPrice'].append({
        'name': areaName,
        'data': echartsSeriesDataUnitPrice,
        'type': 'line',
        'smooth': True,
        'stack': areaKey
    })
    echartsJson['dealCount'].append({
        'name': areaName,
        'data': echartsSeriesDataHouseCount,
        'type': 'line',
        'smooth': True,
        'stack': areaKey
    })
    echartsJson['areaCount'].append({
        'name': areaName,
        'data': echartsSeriesDataAreaCount,
        'type': 'line',
        'smooth': True,
        'stack': areaKey
    })



monthItems = echarsMonthDict.items()
monthItems.sort()
echarsMonthList = []
for key,value in monthItems:
    echarsMonthList.append(key)


echartsJson['monthList'] = echarsMonthList
echartsJson['areaNameList'] = areaNameList



path = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(path):
    jsonFileWiriteDir = path
elif os.path.isfile(path):
    jsonFileWiriteDir = os.path.dirname(path)
jsonFileWiriteDir = jsonFileWiriteDir + '/dist/'
if (not os.path.isdir(jsonFileWiriteDir)):
    os.mkdir(jsonFileWiriteDir)
os.chdir(jsonFileWiriteDir)
with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + 'qd.echarst.json', 'wb') as json_file:
    json_file.write(json.dumps(echartsJson, indent=4, sort_keys=False, ensure_ascii=False))
