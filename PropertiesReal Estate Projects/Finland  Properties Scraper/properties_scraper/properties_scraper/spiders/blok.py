import re
from datetime import datetime

import requests

from .base import BaseSpider
from scrapy import Request


class BlokSpider(BaseSpider):
    name = 'blok'

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
        'authority': 'blok.ai',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'crisp-client%2Fsession%2Fe406cfb5-696d-41cd-b35b-2f5905ad182a=session_4c53ef8b-7c19-43e1-b104-99aa8356197a',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        filename = 'blok_urls.txt'
        self.urls_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        for url in self.urls_from_input_file:
            url_split = url.split('?neighborhood=')[1]
            api_url = f'https://app.blok.ai/api/v2/listings/data/?neighborhood={url_split}&country=FI&sold=false&new=false&page_size=30&order_by=-published_at'
            yield Request(url=api_url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            data = [x.get('data', {}) for x in response.json().get('results', {}).get('items', [])]
        except Exception as e:
            try:
                res = requests.get(url=response.url).json()
                data = res.get('results', [{}])
                if len(data) == 0:
                    error_message = f'Blok Scraper no Apartment found in Parse Method : {e} - {datetime.now()}'
                # else:
                #     error_message = f'Blok Scraper Parse get this error : {e} - {datetime.now()}'
                    self.error_messages.append(error_message)
                    return
            except Exception as e:
                error_message = f'Blok Scraper Parse get this error during fallback request: {e} - {datetime.now()}'
                self.error_messages.append(error_message)
                return

        for property_selector in data:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        address_row = response.get('location_street_address', '')
        address_r = re.sub(r'\d', '', address_row)
        address = address_r.replace('-', '').strip()

        if not address:
            address = response.get('location_street_address', '').split()[0]

        return address

    def get_street_number(self, response):
        address = response.get('location_street_address', '')

        if '-' in address:
            street_no = re.sub(r'^.*?(\d+-\d+).*?$', r'\1', address)
        else:
            street_no = ''.join(re.findall(r'\d', address))

        return street_no

    def get_type(self, response):
        return response.get('price_display', '')

    def get_rooms(self, response):
        rooms = response.get('room_count', '').split('.')[0]
        return rooms

    def get_size(self, response):
        return response.get('area_living', '').split('.')[0]

    def get_agency_url(self, response):
        try:
            return f'{"https://blok.ai/en/property/"}{response.get("slug")}'
        except Exception as e:
            self.error_messages.append(f'Blok Scraper get_agency_url get this error : {e} - {datetime.now()}')
            return ''

    def get_static(self, response):
        return 'blok'
