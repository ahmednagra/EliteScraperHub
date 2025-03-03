import os
import string
from datetime import datetime
from collections import OrderedDict

from nameparser import HumanName

from scrapy import Spider, Request


class SpiderSpider(Spider):
    name = "vancouver_city_spider"
    start_urls = ["https://whitepagescanada.ca/"]

    main_start_datetime_str = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'CLOSESPIDER_ITEMCOUNT': 25000,  # Stop spider after 25,000 items

        'FEEDS': {
            f'output/WhitPages Cities Members Records {main_start_datetime_str}.xlsx': {
                'format': 'xlsx',
                'fields': ['First Name', 'Last Name', 'Phone', 'Address', 'Url']
            }
        },
    }

    cookies = {
        'PHPSESSID': 'fna36pbfmk9e9k66u5tao2a37t',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'PHPSESSID=fna36pbfmk9e9k66u5tao2a37t',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://whitepagescanada.ca/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scraped_product_counter = 0

        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.main_start_datetime_str}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

        self.current_scraped_items = []
        self.scraping_datetime = datetime.now().strftime('%Y-%m-%d %H%M%S')

    def start_requests(self):
        yield Request(url=self.start_urls[0], headers=self.headers, cookies=self.cookies, callback=self.parse)

    def parse(self, response, **kwargs):
        cities_urls = response.css('h4:contains("Cities")')
        cities_urls = ['https://whitepagescanada.ca/bc/vancouver/']
        for city_url in cities_urls:
            print(city_url)

            # called city url A to Z Names wise
            for letter in string.ascii_lowercase:
                url = f'{city_url}a-z/{letter}/'
                yield Request(url=url, headers=self.headers, cookies=self.cookies,
                              callback=self.parse_cities_results)

    def parse_cities_results(self, response):
        surnames_urls = response.css('#wrapper .four a::attr(href)').getall()
        for surname_url in surnames_urls:
            print('Sur name Url: ', surname_url)
            yield Request(url=surname_url, headers=self.headers, cookies=self.cookies,
                          callback=self.parse_surname_results)

        # Pagination
        next_page = response.css('a:contains("[Next]") ::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, headers=self.headers, cookies=self.cookies, callback=self.parse_cities_results)

    def parse_surname_results(self, response):
        persons_urls = response.css('.eleven.columns > table .rsslink-m::attr(href)').getall() or []
        for person_url in persons_urls:
            print('Person Url ', person_url)
            yield Request(url=person_url, headers=self.headers, cookies=self.cookies,
                          callback=self.parse_person_records)

    def parse_person_records(self, response):
        name = response.css('span[itemprop="name"] ::text').get('')
        street_address = response.css('[itemprop="streetAddress"] ::text').get('')
        city = response.css('[itemprop="addressLocality"] ::text').get('')
        region = response.css('[itemprop="addressRegion"] ::text').get('')
        postal_code = response.css('[itemprop="postalCode"] ::text').get('')

        item = OrderedDict()
        item['First Name'] = HumanName(name).first if name else ''
        item['Last Name'] = HumanName(name).last if name else ''
        item['Phone'] = response.css('span[itemprop="telephone"] ::text').get('')
        item['Address'] = f'{street_address} {city}, {region} {postal_code}'
        item['Url'] = response.url

        self.scraped_product_counter += 1
        print('scraped_product_counter: ', self.scraped_product_counter)

        yield item

    def get_formdata(self, address, city):
        params = {
            'txtaddress': address,
            'txtcity': city,
            'search.x': '0',
            'search.y': '0',
        }

        return params

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def close(spider, reason):
        spider.write_logs(f'Total Items are Scraped : {spider.scraped_product_counter}')