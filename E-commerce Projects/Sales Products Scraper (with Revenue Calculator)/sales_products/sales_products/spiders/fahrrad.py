from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class FahrradScraperSpider(BaseSpider):
    name = 'fahrrad'
    base_url = 'https://www.fahrrad.de/'
    start_urls = ['https://www.fahrrad.de/sale/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = '#category-level-0 a::attr(href)'
        self.products = '.grid-tile'
        self.product_url = '.thumb-link::attr(href)'
        self.new_price = '.price-sales::text'
        self.next_page = '.hide-on-xs.page-next::attr(href)'

        self.item_counter = 0  # Initialize item counter
        self.is_file_written = False

    def product_detail(self, response):
        item = OrderedDict()

        item['Product Title'] = response.css('[itemprop="name"]::text').get('').replace(
            '\n', '').strip()
        # item['Price'] = response.css('.price-sales::text').get(
        #     '').replace('€', '').replace(',', '.').strip()
        item['Price'] = self.get_price(response.css('.price-sales::text').get(''))
        item['EAN'] = f"'{response.css('[data-oz-code]::attr(data-oz-code)').get('')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        self.item_counter += 1  # Increment item counter

        # if self.item_counter % 5000 == 0:
        #     if not self.is_file_written:
        #         mode = 'w'
        #         self.is_file_written = True
        #     else:
        #         mode = 'a'
        #
        #     self.write_items_to_csv(mode=mode)

        yield item