import re
from datetime import datetime
from math import ceil

from scrapy import Request

from .base import BaseSpider


class KiinteistomaailmaSpider(BaseSpider):
    name = 'kiinteistomaailma'

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
        'authority': 'www.kiinteistomaailma.fi',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        filename = 'Kiinteistömaailma_locations.txt'
        self.keywords_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        if not self.keywords_from_input_file:
            url = 'https://www.kiinteistomaailma.fi/api/km/KM/?areaType=living&limit=500&maxArea&maxYearBuilt&minArea&minYearBuilt&rental=false&skip=90&sort=latestPublishTimestamp&sortOrder=desc&type=property'
            yield Request(url=url, callback=self.pagination, headers=self.headers)
        for keyword in self.keywords_from_input_file:
            url = f'https://www.kiinteistomaailma.fi/api/km/KM/?areaType=living&limit=1000&maxArea&maxYearBuilt&minArea&minYearBuilt&rental=false&sort=latestPublishTimestamp&sortOrder=desc&type=property&query[]= {{"district":"{keyword}","city":"Helsinki"}}'
            yield Request(url=url, callback=self.parse, headers=self.headers)

    def pagination(self, response):
        try:
            data = response.json()
        except Exception as e:
            self.error_messages.append(f'kiinteistomaailma Scraper pagination Method got error: {e} - {datetime.now()}')
            return

        products = data.get('data', {}).get('matches', 0)

        total_pages = ceil(products / 500)
        for page_no in range(0, total_pages):
            skip_value = page_no * 500
            url = f'https://www.kiinteistomaailma.fi/api/km/KM/?areaType=living&limit=500&maxArea&maxYearBuilt&minArea&minYearBuilt&rental=false&skip={skip_value}&sort=latestPublishTimestamp&sortOrder=desc&type=property'
            yield Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            data = response.json().get('data', {}).get('results', [])
            if len(data) == 0:
                self.error_messages.append(
                    f'Kiinteistomaailma Scraper No Apartment found in Parse Method - {datetime.now()}')

        except Exception as e:
            self.error_messages.append(f'Kiinteistomaailma Scraper Parse Method got error: {e} - {datetime.now()}')
            return

        for property_selector in data:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        try:
            address_row = response.get('address', '')
            address = re.sub(r"\d.*", "", address_row).strip()
            return address
        except Exception as e:
            self.error_messages.append(f'kiinteistomaailma Scraper get_address Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address = response.get('address', '')
            if 'Armfeltintie' in address:
                a=1
            if 'Roobertinkatu' in address:
                if '-' in address:
                    street_number = ''.join(re.findall(r'\d+-\d+', address))
                else:
                    street_number = ''.join(re.findall(r'\d', address))
            else:
                if '-' in address:
                    street_number = ''.join(re.findall(r'\d+-\d+', address))
                else:
                    street_number = re.search(r'(\d+)\D', address).group(1) if re.search(r'(\d+)\D', address) else (''
                                        or  ''.join(re.findall(r'\d+[a-zA-Z]?', address)))
            return street_number
        except Exception as e:
            self.error_messages.append(f'kiinteistomaailma Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        try:
            sale_price = str(response.get('salesPriceUnencumbered', 0)).replace('€', '').split('.')[0]
            return '{:,}'.format(int(sale_price)).replace(',', ' ') + ' €'
        except Exception as e:
            self.error_messages.append(f'kiinteistomaailma Scraper get_type Method got error: {e} - {datetime.now()}')
            return ''

    def get_rooms(self, response):
        rooms = response.get('roomAmount', 0)
        return rooms

    def get_size(self, response):
        try:
            size = response.get('totalArea', None) or response.get('livingArea', 0.0)
            size = size or response.get('landOwnership', {}).get('landArea_m2', 0)
            size = size or response.get('showArea', '').split()[0]

            return size
        except Exception as e:
            self.error_messages.append(f'kiinteistomaailma Scraper get_size Method got error: {e} - {datetime.now()}')
            return ''

    def get_agency_url(self, response):
        return response.get('canonicalUrl', '')

    def get_static(self, response):
        return 'kiinteistomaailma'
