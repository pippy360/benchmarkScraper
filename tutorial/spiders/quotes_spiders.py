from pathlib import Path

import scrapy
import json


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    results = []

    def start_requests(self):
        urls = [
            "https://nanoreview.net/en/phone-list/all-oppo",
            "https://nanoreview.net/en/phone-list/all-oppo?page=2",
            "https://nanoreview.net/en/phone-list/all-xiaomi",
            "https://nanoreview.net/en/phone-list/all-google",
            "https://nanoreview.net/en/phone-list/all-samsung",
            "https://nanoreview.net/en/phone-list/all-samsung?page=2",
            "https://nanoreview.net/en/phone-list/all-samsung?page=3",
            "https://nanoreview.net/en/phone-list/endurance-rating?page=",
            "https://nanoreview.net/en/phone-list/endurance-rating?page=2",
            "https://nanoreview.net/en/phone-list/endurance-rating?page=3",
            "https://nanoreview.net/en/phone-list/endurance-rating?page=4",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # page = response.url.split("/")[-2]
        # filename = f"quotes-{page}.html"
        # Path(filename).write_bytes(response.body)
        #response.css("tr > td:nth-child(2) > div > a").get()
        for next_page in response.css("tr > td:nth-child(2) > div > a::attr(href)").getall():
            next_page_full_url = response.urljoin(next_page)
            self.log(f"Going to {next_page_full_url}")
            yield scrapy.Request(next_page_full_url, callback=self.next_parse)

        #response.css("tr > td:nth-child(2) > div > a").getall()

    def parse_benchmark(self, response):
        for x in response.css("article[id='the-app'] > .card").getall():
            sel = scrapy.Selector(text=x)

            for benchCheck in sel.css(".card-block > h3::text").getall():
                if benchCheck == "Benchmarks":
                    scoreBarsVals = {}
                    for scoreBarText in sel.css(".score-bar").getall():
                        scoreBar = scrapy.Selector(text=scoreBarText)
                        n = scoreBar.css(".score-bar-name::text").get().strip()
                        v = scoreBar.css(".score-bar-result-number::text").get().strip()
                        assert len(n) > 0 and len(v) > 0
                        scoreBarsVals[n] = v

                    tableRows = {}
                    for trHtml in sel.css(".specs-table > tbody > tr").getall():
                        trSelector = scrapy.Selector(text=trHtml)
                        trs = [x.strip() for x in trSelector.css("td::text").getall()]
                        tableRows[trs[0]] = trs[1:]

                    return scoreBarsVals, tableRows



    def next_parse(self, response):
        phoneName = response.css(".title-h1::text").get()

        l = response.css(".chip-top > ul > li > strong::text").getall()
        r = response.css(".chip-top > ul > li::text").getall()
        topData = dict((zip(l, r)))

        scoreBarsVals, tableRows = self.parse_benchmark(response)
        res = {
            "name" : phoneName,
            "topData": topData,
            "scoreBarsVals" : scoreBarsVals,
            "tableRows": tableRows
        }
        self.results.append(res)

    def closed(self, reason):
        self.log(f"Tom: closed")

        json_res = json.dumps(self.results, indent=2)
        f = open("phone_results.json", "w")
        f.write(json_res)
        f.close()



