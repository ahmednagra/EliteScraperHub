import json
import os
import csv
import random
from datetime import datetime
from typing import Any, Union
from urllib.parse import quote
from collections import OrderedDict

import requests
from scrapy.http import Response
from twisted.internet.defer import Deferred
from scrapy import Request, Spider, Selector, signals


class AmazonReviewsSpider(Spider):
    name = "amazon_parts"

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/Amazon Products Reviews {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Part No', 'Question', 'Answer', 'Url']
            }
        }
    }

    def __init__(self):
        super().__init__()
        self.use_proxy = 'true'
        self.proxy_type = ''

        self.part_numbers = self.read_input_from_file('input/part_numbers.txt')[:25]

        self.scraped_item = []
        self.items_scraped_count = 0
        self.part_numbers_count = len(self.part_numbers)
        self.fields = ['Part No', 'Question', 'Answer', 'Url']

        # webshare login and get token
        self.config = self.get_config_from_file()
        # webshare_api_key = f'Token {yhh351p53vphy1rw4n37vrlrgdsn29stl6y84lu9}'  # Office key
        webshare_api_key = self.config.get('webshare_api_key', '')
        self.proxy_list = self.get_webshare_proxy_list(webshare_api_key)
        self.proxy_list = {
            'http': 'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
            'https': 'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        }
        # self.proxy_list = ['http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://ahmednagra9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030',
        #                    'http://diagrammed9---gmail.com:vuLCSA8zGjEy6WQNLYoD9@proxy.wtfproxy.com:3030'
        #                    ]
        a = 1

    def parse_part_number(self, response):
        if response.status != 200:
            print('Response 5033')
            return
            # url = response.url
            # proxies = random.choice(self.proxy_list)
            # if isinstance(proxies, str):
            #     proxies = {"no_proxy": proxies}
            # req = requests.get(url, proxies=proxies)

        # Extracting product information at Listing Page
        part_number = response.meta.get('part_number', '')

        for product in response.css('[data-component-type="s-search-result"]'):
            title = product.css('h2 a span::text').get('')
            asin = product.css('div::attr(data-asin)').get('')
            reviews_count = product.css('.alf-search-csa-instrumentation-wrapper span::attr(aria-label)').get('')

            if part_number in title and reviews_count:
                response.meta['asin'] = asin
                asin_url = f'https://www.amazon.com/ask/livesearch/detailPageSearch/search?query=%22work%22+%2C+%22%09%22+or+%22compatible%22&asin={asin}&liveSearchSessionId=&liveSearchPageLoadId='
                yield Request(url=asin_url, callback=self.parse_part_detail, meta=response.meta)

            # test
            else:
                # print('Part Number and Title not matched')
                pass

        if response.status == 200 and response.css('[data-component-type="s-search-result"]'):
            print('response 200')

    def parse_part_detail(self, response):
        raw_strings = response.css('.a-section.a-spacing-base:contains("Q:")') or []

        for string in raw_strings:
            try:
                item = OrderedDict()
                item['Part No'] = response.meta.get('part_number', '')
                item['Question'] = ''.join(string.css('.a-text-bold:contains("Q:") + span::text').getall())

                answer = string.css('.noScriptDisplayLongText ::text').getall() or string.css(
                    'div.a-section.a-spacing-none > span:not(.a-text-bold):not(#askAuthorDetails)::text').getall() or []

                # Split the answer into words to limit the answer first 20 words
                words = [word.strip() for text in answer for word in text.split() if word.strip()]
                item['Answer'] = ' '.join(words[:20])
                item['Url'] = f"https://www.amazon.com/dp/{response.meta.get('asin')}/"

                # yield item
                self.items_scraped_count += 1
                print('Items Scrape Counter :', self.items_scraped_count)
                self.scraped_item.append(item)

            except Exception as e:
                self.logger.error(f"Error occurred while parsing product information: {e}")
                continue

    def read_input_from_file(self, file_path):
        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def write_items_csv(self):
        """
        Write items to JSON file.
        """
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_file = output_dir + '/' + f'Amazon Products Reviews {datetime.now().strftime("%d%m%Y%H%M")}.csv'
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.fields)
                writer.writeheader()
                for item in self.scraped_item:
                    fields = {field: item.get(field, '') for field in self.fields}
                    writer.writerow(fields)

        except Exception as e:
            print(f"Error occurred while writing items to csv file: {e}")

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

    def get_config_from_file(self):
        """
        Load Proxy Information from a text file.
        """
        try:
            config_filename = 'input/webshare_proxy_key.txt'

            with open(config_filename, mode='r', encoding='utf-8') as file:
                return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file}
        except Exception as e:
            self.logger.error(f'Error loading search parameters: {e}')
            return []

    def get_webshare_proxy_list(self, webshare_api_key):

        # using proxy api key from request a variable get the token then from c request variable get the proxies list for specific country
        a = requests.get(
            "https://proxy.webshare.io/api/v2/proxy/config/",
            headers={"Authorization": f"Token {webshare_api_key}"}
            # headers={"Authorization": "Token hjrmxcduqgcisax9huheyg2xwb2xr7qv2nmwa4kj"} # token belong to ahmed
        )
        b = a.json()
        proxy_token = b.get('proxy_list_download_token', '')  # this token mean to download all proxies all country base
        url = f'https://proxy.webshare.io/api/v2/proxy/list/download/{proxy_token}/us/any/username/direct/-/'

        c = requests.get(url=url)
        d = [proxy for proxy in c.text.replace('\r', '').split('\n') if proxy.strip()]

        # from this req variable get the all proxies in list  with pagination option.
        req = requests.get(
                    "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=250",
                    headers={"Authorization": f"Token {webshare_api_key}"}
                )

        proxy_list = []
        for proxy in d:
            proxy = proxy.split(':')
            ip = proxy[0]
            port_no = proxy[1]
            username = proxy[2]
            password = proxy[3]
            new_proxy = f"http://{username}:{password}@{ip}:{port_no}"
            print('New Proxy Url :', new_proxy)
            proxy_list.append(new_proxy)

        return proxy_list

    # def get_webshare_proxy_list(self, webshare_api_key):
    #     # proxies list
    #     req = requests.get(
    #         "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=250",
    #         headers={"Authorization": f"Token {webshare_api_key}"}
    #     )
    #
    #     response = req.json()
    #
    #     a = '45.94.47.66:8110:cczdbmmz:1t6zkw77ctek'  # proxy from list demo
    #     proxy_list = []
    #     for proxy in response.get('results'):
    #         ip = proxy.get('proxy_address')
    #         port_no = proxy.get('port')
    #         username = proxy.get('username')
    #         password = proxy.get('password')
    #         # new_proxy = f"http://{ip}:{port_no}@{username}:{password}"
    #         new_proxy = f"http://{username}:{password}@{ip}:{port_no}"
    #         # new_proxy = f"{ip}:{port_no}:{username}:{password}"
    #         proxy_list.append(new_proxy)
    #
    #     return proxy_list

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AmazonReviewsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """

        print(f'\n\n{len(self.part_numbers)}/{self.part_numbers_count} Parts Number left to Scrape\n\n')

        if self.part_numbers:
            part_number = self.part_numbers.pop(0)
            url = f'https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords={part_number}'

            response = requests.get(url, proxies=self.proxy_list)
            a=1


            req = Request(url=url, callback=self.parse_part_number,
                          # meta={'proxy': random.choice(self.proxy_list), 'part_number': part_number,
                          meta={'proxy': json.dumps(self.proxy_list), 'part_number': part_number,
                                # meta={'part_number': part_number,
                                'handle_httpstatus_all': True, })
            # self.part_numbers = ''
            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        spider.write_items_csv()
