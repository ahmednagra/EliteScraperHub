import glob
from collections import OrderedDict
import scrapy
from scrapy import Request


class InposscraperSpider(scrapy.Spider):
    name = "inposscraper"
    start_urls = ["https://www.inpos.eu/"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            'output/Inpos Products details.xlsx': {
                'format': 'xlsx',
                'fields': ['Name', 'Product Code', 'Price', 'Brand', 'Description', 'Product URL'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.urls_from_input_file = self.read_input_urls()

    def start_requests(self):
        for url in self.urls_from_input_file[:1]:
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        products_urls = response.css('.product-item-photo::attr(href)').getall()
        for url in products_urls:
            yield Request(url=url, callback=self.parse_detail)

        next_page = response.css('[title="Naslednja"]::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, callback=self.parse)

    def parse_detail(self, response):
        item = OrderedDict()

        item['Name'] = response.css('[itemprop="name"]::text').get('')
        item['Product Code'] = response.css('[itemprop="sku"]::text').get('')
        item['Price'] = response.css('.price::text').get('')
        item['Brand'] = response.css('[itemprop="brand"]::attr(content)').get('')
        # item['Description'] = response.css('[itemprop="description"]::text').get('')
        item['Description'] = ''.join(response.css('.description .value::text').getall())
        item['Product URL'] = response.url

        yield item

    def read_input_urls(self):
        file_path = ''.join(glob.glob('input/categories urls.txt'))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file.readlines()]
            return urls
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            return []
