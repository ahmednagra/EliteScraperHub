from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class TechnoSpider(BaseSpider):
    name = 'techno'
    start_urls = ['https://www.techno-science.net/']

    def parse(self, response, **kwargs):
        article_urls = response.css('.lienTitre > a::attr(href), .conteneur a::attr(href)').getall() or []
        for article in article_urls:
            yield Request(url=article, callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()

        item['Category'] = response.css('.headerModuleCentreGauche a::text').get('').strip()
        item['Title'] = response.css('.titre h1::text').get('').strip()
        item['Sources'] = response.css('.credits > a::text').get('').strip().strip()
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Content'] = '\n\n'.join(response.css('.texte :not(.encadrePubBas):not(script):not(.encadrePubHaut)').getall())[:30000]
        # item['Published At'] = response.meta.get('published_date', '')
        item['Article URL'] = response.url

        self.current_scraped_items.append(item)
