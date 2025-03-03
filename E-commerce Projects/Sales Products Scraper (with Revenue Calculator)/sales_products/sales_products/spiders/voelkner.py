from collections import OrderedDict

from scrapy import Request

from .base import BaseSpider


class VoelknerScraperSpider(BaseSpider):
    name = "voelkner"
    base_url = 'https://www.voelkner.de/'
    start_urls = ['https://www.voelkner.de/categories/13150_13268/Freizeit-Hobby/Sale.html']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.products = '.js_search_product_tracking'
        self.product_url = '.product__title::attr(href)'
        self.new_price = '[itemprop="price"]::attr(content)'
        self.next_page = '[data-next-page]::attr(data-next-page)'

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_products)

    def product_detail(self, response):
        item = OrderedDict()

        item['Product Title'] = response.css('#js_heading::text').get('')
        item['Price'] = response.css('[itemprop="price"]::attr(content)').get('')
        ean = response.css('[itemprop="gtin"]::attr(content)').get('')
        item['EAN'] = f"'{ean}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item
