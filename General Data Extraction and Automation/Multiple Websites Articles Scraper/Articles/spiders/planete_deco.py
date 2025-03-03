import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class PlaneteSpider(BaseSpider):
    name = 'planete'
    start_urls = ['https://planete-deco.fr/']

    def parse(self, response, **kwargs):
        article_selector = response.css('article.post')
        for article in article_selector:
            article_url = article.css('.read-more a::attr(href)').get('').strip()
            published_date = self.get_published_date(article)
            # published_date = '06/10/2023'
            date = datetime.now()
            today_date = date.strftime('%m/%d/%Y').lower().strip()
            if published_date == today_date:
                yield Request(url=article_url, callback=self.parse_article, meta={'published_date': published_date})

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('title::text').get('')
        item['Summary'] = ''
        item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Image Text'] = ''
        item['Description HTML'] = response.css('.content :not(em) :not(.ezoic-autoinsert-ad)').getall()[:3600]
        item['Published At'] = response.meta.get('published_date', '')
        item['Article URL'] = response.url
        response.css('.content:not(span)').getall()
        self.current_scraped_items.append(item)

    def get_published_date(self, response):
        published_date = response.css('.published-date ::text').get('').replace('Publié le', '').lower().strip()
        # Replace the French month name with its English equivalent
        month_translation = {
            'janvier': 'January', 'février': 'February', 'mars': 'March', 'avril': 'April',
            'mai': 'May', 'juin': 'June', 'juillet': 'July', 'août': 'August',
            'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }
        for french_month, english_month in month_translation.items():
            published_date = published_date.replace(french_month, english_month)

        publish_date = datetime.strptime(published_date, '%d %B %Y')
        # Format the datetime object as 'MM/dd/yyyy'
        published_date = publish_date.strftime('%m/%d/%Y')

        return published_date

