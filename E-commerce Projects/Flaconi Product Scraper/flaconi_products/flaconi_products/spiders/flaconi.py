import json
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request


class FlaconiSpider(Spider):
    name = 'flaconi_usama'

    headers = {
        'authority': 'www.flaconi.de',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        # 'cookie': 'FCSESSID0815=2ecbadb195431c375e04b2d1438f3d60; nr-user-session=60590b7a-d30f-415c-a0d3-1a48f15df9ea; flaconi_criteo=criteo-flaconikWWart8cweSd8a6nSKmv7QsiT3Meua9SW9WNcNf3hqhazXYC4; flaconi_algolia=algolia-flaconiRthBrkZahrKsm3esYHKQXoVq3SDAaDjCBrac6ihl3Pr3EIXRh; wtstp_sid=1; wtstp_eid=2168577409236986215; lantern=a2499b51-c719-41f6-9d7e-3b87822df24c; scarab.visitor=%2275B51DC10534E807%22; _hjFirstSeen=1; _hjSession_2289781=eyJpZCI6Ijk1NWQzZDgwLTI0OTItNDI0Ni1iY2ZiLTQ3NGFhNzE0Mzk5NyIsImNyZWF0ZWQiOjE2ODU3NzQwOTg2NDMsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=1; _tt_enable_cookie=1; _ttp=8n9vb95n7Ei1Xif2dhBdn2xhzUV; _dyjsession=hyb8qnfe1akxg31xzwvcivejh1bor4q7; axd=4329835123458753877; _pin_unauth=dWlkPU1qY3pOalppTW1VdFlqbGlNaTAwWlRka0xUbGxOREV0Tnpjd1lqVTVOVGMxTkdabA; tis=; _clck=ywwokx|2|fc5|0|1249; _dyid=-8944147913379225836; _dyid_server=-8944147913379225836; _hjSessionUser_2289781=eyJpZCI6ImRiODQyOGRhLWNiNmQtNTAxYy1hNjJhLWVlZWIwYTM5N2M2MSIsImNyZWF0ZWQiOjE2ODU3NzQwOTg2MDgsImV4aXN0aW5nIjp0cnVlfQ==; scarab.profile=%2280041833-C%7C1685774381%22; wtstp_pli_view=30103357%7C74~30150001%7C3~80041833-c%7C1%2C1~80014066-c%7C24%2C24; _sp_ses.3fa7=*; _sp_id.3fa7=e6fffe8709f7461a.1685774391.2.1685780322.1685777708; __cf_bm=9FANhRY86_QT6ICU1MhP1ROAsSgPSqB9ihr_VMLKT5s-1685780630-0-AbYZU2efUx6otGPNvepTpTXxgwmwCNZfX5/i2/XlBVlbIWGDcwHYGJQs6vtvrbiDqLcExYSddmI+uNYUXH7D540=; _uetsid=c21b367001d811eea933cdc34ce6506f; _uetvid=c21bb3e001d811eeb4704711d7b34b7b; _hjIncludedInSessionSample_2289781=0; dprt_main=v_id:01887ff766bf0069d68cfe1e16180506f001c0670086e$_sn:1$_se:28$_ss:0$_st:1685782442870$ses_id:1685774100161%3Bexp-session$_pn:28%3Bexp-session; _clsk=6puif8|1685780647755|37|1|v.clarity.ms/collect',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    # custom_settings = {
    #     'CONCURRENT_REQUESTS': 8,
    #     'FEEDS': {
    #         f'output/Flaconi {datetime.now().strftime("%d%m%Y %H%M")}.csv': {
    #             'format': 'csv',
    #         }
    #     }
    # }

    def start_requests(self):
        yield Request(url='https://www.flaconi.de/sale/',
                      headers=self.headers
                      )

    def parse(self, response, **kwargs):
        for category_url in response.css('.SubList--1jqct33 li a::attr(href)').getall():

            yield Request(url=response.urljoin(category_url),
                          callback=self.parse_product_urls,
                          headers=self.headers)

    def parse_product_urls(self, response):
        for product in response.css('.Wrapper--1mnqijk'):
            yield Request(url=response.urljoin(product.css('a::attr(href)').get('')),
                          callback=self.parse_variants,
                          headers=self.headers)

        next_page = response.css('.NextPage--12pshlr ::attr(href)').get('')

        if next_page:
            yield Request(url=response.urljoin(next_page),
                          callback=self.parse_product_urls,
                          headers=self.headers
                          )

    def parse_variants(self, response):
        try:
            json_data = json.loads(response.css('script:contains("gtin") ::text').get(''))
        except json.JSONDecoder:
            return

        name = json_data.get('name', '')

        for offer in json_data.get('offers', [{}]):
            item = OrderedDict()
            item['Name'] = name
            item['Price'] = offer.get('price', '')
            item['EAN'] = offer.get('gtin13', '')
            item['URL'] = offer.get('url', '')

            yield item

