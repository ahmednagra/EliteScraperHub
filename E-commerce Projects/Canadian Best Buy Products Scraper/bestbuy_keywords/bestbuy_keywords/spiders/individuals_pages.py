import csv
import datetime
import os.path

from bs4 import BeautifulSoup
from scrapy import Spider, Request, Selector


class SitemapsSpider(Spider):
    name = 'individuals_pages'
    base_url = 'https://quotes.toscrape.com/'
    start_urls = [base_url]

    def __init__(self, urls=None, **kwargs):
        super().__init__(**kwargs)
        self.urls = urls

    def parse(self, response, **kwargs):
        urlss = self.urls
        for url in urlss:
            yield Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        current_date = datetime.datetime.now().strftime('%d-%m-%Y')
        domain_directory = f'output/{current_date}'

        # if not os.path.isdir(domain_directory):
        #     os.mkdir(domain_directory)
        os.makedirs(domain_directory, exist_ok=True)

        filename_part = response.url.rstrip('/').split('/')[-1].split('.')[0]
        file_path = f'{domain_directory}/{filename_part}.txt'

        try:
            self.write_content_to_html(file_path, response.text)
        except AttributeError as e:
            a=0

    def write_content_to_html(self, filepath, html_content):
        # tree = lxml.html.fromstring(html_content)
        soup = BeautifulSoup(html_content)
        page_text = '\n'.join([text_line.strip() for text_line in soup.get_text().split('\n') if text_line.strip()])

        with open(filepath, mode='w', encoding='utf-8') as txt_file:

            txt_file.write(page_text)

    def get_sitempas_from_csv(self):
        with open('input/sitemaps.csv', mode='r', encoding='utf-8') as csv_file:
            return list(csv.DictReader(csv_file))

    def read_input_file(self):
        try:
            file_path = os.path.join('input', 'urls.txt')

            with open(file_path, 'r') as text_file:
                return [url.strip() for url in text_file.readlines() if url.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []
