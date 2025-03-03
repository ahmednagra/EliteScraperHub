import os
import json
import random
from collections import OrderedDict
from datetime import datetime

import requests
from scrapy import Spider, Request


class ChemistSpider(Spider):
    name = "chemist"
    start_urls = ["https://www.directchemistoutlet.com.au"]
    current_dt = datetime.now().strftime("%d%m%Y%H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 1,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/Direct Chemist Outlet Products {current_dt}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Item ID', 'Product ID', 'Category',
                           'Sub Category', 'Sub Sub Category',  # for test
                           'Brand Name', 'Product Name',
                           'Regular Price', 'Special Price', 'Current Price', 'Short Description',
                           'Long Description', 'Product Information', 'Directions', 'Ingredients',
                           'SKU', 'Image URLs'],
            }
        }
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items_scraped_count = 0
        self.total_products = 0  # Category Found Total Products at pagination
        self.current_scraped_item = []
        self.duplicates_product_count = 0

        self.x_algolia_application_id = ''
        self.x_algolia_api_key = ''

        self.category_urls = self.get_category_urls_from_file('input/categories urls.txt')

        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']
        self.logs_filename = f'logs/logs {self.current_dt}.txt'

    def start_requests(self):
        # If user Provides Urls in the input file
        if self.category_urls:
            for url in self.category_urls:
                yield Request(url=url, headers=self.headers, callback=self.parse, meta={'input_urls': True, 'handle_httpstatus_all': True})
        else:
            yield Request(url='https://www.directchemistoutlet.com.au/categories', headers=self.headers,
                          callback=self.parse)

    def parse(self, response, **kwargs):
        """ Get the Api key and Application id for algolia Api """
        try:
            api_config = json.loads(response.css('script:contains("window.algoliaConfig")::text').re_first(r'= (.*);'))
        except json.JSONDecodeError:
            api_config = {}

        if api_config:
            self.x_algolia_application_id = api_config.get('applicationId', '')
            self.x_algolia_api_key = api_config.get('apiKey', '')
        else:
            self.x_algolia_api_key = 'ZmU0NTdkNWI3M2YzOTk5NzJkMWZkOTQ0OGYxZGU2NDIwODUxMjVlMmM1YjM5ODhhOTU0ZThiOTYxZTdmOTk1YnRhZ0ZpbHRlcnM9',
            self.x_algolia_application_id = '92FHP0N82N'

        # For Api request for the user Input Urls Request
        if response.meta.get('input_urls'):
            requested_category = ''.join(response.css('.breadcrumbs ul li.home + li ::text').getall()).strip()
            categories_selector = response.css('#mobile-menu-1-1 .level1') or []  # Categories from Header Menu dropdown
            for category in categories_selector:
                main_cat_name = category.css('.level1 > a::text').get('').strip()
                if requested_category == main_cat_name:
                    sub_categories = category.css('ul .level3 a::attr(href)').getall() or category.css(
                        'ul .level2 a::attr(href)').getall()
                    sub_categories = [sub_cat.rstrip('/').split('/')[-1].replace('.html', '') for sub_cat in sub_categories]

                    for sub_cat in sub_categories:
                        sub_cat = sub_cat.strip()
                        print(f'Category Name :{main_cat_name} , Sub Category :{sub_cat}')

                        data = self.get_formdata(sub_cat.strip())

                        yield Request(
                            url='https://92fhp0n82n-1.algolianet.com/1/indexes/*/queries',
                            body=json.dumps(data),
                            callback=self.parse_category,
                            method='POST',
                            headers=self.get_algolia_headers(),
                            meta={'category_name': main_cat_name, 'sub_category': sub_cat,
                                  'handle_httpstatus_all': True, 'dont_merge_cookies': True}
                        )
            # return

            # if Input Url is subCategory URL
            requested_category = ''.join(response.css('.breadcrumbs ul li.home + li ::text').getall()).strip()
            sub_cat = response.url.rstrip('/').split('/')[-1].replace('.html', '').strip()
            print(f'Category Name :{requested_category} , Sub Category :{sub_cat}')

            data = self.get_formdata(sub_cat.strip())
            yield Request(
                url='https://92fhp0n82n-1.algolianet.com/1/indexes/*/queries',
                body=json.dumps(data),
                callback=self.parse_category,
                method='POST',
                headers=self.get_algolia_headers(),
                meta={'category_name': requested_category, 'sub_category': sub_cat,
                      'handle_httpstatus_all': True, 'dont_merge_cookies': True}
            )

        else:
            # if No Input Url Is provided
            categories_selector = response.css('#mobile-menu-1-1 .level1') or []  # Categories from Header Menu dropdown
            for category in categories_selector:
                main_cat_name = category.css('.level1 > a::text').get('').strip()
                sub_categories = category.css('ul .level3 a::attr(href)').getall() or category.css(
                    'ul .level2 a::attr(href)').getall()
                sub_categories = [sub_cat.rstrip('/').split('/')[-1].replace('.html', '') for sub_cat in sub_categories]

                for sub_cat in sub_categories:
                    sub_cat = sub_cat.strip()
                    print(f'Category Name :{main_cat_name} , Sub Category :{sub_cat}')

                    data = self.get_formdata(sub_cat.strip())

                    yield Request(
                        url='https://92fhp0n82n-1.algolianet.com/1/indexes/*/queries',
                        body=json.dumps(data),
                        callback=self.parse_category,
                        method='POST',
                        headers=self.get_algolia_headers(),
                        meta={'category_name': main_cat_name, 'sub_category': sub_cat,
                              'handle_httpstatus_all': True, 'dont_merge_cookies': True}
                    )

    def parse_category(self, response):
        """
        Parses category page response, fetching products and handling pagination.

        Args:
            response (scrapy.Response): The response object from the category page.
        """

        category = response.meta.get('category_name', '')
        sub_category = response.meta.get('sub_category', '')

        try:
            data = response.json().get('results', [{}])[0]
        except json.JSONDecodeError as e:
            self.error.append(f'error parsing json Category {category} and Sub_category {sub_category} Error :{e}')
            data = {}
            return

        total_products = data.get('nbHits', 0)

        products = []

        if total_products >= 1000:
            products = self.get_products_with_brands(response)
            if products:
                self.total_products += int(len(products))
                self.mandatory_logs.append(f'Category "{category}" Sub Category : "{sub_category}" Has total Products "{len(products)}"')
            else:
                products = self.category_products(data, category, sub_category, total_products)
        else:
            products = self.category_products(data, category, sub_category, total_products)

        if not products:
            self.error.append(f'Category "{category}" Sub Category : "{sub_category}" Has total Products "{len(products)}"')

        for product in products:
            try:
                url = product.get('url', '').lower().strip()

                if url not in [item.get('Product URL', '').lower().strip() for item in self.current_scraped_item]:
                    item = OrderedDict()
                    item['Product ID'] = product.get('objectID', '')
                    item['Product Name'] = product.get('name', '')
                    item['Regular Price'] = product.get('price', {}).get('AUD', {}).get('default_original_formated', '')
                    item['Special Price'] = product.get('price', {}).get('AUD', {}).get('default_formated', '')
                    item['Current Price'] = product.get('price', {}).get('AUD', {}).get('default_formated', '')
                    item['SKU'] = product.get('sku', '')
                    # item['Product URL'] = url
                    response.meta['item'] = item
                    yield Request(url=url, callback=self.parse_product_detail, headers=self.headers, meta=response.meta)
                else:
                    self.duplicates_product_count += 1
                    continue

            except Exception as e:
                self.error.append(f'error parsing json Category {category} and Sub_category {sub_category} Error :{e}')

    def parse_product_detail(self, response):
        """
        Parses product detail page response, extracting desired product information.

        Args:
            response (scrapy.Response): The response object from the product detail page.

        Yields:
            dict: A dictionary containing the extracted product information.
        """

        product = response.meta.get('item', {})

        categories = response.css('.breadcrumbs li:not(.product) a::text').getall() or []

        # Extract brand information with error handling
        try:
            script_tags = response.css('script[type="application/ld+json"]::text').getall() or []
            brand_dict = [json.loads(tag) for tag in script_tags if
                          json.loads(tag).get('@type', '').lower() == 'product']
        except json.JSONDecodeError as e:
            brand_dict = []

        item = OrderedDict()
        try:
            item['Product URL'] = response.url
            item['Item ID'] = product.get('Product ID', '')
            item['Product ID'] = product.get('Product ID', '')
            item['Category'] = response.meta.get('category_name', '').title()
            item['Sub Category'] = categories[-1] if categories else ''
            item['Brand Name'] = brand_dict[0].get('brand', {}).get('name', '') if brand_dict else ''
            item['Product Name'] = product.get('Product Name', '')
            item['Regular Price'] = product.get('Regular Price', '')
            item['Special Price'] = product.get('Special Price', '')
            item['Current Price'] = product.get('Current Price', '')
            item['Short Description'] = ''
            item['Long Description'] = ''
            item['Product Information'] = ', '.join(response.css('.product.description .value ::text').getall())
            item['Directions'] = ', '.join(response.css('.product.directions .value ::text').getall())
            item['Ingredients'] = ', '.join(response.css('.product.ingredients .value ::text').getall())
            item['SKU'] = product.get('SKU', '')
            item['Image URLs'] = self.get_product_images(response)

            self.items_scraped_count += 1
            print('Items Scraped :', self.items_scraped_count)
            self.current_scraped_item.append(item)
            yield item
        except:
            self.error.append(f'Unable Item Yield Product Url : {response.url}')
            return

    def get_formdata(self, category):
        data = {
            "requests": [
                {
                    "indexName": "DCO_Live_directchemistoutlet_store_view_products",
                    "params": f"query={category}&hitsPerPage=1000&page=0"
                }
            ],
            "strategy": "none"
        }
        return data

    def get_products_with_brands(self, response):
        sub_category = response.meta.get('sub_category', '')
        data = {}
        if sub_category == 'vital':
            data = '{"requests":[{"indexName":"DCO_Live_directchemistoutlet_store_view_products","params":"facetFilters=%5B%5B%22categories.level2%3ADiet%20%26%20Nutrition%20%2F%2F%2F%20Diet%20%26%20Weight%20Loss%20%2F%2F%2F%20Vita%20Diet%22%5D%5D&facets=%5B%22brand%22%2C%22categories.level0%22%2C%22categories.level1%22%2C%22categories.level2%22%2C%22categories.level3%22%2C%22price.AUD.default%22%5D&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=1000&maxValuesPerFacet=100&numericFilters=%5B%22visibility_catalog%3D1%22%5D&page=0&ruleContexts=%5B%22magento_filters%22%2C%22magento-category-4201%22%5D&tagFilters="}]}'
        if sub_category == 'baby-skincare':
            data = '{"requests":[{"indexName":"DCO_Live_directchemistoutlet_store_view_products","params":"facetFilters=%5B%5B%22categories.level1%3ABaby%20Care%20%2F%2F%2F%20Baby%20Care%22%5D%5D&facets=%5B%22brand%22%2C%22categories.level0%22%2C%22categories.level1%22%2C%22categories.level2%22%2C%22price.AUD.default%22%5D&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=1000&maxValuesPerFacet=100&numericFilters=%5B%22visibility_catalog%3D1%22%5D&page=0&ruleContexts=%5B%22magento_filters%22%2C%22magento-category-4132%22%5D&tagFilters="}]}'

        try:
            req = requests.post(
                'https://92fhp0n82n-dsn.algolia.net/1/indexes/*/queries',
                headers=self.get_algolia_headers(),
                data=data,
            )

            req.raise_for_status()  # Raise an exception for non-2xx status codes

            response_json = req.json()
            products = response_json.get('results', [])[0].get('hits', [])
            return products

        except requests.exceptions.RequestException as e:
            self.error.append(f"Error making Api request for Category '{response.meta.get('category_name', '')}' :sub-category '{sub_category}': {e}")
            return []

    def category_products(self, data, category, sub_category, total_products):
        products = data.get('hits', [{}])
        self.total_products += int(total_products)
        self.mandatory_logs.append(f'Category "{category}" Sub Category : "{sub_category}" Has total Products "{total_products}"')
        return products

    def get_product_images(self, response):
        try:
            data_dict = json.loads(response.css('script:contains("mage/gallery/gallery") ::text').get(''))
        except json.JSONDecodeError as e:
            data_dict = {}

        img_dict = data_dict.get('[data-gallery-role=gallery-placeholder]', {}).get('mage/gallery/gallery', {}).get(
            'data', [{}])
        images_urls = [img.get('full', '') for img in img_dict]
        return images_urls

    def get_category_urls_from_file(self, file_name):
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            return [line.strip() for line in lines]

        except FileNotFoundError:
            return []

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def close(spider, reason):
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"\n\n')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Found Total Products "{spider.total_products}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Scraped Total Products "{spider.items_scraped_count}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Duplicates Products "{spider.duplicates_product_count}"')

        spider.mandatory_logs.append(f'\n\nSpider Error:: \n')
        spider.mandatory_logs.extend(spider.error)

        spider.write_logs()

    def get_algolia_headers(self):
        USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Mobile Safari/537.36',
        ]

        headers = {
            'X-Algolia-API-Key': self.x_algolia_api_key,
            'X-Algolia-Application-Id': self.x_algolia_application_id,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': random.choice(USER_AGENTS),
        }

        return headers
