from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class EnerzineSpider(BaseSpider):
    name = 'enerzine'
    start_urls = ['https://www.enerzine.com/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.wp-block-post-title a::attr(href), .featured_title_over > a::attr(href), .featured_title_over h2 a::attr(href), h2.entry-title > a::attr(href)').getall() or []
        for article in article_urls:
            yield Request(url=article, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Category'] = ', '.join(response.css('.rank-math-breadcrumb a ::text').getall()[1:])
        item['Title'] = response.css('h1.entry-title::text').get('').strip()
        item['Intro'] = ' '.join(response.css('.entry-content > p strong::text').getall())
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Credits (sources)'] = ' '.join(response.css('div.entry-content p:contains("Source :") ::text').getall())
        item['Tags'] = ', '.join(response.css('.meta-tags a::text').getall())
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)
