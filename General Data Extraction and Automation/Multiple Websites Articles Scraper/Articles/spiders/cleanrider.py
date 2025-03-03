import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class CleanriderSpider(BaseSpider):
    name = 'cleanrider'
    start_urls = ['https://www.cleanrider.com/']

    def parse(self, response, **kwargs):
        article_selector = response.css('[class="sm:py-6"] article, main.pt-2 div[class="lg:col-span-6 lg:text-left mb-8"]')
        for article in article_selector:
            published_date = self.get_published_date(article)

            if published_date == self.get_today_date():
                url = article.css('[class="hover:text-primary"]::attr(href)').get('')
                yield Request(url=url, callback=self.parse_article, meta={'published_date': published_date})

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('.entry-title a::text').get('').strip()
        item['Summary'] = ''
        item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Description HTML'] = '\n'.join(response.css('.entry-content :not(div):not(img):not(aside)').getall())[:32767]
        item['Published At'] = response.meta.get('published_date', '')
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)

    def get_published_date(self, article):
        published_date = article.css('.flex-initial::text').get('')
        publish_date = datetime.strptime(published_date, '%d %b %Y %H:%M')
        published_date = publish_date.strftime('%Y-%m-%d')

        return published_date
