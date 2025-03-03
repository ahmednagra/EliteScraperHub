from scrapy import Request
from collections import OrderedDict
from .base import BaseSpider


class SneakerSpider(BaseSpider):
    name = 'sneaker'
    start_urls = ['https://sneakernews.com/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.popular-stories-list__title a::attr(href), .upcoming-releases__title a::attr(href), .latest-news-v2__content a::attr(href)').getall() or []
        for article in article_urls:
            yield Request(url=article, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Title'] = response.css('.wrapper h1::text').get('').strip()
        item['Intro'] = response.css('.artical-main .wrapper p::text').get('').strip()
        item['Main Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Content'] = self.get_content(response)
        item['Images of Shoes'] = response.css('.gallery-icon.landscape img::attr(src)').getall() or []
        item['Tags'] = ', '.join(response.css('.article-tag-section li ::text').getall())
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)

    def get_content(self, response):
        a= ''
        return a