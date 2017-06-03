# -*- coding: utf-8 -*-
import sys
import scrapy
import json
import re
import time
import math
import os



class ErshoufangSpider(scrapy.Spider):
    name = "ershoufang"
    cityDomain = "qd"
    allowed_domains = [cityDomain + ".lianjia.com"]
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    headers = {
        'User-Agent': user_agent
    }
    cookie = {
        
    }
    start_url = 'https://' + cityDomain + '.lianjia.com/ershoufang/'
    allHouseData = {}
    houseDict = {}

    def start_requests(self):
        yield scrapy.Request(url=self.start_url, headers=self.headers, method='GET', callback=self.dataInit, cookies=self.cookie)
    def dataInit(self, response):
        areaList = response.css('.m-filter .position div[data-role=ershoufang] a')
        for area in areaList:
            try:
                areaHanzi = area.xpath('text()').extract()[0]
                areaPinyin = area.xpath('@href').extract()[0].split('/')[2]
                areaName = areaHanzi + areaPinyin
                self.allHouseData[areaName + "Dict"] = {}
                areaUrl = ('https://' + self.cityDomain + '.lianjia.com/ershoufang/{}/').format(areaPinyin)
                yield scrapy.Request(url=areaUrl, headers=self.headers, callback=self.areaRequest, meta={"areaHanzi":areaHanzi,"areaPinyin":areaPinyin} )
            except Exception:
                pass
    def detailParse(self, response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        areaName = areaHanzi + areaPinyin
        houseId = int(response.meta["houseId"])
        houseItemDict = {}
        houseItemDict["url"] = str(response.url)
        houseItemDict["title"] = str(response.css('.sellDetailHeader .title .main::text').extract()[0])
        houseItemDict["price"] = float(response.css('.overview .price .total::text').extract()[0])
        houseItemDict["unitPrice"] = int(response.css('.overview .price .text .unitPrice .unitPriceValue::text').extract()[0])
        houseItemDict["houseLayout"] = str(response.css('#introduction .introContent .content ul li')[0].css("::text").extract()[1])
        houseItemDict["houseYears"] = str(response.css('#introduction .introContent .content ul li')[12].css("::text").extract()[1])
        houseItemDict["startOnlineTime"] = str(response.css('#introduction .transaction .content ul li')[0].css("::text").extract()[1])
        houseItemDict["housePurpose"] = str(response.css('#introduction .transaction .content ul li')[0].css("::text").extract()[1])
        houseItemDict["record7Days"] = int(response.css('#record .panel .count::text').extract()[0])
        houseItemDict["recordTotalCount"] = int(response.css('#record .panel .totalCount span::text').extract()[0])
        
        self.houseDict[houseId] = houseItemDict
        self.allHouseData[areaName + "Dict"][houseId] = houseItemDict
    def areaParse(self,response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        areaName = areaHanzi + areaPinyin
        areaTotalCount = int(response.css('.leftContent .resultDes .total span::text').extract()[0])
        housePriceArray = response.css('.sellListContent li')
        for house in housePriceArray:
            houseUrl = house.css('.title a::attr(href)').extract()[0]
            reMatchObj = re.search( r'[\D]*(\d+).*', houseUrl, re.M|re.I)
            houseId = int(reMatchObj.group(1))
            yield scrapy.Request(url=houseUrl, 
                                headers=self.headers, 
                                callback=self.detailParse, 
                                meta={"areaHanzi":areaHanzi,"areaPinyin":areaPinyin, "houseId":houseId} )
            
    def areaRequest(self,response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        areaName = areaHanzi + areaPinyin
        areaTotalCount = int(response.css('.leftContent .resultDes .total span::text').extract()[0])
        pageCount = 0;
        if (areaTotalCount <= 0): 
            return
        else:
            pageCount = int(math.ceil(areaTotalCount/30) * 2)
        for i in range(1,pageCount):
            url = ('https://' + self.cityDomain + '.lianjia.com/ershoufang/{}/pg{}/').format(response.meta["areaPinyin"],str(i))
            yield scrapy.Request(url=url, headers=self.headers, callback=self.areaParse, meta={"areaHanzi":areaHanzi,"areaPinyin":areaPinyin} )
    def closed(self, reason):
        path = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(path):
            jsonFileWiriteDir = path
        elif os.path.isfile(path):
            jsonFileWiriteDir = os.path.dirname(path)
        jsonFileWiriteDir = jsonFileWiriteDir + '/../../../scrapy-data/raw/'
        if (not os.path.isdir(jsonFileWiriteDir)):
            os.mkdir(jsonFileWiriteDir)
        os.chdir(jsonFileWiriteDir)
        self.allHouseData['houseDict'] = self.houseDict
        with open(jsonFileWiriteDir + time.strftime("%Y-%m-%d", time.localtime()) + '.' + self.cityDomain + '.json', 'wb') as json_file:
            json_file.write(json.dumps(self.allHouseData, indent=4, sort_keys=False, ensure_ascii=False))
