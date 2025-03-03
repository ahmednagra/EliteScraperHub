from typing import Iterable

import scrapy
from scrapy import Spider, Selector, Request
import json
import re
import requests
from urllib.parse import urljoin, unquote
from collections import OrderedDict


class GsmSpider(scrapy.Spider):
    name = "gsm"
    allowed_domains = ['gsmarena.com']
    start_urls = ["https://www.gsmarena.com/makers.php3"]

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    # xlsx_headers = ['Name', 'Network', 'Launch', 'Body', 'Display',
    #                 'Platform', 'Memory', 'Main Camera', 'Selfie Camera',
    #                 'Sound', 'Comms', 'Features', 'Battery', 'Misc', 'Tests',
    #                 'URL']
    xlsx_headers = ['Make', 'Model', 'Network', 'Network Html', 'Launch', 'Launch Html',
                    'Body', 'Body Html', 'Display', 'Display Html', 'Platform', 'Platform Html',
                    'Memory', 'Memory Html', 'Main Camera', 'Main Camera Html', 'Selfie Camera', 'Selfie Camera Html',
                    'Sound', 'Sound Html', 'Comms', 'Comms Html', 'Features', 'Features Html',
                    'Battery', 'Battery Html', 'Misc', 'Misc Html', 'Tests', 'Tests Html', 'URL']

    custom_settings = {
        # 'log_level': 'error',
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [429],
        'CONCURRENT_REQUESTS': 1,
        # 'AUTOTHROTTLE_ENABLED': True,
        # 'AUTOTHROTTLE_START_DELAY': 1,  # Initial delay in seconds
        # 'AUTOTHROTTLE_MAX_DELAY': 10,  # Maximum delay in seconds
        # 'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,  # Target concurrency
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/Gsmareena Mobiles Details.xlsx': {
                'format': 'xlsx',
                'fields': xlsx_headers,
            }
        },
    }

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        makers_urls = response.css('.st-text table td a::attr(href)').getall()
        for maker in makers_urls[5:6]:
            url = urljoin(response.url, maker)
            print('Maker url:', url)
            yield Request(url, callback=self.parse_maker)

    def parse_maker(self, response):
        mobiles_urls = response.css('.makers li a::attr(href)').getall()
        for mobile_url in mobiles_urls[:1]:
            url = urljoin(response.url, mobile_url)
            print('Mobile url:', url)
            yield Request(url, callback=self.parse_mobile_detail)

    def parse_mobile_detail(self, response):
        item = OrderedDict()
        info_tables = response.css('#specs-list table')

        item['Make'] = response.css('script[type="text/javascript"]:contains("key")::text').get('').split("keyw', '")[1].split("');")[0]
        item['Model'] = response.css('.specs-phone-name-title::text').get('')
        # item['Network'] = self.get_info_text(info_tables, 'Network')
        item['Network Html'] = self.get_info_html(info_tables, 'Network')
        # item['Launch'] = self.get_info_text(info_tables, 'Launch')
        item['Launch Html'] = self.get_info_html(info_tables, 'Launch')
        # item['Body'] = self.get_info_text(info_tables, 'Body')
        item['Body Html'] = self.get_info_html(info_tables, 'Body')
        # item['Display'] = self.get_info_text(info_tables, 'Display')
        item['Display Html'] = self.get_info_html(info_tables, 'Display')
        # item['Platform'] = self.get_info_text(info_tables, 'Platform')
        item['Platform Html'] = self.get_info_html(info_tables, 'Platform')
        # item['Memory'] = self.get_info_text(info_tables, 'Memory')
        item['Memory Html'] = self.get_info_html(info_tables, 'Memory')
        # item['Main Camera'] = self.get_info_text(info_tables, 'Main Camera')
        item['Main Camera Html'] = self.get_info_html(info_tables, 'Main Camera')
        # item['Selfie Camera'] = self.get_info_text(info_tables, 'Selfie Camera')
        item['Selfie Camera Html'] = self.get_info_html(info_tables, 'Selfie Camera')
        # item['Sound'] = self.get_info_text(info_tables, 'Sound')
        item['Sound Html'] = self.get_info_html(info_tables, 'Sound')
        # item['Comms'] = self.get_info_text(info_tables, 'Comms')
        item['Comms Html'] = self.get_info_html(info_tables, 'Comms')
        # item['Features'] = self.get_info_text(info_tables, 'Features')
        item['Features Html'] = self.get_info_html(info_tables, 'Features')
        # item['Battery'] = self.get_info_text(info_tables, 'Battery')
        item['Battery Html'] = self.get_info_html(info_tables, 'Battery')
        # item['Misc'] = self.get_info_text(info_tables, 'Misc')
        item['Misc Html'] = self.get_info_html(info_tables, 'Misc')
        # item['Tests'] = self.get_info_text(info_tables, 'Tests')
        item['Tests Html'] = self.get_info_html(info_tables, 'Tests')
        item['URL'] = response.url

        yield item

    def get_info_html(self, info_tables, key):
        try:
            table = [table for table in info_tables if key in table.css('th::text').get('')]
            if table:
                table_html = table[0].get()  # Get the entire HTML content of the table
                # Remove <th> tags with scope="row" from the HTML content
                table_html = re.sub(r'<th\s+[^>]*\bscope="row"\s*[^>]*>.*?</th>', '', table_html)
                return table_html
            else:
                return ''
        except Exception as e:
            print(f"Error in {key} Method : {e}")
            return ''

    def get_info_text(self, info_tables, key):
        try:
            table = [table.css('tr') for table in info_tables if key in table.css('th::text').get('')]
            if table:
                table = table[0]
                info_list = []
                for tr in table:
                    title = tr.css('tr .ttl ::text').get('')
                    info = tr.css('tr .nfo::text').get('')
                    body = ': '.join([title, info])
                    info_list.append(body)

                return '\n'.join(info_list)
            else:
                return ''
        except Exception as e:
            print(f"Error in {key} Method : {e}")
            return ''
