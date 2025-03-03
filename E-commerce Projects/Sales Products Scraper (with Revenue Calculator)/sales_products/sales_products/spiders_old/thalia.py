from collections import OrderedDict
from urllib.parse import urljoin

from scrapy import Request

from .base import BaseSpider


class ThaliaScraperSpider(BaseSpider):
    name = 'thalia'
    base_url = 'https://www.thalia.de/'
    start_urls = ['https://www.thalia.de/themenwelten/sale/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_proxy = True

        self.products = '.artikel'
        self.product_url = '.artikel a::attr(href)'

    def parse(self, response, **kwargs):
        category_urls = self.get_categories_url(response)
        for url in category_urls:
            yield Request(url=urljoin(response.url, url), callback=self.parse)

        yield from self.parse_products(response)  # To parse products in the given category itself even if it has sub cats

    def parse_products(self, response):
        products_urls = response.css('.artikel a::attr(href)').getall() or ''
        for product in products_urls:
            yield Request(url=urljoin(response.url, product), callback=self.product_detail)

    def product_detail(self, response):

        item = OrderedDict()

        item['Product Title'] = response.css('feedback-ads::attr(data-titel)').get('')
        item['Price'] = response.css('[property="product:price:amount"]::attr(content)').get('')
        item['EAN'] = f"'{response.css('feedback-ads::attr(data-ean)').get('')}"
        item['URL'] = response.url

        yield item

    def get_categories_url(self, response):
        categories = response.css('[icon="forward"]::attr(href)').getall()
        categories = categories or response.css('[interaction="link-SALE"] a::attr(href)').getall() or ''

        return categories
