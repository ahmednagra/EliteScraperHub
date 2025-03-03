import json
import re
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urljoin, quote

from scrapy import Spider, Request


class BestbuySpider(Spider):
    name = 'bestbuy'
    start_urls = ['https://www.bestbuy.com/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'RETRY_TIMES': 7,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/Bestbuy Products Detail.csv': {
                'format': 'csv',
                'fields': ['Brand', 'Model', 'Title', 'Sku', 'GTIN', 'Condition',
                           'Discounted Price', 'Price', 'Description', 'keyword',
                           'Image', 'Status', 'URL'],
                'overwrite': True
            }
        }
    }

    headers = {
        'authority': 'www.bestbuy.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    def __init__(self):
        super().__init__()
        search_keyword = 'input/keywords.txt'
        self.keywords = self.get_input_rows_from_file(search_keyword)

    def start_requests(self):
        for keyword in self.keywords:
            url = f"https://www.bestbuy.com/site/searchpage.jsp?qp=condition_facet=Condition~New&st={keyword.replace(' ', '+')}&intl=nosplash"
            yield Request(url=url,
                          headers=self.headers,
                          callback=self.parse,
                          meta={'keyword': keyword}
                          )

    def parse(self, response):
        products_urls = response.css('.sku-title a::attr(href)').getall()
        for product_url in products_urls:
            yield Request(response.urljoin(product_url),
                          headers=self.headers,
                          callback=self.product_detail,
                          meta=response.meta
                          )

        next_page = response.css('.sku-list-page-next::attr(href)').get('')
        if next_page:
            yield Request(response.urljoin(next_page), headers=self.headers, callback=self.parse,
                          meta=response.meta)

    def product_detail(self, response):
        try:
            json_data = json.loads(response.css('script:contains("priceChangeTotalSavingsAmount")::text').get(''))
            data = json.loads(response.css('script:contains("gtin")::text').get(''))
            price_data = json_data.get("app", {}).get("data", {}) or {}
        except (json.JSONDecodeError, AttributeError):
            data = {}
            json_data = {}
            price_data = {}

        item = OrderedDict()

        discount_price = price_data.get("customerPrice", '') or ''
        was_price = price_data.get('regularPrice', '') or ''
        item['Brand'] = data.get('brand', {}).get('name', '')
        item['Model'] = data.get('model', '') or response.css('.product-data-value::text').get('')
        item['Title'] = data.get('name', '') or response.css('.sku-title h1::text').get('')
        item['Sku'] = data.get('sku', '') or response.css('.sku.product-data .product-data-value::text').get('')
        item['GTIN'] = data.get('gtin13', '')
        item['Condition'] = self.get_condition(data)

        if was_price:
            item['Discounted Price'] = discount_price
            item['Price'] = was_price
        else:
            item['Discounted Price'] = ''
            item['Price'] = discount_price

        # item['Discount Amount'] = price_data.get('priceChangeTotalSavingsAmount', '') or ''
        item['Description'] = data.get('description', '') or response.css('.html-fragment::text').get('')
        item['keyword'] = response.meta['keyword']
        item['Image'] = ','.join(response.css('.seo-list a::attr(href)').getall())or self.get_images(response)
        item['Status'] = 'Out of stock' if response.css(
            '.fulfillment-fulfillment-summary:contains("Sold Out")') else 'In stock'
        item['URL'] = response.url

        yield item

    def get_input_rows_from_file(self, file_path):
        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def get_condition(self, data):
        condition = data.get('offers', {}).get('description', '')
        condition = condition or data.get('offers', {}).get('offers', [{}])[0].get('itemCondition', '').split('/')[
            -1] or ''

        return condition

    def get_images(self, response):
        images = response.css('.media-gallery-base-content.thumbnails a::attr(href)').get()
        images = images or response.css('.primary-image-grid ::attr(src)').getall()

        images = [img for img in images if img]

        return ', '.join(images)


