import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class TopitoSpider(BaseSpider):
    name = 'topito'
    start_urls = ['https://www.topito.com/']

    def parse(self, response, **kwargs):
        article_urls = response.css(
            'section:not(.with-separator) .card-post.type-home .main-link::attr(href), section:not(.with-separator) .card-post.type-post .main-link::attr(href)').getall()
        for article_url in article_urls:
            url = response.urljoin(article_url)
            if url in self.gsheet_scraped_items_urls:
                self.current_scraped_items.append(url)
                print(f'Article Already scraped: {url}')
                continue
            else:
                yield Request(url=url, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        date = datetime.now()
        today_date = date.strftime('%m/%d/%y')

        published_date = self.get_date_time(response)

        if published_date.split(' ')[0] == today_date:
            item['Title'] = response.css('title ::text').get('')
            item['Summary'] = ''
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Image Text'] = ''
            description_html = response.xpath("//div[@class='post-content post-padding container-content with-separator post-intro structured']//*[not(ancestor::div[@class='cow']) and not(@class='cow')]").getall()
            item['Description HTML'] = ''.join(description_html)[:3600]
            item['Published At'] = published_date
            item['Article URL'] = response.url

        # yield item
        # self.append_to_csv(item)
        self.current_scraped_items.append(item)


