import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class MacgSpider(BaseSpider):
    name = 'macg'
    start_urls = ['https://www.macg.co/actu']

    # start_urls = ['https://www.macg.co/']

    def parse(self, response, **kwargs):
        article_selector = response.css('.actu-results section.section.mbs.mbm')
        sidebar_url = response.css('.sidebar-content a::attr(href)').getall()
        print('all Sidebar urls :', '\n'.join(sidebar_url))
        for article in article_selector:
            item = OrderedDict()
            published_date = article.css('.node-time::attr(datetime)').get('')
            date = datetime.now()
            today_date = date.strftime('%Y-%m-%d').lower().strip()

            if published_date == today_date:
                item['Title'] = article.css('.node-title ::text').get('')
                item['Summary'] = ''
                item['Image URL'] = article.css('[loading="lazy"]::attr(src)').get('')
                item['Description HTML'] = article.get()[:3600]
                item['Published At'] = article.css('.node-time::attr(datetime)').get('')
                item['Article URL'] = response.url
                self.current_scraped_items.append(item)
                print(item)

        for article_url in sidebar_url:
            if 'macg.co' in article_url:
                yield Request(url=article_url, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        published_date = response.css('.node-time::attr(datetime)').get('')

        if published_date == self.get_today_date():
            item['Title'] = response.css('.node-title ::text').get('').strip()
            item['Summary'] = ''
            item['Image URL'] = response.css('[loading="lazy"]::attr(src)').get('')
            item['Description HTML'] = response.css('#node-content .even').getall()[:32767]
            item['Published At'] = published_date
            item['Article URL'] = response.url

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
