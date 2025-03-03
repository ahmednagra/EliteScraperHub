import re
import json
from datetime import datetime

from .base import BaseSpider


class WesthouseSpider(BaseSpider):
    name = 'westhouse'
    start_urls = ['https://westhouse.fi/asunnot/#asunnot']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/properties/{name} Properties.xlsx': {
                'format': 'xlsx',
                'fields': BaseSpider.xlsx_headers,
                'overwrite': True,
            }
        },
    }

    def parse(self, response, **kwargs):
        try:
            data = json.loads(response.css('script:contains("window.VueData"):not([type="text/javascript"])').re_first(
                r'(results.*})').replace('results: ', '') + ']')
        except Exception as e:
            self.error_messages.append(f'Westhouse Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        if len(data) == 0:
            self.error_messages.append(f'Westhouse Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in data:
            category = property_selector.get('kategoria', '')
            if 'asunnot' in category:
                item = self.get_item(property_selector)
                yield item
            else:
                continue

    def get_address(self, response):
        address = ''.join(response.get('osoite', '').split()[:1])
        return address

    def get_street_number(self, response):
        try:
            address = ''.join(response.get('osoite', '').split()[1:2])
            if '-' in address:
                street_no = re.sub(r'\D-\D', '', address)
            else:
                street_no = ''.join(re.findall(r'\d', address))
            return street_no
        except Exception as e:
            self.error_messages.append(f'Westhouse Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        return response.get('price', '').strip()

    def get_rooms(self, response):
        rooms = response.get('rooms', '')
        return rooms

    def get_size(self, response):
        return response.get('size', '').replace('m²', '').strip()

    def get_agency_url(self, response):
        return response.get('url', '')

    def get_static(self, response):
        return 'westhouse'
