from scrapy import Spider, Request
from collections import OrderedDict


class WalterSpider(Spider):
    name = 'walter'
    start_urls = ['https://waltertool.com/product-category/multimasters/starlock-blades/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEED_URI': f'output/walter Tools scraper.xlsx',
        'FEED_FORMAT': 'xlsx'
    }

    def parse(self, response, **kwargs):
        products_urls = response.css('a.pp-post-link::attr(href)').getall()
        for url in products_urls:
            yield Request(url=url, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('.fl-heading-text::text').get()
        item['Price'] = response.css('bdi::text').get('')
        item['Short Description'] = response.css('.woocommerce-product-details__short-description p::text').get('')
        item['Long Description'] = response.css('#tab-description p::text').get()
        # item['SKU'] = response.css('.sku::text').get()
        item['Categories'] = ', '.join(response.css('.posted_in a::text').getall())
        item['Image Url'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Product URL'] = response.url

        yield item

