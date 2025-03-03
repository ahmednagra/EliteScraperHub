import re
from datetime import datetime
from urllib.parse import urljoin

from .base import BaseSpider


class RivehomesSpider(BaseSpider):
    name = 'rivehomes'
    start_urls = ['https://rivehomes.com/fi/myytavat-asunnot/suomi/helsinki']

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
        properties_selectors = response.css('.listGrid a.Apartment-Card')
        if len(properties_selectors) == 0:
            self.error_messages.append(f'Rivehomes Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in properties_selectors:
            status = property_selector.css('.Apartment-Card__PriceLabel::text').get('')
            if status == 'Osta':
                item = self.get_item(property_selector)
                yield item
            else:
                continue

    def get_address(self, response):
        try:
            address = response.css('.typography-h5::text').re_first(r'(.*?)\d')
            address = address or response.css('.typography-h5::text').get('')

            return address.strip()
        except Exception as e:
            self.error_messages.append(f'Rivehomes Scraper Parse Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address = response.css('.typography-h5::text').get('')

            if '-' in address:
                street_no = re.sub(r'[^\d-]', '', address)
                if street_no.startswith('-'):
                    street_no = ''.join(re.findall(r'-\d+', street_no)).replace('-', '')
            else:
                street_no = ''.join(re.findall(r'\d+', address)[:1])
            return street_no
        except Exception as e:
            self.error_messages.append(f'Rivehomes Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        return response.css('.Apartment-Card__Price h6::text, .Apartment-Card__Price p:not(.Apartment-Card__PriceLabel) ::text').get('')

    def get_size(self, response):
        return response.css('.typography-caps ::text').get('').strip().replace('m²', '').replace('m', '')

    def get_agency_url(self, response):
        url = response.css('a::attr(href)').get('')
        base_url = 'https://rivehomes.com/'

        return urljoin(base_url, url) if url else ''

    def get_static(self, response):
        return 'rive'
