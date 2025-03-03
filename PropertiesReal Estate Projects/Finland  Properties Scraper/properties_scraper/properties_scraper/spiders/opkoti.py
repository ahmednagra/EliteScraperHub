import glob
import json
import re
from datetime import datetime
from scrapy import Request

from .base import BaseSpider

import locale


class OpkotiSpider(BaseSpider):
    name = 'opkoti'

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
        filename = 'opkoti_postcodes.txt'
        self.postcodes_from_input_file = self.read_input_postcodes(filename=filename)

    def start_requests(self):
        if self.postcodes_from_input_file:
            postal_codes_query = '&'.join([f'postalCode={code}' for code in self.postcodes_from_input_file])
            url = f'https://op-koti.fi/myytavat/asunnot?{postal_codes_query}'
            yield Request(url=url, callback=self.parse)
        else:
            url = 'https://op-koti.fi/myytavat/asunnot?postalCode=00100&postalCode=00120&postalCode=00130&postalCode=00140&postalCode=00150'
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            script_selector = response.css('script:contains(INITIAL_STATE) ::text').re_first(r'STATE__=(.*?);\(function\(\)')
            data = json.loads(script_selector)
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        properties_dict = data.get('apartments', {}).get('apartments', [])

        if len(properties_dict) == 0:
            self.error_messages.append(f'Opkoti Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in properties_dict:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        try:
            address_row = response.get('location', {}).get('streetAddress', '')
            address = re.match(r'^\D+', address_row).group().strip() if address_row else ''
            return address.replace('-', '')
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper get_address Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address_row = response.get('location', {}).get('streetAddress', '')
            street_no = ''.join(re.findall(r'\d', address_row))

            return street_no.strip()
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        try:
            price = response.get('debtFreePrice', '')
            locale.setlocale(locale.LC_ALL, 'fi_FI')
            modify_price = locale.format_string("%.0f €", price, grouping=True)
            return modify_price
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper get_type Method got error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            room_selector = response.get('rooms', '')
            match = re.search(r'(\d+)\s?h', room_selector.lower())

            if match:
                room = match.group(1)
            else:
                room = ''

            return room
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        try:
            size = str(response.get('totalArea', {}).get('size', '')).strip()
            return size
        except Exception as e:
            self.error_messages.append(f'Opkoti Scraper get_size Method got error: {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        p_id = response.get('id', '')
        return f'https://op-koti.fi/kohde/{p_id}' if p_id else ''

    def get_static(self, response):
        return 'opkoti'

    def read_input_postcodes(self, filename):
        file_path = ''.join(glob.glob(f'input/{filename}'))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file.readlines()]
            return urls
        except Exception as e:
            # print(f"An error occurred while reading the file: {e}")
            self.error_messages.append(f'Opkoti Scraper An error occurred while reading the Postcodes file: {e} - {datetime.now()}')
            return []
