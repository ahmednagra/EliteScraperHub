import csv
from urllib.parse import urljoin

from scrapy import Spider, Request


class BaseSpider(Spider):
    name = 'base'
    base_url = ''
    output_filename = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proxy = ''

        # Selectors
        self.categories = ''
        self.product_url = ''
        self.products = ''
        self.new_price = ''
        self.next_page = ''

        self.output_filename = f'output/{self.name} Products.csv'
        self.output_fieldnames = ['Product Title', 'Price', 'EAN', 'URL']

        self.previous_products = self.get_previous_products_from_csv()
        self.current_scraped_items = []

        self.proxy = self.read_config_file().get('scraperapi_key', '')
        self.use_proxy = False

    def parse(self, response, **kwargs):
        data = response.css(f'{self.categories}').getall()
        categories_url = list(set(data))

        for url in categories_url[:1]:
            yield Request(url=urljoin(response.url, url), callback=self.parse_products)

    def parse_products(self, response):
        products = response.css(f'{self.products}')

        for product in products[:10]:
            product_url = product.css(f'{self.product_url}').get('').rstrip('/').strip()
            if not product_url:
                continue

            product_url = urljoin(self.base_url, product_url)

            new_price = product.css(f'{self.new_price}').re_first(r'[0-9,.]+', '').replace(',', '.')

            if self.is_product_exists(product_url, new_price):
                print('product already exist')
                continue

            yield Request(url=product_url, callback=self.product_detail)

        if self.next_page:
            next_page = response.css(f'{self.next_page}').get('')

            if next_page:
                next_url = urljoin(response.url, next_page)
                # yield Request(url=next_url, callback=self.parse_products)

    def product_detail(self, response):
        pass

    def get_previous_products_from_csv(self):
        try:
            with open(self.output_filename, mode='r', encoding='utf-8') as csv_file:
                products = list(csv.DictReader(csv_file))
                return {product.get('URL', '').rstrip('/').strip(): product for product in products}
        except FileNotFoundError:
            return {}

    def is_product_exists(self, product_url, new_price):
        if not hasattr(self, 'previous_products') or not self.previous_products:
            return False

        previous_product = self.previous_products.get(product_url)
        if previous_product:
            previous_price = previous_product.get('Price')
            product_price = new_price if previous_price != new_price else previous_price
            previous_product['Price'] = product_price

            self.current_scraped_items.append(previous_product)
            return True

        return False

    def write_items_to_csv(self, mode='w'):
        if not self.current_scraped_items:
            return

        with open(self.output_filename,  mode=mode, newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.output_fieldnames)

            if csv_file.tell() == 0:
                writer.writeheader()

            writer.writerows(self.current_scraped_items)

    def read_config_file(self):
        file_path = 'input/config.txt'
        config = {}

        try:
            with open(file_path, mode='r') as txt_file:
                for line in txt_file:
                    line = line.strip()
                    if line and '==' in line:
                        key, value = line.split('==', 1)
                        config[key.strip()] = value.strip()

            return config

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def get_price(self, selector):
        return selector.replace('€', '').replace(',', '.').strip()

    def close(spider, reason):
        spider.write_items_to_csv()
