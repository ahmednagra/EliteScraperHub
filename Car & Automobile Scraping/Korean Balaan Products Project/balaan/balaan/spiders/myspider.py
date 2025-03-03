import json
from math import ceil

import scrapy

from ..items import BalaanItem


class BalaanSpider(scrapy.Spider):
    name = "balaan_spider_product"
    start_urls = ["https://balaan.co.kr/api/banners/pc"]

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'output/%(name)s_%(time)s.csv',
        'fields': ['product_Id', 'Title', 'Price', 'Old_Price', 'Brand', 'SKU', 'Color', 'Size', 'Stock_Status',
                   'Category', 'Image_URL', 'Product_URL']
    }

    headers = {
        "authority": "api.balaan.co.kr",
        "accept": "*/*",
        "accept-language": "en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6",
        "content-type": "application/json",
        "origin": "https://www.balaan.co.kr",
        "referer": "https://www.balaan.co.kr/",
        "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }

    def parse(self, response):
        print('welcome Parse method')
        data = self.response_json(response)
        cat_id = list(data.get('data').keys())
        cat_id = [x for x in cat_id if x not in ['009001', '010001', '009007', '010007']]
        print('Cat_id : ', cat_id)
        ids = cat_id
        print('ids : ', ids)

        for category_id in cat_id:
            if category_id not in ids:
                break

            form_params = self.form_data(page_num=1, category_id=category_id)

            yield scrapy.Request(
                url='https://api.balaan.co.kr/v1/goods/list_by_filter',
                method='POST',
                headers=self.headers,
                body=(json.dumps(form_params).encode('utf-8')),
                callback=self.next_page,
                meta={'category_id': category_id}
            )

    def next_page(self, response):
        print('weolcome pagination page')
        data = self.response_json(response)
        total_products = data.get('listGoods', {}).get('total', 0)
        total_pages = ceil(total_products // 400)
        category_id = response.meta.get('category_id')
        all_products_ids = [item['goodsno'] for item in data.get('listGoods', {}).get('result', [])]

        for page_num in range(1, total_pages + 1):
            form_data = self.form_data(page_num=page_num, category_id=category_id)
            url = 'https://api.balaan.co.kr/v1/goods/list_by_filter'
            print(f' page no is {page_num} and category is: {category_id}')

            yield scrapy.Request(
                url=url,
                method='POST',
                headers=self.headers,
                body=(json.dumps(form_data).encode('utf-8')),
                callback=self.product_detail,
                meta={'all_products_ids': all_products_ids, 'category_id': category_id},
                dont_filter=True
            )

    def product_detail(self, response):
        print('welcome to product Detail page')
        data = self.response_json(response)

        dic_data = data.get('listGoods', ' ').get('result', ' ')
        if not dic_data:
            return

        all_products_ids = response.meta.get('all_products_ids', '')
        for product_id, product_data in zip(all_products_ids, dic_data):
            item = BalaanItem()

            item['product_Id'] = product_id
            item['Title'] = product_data.get('goodsnm', '')
            item['Price'] = product_data.get('member_price', '')
            item['Old_Price'] = product_data.get('consumer', '')
            item['Brand'] = product_data.get('brand', '').get('name', '')
            item['SKU'] = product_data.get('sku_id', '')
            item['Color'] = product_data.get('major_color', '')
            item['Size'] = [option.get('size') for option in product_data.get('option', [])]
            item['Stock_Status'] = 'outofstock' if product_data.get('totstock') == 0 else 'instock'
            item['Category'] = product_data.get('catnm', '')
            item['Image_URL'] = product_data.get('img_i', '')
            item['Product_URL'] = f'https://balaan.co.kr/shop/goods/goods_view.php?goodsno={product_id}'

            yield item

    def form_data(self, page_num, category_id):
        return {
            "params": {
                "f_brandno": [],
                "page": page_num,
                "sort": "pageview",
                "f_price": {},
                "category": str(category_id),
                "f_size": [],
                "size": 400,
                "keyword": ""
            },
            "session_id": "71088121b102433db4a2bcdeab689d05",
            "m_no": None
        }

    def response_json(self, response):
        try:
            json_data = json.loads(response.text) or {}
        except json.JSONDecodeError as e:
            print("Error decoding JSON: ", e)
            json_data = {}

        return json_data
