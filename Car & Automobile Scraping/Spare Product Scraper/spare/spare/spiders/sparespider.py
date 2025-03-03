import csv
import glob
import os
import re
from collections import OrderedDict
import requests

from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from scrapy import Request, Spider


class Sparepider(Spider):
    name = "spare"

    headers = {
        'authority': 'spare.avspart.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': '_ga=GA1.1.1732123088.1697867483; __gads=ID=60562290b33ca698:T=1697867485:RT=1697867485:S=ALNI_Mbp2Temfl0F2WBMcfBFpFeNHnoDHg; __gpi=UID=00000cbe00467315:T=1697867485:RT=1697867485:S=ALNI_MZrt6HgxbSSdXH5bkyaTHxOSUTl0w; sid=5c9b9a9b1bcdf0db507b3d4587fa069ebc092e32bdb27e93ff16da71; ved_sid=5c9b9a9b1bcdf0db507b3d4587fa069ebc092e32bdb27e93ff16da71; aws_do=do; FCNEC=%5B%5B%22AKsRol_z3yqoMeD6ilPRY6rmBQNICNBuce8-zYXA3lWZkQ-TpurPrx9xwgOkD_ngm1eTxDh2UHDjhjKhNclg6Af0SBeDxdJR70tPFvabmqPGicJL5kPxq33OYXG1rXyaZDv3vQTxhwh4zrLJ6RNY9eGxrlu-sWAtEg%3D%3D%22%5D%2Cnull%2C%5B%5D%5D; _ga_QQNZ6PDQHF=GS1.1.1697867482.1.1.1697867591.60.0.0',
        'if-modified-since': 'Sat, 21 Oct 2023 05:14:19 GMT',
        'if-none-match': '"65335e2b-1e85"',
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.urls_from_input_file = self.read_input_urls()

    def start_requests(self):
        for url in self.urls_from_input_file:
            yield Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):

        # Url has A no of Products then made request for each product
        more_products = response.css('#node-content .sticky-top').get('')
        if more_products:
            products_selector = response.css('.position-fixed ul .p-2')
            for product in products_selector:
                id = product.css('a::attr(href)').get('').replace('#', '')
                name = response.css(f'#{id} + .mt-5 + .mb-3 h2::text ').get('').strip()
                table_selector = response.xpath(f'//div[@id="{id}"]/following-sibling::div[@class="card mb-3"]').css(
                    '.after_reg .no_tables table')[0]
                table = self.get_table_records(table_selector)
                image_selector = response.css(f'#{id} + .mt-5 + .mb-3 + .not_show +.not_show + .mb-4')
                if image_selector:
                    image = image_selector.css('a::attr(href)').get('').replace('//c1.a2109.com/',
                                                                                'https://storage.googleapis.com/a2109_c1_500/')
                else:
                    image = ''

                item = {
                    'Name': name,
                    'Table': table,
                    'Image': image,
                    'Url': (response.url) + '#' + id,
                }
                excel_filename = self.create_files(item)
                self.write_data_to_csv(excel_filename, table)

        else:
            # if url has single product
            item = OrderedDict()
            item['Name'] = self.get_name(response)
            item['Image'] = response.css('[data-lightbox="image"]::attr(href)').get('').replace('//c1.a2109.com/',
                                                                                                'https://storage.googleapis.com/a2109_c1_500/')
            item['Url'] = response.url
            table_selector = response.css('.no_tables tbody') or []
            item['Table'] = self.get_table_records(table_selector)
            folder_create = self.create_files(item)  # create folder, download image and excel file name return
            self.write_data_to_csv(folder_create, item['Table'])

    def read_input_urls(self):
        file_path = ''.join(glob.glob('input/urls.txt'))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file.readlines()]
            return urls
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            return []

    def get_name(self, response):
        name = response.css('#title::attr(data-en)').get('').strip().replace(' ', '_')
        name = name or response.css('title::text').get('').strip()

        return name

    def get_table_records(self, table_selector):
        table = []

        for row in table_selector.css('tr'):
            part_no = row.css('td[data-title="Part №"] a ::text').get('').strip()
            part_no = part_no or row.css('[data-title="Note"] ::text').get('').strip()
            part_name = ''.join(row.css('td[data-title="Part name"] ::text').getall()).strip()
            part_name = part_name if part_name else ''
            quantity = ''.join(row.css('td[data-title="Qty"] ::text').re('\d+'))
            position = row.css('[data-title="Pos."]::text').get('').strip().replace('.', '')

            row_data = [part_no, part_name, quantity, position]

            # Check if any of the row data elements is non-empty
            if any(row_data):
                table.append(row_data)

        return table

    def download_image(self, image_url, filename):
        if not image_url:
            return
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            response = requests.get(image_url)
            with open(filename, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            print(f"An error occurred while downloading the image: {e}")

    def create_files(self, item):

        # Create a clean and safe folder name
        product_name = re.sub(r'[^\w\s-]', '', item['Name']).strip()[:40]

        if '\n' in product_name:
            product_name = re.sub(r'[\n/:*?"<>|]', ' ', product_name)
            folder_path = os.path.join('output', product_name)
            os.makedirs(folder_path, exist_ok=True)

        # Create the product folder if it doesn't exist
        folder_path = os.path.join('output', product_name)
        os.makedirs(folder_path, exist_ok=True)

        # Save the image
        image_filename = os.path.join(folder_path, 'image.jpg')
        self.download_image(item['Image'], image_filename)

        # Define the Excel filename
        product_name = product_name[:15]
        excel_filename = os.path.join(folder_path, f'{product_name}.csv')
        # excel_filename = os.path.join(folder_path, f'{product_name}.xlsx')

        return excel_filename

    def write_data_to_csv(self, filename, data):
        headers = ['Part no.', 'Name', 'Quantity required', 'Diagram no.', 'Supplier code']
        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(data)
        except Exception as e:
            print('error from writing csv is :', e)
