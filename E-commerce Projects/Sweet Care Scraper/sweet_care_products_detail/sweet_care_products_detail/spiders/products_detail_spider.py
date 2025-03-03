import csv
import json
from urllib.parse import urljoin

import openpyxl
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request, FormRequest


class ProductsDetailSpider(Spider):
    name = 'products_detail'
    allowed_domains = ['www.sweetcare.com']
    start_urls = ['https://www.sweetcare.com/ae']

    custom_settings = {

        # 'SCRAPEOPS_API_KEY': '69407ad1-67b8-4a4f-8083-137167f3b908',
        # 'SCRAPEOPS_PROXY_ENABLED': True,
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
        # },

        'CONCURRENT_REQUESTS': 4,
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },
        'FEEDS': {
            f'output/Amazon Products Reviews {datetime.now().strftime("%d%m%Y%H%M")}.xlsx': {
                'format': 'xlsx',
                'fields': ['SKU', 'Title', 'Brand', 'Price', 'Availability', 'Size', 'Color', 'URL']
            }
        }
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://www.sweetcare.com/ae',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.skus = self.read_sku_from_input_file('input/skus.xlsx')
        self.errors = []
        self.current_date_time = datetime.now().strftime("%Y-%m-%d %H%M%S")
        self.mandatory_logs = []

    def start_requests(self):
        for sku in self.skus[:1]:
            sku_id = sku.get('sweetcare code', '')
            search_url = f'https://www.sweetcare.com/ae/search?q={sku_id}'
            yield Request(url=search_url, headers=self.headers, callback=self.parse)

    def parse(self, response, **kwargs):
        matched_products_urls = response.css('.productList-container div a::attr(href)').getall()
        for url in matched_products_urls:
            product_url = urljoin(response.url, url)
            yield Request(url=product_url, headers=self.headers, callback=self.parse_product_detail)

    def parse_product_detail(self, response):
        item = OrderedDict()

        item['SKU'] = ''
        item['Title'] = ''
        item['Brand'] = ''
        item['Price'] = ''
        item['Availability'] = ''
        item['Size'] = ''
        item['Color'] = ''
        item['URL'] = ''

        yield item

    def read_sku_from_input_file(self, input_file):
        data = []

        try:
            workbook = openpyxl.load_workbook(input_file)
            sheet = workbook.active

            # Extract the data from the sheet
            headers = [cell.value for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_data = {headers[i]: row[i] for i in range(len(headers))}
                data.append(row_data)

            return data
        except FileNotFoundError:
            print(f"File '{input_file}' not found.")
            return
        except Exception as e:
            print(f"An error occurred while reading the file: {str(e)}")
            return
