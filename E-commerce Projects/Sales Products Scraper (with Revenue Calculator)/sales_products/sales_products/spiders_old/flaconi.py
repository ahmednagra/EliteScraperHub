import json
from collections import OrderedDict

from .base import BaseSpider


class FlaconiScraperSpider(BaseSpider):
    name = 'flaconi'
    base_url = 'https://www.flaconi.de/'
    start_urls = ['https://www.flaconi.de/sale/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.categories = 'a[level="1"]::attr(href)'
        self.products = '[data-insights-position]'
        self.product_url = 'a::attr(href)'
        self.new_price = '.iMarYn::text'
        self.next_page = '.Paginationstyle__NextPage-sc-d38xli-3::attr(href)'

        self.item_counter = 0  # Initialize item counter
        self.is_file_written = False

    def product_detail(self, response):

        try:
            json_data = json.loads(response.css('script:contains("gtin") ::text').get(''))
        except json.JSONDecoder:
            return

        name = json_data.get('name', '')

        for offer in json_data.get('offers', [{}]):
            item = OrderedDict()

            item['Product Title'] = name
            item['Price'] = offer.get('price', '')
            item['EAN'] = f"'{offer.get('gtin13', '')}"
            item['URL'] = offer.get('url', '')

            self.current_scraped_items.append(item)
            yield item