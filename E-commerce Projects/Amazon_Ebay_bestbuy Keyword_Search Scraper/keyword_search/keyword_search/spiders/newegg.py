import json
import re
from collections import OrderedDict

from scrapy import Spider, Request


class NeweggSpider(Spider):
    name = 'newegg'
    start_urls = ['https://www.newegg.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 7,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/NewEgg Products Detail.csv': {
                'format': 'csv',
                'fields': ['Brand', 'Model', 'Title', 'Sku', 'GTIN', 'Condition',
                           'Price', 'Discounted Price', 'Description', 'keyword',
                           'Images', 'Status', 'URL'],
                'overwrite': True
            }
        }
    }

    def __init__(self):
        super().__init__()
        search_keyword = 'input/keywords.txt'
        self.keywords = self.get_input_rows_from_file(search_keyword)

    def start_requests(self):
        for keyword in self.keywords:
            # keyword = 'computers'
            page_num = '1'
            yield Request(url=f"https://www.newegg.com/p/pl?d={keyword.replace(' ', '+')}&PageSize=96&page={page_num}",
                          callback=self.parse,
                          meta={'keyword': keyword, 'page_num': page_num}
                          )

    def parse(self, response):
        products_urls = response.css('.item-container .item-img:not([ rel="nofollow"])::attr(href)').getall()
        for product_url in products_urls:
            yield Request(response.urljoin(product_url),
                          callback=self.product_detail,
                          meta=response.meta)

        next_page = response.css('.list-tool-pagination-text strong')
        if next_page:
            page_num = int(response.meta['page_num']) + 1
            next_page_url = re.sub('page=(\d+)', repl=f'page={page_num}', string=response.url)
            yield Request(
                url=next_page_url,
                callback=self.parse,
                meta={'keyword': response.meta['keyword'], 'page_num': page_num}
            )

    def product_detail(self, response):
        try:
            data = json.loads(response.css('script:contains("gtin"), script:contains("sku")').re_first(r'({.*})'))
        except (json.JSONDecodeError, AttributeError):
            data = {}

        item = OrderedDict()
        item['Brand'] = data.get('brand', '')
        item['Model'] = data.get('Model', '')
        item['Title'] = data.get('name', '')
        item['Sku'] = data.get('sku', '')
        item['GTIN'] = data.get('gtin12', '') or data.get('gtin13', '')
        item['Condition'] = data.get('itemCondition', '')

        was_price = response.css('.price-was-data::text').get('').replace('$', '')
        if was_price:
            item['Discounted Price'] = data.get('offers', {}).get('price', '')
            item['Price'] = was_price
        else:
            item['Discounted Price'] = ''
            item['Price'] = was_price

        item['Description'] = data.get('description', '')
        item['keyword'] = response.meta.get('keyword', '')
        item['Images'] = ','.join(response.css('#side-swiper-container img::attr(src)').getall()) or data.get('image',
                                                                                                              '')
        item['Status'] = 'In Stock' if response.css('.product-buy:contains("Add to cart")') else 'Out of Stock'
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
