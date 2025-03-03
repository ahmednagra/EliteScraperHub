import csv
import glob
import re

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class WoopetsSpider(BaseSpider):
    name = 'woopets'
    start_urls = ['https://www.woopets.fr/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.home-actus-1 a::attr(href)').getall()
        for article in article_urls:
            yield Request(url=response.urljoin(article), callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        publish_date_time = response.css('[property="article:published_time"]::attr(content)').get('')
        publish_datetime = datetime.strptime(publish_date_time, '%Y-%m-%dT%H:%M:%S%z')
        published_date = publish_datetime.strftime('%Y-%m-%d')

        if published_date == self.get_today_date():
            item['Title'] = response.css('[itemprop="headline"]::text').get('') or response.css('.h--title::text').get('')
            item['Summary'] = ',  '.join(response.css('.chapo  ::text').getall())
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Description HTML'] = self.get_html_description(response)
            item['Published At'] = published_date
            item['Article URL'] = response.url

            self.current_scraped_items.append(item)

    def get_html_description(self, response):
        raw_html_description = '\n'.join(response.css('[itemprop="text"]').getall())
        html_description_comments_remove = re.sub(r'<!--.*?-->', '', raw_html_description, flags=re.DOTALL)  # Remove comments
        html_description_remove_instag = re.sub(r'<ins.*?</ins>', '', html_description_comments_remove, flags=re.DOTALL)  # Remove <ins> tags
        html_description = re.sub(r'<script.*?</script>', '', html_description_remove_instag, flags=re.DOTALL)  # Remove <script> tags

        return html_description
