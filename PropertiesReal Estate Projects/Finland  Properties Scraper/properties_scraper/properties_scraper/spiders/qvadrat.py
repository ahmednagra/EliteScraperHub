import re
from datetime import datetime

from .base import BaseSpider


class QvadratSpider(BaseSpider):
    name = 'qvadrat'

    start_urls = ['https://www.qvadrat.fi/wp-json/linear/v1_1/listings/all?lang=fi']

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
            data = response.json()
        except Exception as e:
            self.error_messages.append(f'Qvadrat Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        if len(data) == 0:
            self.error_messages.append(f'Qvadrat Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in data:
            permalink = property_selector.get('permalink', '')
            if 'myynti' in permalink and property_selector.get('debtFreePrice', ''):
                item = self.get_item(property_selector)
                yield item
            else:
                continue

    def get_address(self, response):
        return response.get('address', '').split()[0]

    def get_street_number(self, response):
        try:
            address = response.get('address', '')

            if '-' in address:
                street_number = ''.join(re.findall(r'\d+-\d+', address))
            else:
                street_number = ''.join(re.findall(r'\d', address))

            return street_number
        except Exception as e:
            self.error_messages.append(f'Qvadrat Scraper get_street_no Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        return response.get('debtFreePrice', '').strip()

    def get_rooms(self, response):
        try:
            rooms = response.get('roomCount', 0) or ''.join(re.findall(r'\d', response.get('roomCount', '')))
            return rooms
        except Exception as e:
            self.error_messages.append(f'Qvadrat Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        try:
            size = response.get('area', '')

            if size is not None:
                size = size.replace('m²', '').replace(',', '.').strip()
            else:
                size = ''

            return size
        except Exception as e:
            self.error_messages.append(f'Qvadrat Scraper get_size Method got error: {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        return response.get('permalink', '')

    def get_static(self, response):
        return 'qvadrat'
