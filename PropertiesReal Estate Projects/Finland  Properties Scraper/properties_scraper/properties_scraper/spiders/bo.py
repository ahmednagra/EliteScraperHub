import re
from datetime import datetime
from urllib.parse import urlparse
from scrapy import Request
from .base import BaseSpider


class BospiderSpider(BaseSpider):
    name = 'bo'

    custom_settings = {
        'LOG_LEVEL': 'WARNING',
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
        filename = 'bo_urls.txt'
        self.urls_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        for url in self.urls_from_input_file:
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            properties_selectors = response.css('.realty-grid__content .realty-grid__single')
            if len(properties_selectors) == 0:
                self.error_messages.append(f'Bo Scraper No Apartment found in Parse Method - {datetime.now()}')

            for property_selector in properties_selectors:
                item = self.get_item(property_selector)
                yield item

            next_page = response.css('.right::attr(href)').get('')
            if next_page:
                yield Request(url=response.urljoin(next_page), callback=self.parse)
        except Exception as e:
            self.error_messages.append(f'Bo Scraper Parse get this error : {e} - {datetime.now()}')

    def get_address(self, response):
        try:
            address_row = response.css('.realty-grid__single__content__address h3::text').get('')
            address = re.sub(r'\d', '', address_row).strip()
            return address.replace('-', '')
        except Exception as e:
            self.error_messages.append(f'Bo Scraper get_address get this error : {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        address = ''.join(response.css('.realty-grid__single__content__address h3::text').get('').split()[1:2])

        if '-' in address:
            street_no = re.sub(r'\D-\D', '', address)
        else:
            street_no = ''.join(re.findall(r'\d', address))

        if not street_no:
            street_no = response.css('.realty-grid__single__content__address h3::text').get('').split()[2]

        return street_no

    def get_type(self, response):
        return response.css('.realty-grid__single__content__price span::text').get('').strip()

    def get_rooms(self, response):
        rooms = response.css('.realty-grid-oneliner::text').re_first(r'(\d+)s*h')
        rooms = rooms or response.css('.realty-grid-oneliner::text').re_first(r'(\d+)s* h')

        return rooms

    def get_size(self, response):
        return response.css('.realty-grid__single__content__price span + span::text ').get('').strip()\
            .replace('m²', '').replace('m', '').replace(',', '.')

    def get_agency_url(self, response):
        return response.css('a::attr(href)').get('')

    def get_static(self, response):
        url = response.css('a::attr(href)').get('')
        return urlparse(url).netloc.split('.')[0]
