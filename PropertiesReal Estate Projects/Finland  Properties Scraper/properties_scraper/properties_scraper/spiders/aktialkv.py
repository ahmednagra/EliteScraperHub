import json
import re
from datetime import datetime
from math import ceil

from scrapy import Request

from .base import BaseSpider


class AktialkvSpider(BaseSpider):
    name = 'aktialkv'
    start_urls = ['https://www.aktialkv.fi/myytavat-asunnot/helsinki/page-3?categories[]=5500385']

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

    headers = {
        'authority': 'www.aktialkv.fi',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://www.aktialkv.fi/myytavat-asunnot/helsinki/page-1?categories[]=5500385',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        # There is no defined number of products or pages on the website
        total_products = 100
        total_pages = ceil(total_products / 24)

        for page in range(1, total_pages + 1):
            url = f'https://www.aktialkv.fi/api/apartments?region[]=5500722&categories[]=5500385&page={page}&forRent=false&offset=0'
            yield Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            data = response.json().get('apartments', [])

            if len(data) == 0:
                self.error_messages.append(f'Aktialkv Scraper No Apartment get in the Parse Method - {datetime.now()}')
                return

            for property_json in data:
                if not property_json.get('url', ''):
                    continue

                item = self.get_item(property_json)
                yield item

        except Exception as e:
            # print("Caught a general exception:", e)
            self.error_messages.append(f'Aktialkv Scraper parse get this error : {e} - {datetime.now()}')
            return

    def get_address(self, response):
        try:
            address_row = json.loads(response.get('address', '')).get('parts', {}).get('address', '')
        except Exception as e:
            self.error_messages.append(f'Aktialkv Scraper get_address get this error : {e} - {datetime.now()}')
            address_row = ''

        address = address_row or response.get('title', '').split()[0]
        return address

    def get_street_number(self, response):
        try:
            street = json.loads(response.get('address', '')).get('parts', {}).get('number', '')
            street = re.sub(r'[^0-9]', '', street)

            if not street:
                street = ''
        except Exception as e:
            self.error_messages.append(f'Aktialkv Scraper get_street_number get this error : {e} - {datetime.now()}')
            street = ''

        return street

    def get_type(self, response):
        price = response.get('price', '').replace('\xa0', '').replace('€', '').replace('.', ',')

        if price:
            price = price.split(',')[0]
            formatted_price = '{:,}'.format(int(price)).replace(',', ' ')
            return formatted_price + ' €'
        else:
            return ''

    def get_rooms(self, response):
        try:
            rooms = response.get('roomcount', '').replace('huonetta', '').replace('huone', '').strip()
            return rooms
        except Exception as e:
            self.error_messages.append(f'Aktialkv Scraper get_rooms get this error : {e} - {datetime.now()}')
            rooms = ''
            return rooms

    def get_size(self, response):
        try:
            return response.get('propertySize', '').replace(' m²', '').replace(',', '.')
        except Exception as e:
            self.error_messages.append(f'Aktialkv Scraper Get_size get this error : {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        return response.get('url', '')

    def get_static(self, response):
        return 'aktia'
