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

with open('./raw/2017-05-23.bj.deal.json') as json_file:
    houseDealData = json.load(json_file)

exportResultJson = {}
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
    areaDateDealItems = areaValue.items()
    areaName = ''
    areaMonthData = {}
    echartsSeriesDataUnitPrice = []
    echartsSeriesDataHouseCount = []
    echartsSeriesDataAreaUnitPrice = []
    echartsSeriesDataAreaCount = []
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
        echartsSeriesDataHouseCount.append([monthKey, monthValue['houseCount']])
        echartsSeriesDataAreaCount.append([monthKey, monthValue['areaCount']])
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
with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + 'bj.json', 'wb') as json_file:
    json_file.write(json.dumps(exportResultJson, indent=4, sort_keys=False, ensure_ascii=False))
with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + 'bj.echarst.json', 'wb') as json_file:
    json_file.write(json.dumps(echartsJson, indent=4, sort_keys=False, ensure_ascii=False))
