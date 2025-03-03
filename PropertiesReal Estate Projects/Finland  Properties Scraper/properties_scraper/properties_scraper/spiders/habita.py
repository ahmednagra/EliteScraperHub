import re
from datetime import datetime

import requests

from scrapy import Request

from .base import BaseSpider


class HabitaSpider(BaseSpider):
    name = 'habita'

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
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
        filename = 'habita_locations.txt'
        self.keywords_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        try:
            for keyword in self.keywords_from_input_file:
                keyword_ids = self.get_keyword_id(keyword)

                if keyword_ids:
                    for id in keyword_ids:
                        url = f'https://www.habita.com/propertysearch/results/fi/1/28/full?districts={id}&sort=newest&type=ResidenceSale'
                        yield Request(url=url, callback=self.parse)
                else:
                    print('No search City Keyword found in response ')
        except Exception as e:
            self.error_messages.append(f'Habite Scraper Kindly add Desired city in input filee - {datetime.now()}')

    def parse(self, response, **kwargs):
        try:
            data = response.json()
            results = data.get('results', [])
            if len(results) == 0:
                self.error_messages.append(f'Habita Scraper No Apartment found in Parse Method - {datetime.now()}')

        except Exception as e:
            self.error_messages.append(f'Habite Scraper Parse Method get error: {e} - {datetime.now()}')
            results = []
            return

        for row in results:
            property_id = row.get('id', '')
            priced = row.get('price', 0)
            price = str(priced)
            size = row.get('area', '').replace('m²', '').strip()
            property_url = f'https://www.habita.com/kohde/{property_id}'
            yield Request(url=property_url, callback=self.parse_property_detail, meta={'price': price, 'size': size})

    def parse_property_detail(self, response):
        item = self.get_item(response)
        yield item

    def get_address(self, response):
        try:
            address_row = response.css('#descriptions h1::text').get('').replace('Kerrostalo,', '').strip()
            match = re.search(r'^(.*?)\d', address_row)
            if match:
                address = match.group(1)
            else:
                address = address_row

            return address
        except Exception as e:
            self.error_messages.append(f'Habite Scraper get_address Method get error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        address = response.css('#descriptions h1::text').get('')

        if '-' in address:
            # street_no = re.sub(r'\D-\D', '', address)
            street_no = re.findall(r'(\d+-\d+)', address)[0]
        else:
            street_no = ''.join(re.findall(r'(\d+\D*)', address)).split(' ')[0]
            # street_no = ''.join(re.findall(r'\d', address))
        return street_no

    def get_type(self, response):
        try:
            sale_price = response.meta.get('price', '')
            price = int(sale_price)
            formatted_price = "{:,}".format(price).replace(',', ' ')
            return formatted_price + ' €'
        except Exception as e:
            self.error_messages.append(f'Habite Scraper get_type Method get error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        try:
            rooms = response.css('#key-details  div + div span::text').get('')
            return rooms
        except Exception as e:
            self.error_messages.append(f'Habite Scraper get_rooms Method get error: {e} - {datetime.now()}')
            return ''

    def get_size(self, response):
        return response.meta.get('size', '')

    def get_agency_url(self, response):
        return response.url

    def get_static(self, response):
        return 'habita'

    def get_keyword_id(self, keyword):
        res = requests.get(url=f'https://www.habita.com/location/suggestions/fi/{keyword}')
        try:
            data = res.json()
            id = [x.get('id', '') for x in data if x.get('type', '') == 'district']
        except Exception as e:
            id = []

        return id

    def get_city_results(self, id):
        url = f'https://www.habita.com/propertysearch/results/fi/1/28/full?districts={id}&sort=newest&type=ResidenceSale'
        res = requests.get(url=url)
        try:
            data = res.json()
            results = data.get('results', [])
            ids = [x.get('id', '') for x in results]
        except Exception as e:
            self.error_messages.append(f'Habite Scraper get_city_results Method get error: {e} - {datetime.now()}')
            ids = []

        return ids
