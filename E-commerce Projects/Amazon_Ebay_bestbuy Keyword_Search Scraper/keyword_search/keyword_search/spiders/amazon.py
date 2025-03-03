import json
import re
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urljoin, quote

from scrapy import Spider, Request


class AmazonSpider(Spider):
    name = 'amazon'
    start_urls = ['http://www.amazon.com/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 7,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'FEEDS': {
            f'output/Amazon Products Detail.csv': {
                'format': 'csv',
                'fields': ['Brand', 'Model', 'Title', 'ASIN',
                           'Price', 'Discounted Price', 'Description',
                           'keyword', 'Status', 'Image', 'URL'],
                'overwrite': True
            }
        }
    }

    cookies = {
        'i18n-prefs': 'USD',
        'lc-main': 'en_US',
    }

    headers = {
        'authority': 'www.amazon.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'device-memory': '8',
        'downlink': '1.55',
        'dpr': '1.25',
        'ect': '3g',
        'rtt': '450',
        'sec-ch-device-memory': '8',
        'sec-ch-dpr': '1.25',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-ch-viewport-width': '1536',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'viewport-width': '1536',
    }

    def __init__(self):
        super().__init__()

        search_keyword = 'input/keywords.txt'
        self.keywords = self.get_input_rows_from_file(search_keyword)

    def start_requests(self):
        for keyword in self.keywords:
            keywords_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&s=date-desc-rank&ref=sr_nr_p_n_condition-type_1"
            yield Request(url=keywords_url,
                          callback=self.parse,
                          cookies=self.cookies,
                          headers=self.headers,
                          meta={'keyword': keyword})

    def parse(self, response):
        products_url = response.css(".s-main-slot div.s-asin a.s-no-outline::attr(href)").getall()
        for url in products_url[:5]:
            yield Request(url=urljoin(response.url, url),
                          callback=self.parse_product_detail,
                          cookies=self.cookies,
                          headers=self.headers,
                          meta=response.meta
                          )

        next_page = response.css("a.s-pagination-next::attr(href)").get('')
        # if next_page:
        #     yield Request(urljoin(response.url, next_page),
        #                   cookies=self.cookies,
        #                   headers=self.headers,
        #                   callback=self.parse,
        #                   meta=response.meta)

    def parse_product_detail(self, response):
        item = OrderedDict()

        current_price = self.get_discounted_price(response)
        was_price = self.get_regular_price(response)

        item['Brand'] = self.get_brand_name(response)
        item['Model'] = response.css('.a-spacing-small.po-model_name .po-break-word::text').get('')
        item['Title'] = response.css('#productTitle::text').get('').strip()
        item['Product Information'] = self.get_product_information(response)
        asin = item.get('Product Information', {}).get('ASIN', '') or response.url.split('/')[-1]
        item['ASIN'] = asin

        if was_price:
            item['Discounted Price'] = current_price
            item['Price'] = was_price
        else:
            item['Price'] = current_price

        item['Description'] = ','.join(response.css('#feature-bullets .a-list-item::text').getall()) or ''
        item['Image'] = self.get_images(response)
        item['keyword'] = response.meta.get('keyword', '')
        item['Status'] = self.get_status(response)
        item['URL'] = response.url

        see_all_options = response.css('#buybox-see-all-buying-choices a::attr(href)')

        if not current_price and see_all_options:
            url = f'https://www.amazon.com.au/gp/product/ajax/ref=dp_aod_unknown_mbc?asin={asin}&m=&qid=&smid=&sourcecustomerorglistid=&sourcecustomerorglistitemid=&sr=&pc=dp&experienceId=aodAjaxMain'
            yield Request(url=url,
                          meta={'handle_httpstatus_all': True},
                          callback=self.get_process_price, cb_kwargs={'item': item})
        else:
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

    def get_product_information(self, response):
        product_information = {}

        rows = response.css('#productDetails_techSpec_section_1 tr') or response.css(
            '.content-grid-block table tr') or ''
        if not rows:
            product_details = response.css('#detailBullets_feature_div li')
        else:
            product_details = []

        for row in rows:
            key = row.css('th::text').get('') or row.css('td strong::text').get('')
            value = row.css('td p::text').get('') or row.css('td::text').get('')
            if key and value:
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key.strip()] = value

        for detail in product_details:
            key = detail.css('.a-text-bold::text').get('')
            value = detail.css('.a-text-bold + span::text').get('')
            if key and value:
                key = key.replace(':', '').replace('\u200e', '').replace(' \u200f', '')
                key = ' '.join(key.strip().split())
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key] = value

        additional_information = response.css('#productDetails_detailBullets_sections1 tr') or ''

        for row in additional_information:
            key = row.css('th::text').get('')
            value = ' '.join(row.css('td *::text').getall()).strip()
            if key and value:
                value = value.split('\n')[-1].strip()
                product_information[key.strip()] = value

        return product_information

    def get_discounted_price(self, response):
        price = response.css('.reinventPricePriceToPayMargin .a-offscreen::text').get('').replace('$', '')
        price = price or response.css('.apexPriceToPay span.a-offscreen::text').get('').replace('$', '')
        price = price or response.css('.priceToPay span::text').get('').replace('$', '')

        return price

    def get_regular_price(self, response):
        price = response.css('.basisPrice .a-offscreen::text').get('').replace('$', '').replace(',', '')
        price = price or response.css('.a-price[data-a-color="secondary"] .a-offscreen::text').get('').replace('$',
                                                                                                               '').replace(
            ',', '')
        return price

    def get_process_price(self, response, item):
        item['Price'] = response.css('.a-price-whole::text').get('')
        item['Sold By'] = response.css('#aod-offer-soldBy a[role="link"]::text').get('')
        item['Shipped From'] = response.css('#aod-offer-shipsFrom .a-color-base::text').get('')
        item['Shipping Cost'] = response.css(
            '#mir-layout-DELIVERY_BLOCK span[data-csa-c-delivery-price]::attr(data-csa-c-delivery-price)').get('')

        yield item

    def get_brand_name(self, response):
        brand = response.css('.po-brand .po-break-word::text').get('')
        brand = brand or response.css('#brand::text').get('')
        brand = brand or response.css('a#bylineInfo::text').get('').strip().lstrip('Brand:')

        return brand

    def get_status(self, response):
        stat = response.css('#exportsUndeliverable-cart-announce::text').get('') or response.css(
            '#add-to-cart-button::attr(value)').get('')

        status = 'In Stock' if stat else 'Out of Stock'

        return status

    def get_images(self, response):
        try:
            images_json = json.loads(response.css('script[type="text/javascript"]:contains(ImageBlockATF)').re_first(
                f"'colorImages':(.*)").rstrip(',').replace("'", '"')) or {}
            images_json = images_json.get('initial', [])
        except json.JSONDecodeError:
            images_json = []
        except AttributeError:
            images_json = []

        full_size_images = [item.get('hiRes', '') for item in images_json]
        image = [url for url in
                 response.css('.regularAltImageViewLayout .a-list-item .a-button-text img::attr(src)').getall() if
                 'images-na.ssl' not in url] or []

        normal_images = [re.sub(r'\._.*', '._AC_SX522_.jpg', url) for url in image]

        images = full_size_images or normal_images or []

        # Filter out None values from the images list
        images = [img for img in images if img]

        return ', '.join(images)

