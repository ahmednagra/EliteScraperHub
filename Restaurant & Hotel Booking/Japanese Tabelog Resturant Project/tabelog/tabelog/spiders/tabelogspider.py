import glob
from datetime import datetime
from collections import OrderedDict

from scrapy import Spider, Request


class TabelogspiderSpider(Spider):
    name = 'tabelog'
    start_urls = ['https://tabelog.com/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/Tabelog Restaurants {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Name', 'Reviews Count', 'Saves Count', 'Rating', 'Address', 'Genre', 'Business Hours', 'Number of Seats', 'Phone Number', 'URL'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories_urls = self.read_cats_urls()

    def start_requests(self):
        self.write_logs("Scraping is started", mode='w')

        if not self.categories_urls:
            self.write_logs("No category URLs provided. Spider will stop.")
            return

        for category in self.categories_urls:
            yield Request(url=category, callback=self.parse)

    def parse(self, response, **kwargs):
        city = response.css('.list-condition__title::text').get()
        total_products = int(response.css('.c-page-count .c-page-count__num strong::text').extract()[-1])
        self.write_logs(f'The no of Hotels in :{city}  is :{total_products}')

        genre_filters = response.css('.list-balloon__table.list-balloon__table--genre dd a::attr(href)').getall() or []

        if not genre_filters or total_products <= 1200:  # if any search url holds hotels less than or equal 1200
            yield Request(url=response.url, callback=self.parse_products, dont_filter=True)

        else:
            for filter_url in genre_filters:
                yield Request(url=filter_url, callback=self.parse_products)

    def parse_products(self, response):
        hotel_urls = response.css('.js-rstlist-info .list-rst::attr(data-detail-url)').getall()

        if not hotel_urls:
            self.write_logs("No Hotels URLs found from Response. Spider will stop.")
            return

        for hotel_url in hotel_urls:
            yield Request(url=hotel_url, callback=self.parse_product_detail)

        next_page = response.css('[rel="next"]::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, callback=self.parse_products)

    def parse_product_detail(self, response):
        item = OrderedDict()

        item['Name'] = response.css('.rstinfo-table__name-wrap span::text').get('')
        item['Address'] = ' '.join(response.css('.rstinfo-table__address span ::text').getall())
        item['Genre'] = response.css('.rstinfo-table__table th:contains(ジャンル) + td span::text').get('')
        item['Business Hours'] = '\n'.join(
            response.css('.rstinfo-table__table th:contains(営業時間) + td p::text').getall())
        item['Number of Seats'] = response.css('.rstinfo-table__table th:contains(席数) + td p::text').get('')
        item['Phone Number'] = response.css('.rstinfo-table__table th:contains(電話番号) + td strong::text').get('')
        item['Reviews Count'] = response.css('.rdheader-rating__review-target .num::text').get('')
        item['Saves Count'] = response.css('.rdheader-rating__hozon-target .num::text').get('')
        item['Rating'] = response.css('.rdheader-rating__score-val-dtl::text').get('')
        item['URL'] = response.url

        yield item

    def read_cats_urls(self):
        file_name = ''.join(glob.glob('input/categories urls.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except FileNotFoundError as e:
            print(e)
            return []

    def write_logs(self, message, mode='a'):
        with open("logs.txt", mode=mode, encoding='utf-8') as txt_file:
            txt_file.write(f"{datetime.now()} -> {message}\n")

