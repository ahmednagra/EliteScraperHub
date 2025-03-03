import re
from datetime import datetime

from .base import BaseSpider


class NordlkvSpider(BaseSpider):
    name = 'nordlkv'
    start_urls = ['https://www.nordlkv.fi/myytavat-asunnot/?nord_location=helsinki&nord_type=&nord_rooms=&nord_size=&nord_housing_type=sale&nord_orderby=']

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse(self, response, **kwargs):
        try:
            properties_selectors = response.css('.js-results > div')
            if len(properties_selectors) == 0:
                self.error_messages.append(
                    f'Nordlkv Scraper No Apartment found in Parse Method - {datetime.now()}')
                return

            for property_selector in properties_selectors:
                item = self.get_item(property_selector)
                yield item
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper Parse Method got error: {e} - {datetime.now()}')
            return ''

    def get_address(self, response):
        try:
            address_row = response.css('h2.lh-title-mega::text').get('').split(',')[0]
            address = re.sub(r'\d', '', address_row).strip()
            return address.replace('-', '')
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper get_address Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address_row = response.css('h2.lh-title-mega::text').get('').split(',')[0]

            if '-' in address_row:
                street_no_match = re.search(r'\d+-\d+', address_row)
                if street_no_match:
                    street_no = street_no_match.group()
                else:
                    street_no = ''.join(re.findall(r'\d', address_row))
            else:
                street_no = ''.join(re.findall(r'\d', address_row))

            return f'{street_no}'
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        try:
            return response.css('span.lh-title-mega ::text').get('').strip()
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper get_type Method got error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            room_selector = response.css('.lh-copy .db.mt2::text').getall()
            room_selector = ''.join(room_selector) if room_selector else ''

            match = re.search(r'(\d+)\s?h', room_selector.lower())

            if match:
                room = match.group(1)
            else:
                room = ''

            return room
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        try:
            size_selector = response.css('.lh-copy .db.mt2::text ').getall()
            size_selector = ''.join(size_selector) if size_selector else ''
            if 'm |' in size_selector:
                size = size_selector.split('m |')[0]
            else:
                size = ''

            return size.replace(',', '.').strip()
        except Exception as e:
            self.error_messages.append(f'Nordlkv Scraper get_size Method got error: {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        return response.css('a.db::attr(href)').get('')

    def get_static(self, response):
        return 'nord'
