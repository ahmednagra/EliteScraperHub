from datetime import datetime
import json
from urllib.parse import urljoin, quote

from scrapy import Spider, Request, FormRequest, Selector


class TemuSpider(Spider):
    name = 'temu'
    # start_urls = [
    #     'https://www.temu.com/mens-boots-o3-1544.html?opt_level=2&title=Men%27s%20Boots&_x_enter_scene_type=cate_tab&leaf_type=bro&show_search_type=0&opt1_id=-13&refer_page_name=home&refer_page_id=10005_1689832129228_gyq7anpzd4&refer_page_sn=10005']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'CRAWLERA_ENABLED': True,
        'CRAWLERA_APIKEY': 'bb4c6a0e095e44728ff22ec9a779169d',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_crawlera.CrawleraMiddleware': 610
        },
        'FEEDS': {
            f'output/{name} Products Detail {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Product Title', 'Price', 'EAN', 'URL']
            }

        }
    }

    get_headers = {
        'authority': 'www.temu.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        # 'cookie': 'api_uid=CnBuKWS6JJK+gQDAGu2IAg==; region=211; language=en; currency=USD; timezone=Asia%2FKarachi; webp=1; _nano_fp=XpEJlpUxX0EjXpd8XT_ouh5jazcPiqjRYGFvEZY9; shipping_city=211; _bee=3fvNvZGlN2766AzG7h7TuiBk8DQhDapK; njrpl=3fvNvZGlN2766AzG7h7TuiBk8DQhDapK; dilx=pYAihrKauUMIj3ZCd4uvF; hfsc=L32CcYAy6Tj+0JXFfQ==',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
    }

    def __init__(self, **kwargs: Any):
        # self.proxy = f"http://scraperapi:56fc6598d3e0166adfb0f01fc59be3e5&keep_headers=true@proxy-server.scraperapi.com:8001"
        # self.proxy = ''
        super().__init__(**kwargs)
        urls_file_path = 'input/urls.txt'
        self.urls = self.get_input_rows_from_file(urls_file_path)

        # From Amazon proxy
        cookies = quote(
            'api_uid=""; region=211; language=en; currency=USD; timezone=Asia%2FKarachi; webp=1; shipping_city=211')
        # # cookies = quote('i18n-prefs=AUD; lc-acbau=en_AU')
        self.proxy = f"http://cef2263bc9d547608ce8aab5fd735feb1d5c2170fa8:customHeaders=true:setCookies={cookies}@proxy.scrape.do:8080"

    def start_requests(self):
        for url in self.urls[5:6]:
            yield Request(url='https://www.temu.com/',
                          # meta={'dont_redirect': True},
                          # headers=self.get_headers,
                          callback=self.parse,
                          meta={'dont_merge_cookies': True}
                          )

    def parse(self, response):
        try:
            api_uid = response.headers.get('Set-Cookie').decode('utf-8').split('=')[1]
        except (IndexError, AttributeError):
            api_uid = ''

        try:
            data = json.loads(response.css('script:contains("rawData")').re_first(r'window\.rawData=(.*})')).get('store', {})
        except (TypeError, AttributeError, json.JSONDecodeError):
            data = {}

        query = data.get('query', {})

        pageSn = query.get('refer_page_sn', '')
        offset = '0'
        pageSize = str(data.get('pageSize', ''))
        pagelistid = data.get('pageListId', '')
        optId = query.get('opt_id', {}) or data.get('pageSn', '')

        # category list id
        listid = data.get('listIdStore', {}).get('listID', '') or data.get('listId', '')
        listid = 'category_list_' + listid

        form_param = json.dumps(self.get_form_param(listid, pageSn, pagelistid, optId, offset, pageSize))
        cookies = self.get_post_cookies(api_uid)
        referer = response.url
        headers = self.get_post_headers(referer)

        cookies = {
            'region': '211',
            'language': 'en',
            'currency': 'USD',
            'api_uid': 'Cm1ONWS4zipgAgCPICXuAg==',
            'timezone': 'Asia%2FKarachi',
            'webp': '1',
            '_nano_fp': 'XpEJlpCqXq9onqdxno_7alv8CmMqZX~P9wFHHmvj',
            '_bee': 'WbJ1rrUazQLl3bDVk6I0ObKvo2L0IapK',
            'njrpl': 'WbJ1rrUazQLl3bDVk6I0ObKvo2L0IapK',
            'dilx': 'XEUoctKAROf0Fz6lVaX0A',
            'hfsc': 'L32CcYEz6j7425TPfQ==',
            'shipping_city': '211',
            'g_state': '{"i_p":1690184825206,"i_l":1}',
            '__cf_bm': '6heRPTTnG3Wyymz4MNBLkVit6w8_zHkrNyYak09Hit4-1690179591-0-AUHrLI0HMBDh/3sqgqVUnHI4OYxlDbwW/zykimiY0pc6EtDLn2pHYbCcij7MY/3RXi5IsvBu1oBRv6xo0xvbr00=',
        }

        headers = {
            'authority': 'www.temu.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
            # 'anti-content': '0aqAfa5e-wCE6SSRPfFghQZqEoXfRpAHP7ug-WbalDx0YTLq3eCRXG-RsA_bwuDJm8F59aMjtbaJC6__iM-Xdykom5Tx8kkkwLTJHQLZBUQUQrlRSqK3yKBVZcH83ULyqgx6B0ixqTu_ti-DzWA2tpMHMEaroQ_dyVr-XN0LprzZmoQC6TrLjp-pY4L-7d1mNOLwSEWGGlEfoQK3xaG-uAheRptpmqXZxilpHafhmjxUhU4ZHVySg502-_wkxoI-6hTwfEaIYTwcmzxU6M82UkB2xoq-lN4L_mHd3UJ9cFMGfleBqA4DfrgQ2nPCbG-9K2z20gA9NQSd67kzEhC5ft_C-PIWW8xNMtiUOpmdI8UJsqi8n_NEO8ZChxZU-Gu3fqNUSqXh6puWBnuPoX5ErjXUOomRLGdOn_ZRPGginpbb5aDToX0TxXyP0NqauDP5lBS86YsVokA0zoAmUEze1Ezeck-wckBwZk-VVkLV-kz2SD-FKEz21e-sCgn0VBqB8MZgZHqtbH4hyDURRe7eADUfl1DLVUSkPwM317UFamIRPdSB2ISBvCI997XptovtHaXn2dm4oKxdHnpUroq_Jwn5m8y5XYdnGoiTMaiu2wxXInpsuapUrQqnwzmXbIxmyQy0Tyni9a9d4gbX_jat2l1Kdg5SH0vtLW9cp4ZY0PJIq4FPZNJ85oaKNq4luA8X41ZGH4x8X80PrmH1bnSFwQXx9h_2wGlcEDRWc62fFze2A-lLmb2MHbwKErKOIEIjDEauIenQVVJCTg9SRN2CIA3uZPJ',
            'content-type': 'application/json;charset=UTF-8',
            # 'cookie': 'region=211; language=en; currency=USD; api_uid=Cm1ONWS4zipgAgCPICXuAg==; timezone=Asia%2FKarachi; webp=1; _nano_fp=XpEJlpCqXq9onqdxno_7alv8CmMqZX~P9wFHHmvj; _bee=WbJ1rrUazQLl3bDVk6I0ObKvo2L0IapK; njrpl=WbJ1rrUazQLl3bDVk6I0ObKvo2L0IapK; dilx=XEUoctKAROf0Fz6lVaX0A; hfsc=L32CcYEz6j7425TPfQ==; shipping_city=211; g_state={"i_p":1690184825206,"i_l":1}; __cf_bm=6heRPTTnG3Wyymz4MNBLkVit6w8_zHkrNyYak09Hit4-1690179591-0-AUHrLI0HMBDh/3sqgqVUnHI4OYxlDbwW/zykimiY0pc6EtDLn2pHYbCcij7MY/3RXi5IsvBu1oBRv6xo0xvbr00=',
            'origin': 'https://www.temu.com',
            'referer': 'https://www.temu.com/mens-sports-clothing-o3-2023.html',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        form_data = {
            'scene': 'opt',
            'pageSn': '10012',
            'offset': '120',
            'pageSize': '120',
            'pagelistId': 'ace3b21992b147b5b7a025cdc0043f59',
            'optId': '2023',
            'listId': 'category_list_5b9ed5a03dc54b42acfe7775b0e12242',
            'filterItems': '',
        }

        yield FormRequest(
            url='https://www.temu.com/api/poppy/v1/opt?scene=opt',
            formdata=form_data,
            method='POST',
            headers=headers,
            # cookies=cookies,
            callback=self.parse_products,
            meta={'pagelistid': pagelistid, 'pageSn': pageSn, 'pageSize': pageSize, 'dont_merge_cookies': True}
        )

    def parse_products(self, response):
        data = response.json().get('result', {})
        products = data.get('data', {}).get('goods_list', {})
        for product in products:
            url = product.get('link_url', '')
            yield Request(url=urljoin(response.url, url),
                          callback=self.parse_detail_product)

        next_page = data.get('has_more', '')
        if bool(next_page):
            next_record = data.get('data').get('filter_region').get('p_search')
            list_id = next_record.get('list_id')  # category_list
            offset = next_record.get('offset')
            opt_id = next_record.get('opt_id')

    def parse_detail_product(self, response):
        data = json.loads(response.css('script:contains("brand")').re_first(r'({.*})'))
        Title = data.get('name', '')
        Price = data.get('offers', {}).get('price', '')
        Colors_image_links = []
        for images in data.get('image'):
            image_url = images.get('contentURL')
            Colors_image_links.append(image_url)

        # below all variables for Description

        Patterned = data.get('pattern')
        material = data.get('material')

    def get_form_param(self, listid, pageSn, pagelistid, optId, offset, pageSize):
        json_data = {
            'scene': 'opt',
            'pageSn': pageSn,  # 'pageSn': 10012,
            'offset': offset,
            'pageSize': pageSize,
            'pagelistId': pagelistid,  # 'pagelistId': '9304b0fe224a48648e0349ac4ec59c69',
            'optId': optId,  # 'optId': 1544,
            'listId': listid,  # 'listId': 'category_list_f9e5a79f88984932b89a0c3b56e9da13',
            'filterItems': '',
            # 'anti_content': '',
            # 'anti-content': '0aqAfa5e-wCEPJv7XVLM8687zkBg8fhzQce0Ha53HKnqXxGGY3lqgFio51nLpttx28z-doWddTcHN3-kK-QG6PBtGPPwATELxx-ExCZwJ0-8gPwjmHLFAU0ZHCByCFXQTcTwvkai5tOT2se9wT35ZtxMGz6LT-k_0up3YfUUkv9UzySPFyX5i2glK-LsxBGIB6ixpV8gpQ0vOe854c9igQzQExQC7T0jjGBWY2L2FHbERiZeSknD6zGCuTzOSjXqjNoXraVhmDEuKleJpDI9Ne3TQSLLYQB3d0L9lH5aCj8-wFz9Xdh9RUFoPVJ21w2gpGM05l0PSVasaCqVLIpqUSbiyrL5A-UqRshpliNyMaMH-VCq4CKt_ZjYOmhGxb7tYMnGuvGqHbvqY8ntienxHNhtuDnniEyn0daYmHSxmjaqxNSZmifGdhnHpv_tNUHxd-yid8ndqdxGyEyXM94tvAGIJVQq_OfGTGLnpdhnDLUHZ0vn5-a2XVtpsGG_dyXCoCFsAzIszWUFNm7XaxvcLbCYX4qCmy0qH59qXpgonGXoHGdjn0_4BZq-EzFVDBe-kdVU2bTJ29VHcOp_BfFe-7wYaUvRDr3veU3lEMLKMSB4VIV-7UKRA7s4MJV4SEBACDz4U92XanIVTSqgYYsaJt4Mnpoy4phq2fidjnqQzXq2Tyh5a2W6ajsMXqHv978ylpHWgYs3JxZbnadWdn0gqY0gsTPpUaGGX1gk-MTZ4VoimSKm4LXtGpXqxOX1m5G5quQq4-qmXryGExt19coG6WqNXCOxRSCzcd44AumT8RbNB4p1Hx4uXuY3o2Q3JV_a8wDj37HjaCrZjwMpIq99928F5DdOrFjPCb',

        }
        return json_data

    def get_post_cookies(self, api_uid):

        cookies = {
            'api_uid': api_uid,
            # 'region': '211',
            'language': 'en',
            'currency': 'USD',
            'timezone': 'Asia%2FKarachi',
            'webp': '1',
            # 'shipping_city': '211',
            # '_nano_fp': 'XpEJlpCYlpd8n5dyXT_CV7DgduwT~Ce~8sFEfibO',
            # '_bee': '3fvNvZGlN2766AzG7h7TuiBk8DQhDapK',
            # 'njrpl': '3fvNvZGlN2766AzG7h7TuiBk8DQhDapK',
            # 'dilx': 'pYAihrKauUMIj3ZCd4uvF',
            # 'hfsc': 'L32CcYAy6Tj+0JXFfQ==',

        }
        return cookies

    def get_post_headers(self, referer):
        post_headers = {
            'authority': 'www.temu.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            # 'anti-content': '0aqWfqnYyiPdJgu9Q0CjeVc54rAVM4NGUg1JiLeQAR_-zkGuYFO0zW7NAIW8ilJoACRlGv0Xr9uZIyOsdK15Oaqc9GYPFVk_26kfpIdwT7_TkfTr20dA86JR2bRJrR6rqEV1BZbzYAi4GN6VXYmw8Y3KHdOFfaczipp2WT77EnmLgeL9LmTAmK4GisvhVqGL9Hi2OoKgSyQ7zW2Ct7oE9Uipne4GQI2oKBfQBqfI7KNM9q1ZUk638980RTxSEk3APaRVF7yn189vCTLoTR3_y4BLs8ETTCwjJNAZDznRoc-P9QKSCL4Ee9XrDCJb2lD1RlaUomw2i2i2dVoSEwHD9eRlP8WwxCTuRV7cQ2rrjdVlaofFygVpyNJoiKxL-RL94QRMJyarXiW2tdqMF1kqmjlkqDpEvnDGX8BYfVY1HkIDDogsgOgME8MEOmRZnDOfEtzBcB4qm563YZW8Pzj6oEPXS-heN5dkrAl8IHcFI5b70aShwvwG6vfdVFot8LJK62hT_Y-LHG-VwuYkJfIZiLw8lAKrbfDOjXJ0n71EUSByDU6a8EMqCVmBf3UhpPBBrfdxHpGdUspEvMBjI5AilF11yOOkdzkuC5IB8IQrBgXovvUIHwTIjSXvgEpkFxYNHYguKvVLcvMnD6eleBBPxOY7ZsgvZBqUK0-HpBObRy2YcO_OXftK4sK1IlhsHdYvtWCDUSzv6zKY7h5qAJYJ3OJc-CB0LwiUCvqpEjoARpKaEIIc64bPhGxUB8WV-aM7iL8TQb9lj7AcHW3A5Pe',
            # 'anti-content': '',
            'content-type': 'application/json;charset=UTF-8',
            # 'cookie': 'api_uid=CnBuKWS6JJK+gQDAGu2IAg==; region=211; language=en; currency=USD; timezone=Asia%2FKarachi; webp=1; _nano_fp=XpEJlpUxX0EjXpd8XT_ouh5jazcPiqjRYGFvEZY9; shipping_city=211; _bee=3fvNvZGlN2766AzG7h7TuiBk8DQhDapK; njrpl=3fvNvZGlN2766AzG7h7TuiBk8DQhDapK; dilx=pYAihrKauUMIj3ZCd4uvF; hfsc=L32CcYAy6Tj+0JXFfQ==',
            'dnt': '1',
            'origin': 'https://www.temu.com',
            'referer': referer,
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Microsoft Edge";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82',
        }
        return post_headers

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
