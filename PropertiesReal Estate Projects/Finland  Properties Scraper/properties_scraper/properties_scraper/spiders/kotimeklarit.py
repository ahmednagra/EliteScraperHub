import re
from datetime import datetime
from urllib.parse import urlparse

from .base import BaseSpider


class KotimeklaritSpider(BaseSpider):
    name = "kotimeklarit"
    start_urls = ["https://kotimeklarit.com/myynnissa/"]

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
            properties_selectors = response.css('.view-apartments .appartment-list')
            if len(properties_selectors) == 0:
                self.error_messages.append(f'Kotimeklarit Scraper No Apartment found in Parse Method - {datetime.now()}')
                return

            for property_selector in properties_selectors:
                item = self.get_item(property_selector)
                yield item
        except Exception as e:
            self.error_messages.append(f'Kotimeklarit Scraper Parse Method got error: {e} - {datetime.now()}')
            return ''

    def get_address(self, response):
        try:
            return response.css('.info h2::text').get('').split()[0]
        except Exception as e:
            self.error_messages.append(f'Kotimeklarit Scraper get_address Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address = response.css('.info h2::text').get('').split()[1]
            if '-' in address:
                street_no = re.sub(r'\D-\D', '', address)
            else:
                street_no = ''.join(re.findall(r'\d', address))
            return street_no
        except Exception as e:
            self.error_messages.append(f'Kotimeklarit Scraper get_street_no Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        try:
            price = ''.join(response.css('.price::text').get('').split(',')[0]) + ' €'
            return price
        except Exception as e:
            self.error_messages.append(f'Kotimeklarit Scraper get_type Method got error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            rooms = response.css('.room-types::text').re_first(r'(\d+)[sh]*')
            return rooms
        except Exception as e:
            self.error_messages.append(f'Kotimeklarit Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        return response.css('.area::text').get('').strip().replace('m²', '').replace('m', '').replace(',', '.')

    def get_agency_url(self, response):
        return response.css('a::attr(href)').get('')

    def get_static(self, response):
        url = response.css('a::attr(href)').get('')
        return urlparse(url).netloc.split('.')[0]
