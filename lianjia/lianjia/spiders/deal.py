# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import scrapy
from lxml import etree
import json
import re
import time
import math
from ..items import LianjiaItem



class DealSpider(scrapy.Spider):
    name = "deal"
    cityDomain = "jn"
    allowed_domains = [cityDomain + ".lianjia.com"]
    user_agent = 'Mozil data-role="ershoufang"la/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    headers = {'User-Agent': user_agent}
    start_url = 'http://' + cityDomain + '.lianjia.com/chengjiao/'
    allHouseData = {}
    houseDict = {}

    def start_requests(self):
        yield scrapy.Request(url=self.start_url, headers=self.headers, method='GET', callback=self.dataInit)
    def dataInit(self, response):
        areaList = response.css('.m-filter .position div[data-role=ershoufang] a')
        for area in areaList:
            try:
                areaHanzi = area.xpath('text()').extract()[0]
                areaPinyin = area.xpath('@href').extract()[0].split('/')[2]
                areaName = areaHanzi + areaPinyin
                self.allHouseData[areaName + "Dict"] = {}
                areaUrl = ('http://' + self.cityDomain + '.lianjia.com/chengjiao/{}/').format(areaPinyin)
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
        houseItemDict["title"] = str(response.css('.house-title .wrapper::text').extract()[0])
        houseItemDict["price"] = float(response.css('.overview .price .dealTotalPrice i::text').extract()[0])
        houseItemDict["unitPrice"] = int(response.css('.overview .price b::text').extract()[0])
        houseItemDict["lastOnlinePrice"] = float(response.css('.overview .info .msg span')[0].css('label::text').extract()[0])
        houseItemDict["onlineTime"] = int(response.css('.overview .info .msg span')[1].css('label::text').extract()[0])
        houseItemDict["modifyPriceTime"] = int(response.css('.overview .info .msg span')[2].css('label::text').extract()[0])
        houseItemDict["visitTime"] = int(response.css('.overview .info .msg span')[3].css('label::text').extract()[0])
        houseItemDict["focusPeopleCount"] = int(response.css('.overview .info .msg span')[4].css('label::text').extract()[0])
        houseItemDict["houseLayout"] = str(response.css('#introduction .introContent .content ul li')[0].css("::text").extract()[1])
        houseItemDict["houseYears"] = str(response.css('#introduction .introContent .content ul li')[12].css("::text").extract()[1])
        houseItemDict["startOnlineTime"] = str(response.css('#introduction .transaction .content ul li')[0].css("::text").extract()[1])
        houseItemDict["housePurpose"] = str(response.css('#introduction .transaction .content ul li')[0].css("::text").extract()[1])
        self.houseDict[houseId] = houseItemDict
        self.allHouseData[areaName + "Dict"][houseId] = houseItemDict
    def areaParse(self,response):
        areaHanzi = response.meta["areaHanzi"]
        areaPinyin = response.meta["areaPinyin"]
        areaName = areaHanzi + areaPinyin
        housePriceArray = response.css('ul.listContent li')
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
            url = ('http://' + self.cityDomain + '.lianjia.com/chengjiao/{}/pg{}/').format(response.meta["areaPinyin"],str(i))
            yield scrapy.Request(url=url, headers=self.headers, callback=self.areaParse, meta={"areaHanzi":areaHanzi,"areaPinyin":areaPinyin} )
    def closed(self, reason):
        self.allHouseData['houseDict'] = self.houseDict
        with open(time.strftime("%Y-%m-%d", time.localtime()) + '.' + self.cityDomain + '.deal.json', 'wb') as json_file:
            json_file.write(json.dumps(self.allHouseData, indent=4, sort_keys=False, ensure_ascii=False))
