import json
from collections import OrderedDict
from urllib.parse import urljoin

from scrapy import Request

from .base import BaseSpider


class ManomanoScraperSpider(BaseSpider):
    name = "manomano"
    base_url = 'https://www.manomano.de/'
    start_urls = ['https://www.manomano.de/']

    headers = {
        'authority': 'www.manomano.de',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'mm_visitor_id=2117e0b3-400f-4539-bc1d-645daef355cd; ab_testing_theme=a; referer_id=3; didomi_token=eyJ1c2VyX2lkIjoiMTg5M2JhZDAtNjgyOS02YTI1LThjZjctYjA5OTA5MGNmNTgwIiwiY3JlYXRlZCI6IjIwMjMtMDctMDlUMTc6MjI6NDguMTQ0WiIsInVwZGF0ZWQiOiIyMDIzLTA3LTA5VDE3OjIyOjQ4LjE0NFoiLCJ2ZXJzaW9uIjoyLCJwdXJwb3NlcyI6eyJlbmFibGVkIjpbInN0YXRpc3RpY3MiLCJ1c2VyUHJlZmVyZW5jZXMiLCJwZXJzb25hbGlzZWRBZHZlcnRpc2luZyJdfSwidmVuZG9ycyI6eyJlbmFibGVkIjpbImM6dmVuZG9ybmVjLUxhYzJCVzREIiwiYzp2ZW5kb3JzdGEtYXdmVFVDQVAiLCJjOnZlbmRvcnByZS1jRmlYRHhISyIsImM6dmVuZG9ybWFyLUFBR3RQQUhmIl19fQ==; euconsent-v2=CPuo7UAPuo7UAAHABBENDMCgAAAAAAAAAAqIAAAAAAAA.YAAAAAAAAAAA; _gcl_au=1.1.351734686.1688923423; request_uri=L29hdXRoL3Rva2Vu; PHPSESSID=uhhhpd8r2d0sqtqvp5504q4h4k; _gid=GA1.2.2010599047.1689182634; ln_or=eyIzOTMzOTIxIjoiZCJ9; multireferer_id=a%3A1%3A%7Bi%3A3%3Bs%3A24%3A%222023-07-12T17%3A25%3A38%2B0000%22%3B%7D; mm_ab_test_version=018686d7886f9675d9fe639ef7bea1a3; mm_ab_tests=60.1|303.0|368.1|371.1|877.1|945.1|959.1|1016.1|1043.1|1129.1|1140.0|1146.1|1150.1|1151.1|1154.1|1156.1|1207.1|1215.1|1218.1|1233.1|1245.1|1205.1|1331.1|1388.1|1389.1|1455.1|1457.0|1521.0|1522.1|1523.0|1524.0|1526.1|1533.1|1534.1|1686.1|1759.1|1762.1|1765.1|1359.1|1786.1|1916.1|1983.1|1984.1|1985.1|1986.1|2015.1|2312.0|2345.1|2511.1|2513.1|2544.1|2676.0|2708.1|2807.1|2843.1|2906.1|2939.0|2973.1|3039.0|3072.0|3104.1|3171.1|3172.1|3203.1|3205.1|3335.1|3336.1|3006.1|3401.1|3434.0|3533.1|3566.0|3567.0|988.1|3632.0|3665.1|3732.0|3797.0|3863.0|3901.0; OAuth_Token_Request_State=9b23f355-acdc-4572-80a8-cacbdd9895d6; __cf_bm=Z0O5PwGmbgumLSmO89Md4QU.0MOU6ppBbGpL8.Jyw9g-1689234222-0-AVJOwdXqVfFrRFPOy8jhHz5yz/jXxStxaedUWZ4R3tkuO5pqsVaiSf46pnNvqP1RV3C8V9NE91lxiFcFGGUgULBmxFzYpLMRlNlMYK0aPeNcT0+GEvPHsqqvjrcF1zFgDw==; ABTasty=uid=bwn4397px9dy2388&fst=1688923494207&pst=1688923494207&cst=1689182632901&ns=2&pvt=5&pvis=2&th=; _spmm_ses.1a49=*; _spmm_id.1a49=a873ad4e-4ef8-4812-b0a5-edf2c7329914.1688923427.3.1689234221.1689182931.2e43873f-fac3-44b5-82ed-1af681c2e737; amp_eb4016=Bj2LeVd6AyUHH4XShb7eQY...1h5739aa3.1h5739aab.1s.26.42; _uetsid=e01b186020d811eebb08c1578349ee0c; _uetvid=5ad12a201e7d11ee9ec019a9d0d09b8b; _ga=GA1.1.161361708.1688923424; _ga_6WCFY7KGNT=GS1.1.1689234221.4.0.1689234221.60.0.0; cto_bundle=V5NYX19lbVJxUWQ3cklvWWh6UzBlNVclMkIwU2E0VVl4YzVCdUp6JTJGZkdrYjM0SlFBYUNMZXBHczFob1ROTGZNQTd4bG5rQlpwcElCZWV4Uk9keU9rY1JBQWNnZTJ5c2V5YkFrZjY2TDhhdU84OTFLcDUwNUNLdzhzUSUyRkJ1UmwlMkZPak9BdFd4aUNCbWpVJTJGU0ZXdzJsT3dGZkREd213JTNEJTNE',
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_proxy = True
        self.categories = '.W2rWY2:contains(Angebote)::attr(href), .W2rWY2:contains(Top-Verkäufe)::attr(href)'

    def parse_products(self, response):
        if response.css('.tG5dru .c4ZD3Vm::attr(href)'):
            products = response.css('.c4ZD3Vm')
            for product in products:
                product_url = product.css('.c4ZD3Vm::attr(href)').get('').rstrip('/').strip()

                first_price = product.css('[data-testid="price-main"] span.c3orUO::text').get('')
                last_price = product.css('[data-testid="price-main"] span.H6kKtd::text').get('')

                if first_price and last_price:
                    new_price = f"{first_price}.{last_price}"
                else:
                    new_price = first_price

                if not product_url:
                    continue

                product_url = urljoin(self.base_url, product_url)

                if self.is_product_exists(product_url, new_price):
                    continue

                yield Request(url=product_url, callback=self.product_detail)

                next_page = response.css('link[rel="next"]::attr(href)').get('')
                if next_page:
                    url = urljoin(response.url, next_page)
                    yield Request(url=url, callback=self.parse_products)

        else:
            top_sales_cat = response.css('.V1O7Ri::attr(href)').getall()
            for category in top_sales_cat:
                yield Request(url=urljoin(response.url, category), callback=self.top_sale)

    def product_detail(self, response):
        item = OrderedDict()

        try:
            data = json.loads(response.css('script:contains(gtin)').re_first(r'({..*})'))
        except Exception as e:
            data = {}

        item['Product Title'] = response.css('.IRZISl h1::text').get('') or data.get('name', '')
        # item['Price'] = response.css('.MyMPsK::text').get('').replace(' €', '').replace(',','.')
        item['Price'] = data.get('offers', {}).get('price', '')
        item['EAN'] = f"'{data.get('gtin', '')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item

    def top_sale(self, response):
        products = response.css('.c4ZD3Vm')
        for product in products:
            first_price = product.css('[data-testid="price-main"] span.c3orUO::text').get('')
            last_price = product.css('[data-testid="price-main"] span.H6kKtd::text').get('')

            if first_price and last_price:
                new_price = f"{first_price}.{last_price}"
            else:
                new_price = first_price

            product_url = product.css('.c4ZD3Vm::attr(href)').get('').rstrip('/').strip()
            product_url = urljoin(self.base_url, product_url)

            if not product_url:
                continue

            if self.is_product_exists(product_url, new_price):
                continue

            yield Request(url=product_url, callback=self.product_detail)
