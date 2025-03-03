from datetime import datetime
from collections import OrderedDict
from typing import Iterable

import scrapy
from scrapy import Request


class PopulationSpider(scrapy.Spider):
    name = "population"
    allowed_domains = ["www.citypopulation.de"]
    start_urls = ["https://www.citypopulation.de/en/spain/cities/"]

    headers = {
        'authority': 'www.citypopulation.de',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    custom_settings = {

        'FEEDS': {
            f'output/Spain Population {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['City', 'Population'],
            }
        }
    }

    def start_requests(self) -> Iterable[Request]:
        yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        """
        Parse the response to extract city names and their populations.
        """
        try:
            cities = response.css('#ts tbody tr')
            for city in cities:
                item = OrderedDict()
                item['City'] = city.css('[itemprop="name"]::text').get('')
                item['Population'] = city.css('.prio1 ::text').get('').strip()

                yield item
        except Exception as e:
            self.logger.error(f'Error occurred while parsing response: {e}')

