import re
from datetime import datetime

from scrapy import Request
from .base import BaseSpider


class HuoneistokeskusSpider(BaseSpider):
    name = 'huoneistokeskus'

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'LOG_LEVEL': 'WARNING',
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
        filename = 'huoneistokeskus_urls.txt'
        self.urls_from_input_file = self.read_input_urls(filename=filename)

    def start_requests(self):
        for url in self.urls_from_input_file:
            api_url = 'https://huoneistokeskus.fi/wp-json/v1/realtysearch/7'
            print('request url :', url)
            yield Request(url=api_url, callback=self.parse, dont_filter=True, meta={'requested_url': url})

    def parse(self, response, **kwargs):
        try:
            properties_selectors = response.css('.search-result-list  .list-link')
        except:
            properties_selectors = response.json().get('items', [{}])

        url = response.meta.get('requested_url', '')

        # location Filter
        if 'haku' and 'postinumero' in url:
            postinumero = url.split('postinumero:')[1].split('/')[0].split(',')
            properties = [x for x in properties_selectors if
                          x.get('filters', {}).get('location', {}).get('postinumero', '') in postinumero]

        elif 'haku' in url:
            property_type = url.split('haku/')[1].split(':')[0]
            property_location = url.split('haku/')[1].split(':')[1].split('?')[0].rstrip('/')
            if ';' in property_location:
                property_location = url.split('haku/')[1].split(':')[1].split('?')[0].split(';')[0].rstrip('/')

            properties = [x for x in properties_selectors if x.get('filters', {}).get('location', {}).get(property_type) == property_location]

        # zip codes filter
        elif 'postinumero' in url:
            postinumero = url.split('postinumero:')[1].split('/')[0].split(',')
            properties = [x for x in properties_selectors if
                          x.get('filters', {}).get('location', {}).get('postinumero', '') in postinumero]
        else:
            properties = properties_selectors

        if len(properties) == 0:
            self.error_messages.append(f'Huoneistokeskus Scraper No Apartment found in Parse Method - {datetime.now()}')

        for property_selector in properties:
            item = self.get_item(property_selector)
            yield item

    def get_address(self, response):
        try:
            string = response.css('.title::text').get('').split(',')[0]
        except AttributeError:
            string = response.get('title', '') or response.get('location', '')

        if string:
            address = re.match(r'^.*?(?=\d)', string).group(0) if re.search(r'\d', string) else string

            return address.replace('-', '').strip()
        else:
            return ''

    def get_street_number(self, response):
        try:
            address = response.css('.title::text').get('').split(',')[0]
        except AttributeError:
            address = response.get('title', '')

        try:
            if '-' in address:
                street_number = ''.join(re.findall(r'\d+-\d+', address))
            else:
                street_number = ''.join(re.findall(r'\d', address))
        except Exception as e:
            street_number = ''
            self.error_messages.append(f'Habite Scraper get_street_number Method got error: {e} - {datetime.now()}')

        return street_number

    def get_type(self, response):
        try:
            price = response.css('.right.price::text').get('')
        except:
            price = response.get('price', '')

        return price

    def get_rooms(self, response):
        try:
            rooms = response.css('.room-specs::text').re_first(r'(\d+)s*h') or response.css(
                '.room-specs::text').re_first(r'(\d+)s*')
        except:
            rooms = re.sub(r'\D', '', response.get('roomcount', ''))

        return rooms

    def get_size(self, response):
        try:
            size = response.css('.left::text ').get('').strip().replace('m²', '').replace('m', '')
        except:
            size = response.get('sort', {}).get('size', 0)

        return size if size != 0 else ''

    def get_agency_url(self, response):
        try:
            url = response.css('.list-link::attr(href)').get('')
        except:
            url = response.get('link', '').strip()

        return url if url else ''

    def get_static(self, response):
        return 'huoneistokeskus'

    def get_headers(self, url):
        headers = {
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Referer': f'{url}',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
        }

        return headers
