import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class ChienSpider(BaseSpider):
    name = 'chien'
    start_urls = ['https://www.chien.fr/']

    def parse(self, response, **kwargs):
        article_selector = response.css('.container:not(.page-footer) ul.unstyled li a::attr(href)').getall()

        for article in article_selector:
            yield Request(url=response.urljoin(article), callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('.page-title::text').get('').strip()
        item['Category'] = response.css('.textOverflowEllipsis li:not(.active) span::text').getall()[-1]
        item['Intro'] = response.css('.chapo ::text').get('')
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Source Img'] = response.css('.image-copyright::text').get('').strip()
        item['Content'] = response.css('[itemprop="text"]').get('')[:30000]
        item['URL'] = response.url

        self.current_scraped_items.append(item)
