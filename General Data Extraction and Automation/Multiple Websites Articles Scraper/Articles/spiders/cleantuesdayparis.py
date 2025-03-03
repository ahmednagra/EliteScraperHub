import csv
import glob
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request

from .base import BaseSpider


class CleantuesdayparisSpider(BaseSpider):
    name = 'cleantuesdayparis'
    start_urls = ['https://cleantuesdayparis.fr']

    def parse(self, response, **kwargs):
        article_urls = response.css('[rel="bookmark"]::attr(href), #recent-posts-3 li a::attr(href)').getall()
        for article_url in article_urls:
            # if article_url in self.gsheet_scraped_items_urls:
            #     self.gsheet_scraped_items_urls.append(article_url)
            #     print(f'Article Already scraped: {article_url}')
            #     continue
            # else:
            yield Request(url=response.urljoin(article_url), callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        # date = datetime.now()
        # today_date = date.strftime('%m/%d/%y')
        #
        # published_date = self.get_date_time(response)
        #
        # if published_date.split(' ')[0] == today_date:
        item['Category'] = response.css('[itemprop="articleSection"] ::text').get('').strip()
        item['Title'] = response.css('[itemprop="headline"]::text').get('')
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Content'] = '\n\n'.join(response.css('[itemprop="articleBody"] > :not(.code-block)').getall())[:32700]
        item['Article URL'] = response.url or response.css('[property="og:url"]::attr(content)').get('')
        # item['Summary'] = ''
        # item['Image Text'] = response.css('.wp-caption-text::text').get('')
        # item['Description HTML'] = '\n\n'.join(response.css('[itemprop="articleBody"] > :not(.code-block)').getall())[:32700]
        # item['Published At'] = ''

        self.current_scraped_items.append(item)
        # self.append_to_csv(item)

    # def get_date_time(self, response):
    #     date_time = response.css('[property="article:published_time"] ::attr(content)').get('')
    #     parsed_datetime = datetime.fromisoformat(date_time)
    #     readable_datetime = parsed_datetime.strftime('%m/%d/%y : %I:%M %p')
    #     return readable_datetime
