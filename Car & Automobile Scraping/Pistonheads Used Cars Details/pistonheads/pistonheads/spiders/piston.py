import json
from math import ceil
from collections import OrderedDict

from scrapy import Request, Spider


class PistonSpider(Spider):
    name = "piston"
    start_urls = ['https://www.pistonheads.com/buy/search']

    headers = {
        'authority': 'www.pistonheads.com',
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'content-type': 'application/json',
        # 'cookie': 'a98db973kwl8xp1=1; NKCQJDMUIH9ZIX6G3F68QIGCPN2IZ3=1; ph-experiments=a98db973kwl8xp1.1!NKCQJDMUIH9ZIX6G3F68QIGCPN2IZ3.1; _sp_ses.a92f=*; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22false%22%7D; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22p17kvANuRudXTxPjiHW7%22%7D; _fbp=fb.1.1704693035648.1266189882; _gcl_au=1.1.1799202999.1704693036; _gid=GA1.2.1407586926.1704693036; _hjFirstSeen=1; _hjIncludedInSessionSample_1650648=0; _hjSession_1650648=eyJpZCI6IjA0NTY5MDA3LTc2OWUtNDEyMy1iOGZjLWRiNGI2MWEzMWRjYSIsImMiOjE3MDQ2OTMwMzU4NjcsInMiOjAsInIiOjAsInNiIjowfQ==; _hjAbsoluteSessionInProgress=0; _gu=c5b395bc-a368-4c2b-9247-e19bce21f29b; _gs=2.s()c%5BDesktop%2CChrome%2C62%3A385%3A10271%3A%2CWindows%2C39.35.85.5%5D; euconsent-v2=CP4EE4AP4EE4AAKAyAENAiEsAP_gAEPgAAwIg1NX_H__bW9r8Xr3aft0eY1P99j77sQxBhfJE-4FzLvW_JwXx2ExNA26tqIKmRIEu3ZBIQFlHJHURVigaogVryHsYkGcgTNKJ6BkgFMRM2dYCF5vmYtj-QKY5_p9d3fx2D-t_dv83dzzz8VHn3e5fmckcJCdQ58tDfn9bRKb-5IOd_78v4v09F_rk2_eTVn_tcvr7B-uft87_XU-9_ffcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEQagCzDQqIA-yJCQi0HCKBACIKwgIoEAAAAJA0QEAJgwKdgYBLrCRACBFAAMEAIAAUZAAgAAEgAQiACQAoEAAEAgEAAAAAAgEADAwADgAtBAIAAQHQMUwoAFAsIEjMiIUwIQoEggJbKBBICgQVwgCLHAigERMFAAgCQAVgAAAsVgMQSAlYkECWEG0AABAAgFFKFQik6MAQwJmy1U4om0ZWAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAACAA.YAAAAAAAAAAA; _lr_geo_location=PK; cto_bundle=vmmxTV85VTRQVlZTa3pBRjAlMkJYUWRXUDJ4dVYlMkIzWExTZkZoUmhtdXM5S1VLUzJpMm5oREVSRjVDN2ZWV0RlYzNFWnJwa3NMWVV1N0F3JTJCWXdhMmxaelJjenZGeTJ4M0FnR3E1MlNYZSUyQmJlY0RHUWZza1diMmN5Tk9iU1JORDFCYyUyRldhUksySmRKMkhac2U4TXpkTjZjMnRJVkhSZlFMZHpHbiUyQnNuNkxEaTVQS2wzZzVRWnRHSmxISVclMkI3b05MJTJCZzN0QWxaTFJpSGpiUnVFM1lITEdkZmJ0eXBGc3BaRFg0VzBtZEp3eHRrbkdVeTRiZyUzRA; _au_1d=AU1D-0100-001704693045-3MERPT1T-C8LT; _au_last_seen_iab_tcf=1704693045833; _hjSessionUser_1650648=eyJpZCI6IjBiYzE1Zjk4LWEyMzctNTQ4Ni04MzE3LWJlMGE4ZWUzODg0MiIsImNyZWF0ZWQiOjE3MDQ2OTMwMzU4NjUsImV4aXN0aW5nIjp0cnVlfQ==; sailthru_content=c3e02046c636ca71b10c18bbe4ef0a799af7bde02dae1678a601487df6f915d1e6bfdab63184be80fec58618adb4cdb7; __gads=ID=b92b9c0b0eee7439:T=1704693052:RT=1704693506:S=ALNI_Mb99KKLAK6Vvy_JdTtis6aDXlNn1w; __gpi=UID=00000cf14ce1b21e:T=1704693052:RT=1704693506:S=ALNI_MbwbJEQkZfaZpWC0JVmbZOpT2ce0g; sailthru_visitor=a3f286f1-570c-4e81-a6cc-a7b2cd472d54; sailthru_pageviews=7; _gw=2.u%5B%2C%2C%2C%2C%5Dv%5B~gwyi2%2C~7%2C~0%5Da(); _ga=GA1.2.1493886321.1704693035; _sp_id.a92f=e5f1ee8e-def7-469b-99a8-e3922bcc8c72.1704693035.1.1704693860.1704693035.97060937-9eb3-49cd-915a-b4454488b95e; _gat_UA-7771011-33=1; _ga_4NE6HXSTXT=GS1.1.1704693034.1.1.1704693864.0.0.0',
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
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1.0,  # Initial delay in seconds
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  # Adjust as needed
        'AUTOTHROTTLE_DEBUG': True,  # Set to True for debugging

        'CONCURRENT_REQUESTS': 3,
        'FEEDS': {
            'output/Pistonheads Used Cars Details.csv': {
                'format': 'csv',
                'fields': [
                    'Title', 'Make', 'Model', 'Year', 'Vin No', 'Condition', 'Price',
                    'Brand Type', 'Body Type', 'Fuel Type', 'Fuel Consumption',
                    'Engine Cylinders', 'Engine Power', 'Mileage', 'Color',
                    'Drive Wheel',
                    'Dealer ID', 'Dealer Account Type', 'Dealer Account Status',
                    'Dealer Logo URL', 'Dealer Name', 'Dealer City', 'Dealer State',
                    'Dealer Type', 'Dealer Phone', 'Images', 'URL',
                ]
            }
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_proxy = False
        self.product_counter = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.pagination)

    def pagination(self, response):
        try:
            json_data = json.loads(response.css('script#__NEXT_DATA__ ::text').get(''))
            cars_dict = json_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {}).get(
                'ROOT_QUERY', {}).get('searchPage({"input":{"categoryName":"used-cars","distance":"2147483647","includeFullSizeImageUrls":true,"includeSpecificationData":true,"numberOfFeaturedAdverts":3,"returnRefineSearchPanelFacets":true},"limit":18,"offset":0})',
                {})
        except json.decoder.JSONDecodeError:
            print('Error in parsing JSON for pagination')
            return

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
        car_id = info.get('id', '') or response.url.split('/')[-1]

        car = data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

        Specification = f'SpecificationData:{car_id}'
        specification_data = car.get(Specification, {})

        seller = f'Seller:{dealer_id}'
        dealer_data = car.get(seller, {})

        advert = f'Advert:{car_id}'
        advert_data = car.get(advert, {})
        item = OrderedDict()

        item['Title'] = advert_data.get('headline', '')
        item['Make'] = advert_data.get('make', '') or advert_data.get('makeAnalyticsName', '')
        item['Model'] = advert_data.get('model', '')
        item['Year'] = advert_data.get('year', '')
        item['Vin No'] = advert_data.get('id', '')
        item['Condition'] = advert_data.get('categoryUrlName', '')
        item['Price'] = advert_data.get('price', '')

        item['Brand Type'] = advert_data.get('brandType', '')
        item['Body Type'] = specification_data.get('bodyType', '')
        item['Fuel Type'] = specification_data.get('fuelType', '')
        item['Fuel Consumption'] = specification_data.get('fuelConsumption', '')
        item['Engine Cylinders'] = specification_data.get('engineConfiguration', '')
        item['Engine Power'] = specification_data.get('engineConfiguration', '')
        item['Mileage'] = specification_data.get('mileage', '')
        item['Color'] = specification_data.get('colourCode', '')
        item['Drive Wheel'] = specification_data.get('enginePower', '')

        item['Dealer ID'] = dealer_data.get('id', '')
        item['Dealer Account Type'] = dealer_data.get('accountType', '')
        item['Dealer Account Status'] = dealer_data.get('accountStatus', '')
        item['Dealer Logo URL'] = dealer_data.get('dealerLogoUrl', '')
        item['Dealer Name'] = dealer_data.get('name', '')
        item['Dealer City'] = dealer_data.get('location', '').split(',')[0]
        item['Dealer State'] = dealer_data.get('location', '').split(',')[0]
        item['Dealer Type'] = dealer_data.get('sellerType', '')
        item['Dealer Phone'] = dealer_data.get('phone', '')
        item['Images'] = ', '.join(advert_data.get('fullSizeImageUrls', []))
        item['URL'] = response.url

        yield item

    def get_indexpage_request_url(self, page_no):
        json_request = (f'https://www.pistonheads.com/api/graphql?operationName=SearchPage&variables='
                        f'{{"categoryName":"used-cars","distance":"2147483647","limit":18,"offset":{page_no},'
                        f'"numberOfFeaturedAdverts":0}}&extensions={{"persistedQuery":{{"version":1,'
                        f'"sha256Hash":"18ba74a58d81963920bf6c02c5bf57f9bda5dad9783e8749d254bba6344aff0b"}}}}')

        return json_request
