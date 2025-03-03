import json
import re
from datetime import datetime
from collections import OrderedDict
from urllib.parse import urlencode

from scrapy import Request, Spider, Selector
import requests


class CatchSpider(Spider):
    name = "catch"
    start_urls = ["https://www.catch.com.au"]

    headers = {
        'authority': 'www.catch.com.au',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    custom_settings = {
        # 'LOG_LEVEL': 'ERROR',
        'CONCURRENT_REQUESTS': 3,
        'FEEDS': {
            f'output/Catch Products {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Item ID', 'Product ID', 'Category', 'Brand Name',
                           'Product Name', 'Regular Price', 'Special Price', 'Current Price', 'Short Description',
                           'Long Description', 'Product Information', 'Directions', 'Ingredients',
                           'SKU', 'Image URLs'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Read configuration from file
        self.config = self.read_config_file()

        # Set up proxy key and usage flag
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('catch', {}).get('use_proxy', '')

        # Get search URLs from the configuration
        self.search_urls = self.config.get('catch', {}).get('search_urls', [])

        # Initialize variables to keep track of scraped items
        self.current_scrapped_items = []
        self.items_scrapped = 0

    def start_requests(self):
        if self.search_urls:
            for category_url in self.search_urls:
                url_string = category_url.split('au/')[1].split('?')[0].strip('/').lstrip('/')
                url = f"https://www.catch.com.au/{url_string}/search.json"

                # if url is parent dir then we get response 404
                res = requests.get(url=url)

                if not res:
                    slug = url_string.split('/')[-1]
                    yield Request(url=category_url, callback=self.parse, meta={'slug': slug}, headers=self.headers)
                else:
                    yield from self.pagination(res)
                    # yield Request(url=url, callback=self.pagination, headers=self.headers)
        else:
            yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        slug = response.meta.get('slug', '')
        category_urls = self.get_categories_urls(response, slug)

        for category_url in category_urls:
            if not 'https://www.catch.com.au' in category_url:
                # Add the base URL to the category URL if it's missing
                category_url = f'https://www.catch.com.au{category_url}/search.json'

            if not category_url:
                continue

            yield Request(url=category_url, callback=self.pagination)

    def pagination(self, response):
        try:
            print('pagination response url:', response.url)
            json_data = response.json()
        except json.decoder.JSONDecodeError as json_error:
            json_data = {}
            print(f"Error decoding JSON: {json_error}")
            return

        total_products = json_data.get('payload', {}).get('metadata', {}).get('hits', 0)
        category = json_data.get('payload', {}).get('metadata', {}).get('query', '')
        print(f'Total Products in {category} are: {total_products}')

        if total_products >= 45000:
            # Define price ranges
            price_ranges = [
                (1, 10), (11, 15), (16, 20), (21, 25), (26, 30), (31, 40), (41, 45), (46, 51), (51, 55), (56, 60),
                (61, 65), (66, 70), (70, 150), (150, 500), (500, 1000), (1000, 5000), (5000, 20000), (20000, 100000)
            ]

            # Yield requests for each price range
            for min_price, max_price in price_ranges:
                price_filter = f'?f[price_range:max]={max_price}&f[price_range:min]={min_price}&page=1&limit=1000'
                next_url = f"{response.url.split('.json')[0]}.json" + price_filter
                print('Price Range url :', next_url)
                yield Request(url=self.get_scrapeops_url(next_url), callback=self.pagination)

        else:
            total_pages = total_products // 900 + 1
            for page_no in range(1, total_pages + 1):
                url = f'{response.url}?page={page_no}&limit=1000'
                yield Request(url=self.get_scrapeops_url(url), callback=self.parse_category)

    def parse_category(self, response):
        try:
            json_data = response.json()
        except json.decoder.JSONDecodeError as json_error:
            json_data = {}
            print(f"Error decoding JSON: {json_error}")
            return

        products = json_data.get('payload', {}).get('results', [{}])
        for product in products:
            product_dict = product.get('product', {})
            product_id = product_dict.get('id', 0)

            if product_id in self.current_scrapped_items:
                continue

            was_price = product_dict.get('wasPrice', 0) or product_dict.get('retailPrice', 0)
            category = (product_dict.get('sourceId', '').replace(' >', ',')
                        or f"{product_dict.get('category', '')}, {product_dict.get('subCategory', '')}")
            url = product_dict.get('url')
            url = self.start_urls[0] + url if url else ''

            yield Request(url=self.get_scrapeops_url(url), callback=self.parse_product,
                          meta={'was_price': was_price, 'category': category})

    def parse_product(self, response):
        if response.status == 202:
            return

        item = OrderedDict()
        script_tag = response.css('script#__NEXT_DATA__').re_first(r'({.*})')

        try:
            data = json.loads(script_tag)
        except json.decoder.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")
            return

        product = data.get('props', {}).get('pageProps', {}).get('data', {}).get('productById', {})

        item['Product URL'] = product.get('metaURLs', {}).get('canonical', {}).get('url', '')
        item['Item ID'] = ''
        item['Product ID'] = product.get('id', '')
        item['Category'] = self.get_category_name(product, response)
        item['Brand Name'] = product.get('brand', {}).get('name', '')
        item['Product Name'] = product.get('title', '')
        item['Short Description'] = ''
        current_price = response.css('[itemProp="price"]::attr(content)').get('')
        item['Current Price'] = current_price
        item['Long Description'] = self.get_long_description(product)
        item['Product Information'] = ''
        item['Directions'] = ''
        item['Ingredients'] = self.get_ingredients(response)
        item['SKU'] = product.get('id', '')

        image = ',\n'.join([img.get('url', '') for img in product.get('assets', {}).get('gallery', [{}])])
        item['Image URLs'] = image if image else ''

        was_price = response.meta.get('was_price')
        was_price = was_price if was_price != 0 else ''
        was_price = was_price if was_price != current_price else ''

        regular_price = response.css('[itemProp="price"]::attr(content)').get('')

        item['Regular Price'] = regular_price if regular_price else ''
        item['Special Price'] = was_price if was_price else ''

        self.current_scrapped_items.append(item['Product ID'])
        self.items_scrapped += 1
        print('Total Current items are scraped: ', self.items_scrapped)

        yield item

    def get_categories_urls(self, response, slug):
        sub_categories = []

        try:
            # Extract URLs from the response
            json_data = response.css('script#__NEXT_DATA__ ::text').get('')
            if json_data:
                json_dict = json.loads(json_data)
                # Accessing nested structure with proper exception handling
                shops = json_dict.get('props', {}).get('pageProps', {}).get('headerConfiguration', {}).get('megaMenu',
                                                                                                           {}).get(
                    'navData', {}).get('shops', [{}])

                # Filter out categories without 'shopNavigationGroups'
                categories = [x for x in shops if x.get('shopNavigationGroups')]

                if slug:
                    category = [x for x in categories if
                                slug in x.get('url') or [x for x in x.get('shopNavigationGroups', [{}]) if
                                                         slug in x.get('url')]]
                    for category_url in category:
                        sub_cat = [x for x in category_url.get('shopNavigationGroups', [{}])]
                        for subcat in sub_cat:
                            if not subcat.get('shopNavigationItems', [{}]):
                                sub_categories.append(subcat.get('url', ''))
                            else:
                                urls = [x.get('url') for x in subcat.get('shopNavigationItems')]
                                for url in urls:
                                    sub_categories.append(url)
                    return sub_categories

                else:
                    # Extract subcategories' URLs
                    for category in categories:
                        subcategories_url = [y.get('url') for x in category.get('shopNavigationGroups', [{}]) for y in
                                             x.get('shopNavigationItems', [{}])]
                        sub_categories.extend(subcategories_url)

                return sub_categories

        except json.decoder.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

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

    def get_category_name(self, product, response):
        category_data = product.get('category', {})
        category_names = [category_data['name']]

        # Extracting names from nested dictionaries
        while 'parent' in category_data and category_data['parent']:
            category_data = category_data['parent']
            category_names.append(category_data['name'])

        # Reverse the list to get the hierarchy in the correct order
        category_names.reverse()

        # Join the names with a comma
        result = ', '.join(category_names)

        return result

    def get_long_description(self, product):
        desc = product.get('description', '')
        html = Selector(text=desc)
        tags = html.xpath('//html/body/*')
        description = []
        for tag in tags:
            if 'Key Ingredients' in ''.join(tag.css(' ::text').getall()):
                continue
            text = '\n '.join(tag.css(' ::text').getall()).strip().replace('\n', '')
            description.append(text)

        description_text = '\n'.join(description) if description else ''
        return description_text

    def get_scrapeops_url(self, url):
        payload = {'api_key': self.proxy_key, 'url': url}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    def get_ingredients(self, response):
        html_tags = response.xpath('//div[@itemprop="description"]/*')
        ingredients_tag = [element.css(' ::text').getall() for element in html_tags if
                           'Key Ingredients:' in ''.join(element.css(' ::text').getall())]
        ingredients = [' '.join(element) for element in ingredients_tag]

        return ingredients if ingredients else ''
