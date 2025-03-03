import json
from collections import OrderedDict

from scrapy import Request

from .base import BaseSpider


class AlternateScraperSpider(BaseSpider):
    name = 'alternate'
    base_url = 'https://www.alternate.de/'
    start_urls = ['https://www.alternate.de/TagesDeals']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.products = '.productBox'
        self.product_url = 'a::attr(href)'
        self.new_price = '.price ::text'

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_products)

    def product_detail(self, response):

        item = OrderedDict()

        try:
            data = json.loads(response.css('script:contains("offers")::text').get(''))
            data = data[0].get('offers')
        except Exception as e:
            print(f"An error occurred: {e}")
            data = []

        item['Product Title'] = response.css('#product-name-data::attr(data-product-name)').get('') or data.get('name',
                                                                                                                '')
        item['Price'] = data.get('price', '')
        item['EAN'] = f"'{response.css('#product-details tr:contains(EAN) td:nth-child(2)::text').get('')}"
        item['URL'] = data.get('url', '') or response.url

        self.current_scraped_items.append(item)
        yield item
