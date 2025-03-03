import re
from datetime import datetime

from scrapy import Request

from .base import BaseSpider


class RemaxSpider(BaseSpider):
    name = 'remax'
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
        filename = 'remax_locations.txt'
        self.keywords_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        for keyword in self.keywords_from_input_file:
            url = f'https://remax.fi/wp-content/themes/blocksy-child/property_search_LINEAR.php?property-type=asunnot&realty-type=&bedrooms=&location={keyword}&price_min=&price_max=&living_area_m2_min=&living_area_m2_max=&lot_area_min=&lot_area_max=&buildyear_min=&buildyear_max='
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            # Record not exist for this city
            if not response.text:
                return

            data = response.json()
        except Exception as e:
            self.error_messages.append(f'Remax Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        if len(data) == 0:
            self.error_messages.append(f'Remax Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in data:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        try:
            address = response.get('street_address', '')
            if address:
                address = address.split()[0]
            return address
        except Exception as e:
            self.error_messages.append(f'Remax Scraper Parse get_address got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address_row = response.get('street_address', '')
            street_no = ''.join(re.findall(r'\d{1,9}-\d{1,9}', address_row))  # if '-' in result for street no
            if not street_no:
                street_no = ''.join(re.findall(r'(\d[A-Za-z]*)', address_row))

            return street_no
        except Exception as e:
            self.error_messages.append(f'Remax Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        return response.get('price', '').replace('\xa0', '').strip() + ' €'

    def get_rooms(self, response):
        try:
            rooms = response.get('roomAmount', 0)
            rooms = rooms or re.search(r'(\d+)[sh]*', response.get('rooms', '')) and re.search(r'(\d+)[sh]*',
                                                                                               response.get('rooms',
                                                                                                            '')).group(
                1) or ''

            return rooms
        except Exception as e:
            self.error_messages.append(f'Remax Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        size = response.get('totalArea', None)
        return size if size is not None else ''

    def get_agency_url(self, response):
        try:
            town = response.get("town", '')
            district = response.get("district", '')
            listingType = response.get("listingType", '')
            identifier = response.get("identifier", '')
            url = f'{"https://remax.fi/kohde/"}{town}/{district}/{listingType}/{identifier}'

            return response.get('canonicalUrl', '') or url
        except Exception as e:
            self.error_messages.append(f'Remax Scraper get_agency_url Method got error: {e} - {datetime.now()}')
            return
    def get_static(self, response):
        return 'remax'
