import os
import csv
from datetime import datetime
from typing import Any, Union
from collections import OrderedDict

from twisted.internet.defer import Deferred
from scrapy import Request, Spider, signals


class AmazonReviewsSpider(Spider):
    name = "reviews"

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 2,
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
        # Proxy Config
        self.proxy_type = 'scrapeops'  # define for condition at middleware.py
        self.config = self.get_config_from_file()
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('use_proxy', '')

        self.part_numbers = self.read_input_from_file('input/part_numbers.txt')

        self.scraped_item = []
        self.items_scraped_count = 0
        self.part_numbers_count = len(self.part_numbers)
        self.fields = ['Part No', 'Question', 'Answer', 'Url']

    def parse_part_number(self, response):
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
                item['Url'] = f'https://www.amazon.com/dp/{response.meta.get('asin')}/'

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

    def get_config_from_file(self):
        """
        Load Proxy Information from a text file.
        """
        try:
            config_filename = 'input/scrapeops_proxy_key.txt'

            with open(config_filename, mode='r', encoding='utf-8') as file:
                return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file}
        except Exception as e:
            self.logger.error(f'Error loading search parameters: {e}')
            return []

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
            req = Request(url=url, callback=self.parse_part_number,
                          meta={'part_number': part_number,
                                'handle_httpstatus_all': True, })

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        spider.write_items_csv()
