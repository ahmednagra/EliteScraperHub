import json
import os
import re
from datetime import datetime

from scrapy import Spider, Request

from ..items import BestbuyProductsItem


class BestbuySpider(Spider):
    name = 'bestbuy'
    allowed_domains = ['www.bestbuy.com']
    start_urls = ['https://www.bestbuy.com/']

    custom_settings = {
        'FEEDS': {
            f'output/BestBuy Products {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'FEED_STORE_EMPTY': True,
                'fields': ['keyword', 'Title', 'Model', 'Sku', 'Discounted_Price', 'Actual_Price',
                           'Discount_Amount', 'Status', 'Image', 'URL', 'Description']
            }
        }
    }

    headers = {
        'authority': 'www.bestbuy.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'blue-assist-banner-shown=true; SID=b0678d3b-2816-40b7-9e3d-022a765e6dec; pst2=474|N; physical_dma=501; customerZipCode=07094|N; vt=e87ee3b8-0a82-11ee-b834-0ac1cbea7963; bm_sz=91FF0A225554D01B156E3FA2586B82AD~YAAQjIIsF7a5+7WIAQAAwzrAuBQR0uPCiDVFK+Gl/Zg/GlK3JMb7UheX+pSutUfVLkmZhPy84VyiOZ1x6brBgCqL9GE2Zxyn7oy9owAi2iOWClZvPwJu7yhNtT6iu4a7wwGWPkcrEud1CnlF3XG7JxSwwy3vtYrZuBRdGa5/xKOgFVnj40WlETrWZhhtfAk/VDjxy1wLgRZ2jlGe0v71Ubr6BNIgTU9r7ZCB5Mb5z+FiSx4l3k/OKh0DGwAdKqK9N6wl9qVcSZEmKzT8rAM0zRkGKhjpBDl4m6HrvI1C0uYCgLwo37woiuEV67y79N33JOPTG5EKuD1YnTwTY04nrjQYSBR/QNQGCJAqR+AGrtZSWtbUOzPAiQgZ5ERXNA7IfFNcOi9xV0WnqG7WXbKA/Xnr~3684149~3487032; bby_rdp=l; CTT=65f6d438aa8f69aeddf23d035a1b3d56; rxVisitor=16867267904400A6FBAPFE55UHEPCELC22QL2PTM8O78K; _abck=12C04ACFFFC6F06139482EA39138AF6D~0~YAAQjIIsF8u6+7WIAQAAmYDAuAoJpoXcn7+aXrbzCdlIbOvoU3qMs4r2djofqhiC0g6J47hwCOByd5hXSEClY9D7lPxHqDcj+Gkph+zgNYDn0XNpmaclk7u/X/7SCyzNtImBJmQ9Fa7HIwvq/aOGpj25c47CtVZ5od2MM8/58elIvGpxDZlTaIHKpZDaIlF0+Urg1LZWNeqVVfBlWVHU8gtz2cjO+Qi06bdJpyQ7PpQ2gGHuojiN+2ILZsOKrr1qXpVe1Y26EJbhrUkDbYZC0FFuf+1Us4xUbgzD3zHaYmbNjJb0S7eb9Pn8ouuFjrmu6sOqxvflGX1JAQE0YhTRbanXqciLQZnJuhvQabUr2qgdIOq2ZAm1wHGxQlKKCcmS6zxUwpao/s9MEnkqqsIRPuHEA771tD3ZJWxQ5PXAippJ9w09HAzdnMEgnfPv0UaU~-1~||-1||~-1; COM_TEST_FIX=2023-06-14T07%3A13%3A23.175Z; locDestZip=07094; locStoreId=474; sc-location-v2=%7B%22meta%22%3A%7B%22CreatedAt%22%3A%222023-06-14T07%3A13%3A42.471Z%22%2C%22ModifiedAt%22%3A%222023-06-14T07%3A13%3A42.888Z%22%2C%22ExpiresAt%22%3A%222024-06-13T07%3A13%3A42.888Z%22%7D%2C%22value%22%3A%22%7B%5C%22physical%5C%22%3A%7B%5C%22zipCode%5C%22%3A%5C%2207094%5C%22%2C%5C%22source%5C%22%3A%5C%22A%5C%22%2C%5C%22captureTime%5C%22%3A%5C%222023-06-14T07%3A13%3A42.471Z%5C%22%7D%2C%5C%22destination%5C%22%3A%7B%5C%22zipCode%5C%22%3A%5C%2207094%5C%22%7D%2C%5C%22store%5C%22%3A%7B%5C%22storeId%5C%22%3A474%2C%5C%22zipCode%5C%22%3A%5C%2207094%5C%22%2C%5C%22storeHydratedCaptureTime%5C%22%3A%5C%222023-06-14T07%3A13%3A42.887Z%5C%22%7D%7D%22%7D; _gcl_au=1.1.1979793039.1686726825; _cs_c=1; dtCookie=v_4_srv_3_sn_DNPDJG1TQA0IJ3SNTHUV5J8AI2UAEFJE_app-3Aea7c4b59f27d43eb_1_app-3A1b02c17e3de73d2a_1_ol_0_perc_100000_mul_1; s_ecid=MCMID%7C17393200060746450538840418075823270172; AMCVS_F6301253512D2BDB0A490D45%40AdobeOrg=1; _cs_mk=0.17759385916397719_1686727033847; __gsas=ID=b2b071aabe694720:T=1686727054:RT=1686727054:S=ALNI_MYGeqqukdFN5X69Ve6TEpBwiGdqoA; surveyDisabled=true; intl_splash=false; intl_splash=false; AMCV_F6301253512D2BDB0A490D45%40AdobeOrg=1585540135%7CMCMID%7C17393200060746450538840418075823270172%7CvVersion%7C4.4.0%7CMCAID%7CNONE%7CMCOPTOUT-1686740752s%7CNONE%7CMCAAMLH-1687338352%7C3%7CMCAAMB-1687338352%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCCIDH%7C-1411464467; bby_cbc_lb=p-browse-e; ltc=%20; __gads=ID=f62c040d0bce8121:T=1686726811:RT=1686734790:S=ALNI_MaLsx3nZayYxZD3OA_zWlVQ8FlTCg; __gpi=UID=00000c4ec376ba50:T=1686726811:RT=1686734790:S=ALNI_MZGo5SknogdNPhXj1FALKV5AMNDTw; dtSa=-; cto_bundle=zlbDdl94U2glMkZ5dSUyRkEzT3NTYmpxN2RSUkhsZUt4QnVVV1ZjdzV0ZU5ZdW1GSzA5RWVnTlRzVEp0WVpIZkVPaTklMkJrTkRsV1BiUWRseDIwRCUyQm1saGMlMkIyMDZXVHZjY0JodW5EZGk5cGIyaUNxbk1TJTJCNFVUQmRlU1B1OU5ZMjBldVo0eTVtc1ZGdDFQcTR5TGx2T3JnVmtLJTJGNjclMkJBJTNEJTNE; _cs_id=f049f0af-d1c5-a7eb-d2f7-6482cd674e86.1686726826.2.1686735003.1686731203.1645469968.1720890826936; _cs_s=8.0.0.1686736803802; rxvt=1686736809395|1686731034557; dtPC=3$134971816_764h-vQDNUPHAKRECKUIICUOWKUHRFJEIFNPJU-0e0; c2=no%20value; dtLatC=4',
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
        self.all_keywords = self.read_input_file()
        self.counter = 0

    def start_requests(self):
        for keyword in self.all_keywords:
            # url1 = f'https://www.bestbuy.com/site/combo/motherboards/dc0a8810-8594-45c4-8ce3-b9cfa9bfc08a'
            url = f'https://www.bestbuy.com/site/searchpage.jsp?st={keyword}&intl=nosplash'
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.parse,
                meta={'keyword': keyword}
            )

    def parse(self, response):
        products_urls = response.css('.sku-title a::attr(href)').getall()
        for product_url in products_urls:
            yield Request(response.urljoin(product_url), headers=self.headers, callback=self.product_detail,
                          meta=response.meta)

        next_page = response.css('.sku-list-page-next::attr(href)').get('')

        if next_page:
            yield Request(response.urljoin(next_page), headers=self.headers, callback=self.parse,
                          meta=response.meta)

    def product_detail(self, response):

        # script = json.loads(re.search(r'<script[^>]+>\s*({.*?})\s*</script>',
        #                               response.css(
        #                                   'script[type*="application/json"]:contains("app"):contains("abTests")').get(
        #                                   '')).group(1))
        try:
            json_data = json.loads(response.css('script:contains("priceChangeTotalSavingsAmount")::text').get(''))
            price_data = json_data.get("app", {}).get("data", {}) or {}
        except json.JSONDecodeError:
            json_data = {}
            price_data = {}
        except AttributeError:
            json_data = {}
            price_data = {}
        item = BestbuyProductsItem()
        item['Title'] = response.css('.sku-title h1::text').get('')
        item['Model'] = response.css('.product-data-value::text').get('')
        item['Sku'] = response.css('.sku.product-data .product-data-value::text').get('')
        item['Image'] = response.css('.media-gallery-base-content.thumbnails a::attr(href)').get()
        if not item['Image']:
            item['Image'] = response.css('.primary-image-grid ::attr(src)').getall()

        item['URL'] = response.url
        item['Discounted_Price'] = price_data.get("customerPrice", '') or ''
        item['Actual_Price'] = price_data.get('regularPrice', '') or ''
        item['Discount_Amount'] = price_data.get('priceChangeTotalSavingsAmount', '') or ''
        item['Description'] = response.css('.html-fragment::text').get('')
        item['Status'] = 'Out of stock' if response.css(
            '.fulfillment-fulfillment-summary:contains("Sold Out")') else 'In stock'
        item['keyword'] = response.meta['keyword']

        # item['Discounted_Price'] = script.get("app", {}).get("data", {}).get("customerPrice", '')
        # Discounted_Price = response.css('.priceView-customer-price span::text').re_first(r'\d+[\d.,]*')
        # was_price = response.css('.pricing-price__regular-price::text').re_first(r'\d+')

        yield item

    def read_input_file(self):
        try:
            file_path = os.path.join('input', 'keywords.txt')
            all_keywords = []

            with open(file_path, 'r') as text_file:
                return [all_keywords.strip() for all_keywords in text_file.readlines() if all_keywords.strip()]

            #     for line in file:
            #         keyword = line.strip()
            #         all_keywords.append(keyword)
            #
            # return all_keywords
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []
