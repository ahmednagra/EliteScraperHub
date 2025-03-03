import json
from collections import OrderedDict
from math import ceil

import scrapy
from scrapy import Request


class WeedmapsspiderSpider(scrapy.Spider):
    name = 'weedmaps'
    start_urls = [
        'https://weedmaps.com/listings/in/united-states?sortBy=position_distance&filter%5BanyRetailerServices%5D%5B%5D=delivery&filter%5BanyRetailerServices%5D%5B%5D=storefront']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/{name} Stores Scraper Detail.csv': {
                'format': 'csv',
                'overwrite': True,
            }
        }
    }

    headers = {
        'authority': 'weedmaps.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'ajs_anonymous_id=e0bc84ac-7dd4-4f01-b111-cd0e5eef7bc6; _pxhd=EFIHlUFc84Yn47OWPqQUxDdz1IVGnc1Np5EhP9U/bPIRfkOH1tJEsJ50Ss9Um1jX74BA9fNFwKRYqkDJCeJa1Q==:Lh3f6RmjCuD46Fvi-CpFmD50nmlmmBP8sXoYaVNIeEoZ/bQsWUwKbwM0nnjg6vPdYiBDismKwzJB0vEumcfCnh1f1zlCb3KOBli/GivcgXo=; _pxvid=35ef50a9-7540-11ee-917b-c3041da03e27; pxcts=37d41894-7540-11ee-a9d9-f4aea25d70ea; _gid=GA1.2.1793142248.1698462919; _hp2_ses_props.2527959437=%7B%22ts%22%3A1698466586369%2C%22d%22%3A%22weedmaps.com%22%2C%22h%22%3A%22%2Flistings%2Fin%2Funited-states%22%2C%22q%22%3A%22%3FsortBy%3Dposition_distance%26filter%255BanyRetailerServices%255D%255B%255D%3Ddelivery%26filter%255BanyRetailerServices%255D%255B%255D%3Dstorefront%22%7D; ab.storage.deviceId.6f1b7c1f-43af-433a-90c0-cc4c7474dae3=%7B%22g%22%3A%221dac7b02-b8c6-8172-587d-5ffa6e311d1d%22%2C%22c%22%3A1698462928945%2C%22l%22%3A1698466590093%7D; ab.storage.userId.6f1b7c1f-43af-433a-90c0-cc4c7474dae3=%7B%22g%22%3A%22e0bc84ac-7dd4-4f01-b111-cd0e5eef7bc6%22%2C%22c%22%3A1698462928933%2C%22l%22%3A1698466590093%7D; ab.storage.sessionId.6f1b7c1f-43af-433a-90c0-cc4c7474dae3=%7B%22g%22%3A%22498934d7-6a2b-4da5-6289-6482fe7ddfed%22%2C%22e%22%3A1698468957277%2C%22c%22%3A1698466590092%2C%22l%22%3A1698467157277%7D; _wm_max_conf_age=18; dicbo_fetch=true; _px2=eyJ1IjoiZWNhZWVkOTAtNzU0ZS0xMWVlLWExYzctMDkxZjNhZmI0NDhhIiwidiI6IjM1ZWY1MGE5LTc1NDAtMTFlZS05MTdiLWMzMDQxZGEwM2UyNyIsInQiOjE2OTg0Njk1MzU2MzMsImgiOiJiMmJmYmI3YWE2NGVlNGRkMDAxMzgzYTQyYTllN2M3YWYyNDIzNTllMzFlMzBhMTg5Njc5MzlhNzM5M2I4MTI3In0=; _hp2_id.2527959437=%7B%22userId%22%3A%223077696658405656%22%2C%22pageviewId%22%3A%223074755033931071%22%2C%22sessionId%22%3A%224094907024792230%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%224.0%22%7D; _gat=1; _ga_PNX08RFZF3=GS1.1.1698466559.2.1.1698469235.0.0.0; _ga=GA1.1.1353249484.1698462919; _dd_s=rum=0&expire=1698470133455',
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }

    def parse(self, response, **kwargs):
        try:
            data = json.loads(response.css('#__NEXT_DATA__').re_first(r'{.*}'))
            dict_data = [x.get('state', {}.get('data', [{}])) for x in
                         data.get('props', {}).get('dehydratedState', {}).get('queries', [])]
            list_data = [x.get('data', [{}]) for x in dict_data][1]
            # states = [x.get('regionPath', '') for x in list_data[1]]
        except Exception as e:
            data = {}
            list_data = []
            print('def parse :The error is :', e)

        for row in list_data:
            state_name = row.get('name', '')
            url_value = row.get('regionPath', '')
            url = f'https://weedmaps.com/listings/in/{url_value}'
            yield Request(url=url, callback=self.parse_states)

    def parse_states(self, response):
        # state_name = response.meta.get('state_name', '')
        try:
            data = json.loads(response.css('#__NEXT_DATA__').re_first(r'{.*}'))
            dict_data = [x.get('state', {}.get('data', [{}])) for x in
                         data.get('props', {}).get('dehydratedState', {}).get('queries', [])]
            list_data = [x.get('data', [{}]) for x in dict_data][1:2][0]
            # list_data = [x.get('data', [{}]) for x in dict_data]
            # cities = [x.get('regionPath', '') for x in list_data[1]]
        except Exception as e:
            data = {}
            list_data = []
            print('Def parse_states: The error is :', e)

        # for city in cities[:1]:
        for row in list_data:
            city_name = row.get('name', '')
            url_value = row.get('regionPath', '')
            url = f'https://weedmaps.com/listings/in/{url_value}'
            yield Request(url=url, callback=self.parse_city_stores_pagination)

    def parse_city_stores_pagination(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__').re_first(r'{.*}'))
            dict_data = [x.get('state', {}).get('data', [{}]) for x in
                         data.get('props', {}).get('dehydratedState', {}).get('queries', [{}])]
            total_products = [x.get('meta', {}).get('totalListings', {}) for x in dict_data if 'data' in x][0]
            location = data.get('props', {}).get('storeInitialState', {}).get('regions', {}).get('current', {}).get(
                'doctor', {})

        except Exception as e:
            data = {}
            location = {}
            total_products = ''
            print('Def parse_city_stores_pagination: The error is :', e)

        latitude = location.get('latitude', 0)
        longitude = location.get('longitude', 0)

        total_pages = ceil(total_products / 150)
        for page in range(1, total_pages + 1):
            page_size = 150
            url = f'https://api-g.weedmaps.com/discovery/v2/listings?latlng={latitude},{longitude}&sort_by=position_distance&page={page}&page_size={page_size}&filter[bounding_radius]=500mi&filter[bounding_latlng]={latitude},{longitude}'
            yield Request(url=url, callback=self.parse_city_stores, headers=self.headers, meta=response.meta)

    def parse_city_stores(self, response):
        try:
            data = response.json()
            stores_url = [x.get('web_url', '') for x in data.get('data', {}).get('listings', [{}])]
        except Exception as e:
            data = {}
            stores_url = []
            print('Def parse_city_stores: The error is :', e)

        for store in stores_url:
            yield Request(url=store, callback=self.parse_store_detail, headers=self.headers)

    def parse_store_detail(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__').re_first(r'{.*}'))
            store_data = data.get('props', {}).get('storeInitialState', {}).get('listing', {}).get('listing', {})
        except Exception as e:
            data = {}
            store_data = {}
            print('The error is :', e)

        address_row = store_data.get('address', '')
        city = store_data.get('city', '')
        state = store_data.get('state', '')
        zip_code = store_data.get('zip_code', '')

        item = OrderedDict()
        item['State Name'] = store_data.get('state', '')
        item['City Name'] = store_data.get('city', '')
        item['Store Name'] = store_data.get('name', '')
        item['Store Address'] = f'{address_row}, {city}, {state} {zip_code}'
        item['Store Phone Number'] = store_data.get('phone_number', '')
        item['Store Email'] = store_data.get('email', '')
        item['Store Instagram Account URL'] = self.get_instagram_link(store_data)
        # item['Store Instagram Account URL'] = store_data.get('social', {}).get('instagram_id', '')
        item['Store Details Page URL'] = response.url + '#details'

        yield item

    def get_instagram_link(self, store_data):
        insta = store_data.get('social', {}).get('instagram_id', '')
        if insta:
            if not 'instagram.com' in insta:
                url = f'https://www.instagram.com/{insta}/'
            else:
                url = insta
        else:
            url = insta

        return url
