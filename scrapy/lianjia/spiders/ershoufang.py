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
        '_qzja': '1.564479870.1485603777024.1489043542457.1489110874264.1489110874264.1489110901124.0.0.0.55.6',
        'lianjia_uuid':'fc3783b5-406c-4ced-b7d1-22c292f633ff',
        'UM_distinctid':'15b80567dc5325-0b46924d39fb61-1d3c6853-1fa400-15b80567dc638e',
        'gr_user_id':'e367ef2d-6e64-4c37-94f4-e57d3c06bbfd',
        'Hm_lvt_efa595b768cc9dc7d7f9823368e795f1':'1493166026',
        'all-lj':'fa25c352c963a53c37faa70f46a58187',
        'sample_traffic_test':'test_66',
        'select_city':'370200',
        '_smt_uid':'58f5d8b3.57f62786',
        'CNZZDATA1253492431':'1125092302-1492504573-%7C1495201614',
        'CNZZDATA1254525948':'1475292229-1492504669-%7C1495204660',
        'CNZZDATA1255633284':'433543889-1492506529-%7C1495204514',
        'CNZZDATA1255604082':'513345297-1492506773-%7C1495205371',
        '_gat':'1',
        '_gat_past':'1',
        '_gat_global':'1',
        '_gat_new_global':'1',
        '_ga':'GA1.2.377603813.1492506809',
        '_gid':'GA1.2.1610112096.1495206972',
        '_gat_dianpu_agent':'1',
        'lianjia_ssid':'fded5a8e-a7f2-4c02-a9b7-631172522d'
    }
    start_url = 'http://' + cityDomain + '.lianjia.com/ershoufang/'
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
                areaUrl = ('http://' + self.cityDomain + '.lianjia.com/ershoufang/{}/').format(areaPinyin)
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
            url = ('http://' + self.cityDomain + '.lianjia.com/ershoufang/{}/pg{}/').format(response.meta["areaPinyin"],str(i))
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
