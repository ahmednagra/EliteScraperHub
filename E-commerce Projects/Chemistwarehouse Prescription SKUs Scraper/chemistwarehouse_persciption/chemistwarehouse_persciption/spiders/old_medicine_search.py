import csv
import glob
import os
import json
import re
from datetime import datetime
from collections import OrderedDict
from urllib import parse
from urllib.parse import urlencode

import fitz
import requests
from scrapy import Spider, Request, signals, Selector


class MedicineSearchSpider(Spider):
    name = 'old_medicine_search'
    base_url = 'https://www.chemistwarehouse.com.au'

    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {

        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'CONCURRENT_REQUESTS': 3,
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },
        'FEEDS': {
            f'output/Chemist Warehouse Products {datetime.now().strftime("%d%m%Y%H%M")}.xlsx': {
                'format': 'xlsx',
                'fields': ['Search Title', 'Search Price', 'SKU', 'Title', 'URL']
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.medicines_skus = []  # avoid duplicates
        self.item_scraped_count = 0

        # Output file
        os.makedirs('output', exist_ok=True)
        self.output_filename = f'output/Chemist Warehouse Products {datetime.now().strftime("%d%m%Y%H%M")}.csv'
        self.output_file_fields = ['Search Title', 'Search Price', 'SKU', 'Title', 'URL']
        # logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

    def start_requests(self):
        medicines_information = self.get_medicines_dict()
        for medicine in medicines_information:
            name = medicine.get('name', '')
            url = f'https://www.chemistwarehouse.com.au/native-search?pre=1&searchmode=anywords&searchtext={name}'

            yield Request(url=self.get_scrapeops_url(url), callback=self.parse, meta={'medicine': medicine})

    def parse(self, response, **kwargs):
        try:
            name = response.meta.get('medicine', {}).get('name', '')
            price = response.meta.get('medicine', {}).get('price', '')

            products = response.css('.product-container.search-result')
            matched_items = []

            for product in products:
                title = product.css('a::attr(title)').get('').strip()
                product_price = product.css('.Price ::text').get('').strip()

                if price == product_price and any(part.lower() in title.lower() for part in name.split()):
                    item = OrderedDict()

                    sku_selector = product.css('.bvcls::attr(id)').get('')
                    item['Search Title'] = name
                    item['Search Price'] = price
                    item['Title'] = title
                    item['SKU'] = ''.join(sku_selector.split('-')[1:2])
                    item['URL'] = f"{self.base_url}{product.css('a::attr(href)').get('').strip()}"

                    matched_items.append(item)

            if not matched_items:
                self.write_logs(f"Price not matched for Medicine : {name}  Price: {price}")
                return

            # Filter Matched items if first word of title matched with Search Medicine name
            medicine_start_name = name.lower().split(' ')[0]
            filtered_products = [product for product in matched_items if
                                 product['Title'].lower().startswith(medicine_start_name)]

            if not filtered_products:
                # Filter Matched items if Search Medicine name [Words] matched with  filtered_products
                search_keywords = set(name.lower().split())

                def count_matching_keywords(product):
                    title_words = set(product['Title'].lower().split())
                    return len(search_keywords.intersection(title_words))

                # Calculate the number of matched keywords for each product
                filtered_products_with_counts = [(product, count_matching_keywords(product)) for product in
                                                 filtered_products]

                if filtered_products_with_counts:
                    # Find the product with the maximum number of matches
                    best_match = max(filtered_products_with_counts, key=lambda x: x[1])[0]
                    filtered_products = list(best_match)
                else:
                    self.write_logs(f"No products exist for Medicine : {name}  Price: {price}")
                    return

            # Filter the "filtered_products" on the basis of Medicine Doze like MG or ML
            dosage = ['mg', 'ml', 'g']
            dosage_values = {d: re.search(fr'(\d+){d}', name.lower(), re.IGNORECASE) for d in dosage}
            value = next((v.group(1) for v in dosage_values.values() if v), '')

            if value:
                filtered_products = [product for product in filtered_products if value in product['Title']]

            for item in filtered_products:
                sku = item.get('SKU', '')
                if sku not in self.medicines_skus:
                    self.medicines_skus.append(sku)
                    self.item_scraped_count += 1
                    print('item_scraped_count :', self.item_scraped_count)
                    yield item
                else:
                    continue

        except Exception as e:
            self.write_logs(f"Error in parse Medicine Detail Name: {name} price{price} Error: {e}")

    def get_medicines_dict(self):
        input_file = glob.glob('input/*.pdf')[0]

        def format_text(text):
            lines = text.split('\n')
            formatted_lines = []
            current_line = ""

            for line in lines:
                line = line.strip()
                if re.match(r'^\$\d+\.\d{2}$', line):
                    # If the line is a price, add it to the current line
                    current_line += ' ' + line
                    formatted_lines.append(current_line)
                    current_line = ""
                else:
                    # Otherwise, treat it as a part of the description
                    if current_line:
                        formatted_lines.append(current_line)
                    current_line = line

            if current_line:
                formatted_lines.append(current_line)

            return '\n'.join(formatted_lines)

        def extract_medicines_dict(text):
            data_list = []
            seen = set()

            lines = text.split('\n')
            for line in lines:
                match = re.match(r'^(.*?)(\$\d+\.\d{2})$', line)
                if match:
                    # medicine_dict = {}
                    name = match.group(1).strip()
                    price = match.group(2).strip()

                    if (name, price) not in seen:
                        seen.add((name, price))
                        medicine_dict = {'name': name, 'price': price}
                        data_list.append(medicine_dict)
            return data_list

        # Process each input file
        doc = fitz.open(input_file)

        all_text = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():  # If the text is not empty
                formatted_text = format_text(page_text)
                all_text.append(formatted_text)

        # Combine text from all relevant pages
        medicine_string = "\n".join(all_text).strip()
        a = extract_medicines_dict(medicine_string)
        return a

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def get_scrapeops_url(self, url):
        payload = {'api_key': '69407ad1-67b8-4a4f-8083-137167f3b908', 'url': url}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    def close(spider, reason):
        spider.write_logs(f'\n\nItems Are Scraped :{spider.item_scraped_count}')
