import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class ParlonsbasketSpider(BaseSpider):
    name = 'parlonsbasket'
    start_urls = ['https://www.parlons-basket.com/']

    def parse(self, response, **kwargs):
        article_selector = response.css('#posts_of_category_feed-2 a, .site-main__posts a')
        for article in article_selector:
            published_date = self.get_published_date(article)

            if published_date == self.get_today_date():
                url = article.css('a::attr(href)').get('')
                yield Request(url=url, callback=self.parse_article, meta={'published_date': published_date})

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('h1.entry-title::text').get('').strip()
        item['Summary'] = ''
        item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Description HTML'] = response.css('.entry-content').get('')[:32767]
        item['Published At'] = response.meta.get('published_date', '')
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)

    def get_published_date(self, article):
        published_date = article.css('.updated::text').get('').lower().strip()
        # Replace the French month name with its English equivalent
        month_translation = {
            'janvier': 'January', 'février': 'February', 'mars': 'March', 'avril': 'April',
            'mai': 'May', 'juin': 'June', 'juillet': 'July', 'août': 'August',
            'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }
        for french_month, english_month in month_translation.items():
            published_date = published_date.replace(french_month, english_month)

        publish_date = datetime.strptime(published_date, '%d %B %Y')
        # Format the datetime object as 'yyyy-month-date'
        published_date = publish_date.strftime('%Y-%m-%d')

        return published_date
