import json
import csv
from collections import OrderedDict
from urllib.parse import urljoin

from scrapy import Spider, Request
from .base import BaseSpider


class MullerScraperSpider(BaseSpider):
    name = 'muller'
    base_url = 'https://www.mueller.de/'
    start_urls = ['https://www.mueller.de/sale/alle-produkte/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.products = 'div a.mu-product-tile__link:not(.mu-product-tile__link._gtm-push-event)'
        self.product_url = 'a::attr(href)'
        self.new_price = '.mu-product-tile__price::text'
        self.next_page = '.mu-pagination__navigation--next::attr(href)'

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_products)

    def product_detail(self, response):

        item = OrderedDict()

        try:
            data = json.loads(response.css('[is="script"]::text').re_first(r'{"@context":"http://schema.org".*}'))
        except Exception as e:
            data = []

        item['Product Title'] = response.css('.mu-product-details-page__product-name::text').get(
            '').strip() or data.get('name', '')
        item['Price'] = self.get_price(response.css('.mu-product-price__price.mu-product-price__price--promo::text').get('')) or data.get('offers', [{}])[0].get('price')

        item['EAN'] = f"'{data.get('gtin13', '')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        # was_price = response.css('.mu-product-price__price.mu-product-price__price--original::text').get('').replace('€', '').replace(',', '.').strip() or \
        #                 data.get('offers', [{}])[0].get('price', '')

        # item['Price'] = response.css('.mu-product-price__price.mu-product-price__price--promo::text').get('').replace('€', '').replace(',', '.').strip() or data.get('offers', [{}])[0].get('price')

        # if was_price:
        #     item['Price'] = was_price
        #     item['Discounted Price'] = current_price
        # else:
        #     item['Price'] = current_price
        #     item['Discounted Price'] = ''

        #
        # yield item
        #
