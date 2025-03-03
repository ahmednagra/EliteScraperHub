import json
import re
from collections import OrderedDict
from urllib.parse import urljoin

from scrapy import Request

from .base import BaseSpider


class TelekomScraperSpider(BaseSpider):
    name = "telekom"
    base_url = 'https://www.telekom.de/'
    start_urls = ['https://www.telekom.de/mobilfunk/zubehoer/alle?page=30']

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.output_fieldnames = ['Product Title', 'Price', 'SKU', 'URL']

        self.product_url = 'a::attr(href)'
        self.products = '.styles_item__bR7S5'
        self.new_price = '[data-qa="formattedPrice-value"] span::text'

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_products)

    def parse_detail_product(self, response):
        try:
            string = response.css('script:contains("utag_data")').re_first(r'({.*})')
            if string:
                string = string.split(';')[0]
            else:
                string = ''
                return

            add_quotes = re.sub(r'(\w+)(?=:)', r'"\1"', string)
            data = json.loads(add_quotes)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error occurred: {e}")
            data = {}

        item = OrderedDict()

        item['Product Title'] = response.css('.extra_details__name::text').get('').strip()
        item['Price'] = response.css('.price__total-price--big::attr(data-basic-price)').get('')
        item['EAN'] = f"'{data.get('shop_product_sku', '')}"  # Sku will replace with EAN for revnue calulator
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item
