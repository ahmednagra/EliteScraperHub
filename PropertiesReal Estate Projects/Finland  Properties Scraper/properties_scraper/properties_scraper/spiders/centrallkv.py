import re
from datetime import datetime
from urllib.parse import urlparse
from .base import BaseSpider


class centrallkvSpider(BaseSpider):
    name = 'centrallkv'
    start_urls = ['https://centrallkv.fi/fi/myyntikohteet.html']

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
            properties_selectors = response.css('.fm2group .item')
            if len(properties_selectors) == 0:
                self.error_messages.append(f'Centrallkv Scraper No Apartment found in Parse Method - {datetime.now()}')

            for property_selector in properties_selectors:
                item = self.get_item(property_selector)
                yield item
        except Exception as e:
            self.error_messages.append(f'Centrallkv Scraper Parse get this error : {e} - {datetime.now()}')

    def get_address(self, response):
        try:
            address_row = response.css('.header h3::text').get('')
            address = re.sub(r'\d', '', address_row).strip()
            return address.replace('-', '')
        except Exception as e:
            self.error_messages.append(f'Centrallkv Scraper get_address get this error : {e} - {datetime.now()}')

    def get_street_number(self, response):
        address = ''.join(response.css('.header h3::text').get('').split()[1:2])
        if '-' in address:
            street_no = re.sub(r'\D-\D', '', address)
        else:
            street_no = ''.join(re.findall(r'\d', address))
        return street_no

    def get_type(self, response):
        try:
            return ' '.join([x.strip() for x in response.css('.price::text').get('').split(' ')])
        except Exception as e:
            self.error_messages.append(f'Centrallkv Scraper get_type get this error : {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            return response.css('.room-types::text').re_first(r'(\d+)[sh]*')
        except Exception as e:
            self.error_messages.append(f'Centrallkv Scraper get_rooms get this error : {e} - {datetime.now()}')
            return ''
    def get_size(self, response):
        try:
            return response.css('.area::text').get('').strip().replace('m²', '').replace('m', '')
        except Exception as e:
            self.error_messages.append(f'Centrallkv Scraper get_size get this error : {e} - {datetime.now()}')

    def get_agency_url(self, response):
        return response.css('.apartment-link::attr(href)').get('')

    def get_static(self, response):
        url = response.css('.apartment-link::attr(href)').get('')
        return urlparse(url).netloc.split('.')[0]
