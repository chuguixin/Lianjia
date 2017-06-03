# -*- coding: utf-8 -*-
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
import scrapy
import json
import re
import time
import math
import os
import datetime
import random



class DealListSpider(scrapy.Spider):
    def __init__(self, domain="qd", date=time.strftime("%Y.%m", time.localtime())):
        self.cityDomain = domain
        try:
            crawlDate = time.strptime(date, "%Y.%m")
        except Exception as e:
            raise e
        self.crawlYear,self.crawlMonth = crawlDate[0:2]
        self.name = "dealList"
        self.allowed_domains = [self.cityDomain + ".lianjia.com"]
        self.user_agent_list = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            ]

        self.headers = {'User-Agent': random.choice(self.user_agent_list)}
        self.start_url = 'https://' + self.cityDomain + '.lianjia.com/chengjiao/'
        self.cookies = {
        }

    name = "dealList"
    areaDealData = {}
    allDealData = {}

    crawlStatus = {}

    def start_requests(self):
        yield scrapy.Request(url=self.start_url, headers=self.headers, cookies=self.cookies, method='GET', callback=self.dataInit)
    def dataInit(self, response):
        areaList = response.css('.m-filter .position div[data-role=ershoufang] a')
        for area in areaList:
            try:
                areaHanzi = area.xpath('text()').extract()[0]
                areaPinyin = area.xpath('@href').extract()[0].split('/')[2]
                areaName = areaPinyin
                self.areaDealData[areaName] = {}
                areaUrl = ('https://' + self.cityDomain + '.lianjia.com/chengjiao/{}/').format(areaPinyin)
                yield scrapy.Request(
                    url=areaUrl, 
                    headers=self.headers, 
                    callback=self.areaRequest, 
                    meta={
                        "areaHanzi":areaHanzi,
                        "areaPinyin":areaPinyin
                    })
            except Exception:
                pass
    def subAreaParse(self,response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        subAreaPinyin = response.meta["subAreaPinyin"]
        subAreaHanzi = response.meta["subAreaHanzi"]
        areaName = areaPinyin
        housePriceArray = response.css('ul.listContent li')
        for house in housePriceArray:
            houseUrl = house.css('.title a::attr(href)').extract()[0]
            reMatchObj = re.search( r'[\D]*(\d+).*', houseUrl, re.M|re.I)
            houseId = int(reMatchObj.group(1))
            dealDataStr = house.css('.info .dealDate::text').extract()[0]
            try:
                dealDate = time.strptime(dealDataStr, "%Y.%m.%d")
            except Exception as e:
                continue
            dealYear,dealMonth,dealDay = dealDate[0:3]
            # 如果此房子的成交日期已经早于需要爬去的日期
            # 那么设置标志位标示当前二级区域已经可以停止爬取
            # 同时，不保存当前成交
            if (dealYear < self.crawlYear or (dealYear == self.crawlYear and dealMonth < self.crawlMonth)):
                self.crawlStatus[areaPinyin + subAreaPinyin] = 1
                continue

            houseItemDict = {}
            try:
                title = str(response.css('.info .title a::text').extract()[0])
                houseAreaCountStr = title.split()[-1]
                reMatchObj = re.search( r'^([\d|\.]+).*', houseAreaCountStr, re.M|re.I)
                houseAreaCount = float(reMatchObj.group(1))
                houseItemDict["houseAreaCount"] = houseAreaCount
            except Exception as e:
                continue
            houseItemDict["url"] = houseUrl
            houseItemDict["price"] = float(response.css('.info .address .totalPrice span::text').extract()[0])
            houseItemDict["unitPrice"] = int(response.css('.info .flood .unitPrice .number::text').extract()[0]) 
            houseItemDict["areaHanzi"] = areaHanzi
            houseItemDict["subAreaHanzi"] = subAreaHanzi
            if not self.allDealData.has_key(dealDataStr):
                self.allDealData[dealDataStr] = []
            self.allDealData[dealDataStr].append(houseItemDict)
            if not self.areaDealData[areaName].has_key(dealDataStr):
                self.areaDealData[areaName][dealDataStr] = []
            self.areaDealData[areaName][dealDataStr].append(houseItemDict)
    
    def subAreaRequest(self,response):
        areaPinyin = response.meta["areaPinyin"]
        areaHanzi = response.meta["areaHanzi"]
        subAreaPinyin = response.meta["subAreaPinyin"]
        subAreaHanzi = response.meta["subAreaHanzi"]
        areaTotalCount = int(response.css('.leftContent .resultDes .total span::text').extract()[0])
        pageCount = 0;
        if (areaTotalCount <= 0): 
            return
        else:
            pageCount = int(math.ceil(areaTotalCount/30) * 1.1) + 1
        if (pageCount > 101):
            pageCount = 101
        for i in range(1,pageCount):
            time.sleep(1)
            url = ('https://' + self.cityDomain + '.lianjia.com/chengjiao/{}/pg{}/').format(subAreaPinyin,str(i))
            # 如果有标志位标示当前二级区域已经不需要爬取了
            # 那么停止请求
            if (self.crawlStatus[areaPinyin + subAreaPinyin] == 1):
                return
            yield scrapy.Request(
                url=url, 
                headers=self.headers, 
                callback=self.subAreaParse, 
                meta={
                    "areaHanzi":areaHanzi,
                    "areaPinyin":areaPinyin,
                    "subAreaHanzi":subAreaHanzi,
                    "subAreaPinyin":subAreaPinyin
                })

    def areaRequest(self,response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        areaName = areaPinyin
        subAreaList = response.css('.m-filter .position div[data-role=ershoufang] div')[1].css('a')
        for subArea in subAreaList:
            try:
                subAreaHanzi = subArea.xpath('text()').extract()[0]
                subAreaPinyin = subArea.xpath('@href').extract()[0].split('/')[2]
                self.areaDealData[areaName] = {}
                self.crawlStatus[areaPinyin + subAreaPinyin] = 0
                subAreaUrl = ('https://' + self.cityDomain + '.lianjia.com/chengjiao/{}/').format(subAreaPinyin)
                yield scrapy.Request(
                    url=subAreaUrl, 
                    headers=self.headers, 
                    callback=self.subAreaRequest, 
                    meta={
                        "areaHanzi":areaHanzi,
                        "areaPinyin":areaPinyin,
                        "subAreaHanzi":subAreaHanzi,
                        "subAreaPinyin":subAreaPinyin
                    })
            except Exception:
                pass
    def closed(self, reason):
        allData = {}
        allData['areaDealData'] = self.areaDealData
        allData['allDealData'] = self.allDealData
        path = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(path):
            jsonFileWiriteDir = path
        elif os.path.isfile(path):
            jsonFileWiriteDir = os.path.dirname(path)
        jsonFileWiriteDir = jsonFileWiriteDir + '/../../../scrapy-data/raw/'
        if (not os.path.isdir(jsonFileWiriteDir)):
            os.mkdir(jsonFileWiriteDir)
        os.chdir(jsonFileWiriteDir)
        with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + self.cityDomain + '.deal.json', 'wb') as json_file:
            json_file.write(json.dumps(allData, indent=4, sort_keys=False, ensure_ascii=False))
