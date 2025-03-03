import os
import csv
import glob
import json
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Request, Spider, Selector


class SkuSearchProductsSpider(Spider):
    name = "search_products"
    start_urls = ["https://www.setin.fr/"]
    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/Setin Product Scraper {current_dt}.csv': {
                'format': 'csv',
                'fields': ['Searched SKU', 'Search EAN', 'Title', 'Price', 'Length', 'Material',
                           'Reference Number', 'Box Of', 'SKU', 'EAN', 'URL']
            }
        }
    }

    def __init__(self):
        super().__init__()
        # Read Sku & Ean Numbers from Csv File
        self.sku_numbers = self.read_input_from_file()

        self.items_scraped_count = 0
        self.current_scraped_item = []

        # Logs
        self.error = []
        self.mandatory_logs = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']
        self.logs_filename = f'logs/logs {self.current_dt}.txt'

    def start_requests(self):
        for row in self.sku_numbers:
            sku = row.get('SKU', '')
            ean = row.get('EAN', '')
            url = f'https://www.setin.fr/ajax/recherche_autocomplete.php?term={sku}'
            yield Request(url=url, callback=self.parse, meta={'sku': sku, 'ean': ean, 'request': 'sku'})

    def parse(self, response, **kwargs):
        ean_url = f"{response.url.split('=')[0]}={response.meta.get('ean')}"

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.error.append(f'Error Parsing Json response :{e} URL: {response.url}')

            # if error arises during response json read then make new request using EaN number Search
            response.meta['request'] = 'ean'
            yield Request(url=ean_url, headers=self.headers, callback=self.parse, meta=response.meta)
            return

        products_count = data.get('count', {}).get('article') or 0

        # No Product found from sku Search and now make new search the ean
        if products_count == 0 and not response.meta.get('request') == 'ean':
            self.mandatory_logs.append(f"0 Found Product in SKU: {response.meta.get('sku', '')}")
            response.meta['request'] = 'ean'
            yield Request(url=ean_url, headers=self.headers, callback=self.parse, meta=response.meta)

        # No product searched from Sku and Ean Search form the row
        if products_count == 0 and response.meta.get('request') == 'ean':
            self.mandatory_logs.append(f"0 Found Product in SKU: {response.meta.get('sku', '')} & Ean: {response.meta.get('sku', '')}")
            return

        product = ''.join([url.get('lien', '') for url in data.get('result', []) if url.get('lien')])

        if not product:
            return

        url = urljoin(self.start_urls[0], product)
        yield Request(url=url, headers=self.headers, callback=self.parse_product_detail, meta=response.meta)

    def parse_product_detail(self, response):
        try:
            variant_script = response.css('script:contains("customer_ref_var") ::text').re_first(r'= (.*);')
            variant_dict = json.loads(variant_script)
        except json.JSONDecodeError as e:
            self.error.append(f"Error Parsing the Product: {response.url}  & Error: {e}")
            variant_dict = {}
            return

        for key, value in variant_dict.items():
            try:
                html_selector = Selector(text=value.get('description_courte', ''))
                price = self.get_price(key, response)
                sku = response.css('.syte-discovery::attr(data-sku)').get('')
                ean = value.get('code_barre', '')
                material_keywords = ['Matière', 'Material', 'Matériau']
                length_keywords = ['Long.', 'L mm', ' mm', 'Dimensions hors tout', 'Dimensions', 'ø', 'Longueur utile', 'Diamètre']
                box_keyword = ['Box', 'Boîte de']

                item = OrderedDict()
                item['Title'] = value.get('designation', '')
                item['Price'] = price
                item['Length'] = self.get_keyword_value(response, html_selector, length_keywords)
                item['Material'] = self.get_keyword_value(response, html_selector, material_keywords)
                item['Reference Number'] = value.get('ref_fournisseur', '').replace(' ', '')
                item['Box Of'] = self.get_keyword_value(response, html_selector, box_keyword)
                item['SKU'] = f'`{sku}' if sku else ''
                item['EAN'] = f'`{ean}' if ean else ''
                item['URL'] = response.url

                if response.meta.get('request') == 'sku':
                    item['Searched SKU'] = response.meta.get('sku', '')
                    item['Searched EAN'] = ''

                if response.meta.get('request') == 'ean':
                    item['Searched SKU'] = ''
                    item['Searched EAN'] = response.meta.get('ean', '')

                yield item
            except Exception as e:
                self.error.append(f'Error Parsing the Variant from Product Url: "{response.url}" & Error: {e}')

        self.items_scraped_count += 1
        print('Scrape Items Counter:', self.items_scraped_count)

    def get_price(self, key, response):
        """
        Extracts and formats the price from the response CSS selector.

        Args:
            key (str): The key used in the CSS selector.
            response (scrapy.http.Response): The response object.

        Returns:
            str: The formatted price with two decimal places.
        """
        try:
            price = response.css(f'.qte-selector-{key}::attr(data-price)').get('')

            if price:
                formatted_price = '{:.2f}'.format(float(price))
            else:
                formatted_price = ''
        except (TypeError, ValueError):
            formatted_price = ''

        return formatted_price

    def read_input_from_file(self):
        """
        Reads input data from CSV files located in the 'input' directory.

        Returns:
            list: A list of dictionaries representing the data read from the CSV files.
                  Each dictionary corresponds to a row in the CSV file, with keys
                  as header names and values as field values.
        """
        try:
            files = glob.glob('input/*.csv')
            all_data = []
            for file in files:
                with open(file, 'r', encoding='utf-8') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        all_data.append(row)

            return all_data
        except IOError as e:
            self.error.append(f"Error reading input files: {e}")
            return []  # Return an empty list if there's an error reading files

    def get_keyword_value(self, response, html_selector, keyword_list):
        for keyword in keyword_list:
            value = html_selector.css(f'.carac:contains("{keyword}") span::text').get('')
            if value:
                return value

        for keyword in keyword_list:
            value = response.css(f'.cont-onglet-produits .carac:contains("{keyword}") span::text').get('')
            if value:
                return value

        return ''

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

        spider.mandatory_logs.append(f'\n\nSpider Error:: \n')
        spider.mandatory_logs.extend(spider.error)

        spider.write_logs()
