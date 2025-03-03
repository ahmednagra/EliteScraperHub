import copy
import json
import os
import re
from collections import OrderedDict
from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

import requests
from scrapy import Spider, Request, signals, Selector


class AshSpider(Spider):
    name = "old_ash"
    base_url = "https://www.ahscompany.com/"
    start_urls = ["https://www.ahscompany.com/"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
    }

    headers = {
        'authority': 'www.ahscompany.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.brands = []
        self.items_scraped_count = 0
        self.total_brands_count = 0

        self.current_scraped_item = []
        self.brand_name = ''
        self.category_name = ''

        self.fields = ['SKU', 'Type', 'Size', 'Color', 'Options', 'Price Per Each', 'Category', 'Sub Category',
                       'Material', 'Title', 'Description', 'Images', 'Url']
        self.output_directory = f'output/{datetime.now().strftime("%d%m%Y%H%M%S")}'

    # def start_requests(self) -> Iterable[Request]:
    #     yield Request(
    #         'https://www.ahscompany.com/Cotton-Craft-St-Lucia-Pool-Towels-35x70-100-Ring-Spun-Cotton-15LbsDz-2-Dz-Per-Case-Price-Per-Dz_p_27561.html',
    #         callback=self.parse_product_details)

    def parse(self, response, **kwargs):
        """
        Parse the initial page to extract brand names and URLs.
        """
        brands = response.css('#catMenu2 .cat-list li')[15:]
        for brand in brands:
            name = brand.css('a ::text').get('')
            url = urljoin(self.base_url, brand.css('a::attr(href)').get(''))

            brand_info = {
                'name': name,
                'url': url
            }

            self.brands.append(brand_info)

        self.total_brands_count = len(self.brands)

    def parse_brand_categories(self, response):
        """
        - Parse brand pages to extract categories and all sub categories until the leaf category reached.
        - If there is no categories found, check if its a products listings page, if yes, send request for each that product
        - if its not a categories page nor a products page, check if its a details page of product, if yes, scrape the details of the product
        - At a time, there will be only one type of page. Either Category or products listings page or product details page
        """
        try:
            # If there are categories, parse them until the products listings page shows
            # Request on categories until the products listings page appears
            brand_categories = response.css('.sub-categories-format .sub-categories')

            for category in brand_categories:
                # Check and update meta information
                if not response.meta.get('category', ''):
                    self.category_name = category.css('.name::text').get('')
                    response.meta['category'] = self.category_name

                # Extract the URL for the category
                category_url = category.css('a::attr(href)').get('')
                if not category_url:
                    continue

                category_url = urljoin(self.base_url, category_url)
                print('Category Url :', category_url)
                yield Request(url=category_url, callback=self.parse_brand_categories,
                              headers=self.headers, meta=response.meta)

        except Exception as e:
            print(f'Error parsing category: {response.url}')
            self.logger.error(f'Error parsing category: {response.url} and Error : {e}')

        try:
            # Check if there are products on the page, then send request for each that product
            if response.css('#itemsBlock'):
                products = response.css('#itemsBlock .productBlockContainer .product-item') or response.css(
                    '#itemsBlock .productBlockContainer')
                for product in products:
                    product_url = product.css('.name a::attr(href)').get('')
                    if not product_url:
                        continue

                    url = urljoin(self.base_url, product_url)
                    print('Request url of detail page :', url)
                    yield Request(url, callback=self.parse_product_details, meta=response.meta)

            # Check if the detailed page of a product, then scrape the details from the parse_product_details method
            if not brand_categories and not response.css('#itemsBlock'):
                request = requests.get(response.url, headers=self.headers)
                if request.status_code != 200:
                    res = requests.get(response.url, headers=self.headers)
                    html = Selector(text=res.text)
                    yield from self.parse_product_details(response=html)
                    return
                else:
                    html = Selector(text=request.text)
                    yield from self.parse_product_details(response=html)
                    return

        except Exception as e:
            return

    def parse_product_details(self, response):
        """
        Parse product detail pages to extract product information.
        """
        try:
            title = response.css('h1[itemprop="name"] ::text').get('')
            pid = response.css('input[name="item_id"]::attr(value)').get('')
            description = response.css('[itemprop="description"]  ::text').getall()
            price = float(response.css('meta[itemprop="price"]::attr(content)').get(''))
            sku = response.css('#product_id ::text').re_first(r'\s(.*)$')
            price_per_unit = self.get_price_per_unit(title, price)

            if not title and not pid:
                return

            item = OrderedDict()
            item['SKU'] = sku
            item['Type'] = self.get_value(response, 'Type')
            item['Size'] = self.get_value(response, 'Size')
            item['Options'] = {}
            item['Price Per Each'] = str(round(float(price_per_unit), 2)) if price_per_unit else ''
            item['Category'] = ''.join(response.css('.breadcrumbs a ::text').getall()[2:3]) or self.category_name
            item['Sub Category'] = ', '.join(response.css('.breadcrumbs a ::text').getall()[3:])
            item['Material'] = self.get_value(response, 'Material')
            item['Title'] = title
            item['Description'] = '\n'.join(
                [item.strip() for item in description if item.strip()]) if description else ''
            item['Images'] = self.get_product_images(response)
            item['Url'] = response.css('link[rel="canonical"] ::attr(href)').get('')

            variants = response.css('#divOptionsBlock option')

            if not variants:
                self.items_scraped_count += 1
                print(f'Current items scraped: {self.items_scraped_count}')

                self.current_scraped_item.append(item)

                return

            # Parse Variants

            first_variant_group = response.css('#divOptionsBlock .container > :nth-child(1) option')[1:]
            first_variant_label = response.css('#divOptionsBlock .container > :nth-child(1) option::text').get(
                '').strip()
            second_variant_group = response.css('#divOptionsBlock .container > :nth-child(3) option')[1:]
            second_variant_label = response.css('#divOptionsBlock .container > :nth-child(3) option::text').get(
                '').strip()
            third_variant_group = response.css('#divOptionsBlock .container > :nth-child(5) option')[1:] or ''
            third_variant_label = response.css('#divOptionsBlock .container > :nth-child(5) option::text').get(
                '').strip() or ''

            fourth_variant_group = response.css('#divOptionsBlock .container > :nth-child(7) option')[1:] or ''
            fourth_variant_label = response.css('#divOptionsBlock .container > :nth-child(7) option::text').get(
                '').strip() or ''

            # if there is one single type of variant
            if len(response.css('#divOptionsBlock .dropdown-format').getall()) == 1:
                variants = response.css('#divOptionsBlock option')[1:]
                label = response.css('#divOptionsBlock option::text').get('').strip()
                self.get_single_variant_group(variants, label, item, response, price_per_unit, sku)
                return

            # If there are 2 types of variants in dropdowns selection
            elif len(response.css('#divOptionsBlock .dropdown-format').getall()) == 2:
                # Check if third variant group is empty
                if not third_variant_group:
                    # Iterate over first and second variant groups only
                    self.get_double_variants_group(response, first_variant_group, first_variant_label,
                                                   second_variant_group, second_variant_label, price_per_unit, sku,
                                                   item)
                    return

            # If there are 3 types of variants in dropdowns selection
            elif len(response.css('#divOptionsBlock .dropdown-format').getall()) == 3:
                self.get_triple_variants_group(response, first_variant_group, first_variant_label,
                                               second_variant_group, second_variant_label, third_variant_group,
                                               third_variant_label, price_per_unit, sku, item)
                return

            else:
                self.get_fourth_variants_group(response, first_variant_group, first_variant_label,
                                               second_variant_group, second_variant_label, third_variant_group,
                                               third_variant_label, price_per_unit, sku, item,
                                               fourth_variant_group, fourth_variant_label)

        except Exception as e:
            print(f'Error parsing product detail: {response.url}')
            self.logger.error(f'Error parsing product detail: {response.url} and Error : {e}')
            return

    def get_value(self, response, key):
        elements = response.css(f'.breadcrumbsBlock ul li:contains("{key}") ::text').getall()
        if elements:
            return elements[-1]
        else:
            return ''

    def get_product_images(self, response):
        images = response.css('.slides .prod-thumb a::attr(href)').getall() or []
        images = images or response.css('.main-image a::attr(href)').getall() or []
        return images

    def get_variant_price(self, response, variant, price_per_unit, sku, label):
        # Assume base_price is the price provided by the variant
        # First, let's correct the base price parsing logic if not done already
        variant_value = variant.css('::attr(value)').get('')
        price_adjustment = response.css(f'.container input[name="price_{variant_value}"]::attr(value)').get('')
        variant_name = variant.css('::text').get('').strip()

        if not variant_value:
            info = {
                'price': str(price_per_unit),
                'sku': sku,
                'variant_name': {label: variant_name}
            }
            return info

        if float(price_adjustment) == 0 and price_adjustment is None:
            adjusted_price = price_per_unit
        else:
            adjusted_price = float(price_per_unit) + float(price_adjustment)

        script_tag = response.css(f'script[type="text/javascript"]:contains("{variant_value}")').get('')
        if script_tag:
            p_number = script_tag.split(variant_value)[1].split('=')[1].split(';')[0].strip().replace("'", "") or ''
            p_number = re.findall(r'\s(.+)', p_number)
            if p_number:
                p_number = p_number[0]
            if not p_number:
                p_number = sku
        else:
            p_number = sku

        info = {
            'price': str(adjusted_price),
            'sku': p_number,
            'variant_name': {label: variant_name}
        }
        return info

    def get_variant_group(self, response, first_variant, first_variant_label, second_variant, second_variant_label,
                          price, sku, third_variant, third_variant_label, fourth_variant, fourth_variant_label):

        f_variant = self.get_variant_price(response, first_variant, price, sku, first_variant_label)
        sec_variant = self.get_variant_price(response, second_variant, price, sku, second_variant_label)

        if third_variant:
            thi_variant = self.get_variant_price(response, third_variant, price, sku, third_variant_label)
        else:
            thi_variant = {}

        if fourth_variant:
            forth_variant = self.get_variant_price(response, fourth_variant, price, sku, fourth_variant_label)
        else:
            forth_variant = {}

        p_number = f_variant.get('sku', '')
        f_variant_price = f_variant.get('price', '')

        info = {
            'sku': p_number,
            'price': str(f_variant_price),
            'variant_name': {
                **f_variant.get('variant_name', {}),
                **sec_variant.get('variant_name', {}),
                **thi_variant.get('variant_name', {}),
                **forth_variant.get('variant_name', {})}
        }
        return info

    def write_items_to_json(self, brand_name):
        """
        Write items to JSON file.
        """
        # output_directory = 'output'
        os.makedirs(self.output_directory, exist_ok=True)
        output_file = os.path.join(self.output_directory, f'{brand_name}.json')

        try:
            with open(output_file, 'w') as file:
                for item in self.current_scraped_item:
                    fields = {field: item.get(field, '') for field in self.fields}
                    file.write(json.dumps(fields, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"Error occurred while writing items to JSON file: {e}")

    def get_price_per_unit(self, title, price):
        # Default values
        price_per_unit = price
        items_per_case = 1
        title_lower = title.lower()

        # Check if the title indicates price per dozen
        if "price per dz" in title_lower or "per dz" in title_lower:
            price_per_unit = price / 12
        # Check if the title indicates price per case
        elif "price per case" in title_lower or "per case" in title_lower:
            # Extract the number of items per case if specified, default to 1 if not
            match = re.search(r'(\d+)\s*per case', title_lower)
            if match:
                items_per_case = int(match.group(1))
            price_per_unit = price / items_per_case
        # Check if the title indicates price per each
        elif "price per each" in title_lower or "per each" in title_lower:
            price_per_unit = price  # Already per each, no adjustment needed

        return price_per_unit

    def get_single_variant_group(self, variants, label, item, response, price_per_unit, sku):
        """
        Process single variant group and add variant items to the scraped items list.
        """
        try:
            for variant in variants:
                variant_item = copy.deepcopy(item)
                options = self.get_variant_price(response, variant, price_per_unit, sku, label)
                price = options.get('price', '')
                variant_item['Price Per Each'] = str(round(float(price), 2)) if price else ''
                p_number = options.get('sku', '')
                variant_item['SKU'] = p_number.replace("'", '').strip() if p_number else ''
                variant_item['Options'] = options.get('variant_name', '')
                variant_item['Color'] = options.get('variant_name', '').get('Color Selection', '') or options.get(
                    'variant_name', '').get('Carpet Color Selection', '')
                self.items_scraped_count += 1
                print(f'Current items scraped: {self.items_scraped_count}')
                self.current_scraped_item.append(variant_item)
        except Exception as e:
            self.logger.error(f'Error processing single variant group: {e}')
            print(f'Error processing single variant group: {e}')

    def get_double_variants_group(self, response, first_variant_group, first_variant_label,
                                  second_variant_group, second_variant_label, price_per_unit, sku, item):
        """
            Process double variants group and add variant items to the scraped items list.
            """
        try:
            for first_variant in first_variant_group:
                for second_variant in second_variant_group:
                    variant_item = copy.deepcopy(item)
                    options = self.get_variant_group(response, first_variant, first_variant_label,
                                                     second_variant, second_variant_label, price_per_unit, sku,
                                                     third_variant='', third_variant_label='',
                                                     fourth_variant='', fourth_variant_label='')

                    price = options.get('price', '')
                    variant_item['Price Per Each'] = str(round(float(price), 2)) if price else ''
                    variant_item['SKU'] = options.get('sku', '')
                    variant_item['Options'] = options.get('variant_name', '')
                    # Convert 'Options' to dictionary if it's a string
                    variant_name_dict = json.loads(variant_item['Options']) if isinstance(
                        variant_item['Options'], str) else variant_item['Options']
                    # Access the color option from the variant name dictionary
                    variant_item['Color'] = variant_name_dict.get('Color Selection', '')
                    self.items_scraped_count += 1
                    print(f'Current items scraped: {self.items_scraped_count}')
                    self.current_scraped_item.append(variant_item)
        except Exception as e:
            self.logger.error(f'Error processing Double variant group: {e}')
            print(f'Error processing Double variant group: {e}')

    def get_triple_variants_group(self, response, first_variant_group, first_variant_label,
                                  second_variant_group, second_variant_label, third_variant_group,
                                  third_variant_label, price_per_unit, sku, item):
        """
            Process triple variants group and add variant items to the scraped items list.
            """
        try:
            for first_variant in first_variant_group:
                for second_variant in second_variant_group:
                    for third_variant in third_variant_group:
                        variant_item = copy.deepcopy(item)
                        options = self.get_variant_group(response, first_variant, first_variant_label,
                                                         second_variant, second_variant_label,
                                                         price_per_unit, sku,
                                                         third_variant, third_variant_label,
                                                         fourth_variant='', fourth_variant_label='')

                        price = options.get('price', '')
                        variant_item['Price Per Each'] = str(round(float(price), 2)) if price else ''
                        variant_item['SKU'] = options.get('sku', '')
                        variant_item['Options'] = options.get('variant_name', '')
                        # Convert 'Options' to dictionary if it's a string
                        variant_name_dict = json.loads(variant_item['Options']) if isinstance(
                            variant_item['Options'], str) else variant_item['Options']
                        # Access the color option from the variant name dictionary
                        variant_item['Color'] = variant_name_dict.get('Color Selection', '')
                        self.items_scraped_count += 1
                        print(f'Current items scraped: {self.items_scraped_count}')
                        self.current_scraped_item.append(variant_item)
        except Exception as e:
            self.logger.error(f'Error processing Triple variant group: {e}')
            print(f'Error processing Triple variant group: {e}')

    def get_fourth_variants_group(self, response, first_variant_group, first_variant_label,
                                  second_variant_group, second_variant_label, third_variant_group,
                                  third_variant_label, price_per_unit, sku, item,
                                  fourth_variant_group, fourth_variant_label):
        """
            Process triple variants group and add variant items to the scraped items list.
            """
        try:
            for first_variant in first_variant_group:
                for second_variant in second_variant_group:
                    for third_variant in third_variant_group:
                        for fourth_variant in fourth_variant_group:
                            variant_item = copy.deepcopy(item)
                            options = self.get_variant_group(response, first_variant, first_variant_label,
                                                             second_variant, second_variant_label,
                                                             price_per_unit, sku, third_variant, third_variant_label,
                                                             fourth_variant, fourth_variant_label)

                            price = options.get('price', '')
                            variant_item['Price Per Each'] = str(round(float(price), 2)) if price else ''
                            variant_item['SKU'] = options.get('sku', '')
                            variant_item['Options'] = options.get('variant_name', '')
                            # Convert 'Options' to dictionary if it's a string
                            variant_name_dict = json.loads(variant_item['Options']) if isinstance(
                                variant_item['Options'], str) else variant_item['Options']
                            # Access the color option from the variant name dictionary
                            variant_item['Color'] = variant_name_dict.get('Color Selection', '')
                            self.items_scraped_count += 1
                            print(f'Current items scraped: {self.items_scraped_count}')
                            self.current_scraped_item.append(variant_item)
        except Exception as e:
            self.logger.error(f'Error processing Triple variant group: {e}')
            print(f'Error processing Triple variant group: {e}')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AshSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """

        print(f'\n\n{len(self.brands)}/{self.total_brands_count} Brands left to Scrape\n\n')

        if self.current_scraped_item:
            print(f'\n\nTotal {self.items_scraped_count} items scraped from Brand {self.brand_name}')
            self.write_items_to_json(self.brand_name)
            self.brand_name = ''
            self.category_name = ''
            self.current_scraped_item = []

        if self.brands:
            brand = self.brands.pop(0)
            self.brand_name = brand.get('name', '')
            brand_url = brand.get('url', '')

            req = Request(url=brand_url,
                          callback=self.parse_brand_categories, dont_filter=True,
                          meta={'handle_httpstatus_all': True, 'brand': self.brand_name})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
