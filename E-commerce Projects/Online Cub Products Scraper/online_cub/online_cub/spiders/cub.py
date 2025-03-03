import os
import json
from typing import Iterable
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy.exceptions import CloseSpider
from scrapy import Spider, Selector, FormRequest, Request, signals


class CubSpider(Spider):
    name = "cub"
    base_url = 'https://online.cub.com.au/'
    start_urls = ["https://online.cub.com.au/"]

    current_datetime = datetime.now().strftime("%d%m%Y%H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'log_level': 'WARNING',
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},

        'FEEDS': {
            f'output/Cub Products {current_datetime}.xlsx': {
                'format': 'xlsx',
                'fields': ['EAN', 'SKU', 'Name', 'Price', 'Save', 'Deal',
                           'Deal Start Date', 'Deal End Date', 'URL', ],
            }
        }
    }

    headers = {
        'authority': 'online.cub.com.au',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://online.cub.com.au',
        'pragma': 'no-cache',
        'referer': 'https://online.cub.com.au/sabmStore/en/login',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reports_directory = 'output/reports'
        self.report_filename = f'{self.reports_directory}/Report {self.current_datetime}.txt'

        self.current_scraped_items = []
        self.category_products = {}
        self.scraped_items = 0
        self.categories_urls = []

    def start_requests(self) -> Iterable[Request]:
        if not os.path.isdir(self.reports_directory):
            os.makedirs(self.reports_directory)

        yield Request('https://online.cub.com.au/sabmStore/en/login', callback=self.parse)

    def parse(self, response, **kwargs):
        form_data = self.get_formdata(response)

        yield FormRequest(url='https://online.cub.com.au/sabmStore/en/j_spring_security_check',
                          formdata=form_data,
                          headers=self.headers,
                          callback=self.parse_login)

    def parse_login(self, response):
        is_logout_link_exists = response.css('.logout-link')

        if is_logout_link_exists:
            self.logger.info(f'Login Successful!')

            categories = response.css('.container a[data-toggle="dropdown"]:not(:contains("Brands")):not(:contains("Support")) ::attr(href)').getall()
            urls = [urljoin(self.base_url, category) for category in categories if category]
            self.categories_urls.extend(urls)

        else:
            self.logger.error('Login Failed!')
            raise CloseSpider('Login Failed')

    def parse_category_products(self, response):
        if 'deals' in response.url:
            category_name = 'Deals'
            category_products = (response.css('#d_circle span::text').get('') or
                                 response.css('.col-md-6 .num-products label ::text').get(''))

            self.category_products[category_name] = category_products

            products = json.loads(response.css('#dealsData ::text').get('').encode().decode('unicode-escape'))

            for product in products:
                product_url = product.get('ranges', [])[0].get('baseProducts', [])[0].get('url', '')
                url = urljoin(self.base_url, product_url)
                deal = ''.join(Selector(text=product.get('title','')).css(' ::text').getall())

                yield Request(url=url, callback=self.parse_product_detail,
                              meta={'deal': deal}, dont_filter=True)

        elif 'Beer' in response.url:
            category_name = response.css('meta[name="description"]::attr(content)').get('')
            category_products = response.css('.col-md-6 .num-products label ::text').get('').replace('Products', '')
            self.category_products[category_name] = category_products

            all_subcategories_urls = response.css('#Brand li input[name="q"] ::attr(value)').getall() or []
            for subcategory in all_subcategories_urls:
                url = f"{response.url}?q={subcategory}&text=#"
                yield Request(url=url, callback=self.parse_subcategory_index, dont_filter=True)
        else:
            yield from self.parse_subcategory_index(response=response)

    def parse_subcategory_index(self, response):
        try:
            category_name = response.css(
                'meta[name="description"]::attr(content)').get('')
            category_products = response.css(
                '.col-md-6 .num-products label ::text').get('')
            if category_products:
                category_products = ''.join(
                    [str(s) for s in category_products.split() if s.isdigit()])

            if int(category_products) > 21:
                yield from self.subcategories_filters(response)
                return

            products_urls = response.css(
                '#resultsListRow .productImpressionTag .productMainLink::attr(href)').getall() or []
            for product_url in products_urls:
                url = urljoin(response.url, product_url)
                if url in self.current_scraped_items:
                    print('Url already scraped :', url)
                    continue

                if 'Beer' in self.category_products:
                    yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)
                else:
                    self.category_products[category_name] = category_products
                    yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)

        except Exception as e:
            print('Error form parse_subcategory_index Method : ', e)

    def parse_product_detail(self, response):
        try:
            deal = response.meta.get('deal', '')
            if not deal:
                product = response.css('#dealsData ::text').get('').encode().decode('unicode-escape')
                if product:
                    product_data = json.loads(product)
                    if isinstance(product_data, list) and product_data:
                        deal = ''.join(Selector(text=product_data[0].get('title', '')).css(' ::text').getall())

            deal_start_date = response.xpath('//text()').re_first(r"'dimension15':\s*\"([^\"]+)\"")
            deal_start_date = deal_start_date.split('|')[0] if deal_start_date != 'NA' else ''
            deal_end_date = response.xpath('//text()').re_first(r"'dimension16':\s*\"([^\"]+)\"")

            item = OrderedDict()
            item['EAN'] = response.url.rstrip('/').split('/')[-1]
            item['SKU'] = response.css('h4 + table td:contains(SKU) + td::text').get('')
            item['Name'] = response.css('.last ::text').get('')
            item['Price'] = response.css('.product-summary .price-yourPrice .h1 ::text').get('')
            item['Save'] = response.css('.product-summary .price-save span + span::text').get('')

            if 'sabmStore' not in response.url:
                item['Deal'] = deal if deal else ''
            else:
                item['Deal'] = ''

            item['Deal Start Date'] = deal_start_date if 'sabmStore'not in response.url else ''
            item['Deal End Date'] = deal_end_date if 'sabmStore' not in response.url else ''
            item['URL'] = response.url

            self.current_scraped_items.append(item['URL'])
            self.scraped_items += 1
            print('scraped items are :', self.scraped_items)

            yield item

        except Exception as e:
            print('error from parse_product_detail Method : ', e)
            return

    def get_formdata(self, response):
        with open('input/login.txt', mode='r', encoding='utf-8') as txt_file:
            username, password = txt_file.readline().split(':')

        data = {
            'j_username': username.strip(),
            'j_password': password.strip(),
            'targetUrl': '',
            '_spring_security_remember_me': 'on',
            'CSRFToken': response.css('[name="CSRFToken"]::attr(value)').get(''),
        }

        return data

    def subcategories_filters(self, response):
        filters = response.css('#Package li input[name="q"] ::attr(value)').getall() or []
        for filter_name in filters:
            url = f"{response.url.split('?q=')[0]}?q={filter_name}"
            yield Request(url=url, callback=self.subcategories_filters_index, dont_filter=True)

    def subcategories_filters_index(self, response):
        try:
            products_urls = response.css(
                '#resultsListRow .productImpressionTag .productMainLink::attr(href)').getall() or []
            for product_url in products_urls:
                url = urljoin(response.url, product_url)
                if url in self.current_scraped_items:
                    print('Url already scraped :', url)
                    continue

                yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)
        except Exception as e:
            print('Error form subcategories_filters_index Method : ', e)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CubSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.category_products:

            try:
                with open(self.report_filename, mode='a', encoding='utf-8') as f:
                    f.write(f"Category: `{''.join(self.category_products.keys())}` \nProducts on Web: {''.join(self.category_products.values())} \nProducts Scraped:{self.scraped_items}\n\n")

                self.category_products = {}
                self.scraped_items = 0
            except Exception as e:
                print(f"Error writing to file: {e}")

        if self.categories_urls:
            url = self.categories_urls.pop(0)

            req = Request(url=url,
                          callback=self.parse_category_products)

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
