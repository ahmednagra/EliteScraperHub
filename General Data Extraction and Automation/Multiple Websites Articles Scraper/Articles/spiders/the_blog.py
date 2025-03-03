import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class The_blogSpider(BaseSpider):
    name = 'the_blog'
    start_urls = ['https://the-blog.fr/']

    headers = {
        'authority': 'the-blog.fr',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9',
        'cache-control': 'max-age=0',
        # 'cookie': 'cf_clearance=mdQeAASavX2vQ1rM3supWQakBCLby56TOBMUs4ccCPg-1698739223-0-1-8314b3d7.33a9ccf.6723f89b-0.2.1698739223; _ga=GA1.1.734638562.1698739240; __gads=ID=2afc27f76f101768-22cb29fab1e400db:T=1698739243:RT=1698740621:S=ALNI_MaySbtHIfQlSU9Pc9ORvJYPgYfA7A; __gpi=UID=00000d9deccaccc3:T=1698739243:RT=1698740621:S=ALNI_MYDD_aIdzyHVQEL35Pv9F7VfD1vsA; _ga_CDMZLN445T=GS1.1.1698739240.1.1.1698740874.0.0.0',
        'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    }

    def parse(self, response, **kwargs):
        # article_selector = response.css('.rivax-posts-wrapper .post-item')
        # for article in article_selector:
        #     published_date = self.get_published_date(article)
        #
        #     if published_date == self.get_today_date():
        #         url = article.css('a.item-link::attr(href)').get('')
        #         yield Request(url=url, callback=self.parse_article, meta={'published_date': published_date})
        atricles_url = response.css('h2.title a::attr(href), h4.title a::attr(href)').getall()
        for article_url in atricles_url:
            yield Request(url=article_url, callback=self.parse_article, headers=self.headers)

        next_page = response.css('.next.page-numbers::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, callback=self.parse)

    def parse_article(self, response):
        item = OrderedDict()

        # item['Title'] = response.css('.title .title-span::text').get('').strip()
        # item['Summary'] = ''
        # item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
        # item['Description HTML'] = '\n'.join(response.css('.status-publish :not(div)').getall())[:32767]
        # item['Published At'] = response.meta.get('published_date', '')
        # item['Article URL'] = response.url
        item['Title'] = response.css('.title .title-span::text').get('').strip()
        item['Intro'] = response.css('.subtitle ::text').get('').strip()
        item['Image'] = response.css('[property="og:image"]::attr(content)').get('')
        item['Content'] = '\n\n\n'.join(response.css(
            'article :not(.code-block):not(.google-auto-placed):not(.su-box):not(.su-box-title):not(.su-box-content):not(script):not(.adsbygoogle)').getall())[:30000]
        item['Category'] = response.css('.category a::text').get('')
        item['Tags'] = ', '.join(response.css('[rel="tag"] ::text').getall())
        item['URL'] = response.url
        self.current_scraped_items.append(item)

    def get_published_date(self, article):
        published_date = ''.join(
            [x.replace('\n', '').replace(',', '').strip() for x in article.css('.date ::text').getall()])
        # Replace the French month name with its English equivalent
        month_translation = {
            'janvier': 'January', 'février': 'February', 'mars': 'March', 'avril': 'April',
            'mai': 'May', 'juin': 'June', 'juillet': 'July', 'août': 'August',
            'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'décembre': 'December'
        }
        for french_month, english_month in month_translation.items():
            published_date = published_date.replace(french_month, english_month)

        publish_date = datetime.strptime(published_date, '%B %d %Y')
        # Format the datetime object as 'MM/dd/yyyy'
        published_date = publish_date.strftime('%Y-%m-%d')

        return published_date
