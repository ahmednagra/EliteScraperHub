import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class JournalzibelineSpider(BaseSpider):
    name = 'journalzibeline'
    start_urls = ['https://journalzibeline.fr/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.block .mask-img::attr(href)').getall()
        for url in article_urls:
            yield Request(url=url, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        publish_date_time = response.css('.date .entry-date::attr(datetime)').get('')
        publish_datetime = datetime.strptime(publish_date_time, '%Y-%m-%dT%H:%M:%S%z')
        published_date = publish_datetime.strftime('%Y-%m-%d')

        if published_date == self.get_today_date():
            item['Title'] = response.css('h1.title::text').get('')
            item['Summary'] = ''
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Description HTML'] = '\n'.join(response.css('.entry-content.body-color').getall())[:32767]
            item['Published At'] = published_date
            item['Article URL'] = response.url

            self.current_scraped_items.append(item)
