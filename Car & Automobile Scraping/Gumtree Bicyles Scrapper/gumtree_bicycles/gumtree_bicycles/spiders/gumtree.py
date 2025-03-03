import datetime

import os
from datetime import timedelta

from scrapy import Spider, Request

from ..items import GumtreeBicyclesItem


class GumtreeSpider(Spider):
    name = "gumtree"

    start_urls = ['https://www.gumtree.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,

        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEED_FORMAT': 'xlsx',
        'FEED_URI': 'output/%(name)s_%(time)s.xlsx',
        'FEED_STORE_EMPTY': True,
        'FEED_EXPORT_FIELDS': ['Name', 'Location', 'Price', 'Date_Posted', 'Image_URL', 'Product_URL'],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.seen_urls = set()
        self.counter = 0
        self.scrape_ids = self.product_ids()
        self.urls = []
        self.logger.info(f'previous_scrape_ids :: {len(self.scrape_ids)}')

    def parse(self, response, **kwargs):
        for city_name in response.xpath('//div[@class="tabs-content is-active"]//a/@href').getall():
            url = f'https://www.gumtree.com/for-sale/sports-leisure-travel/bicycles/uk{str(city_name)}'

            self.counter += 1
            yield Request(
                url=url,
                callback=self.products_page,
            )

    def products_page(self, response):
        date_obj = None
        for product in response.xpath('//ul[contains(@class, "list-listing-maxi")]/li/article'):
            product_url = response.urljoin(product.xpath('.//a/@href').get(''))
            product_id = product_url.rsplit('/', 1)[-1]
            item = GumtreeBicyclesItem()

            if product_id in self.scrape_ids:
                self.logger.info(f'the product url {product_url} already exists')
                continue

            if product_url in self.seen_urls:
                self.logger.info(f'Drop-item  {product_url} because it already exists')
                continue

            self.seen_urls.add(product_url)

            item['Name'] = product.xpath('.//h2[contains(@class, "listing-title")]/text()').get('').replace('\n', '')
            item['Location'] = product.xpath('.//div[contains(@class, "listing-location")]/span/text()').get(
                '').replace('\n', '')
            item['Price'] = float(
                product.xpath('.//span[contains(@class, "listing-price")]/strong/text()').get('').replace(',', '').strip('£'))
            item['Image_URL'] = product.xpath('.//div[@class = "listing-thumbnail"]//noscript//img/@src').get('')
            item['Product_URL'] = product_url
            today_date = datetime.datetime.now().date()
            date_posting = ''.join(product.xpath('.//span[@data-q="listing-adAge"]/text()').getall()).strip()

            if any(keyword in date_posting for keyword in ['Just now', 'mins', 'hours', 'hour']):
                item['Date_Posted'] = today_date

            elif any(keyword in date_posting for keyword in ['days', 'day']):
                days = int(date_posting.split()[0])
                date = (today_date - timedelta(days=days)).strftime("%Y, %m, %d")
                item['Date_Posted'] = date
                date_obj = datetime.datetime.strptime(date, "%Y, %m, %d").date()

            else:
                item['Date_Posted'] = None

            if date_obj and (today_date - date_obj).days > 30:
                self.logger.info(f'Skipping item {product_url} because it is older than 30 days')
                continue

            self.urls.append(product_url)

            yield item

        next_page = response.xpath('//li[@class="pagination-next"]/a/@href').get('')

        if next_page:
            yield response.follow(
                url=next_page,
                callback=self.products_page,
            )

    def product_ids(self):
        file_path = 'output/ids.txt'

        try:
            with open(file_path, 'r') as txt_file:
                return [line.strip() for line in txt_file if line.strip()]

        except Exception as e:
            self.logger.info(f"Error reading file: {file_path} - {e}")

        return []

    def closed(self, reason):
        file = os.path.join('output', 'ids.txt')

        with open(file, 'a', encoding='utf-8') as ids_file:
            for url in self.urls:
                product_id = url.rsplit('/', 1)[-1]
                ids_file.write(f"{product_id}\n")

        self.logger.info('Total requests made: %s', self.counter)
        self.logger.info(f'Scraped Product URLs: {len(self.urls)}')
