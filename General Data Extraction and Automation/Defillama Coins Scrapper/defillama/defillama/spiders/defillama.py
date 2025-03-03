import json

import requests
import scrapy
from scrapy import Request


class DefillamaSpider(scrapy.Spider):
    name = "defillama"
    start_urls = ["https://defillama.com/stablecoins"]  # by defualt url
    # start_urls = ["https://stablecoins.llama.fi/stablecoins"]  # all currencies json output

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,

        'FEEDS': {
            f'output/Defillama details.csv': {
                'format': 'csv',
                'fields': ['Title', 'EAN', 'Price', 'Description', 'Description HTML', 'Image1 URL', 'Image2 URL',
                           'Image3 URL', 'Image4 URL', 'URL'],
            }
        },
        'MEDIA_ALLOW_REDIRECTS': True,
    }

    headers = {
        'authority': 'defillama.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'if-none-match': 'W/"16l6x5idykp3dau"',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/117.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response, **kwargs):
        # response from https://defillama.com/stablecoins

        json_data = json.loads(response.css('#__NEXT_DATA__').re_first(r'{.*}'))

        session_id = json_data.get('buildId', '')
        session_id = session_id or response.css('script[src*="_buildManifest.js"]::attr(src)').get('').split('/')[3]
        chains = [x.get('gecko_id') for x in json_data.get('props', {}).get('pageProps', {}).get('filteredPeggedAssets', [])]

        for chain in chains:
            url = f'https://defillama.com/_next/data/{session_id}/stablecoin/{chain}.json?peggedasset={chain}'
            yield Request(url=url, callback=self.parse_detail)

        # try:
        #     data = response.json().get('peggedAssets')
        # except Exception as e:
        #     print("Caught a general exception:", e)
        #
        # currencies_urls = [x.get('gecko_id') for x in data]
        #
        # for currency_url in currencies_urls[:1]:
        #     url = f'https://defillama.com/stablecoin/{currency_url}'
        #     default_url = 'https://defillama.com/_next/data/5496985bff0c2ce04b321592c465852a7437b59e/stablecoin/usd-coin.json?peggedasset=usd-coin'
        #     # url = f'https://defillama.com/_next/data/5496985bff0c2ce04b321592c465852a7437b59e/stablecoins/{currency_url}.json?peggedasset={currency_url}'
        #     yield Request(url=url, callback=self.parse_detail)

    def parse_detail(self, response):
        try:
            json_data = response.json().get('pageProps', {})
        except Exception as e:
            json_data = {}
            print('error is as :', e)

        # coins_selectors = response.css('.fchSFM tr')
        # session_id = response.css('script[src*="_buildManifest.js"]::attr(src)').get('').split('/')[3]
        #
        # for coin_selector in coins_selectors:
        #     chain = coin_selector.css(' a::text').get('')
        #     bridge = coin_selector.css('a:contains("Bridge").dJIwUT ::text').get('')
        #     keyword = chain.split()[0]
        #     url = f'https://defillama.com/_next/data/5496985bff0c2ce04b321592c465852a7437b59e/stablecoins/{keyword}.json?peggedasset={keyword}'
        #
        #     print(f'chain Name:{chain}.,  Bridge Names :{bridge}')
        #     a = 1
