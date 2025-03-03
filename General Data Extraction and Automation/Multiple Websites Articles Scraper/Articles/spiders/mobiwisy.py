import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class MobiwisySpider(BaseSpider):
    name = 'mobiwisy'
    start_urls = ['https://mobiwisy.fr/']

    def parse(self, response, **kwargs):
        article_selector = response.css('#tdi_7 .td-animation-stack, #tdi_17 .td-animation-stack')
        for article in article_selector:
            published_date = self.get_published_date(article)

            if published_date == self.get_today_date():
                url = article.css('[rel="bookmark"]::attr(href)').get('')
                yield Request(url=url, callback=self.parse_article, meta={'published_date': published_date})

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('[property="og:title"]::attr(content)').get('').strip()
        item['Summary'] = ''
        item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Description HTML'] = response.css('.td-post-content').get('')[:32767]
        item['Published At'] = response.meta.get('published_date', '')
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)

    def get_published_date(self, article):
        published_date = article.css('.updated::attr(datetime)').get('').lower().strip()
        publish_date = datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%S%z')
        # Format the datetime object as 'yyyy-month-date'
        published_date = publish_date.strftime('%Y-%m-%d')

        return published_date
