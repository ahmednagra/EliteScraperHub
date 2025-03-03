import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class DemotivateurSpider(BaseSpider):
    name = 'demotivateur'
    start_urls = ['https://www.demotivateur.fr/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.col-lg-12 .row .mb-3 a::attr(href)').getall()
        for article in article_urls:
            yield Request(url=response.urljoin(article), callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        if self.get_published_date(response) == self.get_today_date():
            item['Title'] = response.css('title::text').get('').strip()
            item['Summary'] = ''
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Description HTML'] = response.css('.article-body').get('')[:32676]
            item['Published At'] = self.get_published_date(response)
            item['Article URL'] = response.url

            self.current_scraped_items.append(item)

    def get_published_date(self, response):
        published_date = response.css('time::attr(datetime)').get('')

        publish_date = datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%S%z')
        # Format the datetime object as 'yyyy-month-date'
        published_date = publish_date.strftime('%Y-%m-%d')

        return published_date
