import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime


class TopitospiderSpider(Spider):
    name = 'topito'
    start_urls = ['https://www.topito.com/']

    # custom_settings = {
    #     'CONCURRENT_REQUESTS': 8,
    #     'FEEDS': {
    #         f'output/Topito Articles Sscraper.csv': {
    #             'format': 'csv',
    #             'fields': ['Title', 'Summary', 'Image URL', 'Image Text', 'Description HTML', 'Published At',
    #                        'Article URL'],
    #             'overwrite': True,
    #         }
    #     }
    # }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_file = 'output/Topito Articles Scraper.csv'
        self.previous_scraped_articles = self.get_previous_products_from_csv()

    def parse(self, response, **kwargs):
        article_urls = response.css(
            'section:not(.with-separator) .card-post.type-home .main-link::attr(href), section:not(.with-separator) .card-post.type-post .main-link::attr(href)').getall()
        for article_url in article_urls:
            url = response.urljoin(article_url)
            if url in self.previous_scraped_articles:
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
            self.append_to_csv(item)

    def get_date_time(self, response):
        date_time = response.css('[property="article:published_time"] ::attr(content)').get('')
        parsed_datetime = datetime.fromisoformat(date_time)
        readable_datetime = parsed_datetime.strftime('%m/%d/%y : %I:%M %p')
        return readable_datetime

    def get_previous_products_from_csv(self):
        try:
            file_name = ''.join(glob.glob('output/*.csv'))
            with open(file_name, mode='r', encoding='utf-8') as csv_file:
                products = list(csv.DictReader(csv_file))
                return [product.get('Article URL', '') for product in products]

        except FileNotFoundError:
            return []

    def append_to_csv(self, item):
        try:
            with open(self.output_file, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=item.keys())

                # Check if the file is empty, and if so, write the header row
                if csv_file.tell() == 0:
                    writer.writeheader()

                writer.writerow(item)
        except Exception as e:
            print(f"Error appending to CSV: {str(e)}")
