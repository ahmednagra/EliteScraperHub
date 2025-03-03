from scrapy import Request
from collections import OrderedDict
from .base import BaseSpider


class TekpolisSpider(BaseSpider):
    name = 'tekpolis'
    start_urls = ['https://www.tekpolis.fr/']

    def parse(self, response, **kwargs):
        article_selector = response.css('.columns-3 li a::attr(href)').getall()
        for article_url in article_selector:
            yield Request(url=article_url, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('[itemprop="headline"] ::text').get('')
        item['Intro'] = ', '.join(response.css('[role="doc-subtitle"] ::text').getall())
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        # item['Content'] = response.css('#node-content .even').getall()[:32767]
        item['Content'] = response.css('.entry-content').get('')
        item['Category'] = ', '.join(response.css('a[rel="category tag"] ::text ').getall())
        item['Tags'] = ', '.join(response.css('a[rel="category tag"] ::text, a[rel="tag"] ::text ').getall())
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)
