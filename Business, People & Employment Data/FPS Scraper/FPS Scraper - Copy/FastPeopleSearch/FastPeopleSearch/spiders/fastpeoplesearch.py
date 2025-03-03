import csv
import glob
import json
import os
from urllib.parse import urlencode

import openpyxl
import requests
import scrapy
from datetime import datetime


class FastpeoplesearchSpider(scrapy.Spider):
    name = 'fastpeoplesearch'
    url = 'https://www.fastpeoplesearch.com/address/{}_{}-{}'

    custom_settings = {
        # Zyte API Configuration
        # 'ZYTE_API_KEY': "bae3c3b2c954411ba6d0d8c0bae1842a", # currys & amazon
        'ZYTE_API_KEY': "ee13c722f64e47a1955faf2e864e63f8",
        'ZYTE_API_TRANSPARENT_MODE': True,

        # Default headers for Zyte API
        'DEFAULT_REQUEST_HEADERS': {
            "zyte_api": {
                "browserHtml": True,
                # "httpResponseBody": True,
                # "httpResponseHeaders": True,
            }
        },

        # Download Handlers
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
            "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        },

        # Middlewares
        'DOWNLOADER_MIDDLEWARES': {
            "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633,
        },
        'SPIDER_MIDDLEWARES': {
            "scrapy_zyte_api.ScrapyZyteAPISpiderMiddleware": 100,
        },

        # Request Fingerprinter
        'REQUEST_FINGERPRINTER_CLASS': "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter",

        # Retry and concurrency settings
        'DOWNLOAD_TIMEOUT': 300,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        # 'CONCURRENT_REQUESTS': 3,

        'CONCURRENT_REQUESTS': 1, # test
        'FEED_URI': f'output/fastpeopleData_{datetime.now().timestamp()}.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_ENCODING': 'utf-8-sig',
        'FEED_EXPORT_FIELDS': [
            "Address", "City", "State", "Zip", "Owner 1 First Name",
            "Owner 1 Last Name",
            "Owner 2 First Name", "Owner 2 Last Name", "Owner Mailing Address",
            "Owner Mailing City", "Owner Mailing State",
            "Owner Mailing Zip",
            "searchedAddress",
            "Person 1 Name", "Person 1 Age", "Person 1 location", "Person 1 currentAddress", "Person 1 AKA",
            "Person 1 phone 1", "Person 1 phone 2", "Person 1 phone 3",
            "Person 1 phone 4", "Person 1 phone 5",
            "Person 2 Name", "Person 2 Age", "Person 2 location", "Person 2 currentAddress", "Person 2 AKA",
            "Person 2 phone 1", "Person 2 phone 2", "Person 2 phone 3",
            "Person 2 phone 4", "Person 2 phone 5",
            "Person 3 Name", "Person 3 Age", "Person 3 location", "Person 3 currentAddress", "Person 3 AKA",
            "Person 3 phone 1", "Person 3 phone 2", "Person 3 phone 3",
            "Person 3 phone 4", "Person 3 phone 5",
            "Person 4 Name", "Person 4 Age", "Person 4 location", "Person 4 currentAddress", "Person 4 AKA",
            "Person 4 phone 1", "Person 4 phone 2", "Person 4 phone 3",
            "Person 4 phone 4", "Person 4 phone 5",
            "Person 5 Name", "Person 5 Age", "Person 5 location", "Person 5 currentAddress", "Person 5 AKA",
            "Person 5 phone 1", "Person 5 phone 2", "Person 5 phone 3",
            "Person 5 phone 4", "Person 5 phone 5",

        ]

    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Logs
        os.makedirs('logs', exist_ok=True)
        # self.logs_filepath = f'logs/Currys_logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        # self.write_logs(f'[INIT] Script started at {self.script_starting_datetime}')

        # Initialize search keywords from the input file
        # self.search_keywords = self.get_search_keywords_from_file()

        # Set up proxy key and usage flag
        self.proxy = self.get_scrapeops_api_key_from_file()
        self.location = 'eu'

    def read_xlsx(self):
        # try:
        #     with open('input/Sample Set.csv', 'r') as csv_file:
        #         return list(csv.DictReader(csv_file))
        #
        # except Exception as e:
        #     print(f"Error reading the Excel file: {e}")
        #     return None
        try:
            # Find the first Excel file in the input directory
            file_path = glob.glob('input/*.xlsx')[0]

            # Load the workbook and select the active sheet
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active

            # Get headers from the first row
            headers = [cell.value for cell in sheet[1]]

            # Collect data rows, converting each row to a dictionary
            data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                data.append(dict(zip(headers, row)))

            return data

        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return None

    def start_requests(self):
        list_data = self.read_xlsx()
        for data in list_data[:]:
            street = data.get('Owner Mailing Address')
            city = data.get('Owner Mailing City')
            state = data.get('Owner Mailing State')
            if 'Mailing' not in city:
                url = self.url.format(street.replace(' ', '-').lower(), city.replace(' ', '-').lower(), state.replace(' ', '-').lower())
                print('URl from start', url)
                searchAddress = street + ' , ' + city + ' ' + state
                print('searchAddress from start', searchAddress)
                # yield scrapy.Request(url=self.get_scrapeops_url(url), callback=self.parse, meta={'item': searchAddress, 'data': data,
                yield scrapy.Request(url=url, callback=self.parse, meta={'item': searchAddress, 'data': data, "handle_httpstatus_all": True})

    def parse(self, response):
        data_dict = dict()
        item_dict = response.meta['data']
        data_dict['Address'] = item_dict.get('Address')
        data_dict['City'] = item_dict.get('City')
        data_dict['State'] = item_dict.get('State')

        data_dict['Zip'] = item_dict.get('Zip')
        data_dict['Owner 1 First Name'] = item_dict.get('Owner 1 First Name')
        data_dict['Owner 1 Last Name'] = item_dict.get('Owner 1 Last Name')
        data_dict['Owner 2 First Name'] = item_dict.get('Owner 2 First Name')
        data_dict['Owner 2 Last Name'] = item_dict.get('Owner 2 Last Name')
        data_dict['Owner Mailing Address'] = item_dict.get('Owner Mailing Address')
        data_dict['Owner Mailing City'] = item_dict.get('Owner Mailing City')
        data_dict['Owner Mailing State'] = item_dict.get('Owner Mailing State')
        data_dict['Owner Mailing Zip'] = item_dict.get('Owner Mailing Zip')
        data_dict['searchedAddress'] = response.meta['item']
        person = 1
        persons = []
        for data in response.xpath('//div[@class="people-list"]/div[@class="card"]/div[@class="card-block"]'):
            if person <= 5:
                item = dict()
                item[f'Person {person} Name'] = data.xpath('.//h3[contains(text(),"Full Name:")]/following-sibling::text('
                                                           ')[1]').get(
                    '').strip() or data.xpath('./h2/a/span[@class="larger"]/text()').get('').strip()
                item[f'Person {person} Age'] = data.xpath('.//h3[contains(text(),"Age:")]/following-sibling::text()[1]').get('').strip()
                item[f'Person {person} location'] = data.xpath('./h2/a/span[@class="grey"]/text()').get('').strip()
                item[f'Person {person} currentAddress'] = ''.join(data.xpath('./h3[contains(text(),"Current Home '
                                                            'Address:")]/following::div[1]/strong/a/text()').getall(

                )).replace('\n', ', ').strip()
                item['currentPhoneNumber'] = data.xpath('./h3[strong[contains(text(),"Phone:")]]/following::strong['
                                                        '1]/a/text()').get('').strip()
                item[f'"Person {person} AKA",'] = ' | '.join(aka.xpath('./text()').get('') for aka in data.xpath('./h3[strong[contains(text(),'
                                                                                             '"AKA:")]]/following::span'))
                i = 1
                for phone in data.css('[title*="phone number"]'):
                    if i <= 5:
                        item[f'Person {person} phone {i}'] = ''.join(phone.xpath('./text()').getall()).strip().replace('\n', ', ')
                        i = i + 1
                persons.append(item)
            person = person + 1
        for datas in persons:
            data_dict.update(datas)
        yield data_dict

    def get_scrapeops_api_key_from_file(self):
        key = self.get_input_from_txt(file_path=glob.glob('input/scraperapi_key.txt')[0])
        if not key:
            return ''

        api_endpoint = f'http://scraperapi:{key[0]}@proxy-server.scraperapi.com:8001'
        return api_endpoint

    # def get_search_keywords_from_file(self):
    #     return self.get_input_from_txt(glob.glob('input/search_keywords.txt')[0])

    def get_input_from_txt(self, file_path):
        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            self.write_logs(f'[GET_INPUT_FROM_TXT] File not found: {file_path}')
            return []
        except Exception as e:
            self.write_logs(f'[GET_INPUT_FROM_TXT] Error reading file "{file_path}": {e}')
            return []

    def get_scrapeops_url(self, url):
        # payload = {'api_key': '1f4ba498-2bdb-42bc-8106-28c1c368b5c3', 'url': url, 'country': 'us'}
        payload = {'api_key': 'e21c645a-361a-4874-8dcf-816e85a40c77', 'url': url, 'country': 'us'}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url