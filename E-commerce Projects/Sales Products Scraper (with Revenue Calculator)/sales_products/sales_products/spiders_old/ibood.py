import json
from collections import OrderedDict

from scrapy import Request

from .base import BaseSpider


class IboodScraperSpider(BaseSpider):
    name = 'ibood'
    base_url = 'https://www.ibood.com/'
    start_urls = ['https://www.ibood.com/offers/de/s-de/all-offers?mode=all-deals']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse(self, response):
        url = 'https://api.ibood.io/search/items/live?mode=all-deals&shop=s-de&skip=0&take=12000'
        headers = self.get_headers(response)
        yield Request(url=url, headers=headers, callback=self.parse_products)

    def parse_products(self, response):
        try:
            data = response.json()
            items = data.get('data', {}).get('items', [])
        except Exception as e:
            items = []

        for record in items:
            slug = record.get('slug', '')
            classicId = record.get('classicId', '')
            product_url = f'https://www.ibood.com/offers/de/s-de/o/{slug}/{classicId}'

            if not product_url:
                continue

            new_price = record.get('price', {}).get('value', '')

            if self.is_product_exists(product_url, new_price):
                continue

            yield Request(url=product_url, callback=self.product_detail)

    def product_detail(self, response):
        item = OrderedDict()

        try:
            data = json.loads(response.css('#__NEXT_DATA__').re_first(r'({.*})'))
            product= data.get('props', {}).get('pageProps', {}).get('offer', {})
            items = product.get('items')

            if not items or not isinstance(items, list):
                return

        except (json.JSONDecodeError, AttributeError):
            return

        item['Product Title'] = product.get('contents', [{}])[0].get('title', '')
        item['Price'] = items[0].get('price', {}).get('value', '')
        ean = items[0].get('ean', '')
        item['EAN'] = f"'{ean}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item

    def get_headers(self, response):
        try:
            data = json.loads(response.css('script[type="application/json"]').re_first(r'({.*})'))
        except (json.JSONDecodeError, AttributeError):
            data = {}

        Ibex_Shop_Id = data.get('props', {}).get('pageProps', {}).get('shop', {}).get('id', '')
        Ibex_Tenant_Id = data.get('props', {}).get('pageProps', {}).get('tenant', '')

        headers = {
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-platform': '"Windows"',
            'X-Correlation-Id': 'bb6f1494-02e0-4e80-9e7f-bf06a2aaacb1',
            'Ibex-Shop-Id': Ibex_Shop_Id,
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.ibood.com/',
            'Ibex-Language': 'de',
            'Ibex-Tenant-Id': Ibex_Tenant_Id,
        }
        return headers
