import re
from datetime import datetime
from urllib.parse import urlparse, urljoin

from .base import BaseSpider


class SolidhouseSpider(BaseSpider):
    name = 'solidhouse'
    start_urls = ['https://www.solidhouse.fi/myytavat-asunnot']

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
            properties_selectors = response.css('#property-list div.property')
            if len(properties_selectors) == 0:
                self.error_messages.append(f'SolidHouse Scraper No Apartment found in Parse Method - {datetime.now()}')
                return

            for property_selector in properties_selectors:
                item = self.get_item(property_selector)

                if 'k' not in item.get('Type', ''):
                    yield item
        except Exception as e:
            self.error_messages.append(f'Solidhouse Scraper Parse Method got error: {e} - {datetime.now()}')
            return ''

    def get_address(self, response):
        try:
            address_row = response.css('p::text').getall()[1]
            address = re.sub(r'\d.*', '', address_row).strip().replace('-', '')

            return address
        except Exception as e:
            self.error_messages.append(f'Solidhouse Scraper get_address Method got error: {e} - {datetime.now()}')
            return ''

    def get_street_number(self, response):
        try:
            address_row = response.css('p::text').getall()[1]
            street_no = ''.join(re.findall(r'\d{1,9}-\d{1,9}', address_row))  # if '-' in result for street no
            if not street_no:
                if '/' in address_row or 'ahp' in address_row:
                    street = address_row.split()[1]
                else:
                    if re.search(r'\d+[A-Za-z]', address_row):  # address = house 44 , street = 44
                        street = ''.join(re.findall(r'(\d[A-Za-z]*)', address_row))  # for street no a 45b
                    else:
                        result = re.search(r'\b(\d+)\b', address_row)  # adress = house 12/ house 13 , result = 12
                        if result:
                            street = result.group(1)
                        else:
                            street = ''.join(re.findall(r'\d+[A-Za-z]*', address_row))  # adress = house 45b 4 result = 45b
            else:
                street = None

            return street_no.replace('/', '') or street.replace('/', '')
        except Exception as e:
            self.error_messages.append(f'Solidhouse Scraper get_street_number Method got error: {e} - {datetime.now()}')
            return ''

    def get_type(self, response):
        return response.css('p + p::text').get('').replace('Vh.', '').strip()

    def get_size(self, response):
        return response.css('h3 + h3::text').get('').strip().replace('m²', '').replace('m', '')

    def get_agency_url(self, response):
        url = 'https://www.solidhouse.fi/'
        return urljoin(url, response.css('a::attr(href)').get(''))

    def get_static(self, response):
        try:
            url = 'https://www.solidhouse.fi/'
            return urlparse(url).netloc.split('.')[1]
        except Exception as e:
            self.error_messages.append(f'Solidhouse Scraper get_static Method got error: {e} - {datetime.now()}')
            return ''
