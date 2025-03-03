import glob
import os
from datetime import datetime
from collections import OrderedDict

import openpyxl
import requests

from nameparser import HumanName

from scrapy import Spider, Request, Selector, FormRequest


class SpiderSpider(Spider):
    name = "spider"
    allowed_domains = ["whitepagescanada.ca"]

    main_start_datetime_str = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEEDS': {
            f'output/WhitPages Search Address Records {main_start_datetime_str}.xlsx': {
                'format': 'xlsx',
                'fields': ['Address', 'City', 'Province', 'Postal Code', 'City Assessment 2024', 'Last Estimated Price',
                           'Last Estimated Date', 'Sold Price', 'Sold Date', 'Notes:', 'First Name', 'Last Name', 'Phone'
                           ]
            }
        },
    }

    cookies = {
        'PHPSESSID': 'fna36pbfmk9e9k66u5tao2a37t',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'PHPSESSID=fna36pbfmk9e9k66u5tao2a37t',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://whitepagescanada.ca/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scraped_product_counter = 0
        self.addresses = self.read_input_excel_file()
        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.main_start_datetime_str}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

        self.current_scraped_items = []
        self.scraping_datetime = datetime.now().strftime('%Y-%m-%d %H%M%S')

    def start_requests(self):
        for address in self.addresses:
            search_url = 'https://whitepagescanada.ca/dir/address_search.php'
            street_address = address.get('Address', '').lower().replace('street', 'st').replace('avenue', 'ave')
            city = address.get('City', '')

            data = self.get_formdata(address=street_address, city=city)
            res = requests.get(search_url, params=data, headers=self.headers, cookies=self.cookies)

            if 'Results' in res.text:
                yield from self.parse_search_results(response=res, address=address)
            else:
                yield Request(url='https://quotes.toscrape.com/', callback=self.parse_person_records,
                              meta={'address': address}, dont_filter=True)

    def parse_search_results(self, response, address):
        html = Selector(text=response.text)
        persons_urls = html.css('.eleven.columns > table .rsslink-m::attr(href)').getall() or []
        for person_url in persons_urls:
            print('Person Url ', person_url)
            yield Request(url=person_url, headers=self.headers, cookies=self.cookies,
                          meta={'address': address}, callback=self.parse_person_records)

    def parse_person_records(self, response):
        item = OrderedDict()

        address_dict = response.meta.get('address', {})
        name = response.css('span[itemprop="name"] ::text').get('')

        item['Address'] = address_dict.get('Address', '')
        item['City'] = address_dict.get('City', '')
        item['Province'] = address_dict.get('Province', '')
        item['Postal Code'] = address_dict.get('Postal Code', '')
        item['City Assessment 2024'] = address_dict.get('City Assessment 2024', '')
        item['Last Estimated Price'] = address_dict.get('Last Estimated Price', '')
        item['Last Estimated Date'] = ''
        item['Sold Price'] = address_dict.get('Sold Price', '')
        item['Notes:'] = address_dict.get('Notes:', '')
        item['First Name'] = HumanName(name).first if name else ''
        item['Last Name'] = HumanName(name).last if name else ''
        item['Phone'] = response.css('span[itemprop="telephone"] ::text').get('')

        # Format the Sold Date as 'DD/MM/YYYY'
        sold_date = address_dict.get('Sold Date', '')
        if isinstance(sold_date, datetime):
            item['Sold Date'] = sold_date.strftime('%d/%m/%Y')
        else:
            item['Sold Date'] = sold_date

        item['Url'] = response.url

        self.scraped_product_counter += 1
        print('scraped_product_counter: ', self.scraped_product_counter)

        yield item

    def read_input_excel_file(self):
        file_path = glob.glob('input/properties.xlsx')[0]
        # Load the workbook and select the active worksheet
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        # Get the column headers
        headers = [cell.value for cell in sheet[1] if cell.value is not None]

        # Iterate over the rows and build the list of dictionaries
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = {headers[i]: row[i] if row[i] is not None else '' for i in range(len(headers))}
            data.append(row_dict)

        return data

    def get_formdata(self, address, city):
        params = {
            'txtaddress': address,
            'txtcity': city,
            'search.x': '0',
            'search.y': '0',
        }

        return params

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)
