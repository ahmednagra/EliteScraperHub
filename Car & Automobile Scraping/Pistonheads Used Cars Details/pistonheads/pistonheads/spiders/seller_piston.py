from scrapy import Request, Spider
import json
from collections import OrderedDict

from math import ceil


class SellerPistonSpider(Spider):
    name = "sellerpiston"
    start_urls = ['https://www.pistonheads.com/buy/search']

    headers = {
        'authority': 'www.pistonheads.com',
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'content-type': 'application/json',
        'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjM3NjA0IiwiYXAiOiI0NDg0MTY0ODYiLCJpZCI6ImY0MzAwNGVhMWM2ZTJlOTUiLCJ0ciI6IjcyMjBhYzMxMDc3YzEyNGI3ZjgwMGUxZTU1Yzk1ZjgwIiwidGkiOjE3MDQ2OTM4NjQ4ODh9fQ==',
        'referer': 'https://www.pistonheads.com/buy/search',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'traceparent': '00-7220ac31077c124b7f800e1e55c95f80-f43004ea1c6e2e95-01',
        'tracestate': '37604@nr=0-1-37604-448416486-f43004ea1c6e2e95----1704693864888',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    custom_settings = {
        'FEEDS': {
            'output/Pistonheads Sellers Details.csv': {
                'format': 'csv',
                'fields': [
                    'Dealer ID', 'Dealer Name', 'Dealer Account Type', 'Dealer Account Status',
                    'Dealer Type', 'Dealer Post Code', 'Dealer Address', 'Dealer Phone',
                    'Dealer Logo URL', 'Dealer Stock List', 'URL',
                ],
                'overwrite': 'yes',
            }
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = self.read_config_file()
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = True
        self.product_counter = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.pagination)

    def pagination(self, response):
        json_data = json.loads(response.css('script#__NEXT_DATA__ ::text').get(''))
        cars_dict = (json_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})
        .get('ROOT_QUERY', {}).get(
            'searchPage({"input":{"categoryName":"used-cars","distance":"2147483647","includeFullSizeImageUrls":true,"includeSpecificationData":true,"numberOfFeaturedAdverts":3,"returnRefineSearchPanelFacets":true},"limit":18,"offset":0})',
            {}))

        total_cars = cars_dict.get('total', 0)
        total_pages = ceil(total_cars / 100)

        for page_no in range(1, total_pages + 1):
            url = self.get_indexpage_request_url(page_no)
            yield Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            data = response.json()
        except json.decoder.JSONDecodeError:
            print('Error in parsing JSON')
            return
        if data.get('errors') or not data.get('data', {}):
            return

        cars_ids = [x.get('id') for x in data.get('data', {}).get('searchPage', {}).get('adverts', [{}])]
        for car_id in cars_ids:
            url = f'https://www.pistonheads.com/buy/listing/{car_id}'
            yield Request(url=url, callback=self.parse_details, headers=self.headers)

    def parse_details(self, response):
        try:
            data = json.loads(response.css('script#__NEXT_DATA__ ::text').get(''))
        except json.decoder.JSONDecodeError:
            print('Error in parsing JSON')
            return

        info = data.get('props', {}).get('pageProps', {}).get('pageDna').get('product', {})
        dealer_id = info.get('dealer_id')

        car = data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

        seller = f'Seller:{dealer_id}'
        dealer_data = car.get(seller, {})

        item = OrderedDict()

        item['Dealer ID'] = dealer_data.get('id', '')
        item['Dealer Account Type'] = dealer_data.get('accountType', '')
        item['Dealer Account Status'] = dealer_data.get('accountStatus', '')
        logo_url = dealer_data.get("dealerLogoUrl", "")
        item['Dealer Logo URL'] = f'https:{logo_url}' if logo_url else ''
        item['Dealer Stock List'] = dealer_data.get('dealerStockListUrl', '')
        dealer_name = dealer_data.get('name', '')
        item['Dealer Name'] = dealer_name
        address = dealer_data.get('location', '')
        item['Dealer Address'] = f"{dealer_name}, {address}" if address else ''
        item['Dealer Post Code'] = dealer_data.get('sellerPostcodeDistrict', '')
        item['Dealer Type'] = dealer_data.get('sellerType', '')
        item['Dealer Phone'] = dealer_data.get('phone', '')
        item['URL'] = response.url

        self.product_counter += 1
        print(f'Product Counter : {self.product_counter}')

        yield item

    def get_indexpage_request_url(self, page_no):
        json_request = f'https://www.pistonheads.com/api/graphql?operationName=SearchPage&variables={{"categoryName":"used-cars","distance":"2147483647","sellerType":"Trade","limit":100,"offset":{page_no},"numberOfFeaturedAdverts":3}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"18ba74a58d81963920bf6c02c5bf57f9bda5dad9783e8749d254bba6344aff0b"}}}}'
        return json_request

    def read_config_file(self):
        file_path = 'input/config.json'
        config = {}

        try:
            with open(file_path, mode='r') as json_file:
                data = json.load(json_file)
                config.update(data)

            return config

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            return {}
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return {}
