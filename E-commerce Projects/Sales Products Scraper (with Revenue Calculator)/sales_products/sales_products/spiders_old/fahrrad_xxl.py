from collections import OrderedDict
from datetime import datetime

from .base import BaseSpider


class FahrradxxlScraperSpider(BaseSpider):
    name = 'fahrrad_xxl'
    base_url = 'https://www.fahrrad-xxl.de/'
    start_urls = ['https://www.fahrrad-xxl.de/angebote/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.categories = '#fxxl-warengruppe-category-1 a::attr(href)'
        self.products = '.fxxl-element-artikel--slider'
        self.product_url = '.fxxl-element-artikel__link::attr(href)'
        self.new_price = '.fxxl-element-artikel__price--new::text'
        self.next_page = '[title="nächste Seite"]::attr(href)'
        self.item_counter = 0  # Initialize item counter
        self.is_file_written = False

    def product_detail(self, response):
        item = OrderedDict()

        item['Product Title'] = response.css('.fxxl-artikel-detail__product_name::text').get('')
        # item['Price'] = response.css('option[data-onlinesizer-ean]::attr(data-price)').get('').replace('€', '').replace(
        #     ',', '.').strip()
        item['Price'] = self.get_price(response.css('option[data-onlinesizer-ean]::attr(data-price)').get(''))
        item['EAN'] = f"'{response.css('option[data-onlinesizer-ean]::attr(data-onlinesizer-ean)').get('')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        self.item_counter += 1  # Increment item counter

        # if self.item_counter % 25 == 0:
        #     if not self.is_file_written:
        #         mode = 'w'
        #         self.is_file_written = True
        #     else:
        #         mode = 'a'
        #
        #     self.write_items_to_csv(mode=mode)

        yield item
