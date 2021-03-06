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



class DealSpider(scrapy.Spider):
    name = "deal"
    cityDomain = "sz"
    allowed_domains = [cityDomain + ".lianjia.com"]
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    headers = {'User-Agent': user_agent}
    start_url = 'https://' + cityDomain + '.lianjia.com/chengjiao/'
    cookies = {
    }
    areaDealData = {}
    allDealData = {}

    def start_requests(self):
        yield scrapy.Request(url=self.start_url, headers=self.headers, cookies=self.cookies, method='GET', callback=self.dataInit)
    def dataInit(self, response):
        areaList = response.css('.m-filter .position div[data-role=ershoufang] a')
        for area in areaList:
            try:
                # time.sleep(3)
                areaHanzi = area.xpath('text()').extract()[0]
                areaPinyin = area.xpath('@href').extract()[0].split('/')[2]
                areaName = areaPinyin
                self.areaDealData[areaName] = {}
                areaUrl = ('https://' + self.cityDomain + '.lianjia.com/chengjiao/{}/').format(areaPinyin)
                yield scrapy.Request(url=areaUrl, headers=self.headers, callback=self.areaRequest, meta={"areaHanzi":areaHanzi,"areaPinyin":areaPinyin} )
            except Exception:
                pass
    def detailParse(self, response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        subAreaPinyin = response.meta["subAreaPinyin"]
        subAreaHanzi = response.meta["subAreaHanzi"]
        areaName = areaPinyin
        houseId = int(response.meta["houseId"])
        dealDataStr = response.css('.house-title .wrapper span::text').extract()[0][0:10]
        dealDate = time.strptime(dealDataStr, "%Y.%m.%d")
        dealDatetime = datetime.datetime.strptime(dealDataStr, "%Y.%m.%d")
        dealYear,dealMonth,dealDay = dealDate[0:3]
        dealWeekDay, = dealDate[6:7]
        if dealWeekDay > 0:
            dealDataStr = (dealDatetime - (datetime.timedelta(days=dealWeekDay))).strftime("%Y.%m.%d")
        if not self.allDealData.has_key(dealDataStr):
            self.allDealData[dealDataStr] = []
        houseItemDict = {}
        #房子url
        houseItemDict["url"] = str(response.url)
        #房子名称
        houseItemDict["title"] = str(response.css('.house-title .wrapper::text').extract()[0])
        #成交价格
        houseItemDict["price"] = float(response.css('.overview .price .dealTotalPrice i::text').extract()[0])
        #成交单价
        houseItemDict["unitPrice"] = int(response.css('.overview .price b::text').extract()[0]) 
        #最后挂牌价
        try:
            houseItemDict["lastOnlinePrice"] = float(response.css('.overview .info .msg span')[0].css('label::text').extract()[0])
        except Exception:
            houseItemDict["lastOnlinePrice"] = 0
        #成交周期
        try:
            houseItemDict["dealUsedDays"] = int(response.css('.overview .info .msg span')[1].css('label::text').extract()[0])
        except Exception:
            houseItemDict["dealUsedDays"] = 0
        #成交带看次数
        houseItemDict["dealUsedVisitTimes"] = int(response.css('.overview .info .msg span')[3].css('label::text').extract()[0])
        #建筑面积
        houseAreaCountStr = str(response.css('#introduction .introContent .base .content ul li')[2].css("::text").extract()[1])
        reMatchObj = re.search( r'^([\d|\.]+).*', houseAreaCountStr, re.M|re.I)
        houseAreaCount = float(reMatchObj.group(1))
        houseItemDict["houseAreaCount"] = houseAreaCount

        self.allDealData[dealDataStr].append(houseItemDict)
        if not self.areaDealData[areaName].has_key(dealDataStr):
            self.areaDealData[areaName][dealDataStr] = []
        self.areaDealData[areaName][dealDataStr].append(houseItemDict)
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
            dealDate = time.strptime(dealDataStr, "%Y.%m.%d")
            dealYear,dealMonth,dealDay = dealDate[0:3]
            houseItemDict = {}
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
            url = ('https://' + self.cityDomain + '.lianjia.com/chengjiao/{}/pg{}/').format(subAreaPinyin,str(i))
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
