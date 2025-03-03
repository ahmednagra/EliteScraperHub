import re
from datetime import datetime

from scrapy import Request

from .base import BaseSpider


class NeliotliikkuuSpider(BaseSpider):
    name = 'neliotliikkuu'
    base_url = 'https://neliotliikkuu.fi/myytavat-asunnot/'
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
        filename = 'neliotliikkuu_locations.txt'
        self.cities_name_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        if not self.cities_name_from_input_file:
            yield Request(url=self.base_url, callback=self.parse_html)
        else:
            for city in self.cities_name_from_input_file:
                yield Request(url=self.base_url, callback=self.parse_html, meta={'city_name': city})

    def parse_html(self, response):
        try:
            data_secret_key = response.css('article div::attr(data-secret)').get('')
            url = f"https://middleware.linear.fi/v2/listings/{data_secret_key}?env=prod"
            yield Request(url=url, callback=self.parse, meta=response.meta)
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper Parse Method got error: {e} - {datetime.now()}')

    def parse(self, response, **kwargs):
        try:
            data = response.json()
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        properties = data.get('data', [{}])
        search_city = response.meta.get('city_name')
        search_city = search_city.strip().lower() if search_city else ''

        if 'neliotliikkuu' not in search_city and search_city:
            properties_selectors = [pro for pro in properties if pro.get('city', '').strip().lower() == search_city]
        else:
            properties_selectors = [pro for pro in properties]

        if len(properties_selectors) == 0:
            self.error_messages.append(f'Neliotliikkuu Scraper No Apartment found in Parse Method - {datetime.now()}')
            return

        for property_selector in properties_selectors:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        try:
            address_row = response.get('address', '')
            address = re.match(r'^\D+', address_row).group().strip() if address_row else ''
            return address.replace('-', ' ')
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper Parse Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address = response.get('address', '')
            if '-' in address:
                street_number = ''.join(re.findall(r'\d+-\d+', address))
            else:
                street_number = re.search(r'(\d+)\D', address).group(1) if re.search(r'(\d+)\D', address) else (
                            '' or ''.join(
                        re.findall(r'\d+[a-zA-Z]?', address)))
            return street_number
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        try:
            price = response.get('debtFreePrice', '')
            price = price.strip() if price else ''
            return price
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper get_type Method got error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            return response.get('roomCount', '')
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper get_rooms Method got error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        try:
            area = response.get('area', '')
            area = area.replace('m²', '').replace(',', '.').strip() if area else ''
            return area
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper get_size Method got error: {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        try:
            return f"{self.base_url}?activeListing={response.get('id')}"
        except Exception as e:
            self.error_messages.append(f'Neliotliikkuu Scraper get_agency_url Method got error: {e} - {datetime.now()}')
            return ''
    def get_static(self, response):
        return 'neliotliikkuu'