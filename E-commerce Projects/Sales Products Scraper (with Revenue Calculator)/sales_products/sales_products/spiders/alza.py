import json
from collections import OrderedDict
from urllib.parse import urljoin

from .base import BaseSpider


class AlzaScraperSpider(BaseSpider):
    name = 'alza'
    base_url = 'https://www.alza.de/'
    start_urls = ['https://www.alza.de/verkauf-aktion-rabatt/e0.htm']

    headers = {
        'authority': 'www.alza.de',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'de-DE',
        'cache-control': 'no-cache',
        'content-type': 'application/json; charset=UTF-8',
        # 'cookie': 'VZTX=7502826057; VST=babd7a37-7c1d-ee11-8433-0c42a19546e5; .AspNetCore.Culture=c%3Dde-DE%7Cuic%3Dde-DE; __ssds=2; __ssuzjsr2=a9be0cd8e; __uzmaj2=c773fd62-ffa2-483d-a6df-888d7cceadbe; __uzmbj2=1688812999; ALWCS=1023; CBARIH=1; _gcl_au=1.1.1634620087.1688813008; _fbp=fb.1.1688813008690.466195436; PAPVisitorId=eEWdmkx8z488BbIfUuMen76WjKWvxHCV; PAPVisitorId=eEWdmkx8z488BbIfUuMen76WjKWvxHCV; _hjSessionUser_2285381=eyJpZCI6IjE5NzQyZGE5LTUyYzItNWE2Ny1hZjllLTBjNGVhNzY3YTM3OCIsImNyZWF0ZWQiOjE2ODg4MTMwMDk1MzIsImV4aXN0aW5nIjp0cnVlfQ==; ai_user=HFa0Z3KkqTT5YJJypqAYSt|2023-07-13T10:54:56.764Z; disable_chat=disable; __uzmcj2=2389828679306; __uzmdj2=1689357153; _ga_TLYLXDRYPJ=GS1.1.1689357061.9.1.1689357505.60.0.0; lb_id=5b7872cc7c335cedda08fabf709c7ae6; CriticalCSS=5195256; _gid=GA1.2.1478587554.1689759979; _hjSession_2285381=eyJpZCI6Ijg4MjQyZjgzLTYyMzMtNGE4Yi1iMjk2LWU3NTJjNjFhMjJmOCIsImNyZWF0ZWQiOjE2ODk3NTk5ODQzMTMsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; _hjIncludedInSessionSample_2285381=0; cf_clearance=MPg02nAabuIbkVZaGCWlvtaaf2OiVA9jbSgGRZ.OdhI-1689762040-0-0.2.1689762040; _ga=GA1.1.1004306112.1688813008; hvrcomm=7679856; sc/computer-und-laptops/ausverkauf/18890188-y842.htm=7502.39990234375; PVCFLP=92; __cf_bm=bgKTASLE2EKU7MCMFjCunEiLeKil0BYTgVnaTBCDyOQ-1689762926-0-ATsgrwr0rYKwrHr7153Iuys9fsRNe3UD5Nue6CswBoXqN/oIe1OXRNdmcvLRwgA1vHJjNyU093asZ0KC9Slu168=; _ga_PNTL7LXH7F=GS1.1.1689759978.10.1.1689762930.60.0.0; ai_session=qqBdGwOtE4H0Zgaa3U8s5U|1689759971296|1689762934395',
        'origin': 'https://www.alza.de',
        'referer': 'https://www.alza.de/computer-und-laptops/ausverkauf/18890188-y842.htm',
        'request-id': '|0436c348fef044809748dd0062ecd44b.08fe1330cbc24195',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'traceparent': '00-0436c348fef044809748dd0062ecd44b-08fe1330cbc24195-01',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_proxy = True
        self.categories = '.top .de a:not(.til)::attr(href)'
        self.product_url = '.browsinglink::attr(href)'
        self.products = '.inStockAvailability'
        self.new_price = '.browsinglink::attr(data-gtm-commodity-price-vat)'
        self.next_page = '.fa-chevron-right::attr(href)'

    def product_detail(self, response):
        item = OrderedDict()

        try:
            data = json.loads(response.css('script:contains(gtin)::text').get())
        except Exception as e:
            print(f"An error occurred: {e}")
            data = []

        item['Product Title'] = data.get('name', '')
        item['Price'] = data.get('offers', {}).get('price', '')
        item['EAN'] = f"'{data.get('gtin13', '')}"
        item['URL'] = response.url

        self.current_scraped_items.append(item)
        yield item

