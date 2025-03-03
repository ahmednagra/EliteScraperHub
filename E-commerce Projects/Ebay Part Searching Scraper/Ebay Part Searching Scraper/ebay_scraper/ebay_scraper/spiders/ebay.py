from datetime import datetime

from scrapy import Request, Spider

from ..items import EbayScraperItem


class EbaSpider(Spider):
    name = "ebay"
    allowed_domains = ["www.ebay.com"]
    start_urls = ["https://www.ebay.com"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.2,
        'AUTOTHROTTLE_MAX_DELAY': 3,

        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],

        'FEED_FORMAT': 'csv',
        'FEED_URI': f'output/Results {datetime.now().strftime("%d%m%Y%H%M%S")}.csv',
        'FEED_EXPORT_FIELDS': ['part_number', 'results_count']

    }

    def parse(self, response, **kwargs):
        part_numbers = self.get_part_numbers_from_file()

        for part_number in part_numbers:
            url = f'https://www.ebay.com/sch/i.html?_from=R40&_nkw={part_number}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1'
            yield Request(url=url, callback=self.search_part_number,
                          meta={'part_number': part_number, 'handle_httpstatus_all': True})

    def search_part_number(self, response):
        items = EbayScraperItem()
        items['part_number'] = response.meta['part_number']
        items['results_count'] = response.css('.srp-controls__count-heading .BOLD ::text').get()

        yield items

    def get_part_numbers_from_file(self):
        with open('input/parts_numbers.txt', 'r') as txt_file:
            return [line.strip() for line in txt_file.readlines() if line.strip()]
