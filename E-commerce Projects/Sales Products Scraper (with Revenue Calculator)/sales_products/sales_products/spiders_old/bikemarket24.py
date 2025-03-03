import json
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urljoin

from scrapy import Request, Selector

from .base import BaseSpider


class BikeMarketScraperSpider(BaseSpider):
    name = "bikemarket24"
    base_url = 'https://bikemarket24.de'
    start_urls = ['https://bikemarket24.de/angebote.html']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories= 'div[data-filtername="cat"]:contains("Kategorie") a::attr(href)'
        self.products = '.product-item'
        self.product_url = '.product-item-link::attr(href)'
        self.new_price = '.price-wrapper[data-price-type="finalPrice"]::attr(data-price-amount)'
        self.next_page = '.pages-item-next .next::attr(href)'

    def parse(self, response, **kwargs):
        data = response.css(f'{self.categories}').getall()
        categories_url = list(set(data))
        for url in categories_url:
            url = url + '?product_list_limit=105'
            yield Request(url=url, callback=self.parse_products)

    def product_detail(self, response):
        item = OrderedDict()

        try:
            data = json.loads(
                response.css('script:contains("var awag_info")').re_first('var awag_info =(.*)').rstrip(';'))
            data = data.get('childs', [])
        except Exception as e:
            print(f"An error occurred: {e}")
            data = []
        sku = response.css('.prod_sku::text').get('').split(':')[-1].strip()
        item['Product Title'] = response.css('.page-title span::text').get('')
        item['Price'] = response.css('[itemprop="price"]::attr(content)').get('')
        item['EAN'] = f"'{response.css('[data-oz-code]::attr(data-oz-code)').get('') or data.get(f'{sku}').get('c_ean', '').get('text', '')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item
