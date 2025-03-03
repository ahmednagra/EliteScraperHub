import json
from collections import OrderedDict

from scrapy import Spider, Request, signals


class AppslandSpider(Spider):
    name = 'appsland'
    base_url = 'https://apps.land.gov.il/'
    quotes_url = 'https://quotes.toscrape.com/'
    start_urls = [quotes_url]

    custom_settings = {
        # 'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEED_URI': f'output/AppsLandTenderPremises.xlsx',
        'FEED_FORMAT': 'xlsx'
    }

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://apps.land.gov.il/MichrazimSite/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    def __init__(self, urls=None, **kwargs):
        super().__init__(**kwargs)
        self.urls = urls

    def parse(self, response, **kwargs):
        # search_url = self.urls.pop(0)
        search_url = self.urls
        # search_url = 'https://apps.land.gov.il/MichrazimSite/#/michraz/20230078'
        url_id = search_url.split('/')[-1]

        yield Request(url=f'https://apps.land.gov.il/MichrazimSite/api/MichrazDetailsApi/Get?michrazID={url_id}',
                      callback=self.parse_detail,
                      headers=self.headers,
                      meta={'search_url': search_url})

    def parse_detail(self, response):
        try:
            table_data = json.loads(response.text).get('Tik', [{}])
        except json.JSONDecodeError:
            return

        for row in table_data:
            item = OrderedDict()
            try:
                sub_table_1 = row.get('TochnitMigrash', [{}])[0]
                sub_table_2 = row.get('GushHelka', [{}])[0]
            except IndexError:
                sub_table_1 = {}
                sub_table_2 = {}
            except AttributeError:

                sub_table_1 = {}
                sub_table_2 = {}

            bid_numbers = [str(value.get('HatzaaSum', '')) for value in row.get('mpHatzaaotMitcham', [])] or []

            item['מספר מתחם'] = row.get('MitchamName', '')
            item['יח"ד'] = row.get('Kibolet', '')
            item['שם זוכה'] = row.get('ShemZoche', '')
            item['מחיר סופי ב₪'] = row.get('SchumZchiya', '')
            item['הוצאות פיתוח ב₪'] = row.get('HotzaotPituach', '')
            item['שטח במ"ר'] = row.get('Shetach', '')
            item['מחיר מינימום ב₪'] = row.get('MechirSaf', '')
            item['מחיר שומה ב₪'] = row.get('mechirShuma', '')
            item['תוכנית'] = sub_table_1.get('Tochnit', '')
            item['מגרש'] = sub_table_1.get('MigrashName', '')
            item['גוש'] = sub_table_2.get('Gush', '')
            item['חלקה'] = sub_table_2.get('Helka', '')
            item['סכום הצעה ב₪'] = ', '.join(bid_numbers)
            item[' Counts סכום הצעה ב₪'] = len(bid_numbers)
            item['Search URL'] = response.meta.get('search_url', '')

            yield item

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AppslandSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if not self.urls:
            return
