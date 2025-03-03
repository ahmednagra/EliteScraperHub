import re
import json
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Request

from .base import BaseSpider


class MediamarketScraperSpider(BaseSpider):
    name = "mediamarkt"
    base_url = 'https://www.mediamarkt.de/'
    start_urls = ['https://www.mediamarkt.de/de/campaign/restposten']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.use_proxy = False
        self.categories = '.sc-dkrFOg.rnwug a::attr(href)'

    def parse_products(self, response):
        products = response.css('.bIXshs')
        for product in products:
            product_url = product.css('[data-test="mms-product-list-item-link"]::attr(href)').get('').rstrip('/').strip()
            product_url = urljoin(self.base_url, product_url)

            if not product_url:
                continue

            new_price = product.css('.bYXcqh .kfiqCI::text').re_first(r'[0-9,.]+', '').replace(',', '.')

            if self.is_product_exists(product_url, new_price):
                continue

            yield Request(url=product_url, callback=self.parse_detail_product)

        next_page = response.css('[data-test="mms-search-srp-loadmore"]')
        if next_page:
            url = response.url
            pattern = r"\?page="
            if re.search(pattern, url):
                current_page = response.url
                current_page_num_match = re.search(r"\bpage=(\d+)\b", response.url)
                current_page_num = int(current_page_num_match.group(1))
                next_page = current_page.replace(f"?page={current_page_num}", f"?page={current_page_num + 1}")
                yield Request(url=next_page, callback=self.parse_products)

            else:
                yield Request(url=urljoin(response.url, '?page=2'), callback=self.parse_products)

    def parse_detail_product(self, response):
        item = OrderedDict()

        try:
            data = json.loads(response.css('script[data-rh="true"]').re_first(r'({.*})')).get('object', {})
        except Exception as e:
            data = {}

        item['Product Title'] = data.get('name', '')
        item['Price'] = data.get('offers', {}).get('price', '')
        item['EAN'] = f"'{data.get('gtin13', '')}"
        item['URL'] = data.get('url', '')

        self.current_scraped_items.append(item)

        yield item
