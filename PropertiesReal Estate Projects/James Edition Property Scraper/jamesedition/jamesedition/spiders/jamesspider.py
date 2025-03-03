import json
from json import loads
import re
from datetime import datetime
from math import ceil
from urllib.parse import urljoin, unquote

from collections import OrderedDict

import scrapy
from scrapy import Request


class JameSpider(scrapy.Spider):
    name = "jamespider"
    start_urls = ["https://www.jamesedition.com/real_estate/united-arab-emirates"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/James Edition Properties {datetime.now().strftime("%d%m%Y%H%M%S")}.xlsx': {
                'format': 'xlsx',
                'fields': ['Price', 'No. of Bedrooms', 'No. of Bathrooms', 'Size (sqm)', 'Property Type', 'Agent Name',
                           'Agency Name', 'Breadcrumb', 'Listing Date', 'Location',
                           'Property Title', 'Property URL'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize variables to keep track of scraped items
        self.current_scrapped_items_urls = []

        self.config = self.read_config_file()

        # Set up proxy key and usage flag
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('jamesedition', {}).get('use_proxy', '')

    def start_requests(self):
        price_ranges = [
            (0, 40000050), (40000050, 60000050), (60000050, 80000050), (80000050, 100000050),  # 0 M to 1 M
            (100000050, 150000050), (150000050, 200000050), (200000050, 250000050),  # 10 M to 25 M
            (250000050, 300000050), (300000050, 520000050), (520000050, 800000050),  # 25 M to 80 M
            (800000050, 1500000050), (1500000050, 4500000050), (4500000050, 110000000050)  # 80 M 110 M
        ]

        for min_price, max_price in price_ranges:
            price_filter_url = f"https://www.jamesedition.com/real_estate/united-arab-emirates?eur_price_cents_from={min_price}&eur_price_cents_to={max_price}"
            yield Request(url=price_filter_url, callback=self.pagination, meta={'min_price': min_price, 'max_price': max_price})

    def pagination(self, response):
        script_tag = response.css('script#exposed-vars ::text').re_first(r'JEParams,\s*(\{.*\})')
        data = loads(script_tag) if script_tag else ''
        total_products = data.get('searchPageParams', {}).get('numberOfListings', 0)

        if total_products == 0:
            return

        total_pages = ceil(total_products / 140)

        for page_number in range(total_pages):
            page_no = page_number + 1
            filter_type = unquote(response.url).split('url=')[1].replace('%5B%5D', '[]').split('united-arab-emirates')[1]
            price_url = f'https://www.jamesedition.com/real_estate/listings.json{filter_type}&page=1&page={page_no}&brand_or_place=united-arab-emirates'
            yield Request(url=price_url, callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            products_dict = response.json()
        except:
            products_dict = []
            return

        for product in products_dict:
            product_path = product.get('path', '') or f"https://www.jamesedition.com/real_estate/united-arab-emirates/{product.get('id')}"
            url = urljoin(self.start_urls[0], product_path)

            if url not in self.current_scrapped_items_urls:
                meta = response.meta.copy()
                meta['product_info'] = product
                self.current_scrapped_items_urls.append(url)
                yield Request(url=url, callback=self.parse_property_detail, meta=meta)

            else:
                pass

    def parse_property_detail(self, response):
        item = OrderedDict()

        product_info = response.meta.get('product_info', {})
        script_selector = response.css('script[type="application/ld+json"]:contains("offers") ::text').get('')
        product_dict = json.loads(script_selector) if script_selector else ''

        listed_date = response.css('.je2-listing-info__insights li:contains("Listed") ::text').getall()
        listed_date = ''.join([value.strip() for value in listed_date if value.strip()]).replace('Listed', '')

        path = product_info.get('path', '')
        url = urljoin(self.start_urls[0], path) if path else ''

        breadcrumb = [value.strip() for value in response.css('.je3-breadcrumbs ol li ::text').getall() if
                      value.strip()]

        item['Price'] = ','.join(re.findall(r'\d+', response.css('.je2-button__tooltip ::text').get('')))
        item['No. of Bedrooms'] = product_info.get('bedrooms', '')
        item['No. of Bathrooms'] = product_info.get('bathrooms', '')
        item['Size (sqm)'] = self.get_property_size(response, product_info)
        item['Property Type'] = (response.css('.je2-listing-about-building li:contains(type) p::text').get('').strip()
                                 or response.meta.get('property_type').title())
        item['Agent Name'] = response.css('p[aria-label="Agent name"] ::text').get('').strip()
        item['Agency Name'] = response.css('a[data-type="internal_office_link"] span::text').get(
            '') or product_dict.get('offers', {}).get('seller', {}).get('name', '')
        item['Breadcrumb'] = ' ,'.join(breadcrumb)
        item['Listing Date'] = listed_date
        item['Location'] = response.css('.je2-listing-map.js-listing-map > span ::text').get('').strip()
        item['Property Title'] = product_info.get('headline', '') or product_dict.get('name', '')
        item['Property URL'] = url or product_dict.get('url', '')

        yield item

    def read_config_file(self):
        file_path = 'input/config.json'
        config = {}

        try:
            with open(file_path, mode='r') as json_file:
                data = json.load(json_file)
                config.update(data)

            return config

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            return {}
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {}

    def get_property_size(self, response, product_info):
        # Extract living area from product_info
        living_area = product_info.get('living_area', '')

        # Extract size in square feet from living area
        size_sqm = ''
        if living_area:
            try:
                size_feet = re.findall(r'\d+', living_area)[0]
                size_sqm = ceil(int(size_feet) * 0.092903)  # Convert square feet to square meters
            except IndexError:
                print("Error: Unable to extract size from living area.")

        # Extract size from response
        size_from_response = ''
        try:
            size_from_response = ''.join(
                [value.strip() for value in response.css('.je2-listing-info__specs li::text').getall() if
                 'sqm' in value and 'lot' not in value and '€' not in value and '$' not in value]).replace('sqm', '')
        except AttributeError:
            print("Error: Unable to extract size from response.")

        # Choose property size based on availability of data
        property_size = size_from_response if size_from_response else size_sqm

        return property_size