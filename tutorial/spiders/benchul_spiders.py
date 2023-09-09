from pathlib import Path

import scrapy
import json


class BenchulSpider(scrapy.Spider):
    name = "benchul"
    results = []
    old_results = []

    def start_requests(self):
        urls = [
            "https://benchmarks.ul.com/compare/best-smartphones?amount=0&sortBy=PERFORMANCE&reverseOrder=true&osFilter=ANDROID,IOS,WINDOWS&test=WILD_LIFE_EXTREME&deviceFilter=PHONE&displaySize=3.0,15.0",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        # page = response.url.split("/")[-2]
        # filename = f"quotes-{page}.html"
        # Path(filename).write_bytes(response.body)
        #response.css("tr > td:nth-child(2) > div > a").get()
        count = 0
        for next_page in response.css("#productTable > tbody > tr > .pr1 > .OneLinkNoTx::attr(href)").getall():
            # next_page_full_url = response.urljoin(next_page)
            count += 1
            self.log(f"Going to {next_page}")
            yield scrapy.Request(next_page, callback=self.next_parse)

        #response.css("tr > td:nth-child(2) > div > a").getall()


    def next_parse(self, response):
        phoneData = {}
        phoneName = response.css(".mainheader > h1 > .OneLinkNoTx::text").get()
        phoneData["name"] = phoneName
        for dataCont in response.css(".data-container").getall():
            sel = scrapy.Selector(text=dataCont)
            title = sel.css("h3::text").get()
            dts = [x.strip() for x in sel.css("dl > dt::text").getall() if len(x.strip()) > 0]
            dds = [x.strip() for x in sel.css("dl > dd ::text").getall() if len(x.strip()) > 0]
            phoneData[title] = dict(zip(dts, dds))
            # self.log(f"Going to {dic}")

        self.results.append(phoneData)


    def closed(self, reason):
        self.log(f"Tom: closed")

        json_res = json.dumps(self.results, indent=2)
        f = open("benchul.json", "w")
        f.write(json_res)
        f.close()



