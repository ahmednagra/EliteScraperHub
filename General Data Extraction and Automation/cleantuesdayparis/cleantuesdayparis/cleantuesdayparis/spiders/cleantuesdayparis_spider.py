import csv
import glob
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request


class CleantuesdayparisSpiderSpider(Spider):
    name = 'cleantuesdayparis'
    start_urls = ['https://cleantuesdayparis.fr']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_file = 'output/cleantuesdayparis Articles Sscraper.csv'
        self.previous_scraped_articles = self.get_previous_products_from_csv()

    def parse(self, response, **kwargs):
        article_urls = response.css('[rel="bookmark"]::attr(href), #recent-posts-3 li a::attr(href)').getall()
        for article_url in article_urls:
            if article_url in self.previous_scraped_articles:
                print(f'Article Already scraped: {article_url}')
                continue
            else:
                yield Request(url=response.urljoin(article_url), callback=self.parse_article)

    def parse_article(self, response):

        item = OrderedDict()
        date = datetime.now()
        today_date = date.strftime('%m/%d/%y')

        published_date = self.get_date_time(response)

        if published_date.split(' ')[0] == today_date:
            item['Title'] = response.css('[itemprop="headline"]::text').get('')
            item['Summary'] = ''
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Image Text'] = response.css('.wp-caption-text::text').get('')
            item['Description HTML'] = '\n\n'.join(
                response.css('[itemprop="articleBody"] > :not(.code-block)').getall())[
                                       :3600]
            item['Published At'] = published_date
            item['Article URL'] = response.url or response.css('[property="og:url"]::attr(content)').get('')

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
