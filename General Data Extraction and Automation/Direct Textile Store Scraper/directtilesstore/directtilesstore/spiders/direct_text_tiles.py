import os
import json
import re
from collections import OrderedDict
from datetime import datetime
from math import ceil
from urllib.parse import urljoin

from scrapy import Spider, Request, signals


class DirectTextTilesSpider(Spider):
    name = "direct_text_tiles"
    start_urls = ["https://directtextilestore.com/brands"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.brands = []
        self.brand_name = ''
        self.items_scraped_count = 0
        self.total_brands_count = 0
        self.total_products = 0   # Brand Found Total Products at pagination
        self.current_scraped_item = []

        self.fields = ['SKU', 'Type', 'Size', 'Color', 'Options', 'Price Per Each', 'Full Price', 'Stock Status',
                       'Brand',
                       'Category', 'Sub Category', 'Material', 'Title', 'Description', 'Images', 'Url']

        self.current_dt = datetime.now().strftime("%d%m%Y%H%M%S")
        self.output_directory = f'output/{self.current_dt}'

        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']
        self.logs_filename = f'logs/logs {self.current_dt}.txt'

    def parse(self, response, **kwargs):
        """
        Parse the initial page to extract brand names and URLs.
        """
        brands = response.css('.brandGrid li.brand')
        for brand in brands:
            name = brand.css('.card-title a::text').get('').replace('|', '').replace('/', '').strip()
            url_string = brand.css('.card-title a::attr(href)').get('')
            url = url_string.split('.com/')[1]

            brand_info = {
                'name': name,
                'url': url
            }

            self.brands.append(brand_info)

        self.total_brands_count = len(self.brands)

        next_page = response.css('.pagination-item--next a::attr(href)').get('')
        if next_page:
            yield Request(url=urljoin(response.url, next_page))
            return

        self.mandatory_logs.append(f'Total Brands Exist: {self.total_brands_count}')

    def parse_brand_categories_pagination(self, response):
        brand_url = response.meta.get('brand_url', '')
        try:
            data = response.json()
        except json.decoder.JSONDecodeError as e:
            data = {}
            self.error.append(f'Parse error for Json Response in brand :"{self.brand_name}" , Url :"{response.url}"')
            return

        try:
            self.total_products = data.get('totalItems', 0)

            # if wrong url is called
            if response.meta.get('cat_req', '') and self.total_products >= 2000:
                return

            if not self.total_products and not response.meta.get('cat_req', ''):
                response.meta['cat_req'] = '1'
                url = f'https://searchserverapi.com/getresults?api_key=7d3I0U1p0q&q=&sortBy=title&sortOrder=asc&startIndex=0&maxResults=250&items=true&pageStartIndex=0&facets=true&category=https://directtextilestore.com/{brand_url}&output=jsonp'
                yield Request(url=url, callback=self.parse_brand_categories_pagination, meta=response.meta)
                return

            if not self.total_products:
                print(f'No Product Found:   https://directtextilestore.com/{brand_url}')
                self.mandatory_logs.append(f'No product found in Brand :"{self.brand_name}", Url :https://directtextilestore.com/{brand_url} ')
                return

            total_pages = ceil(self.total_products / 250)

            for page in range(0, total_pages):
                startIndex = page * 250
                url = f'https://searchserverapi.com/getresults?api_key=7d3I0U1p0q&q=&sortBy=title&sortOrder=asc&startIndex={startIndex}&maxResults=250&items=true&pageStartIndex=0&facets=true&brand_url=/{brand_url}&output=jsonp'
                yield Request(url=url, callback=self.parse_products_details, dont_filter=True)
        except Exception as e:
            self.error.append(f'Error Parsing Brand: "{self.brand_name}" , Url :"{response.url} ')
            return

    def parse_products_details(self, response):
        """
        Parse brand pages to extract categories and all subcategories until the leaf category is reached.
        If there are no categories found, check if it's a product listings page. If yes, send a request for each product.
        If it's not a categories page nor a products page, check if it's a details page of a product. If yes, scrape the details of the product.
        At a time, there will be only one type of page: either a Category or products listings page or a product details page.

        Args:
            response: Scrapy response object.

        Returns:
            None
        """
        try:
            data = response.json()
        except json.decoder.JSONDecodeError as e:
            # Handle JSON decoding error
            print(f"JSON decoding error: {e}")
            data = {}

        products = data.get('items', [])

        for product in products:
            try:
                variants = product.get('bigcommerce_variants', [])
                if not variants:
                    # If no variants, append item directly
                    item = self.extract_product_details(product)
                    # self.items_scraped_count += 1
                    # print(f'Current items scraped: {self.items_scraped_count}')
                    self.current_scraped_item.append(item)
                else:
                    # If variants exist, append item for each variant
                    for variant in variants:
                        item = self.extract_product_details(product)
                        self.process_product_variants(product, variant, item)
                        # self.items_scraped_count += 1
                        # print(f'Current items scraped: {self.items_scraped_count}')
                        self.current_scraped_item.append(item)

                self.items_scraped_count += 1
                print(f'Current items scraped: {self.items_scraped_count}')
                a=1
            except Exception as e:
                # Handle any other exceptions
                self.error.append(f'An error occurred while parsing product: "{response.url}",  details: {e}')
                return

    def extract_product_details(self, product):
        """
        Extract product details from the product data.

        Args:
            product: Dictionary containing product data.

        Returns:
            OrderedDict: Extracted product details.
        """
        item = OrderedDict()
        try:
            category = self.get_value(product, key='category', value='custom_field_afc508f2890ba24361262f0ebdd8d120')
            item['SKU'] = product.get('product_code', '')
            item['Type'] = ''
            item['Size'] = self.get_value(product, key='Size', value='custom_field_f7bd60b75b29d79b660a2859395c1a24')
            item['Color'] = self.get_value(product, key='Color', value='custom_field_f7bd60b75b29d79b660a2859395c1a24')
            item['Options'] = {}
            item['Stock Status'] = 'In Stock' if product.get('price') else 'Out of Stock'
            item['Brand'] = self.brand_name
            item['Category'] = ''.join(category.get('category', '').split('[:ATTR:]')[0:1]) if category else ''
            item['Sub Category'] = ''.join(category.get('category', '').split('[:ATTR:]')[1:2]) if category else ''
            item['Material'] = self.get_value(product, key='Material',
                                              value='custom_field_eeeb53838b3ce6b81ce2f43d43762a10')
            item['Title'] = product.get('title', '')
            item['Description'] = product.get('description', '')
            item['Images'] = product.get('bigcommerce_images', [])
            item['Url'] = product.get('link', '')
            return item
        except Exception as e:
            print('Parse Error Product :', e)
            return item

    def process_product_variants(self, product, variant, item):
        try:
            options = variant.get('options', {})
            color_key = next((key for key in options.keys() if 'color' in key.lower()), None)
            size_key = next((key for key in options.keys() if 'size' in key.lower()), None)

            item['SKU'] = variant.get('sku', '')
            item['Color'] = options.get(color_key, '') if color_key else ''
            item['Size'] = options.get('size', '') or options.get('Size', '') or options.get(size_key, '') if size_key else ''
            item['Material'] = item['Material'].get('Material', '').replace('[:ATTR:]', '') if item['Material'] else ''
            item['Full Price'] = variant.get('price', '')
            item['Price Per Each'] = self.get_unit_price(variant, options)
            item['Options'] = options
            item['Url'] = product.get('link', '')
            return item
        except Exception as e:
            print('Error Variants Parse :', e)
            return item

    def get_unit_price(self, variant, options):
        # Check if variant and options are not None
        if variant is None or options is None:
            return ''

        price = variant.get('price', '')

        if options:
            try:
                size_string = options.get('CHOOSE PACK SIZE', '') or options.get('Choose Pack Size', '')
                pack_size_match = re.search(r'\d+', size_string)
                if pack_size_match:
                    pack_size = int(pack_size_match.group(0))
                    if pack_size != 0:
                        price = float(price) / pack_size
                        price = "{:.2f}".format(price)
            except (TypeError, ValueError, IndexError):
                pass

        return price

    def get_value(self, product, key, value):
        result_dict = {}

        try:
            custom_fields = product.get('bigcommerce_custom_fields', {})
            product_value = custom_fields.get(value, '')

            if product_value:
                result_dict[key] = product_value
        except Exception as e:
            print(f"An error occurred while getting value for key '{key}': {e}")

        return result_dict

    def write_items_to_json(self, brand_name):
        """
        Write items to JSON file.
        """
        os.makedirs(self.output_directory, exist_ok=True)

        output_file = os.path.join(self.output_directory, f'{brand_name}.json')
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                for item in self.current_scraped_item:
                    fields = {field: item.get(field, '') for field in self.fields}
                    file.write(json.dumps(fields, ensure_ascii=False) + '\n')

        except Exception as e:
            self.error.append(f'Error occurred while writing items to JSON file: "{output_file}", Error: {e}')

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(DirectTextTilesSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """

        print(f'\n\n{len(self.brands)}/{self.total_brands_count} Brands left to Scrape\n\n')

        if self.current_scraped_item:
            print(f'\n\nTotal {self.items_scraped_count}/ {self.total_products} items scraped from Brand {self.brand_name}')
            self.mandatory_logs.append(f'\n\nTotal {self.items_scraped_count}/ {self.total_products} items scraped from Brand {self.brand_name}')
            self.write_items_to_json(self.brand_name)
            self.brand_name = ''
            self.current_scraped_item = []
            self.items_scraped_count = 0
            self.total_products = 0

        if self.brands:
            brand = self.brands.pop(0)
            self.brand_name = brand.get('name', '')
            brand_url = brand.get('url', '')

            url = f'https://searchserverapi.com/getresults?api_key=7d3I0U1p0q&q=&sortBy=title&sortOrder=asc&startIndex=0&maxResults=250&items=true&pageStartIndex=0&facets=true&brand_url=/{brand_url}&output=jsonp'

            req = Request(url=url,
                          callback=self.parse_brand_categories_pagination,
                          meta={'handle_httpstatus_all': True, 'brand_url': brand_url})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"\n\n')
        spider.mandatory_logs.append(f'Spider Error:: \n')
        spider.mandatory_logs.extend(spider.error)
        spider.write_logs()

