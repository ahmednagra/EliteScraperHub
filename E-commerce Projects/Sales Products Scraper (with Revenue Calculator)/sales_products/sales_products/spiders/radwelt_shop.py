from collections import OrderedDict
from urllib.parse import urljoin, unquote
from scrapy import Request

from .base import BaseSpider


class RadweltScraperSpider(BaseSpider):
    name = "radwelt"
    base_url = 'https://www.radwelt-shop.de/'
    start_urls = ['https://www.radwelt-shop.de/sale/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.products = 'product-box--outer'
        self.products = '.product-box--outer'
        self.product_url = '.product--title::attr(href)'
        self.new_price = '.additional--variant::attr(data-additional-price), .price--defaul::text, .price--default, .is--discount'
        self.next_page = '[title="Nächste Seite"]::attr(href)'

    def parse(self, response, **kwargs):
        data = response.css('.is--level1 [role="menuitem"] a::attr(href)').getall()
        categories_url = list(set(data))
        for url in categories_url:
            url = url + '?p=1&o=2&n=48'
            yield Request(url=urljoin(response.url, url), callback=self.parse_products)

    def product_detail(self, response):
        frames_url = response.css('.detail--configuration--selection::attr(href)').getall()
        if frames_url:
            for frame_url in frames_url:
                url = urljoin(response.url, frame_url)

                yield Request(url=url, callback=self.frame_detail)

        else:
            item = OrderedDict()

            item['Product Title'] = response.css('.product--title[itemprop="name"]::text').get('')
            item['Price'] = response.css('meta[itemprop="price"]::attr(content)').get('')
            ean = response.css('meta[itemprop="gtin13"]::attr(content)').get('')
            item['EAN'] = f"'{ean}"
            item['URL'] = unquote(response.url)

            self.current_scraped_items.append(item)
            yield item

    def frame_detail(self, response):
        item = OrderedDict()

        item['Product Title'] = response.css('.product--title[itemprop="name"]::text').get('')
        item['Price'] = response.css('meta[itemprop="price"]::attr(content)').get('')
        # item['EAN'] = [ean for ean in response.css('.detail--configuration--selection::attr(data-oz-ean)').getall() if ean]
        ean = response.css('meta[itemprop="gtin13"]::attr(content)').get('')
        item['EAN'] = f"'{ean}"
        item['URL'] = unquote(response.url)

        self.current_scraped_items.append(item)
        yield item

