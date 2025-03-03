import csv
import glob
import json
import os
from urllib.parse import urlencode

import openpyxl
import requests
import scrapy
from datetime import datetime

from scrapy import Selector


class FastpeoplesearchSpider(scrapy.Spider):
    name = 'api_fastpeoplesearch'
    # url = 'https://www.fastpeoplesearch.com/address/{}_{}-{}'

    custom_settings = {
        'CONCURRENT_REQUESTS': 1, # test
        'FEED_URI': f'output/api_fastpeopleData_{datetime.now().timestamp()}.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_ENCODING': 'utf-8-sig',
        'FEED_EXPORT_FIELDS': [
            "Address", "City", "State", "Zip", "Owner 1 First Name",
            "Owner 1 Last Name",
            "Owner 2 First Name", "Owner 2 Last Name", "Owner Mailing Address",
            "Owner Mailing City", "Owner Mailing State",
            "Owner Mailing Zip", "searchedAddress",
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

    headers = {
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'cookie': '_pxvid=8e0d9a0e-9b97-11ef-a961-49b3a63830c0; ALLOW_COOKIES=true; __cf_bm=T1BY4uvD8P84aKlShhtX5OdNYRAFz14h8OQ5Omxe1nw-1730987286-1.0.1.1-5kJH3rcbi7WauIVYY1aYscnhYBqJ4vt9xQoqY3H05ICML7P_i3HpT4zGwBilBscef1F_ul8Jf6px_1jKX7D7gA; cf_chl_rc_m=1; _pxhd=5a7f588b255a5ccd0f3495d8a0c1630a412d0e607497112f30f946b1ad23d437:8e0d9a0e-9b97-11ef-a961-49b3a63830c0; cf_clearance=_c8hGJvy724.PCLgnBW8HJbpn5t5YxKwEG1Fi5VrRYY-1730987440-1.2.1.1-uq5znzs5PRAOeAUSnywn10V7fhWgju8ZOvkaQTYcAUuJ7QVYtTJnrM.AnbS_ZbiM.W6sSqLkMC4ltetmHIH3oACdnxVJazsv7EHFg5mGi.gAu8rQgjKiSSEaapazgfw5qgnU3r5or2YojgRLX9Kp4iFgU9FD2APdhD4igSs97Z.64ZiqwvsCNFJiOEvD3HoWgf_N13t7LMGlSE6Yn_lyxzpNcpqmXWAFsYeO81wWaK8_W44h5hb.ypX47vQbIjQqL.6_aXVPolgebklbklhYsK1_5BKUxkKU8ENMo_ZiIqRcdFGYuW2I0sRIM6Eo4WrgLPAhWoz61dcs0w1I_h8P_SRz9L6pL.NeHYyfEI.Dt408dq8jhuSft4kqddaYVzpn9PaxkjDJQv8h6XCDjFgHdz_mdEKY..f06DPBjm11_mwGkbXkNELvAjCRDgTHoLYD; pxcts=4e63a276-9d0f-11ef-a5d2-a7a072593d22; _px3=3637ce5edde17176b8497d6a582306bdd815c241ef1f5cc72443e81b1bbb95b4:dvYXocr5xVTIizDHiiTZcu92KI/Hs0baXIO21pY9NyXbpzYsWg1qRJWfAJL+rwKz30zlsHsMAnC+1tropsCFFw==:1000:k7mOfJUNRuEKBQqiHVTiFShm2I/mAC1Hcn4OB9KYs9i9SQWFJg3opLShiem1LGu2jMI/s5O3Y+3831r5T4YDqkaR+7TV2HIZzGQukZRWilLd2KEpeAWi/qVbjnxqPmThRoCUq4DIL/hHwMbZNt8rzcsqqdehLVwYwrui+8xfihZtzIrowswywjJUp1nm93l4Ns21SVaVxF4DGIy9oqJjYxCcMc09CoPzHtah8m9DILU=',
        'origin': 'https://www.fastpeoplesearch.com',
        'priority': 'u=1, i',
        'referer': 'https://www.fastpeoplesearch.com/address/1423-e-78th-st_los-angeles-ca',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"130.0.6723.92"',
        'sec-ch-ua-full-version-list': '"Chromium";v="130.0.6723.92", "Google Chrome";v="130.0.6723.92", "Not?A_Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
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
        for data in list_data[:1]:
            street = data.get('Owner Mailing Address')
            city = data.get('Owner Mailing City')
            state = data.get('Owner Mailing State')
            if 'Mailing' not in city:
                # url = self.url.format(street.replace(' ', '-'), city.replace(' ', '-'), state.replace(' ', '-'))
                searchAddress = street + ' , ' + city + ' ' + state

                demo_url = 'https://www.fastpeoplesearch.com/address/1423-E-78th-St_Los-Angeles-CA'
                data = {
                    'wamPage': 'Listing - Address',
                    'section': 'list',
                    'searchType': 'address',
                    'fn': '',
                    'mn': '',
                    'ln': '',
                    'city': 'Los+Angeles',
                    'state': 'CA',
                    'age': '',
                    'phone': '',
                    'address_1': '1423+e+78th+st',
                    'address_2': 'los+angeles+ca',
                    'email': '',
                    # 'userIP': '174.175.217.128',
                    'userIP': '198.44.138.101',
                    'noResults': '',
                    'gResults': '[{&quot;firstname&quot;:&quot;Jesus&quot;,&quot;middlename&quot;:&quot;J&quot;,&quot;lastname&quot;:&quot;Hernandez&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Jesus J Hernandez&quot;,&quot;age&quot;:75,&quot;city&quot;:&quot;Whittier&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90605&quot;,&quot;tahoeId&quot;:&quot;G-3762633844884142977&quot;},{&quot;firstname&quot;:&quot;Gregorio&quot;,&quot;middlename&quot;:&quot;Michael&quot;,&quot;lastname&quot;:&quot;Vargas&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Gregorio Michael Vargas&quot;,&quot;age&quot;:60,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90011&quot;,&quot;tahoeId&quot;:&quot;G4812462561777258990&quot;},{&quot;firstname&quot;:&quot;Reynaldo&quot;,&quot;middlename&quot;:&quot;D&quot;,&quot;lastname&quot;:&quot;Medellin&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Reynaldo D Medellin&quot;,&quot;age&quot;:33,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G-3890030625198376881&quot;},{&quot;firstname&quot;:&quot;Nayeli&quot;,&quot;middlename&quot;:&quot;Dayanara&quot;,&quot;lastname&quot;:&quot;Hernandez&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Nayeli Dayanara Hernandez&quot;,&quot;age&quot;:30,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G8558726438371413608&quot;},{&quot;firstname&quot;:&quot;Nilda&quot;,&quot;middlename&quot;:null,&quot;lastname&quot;:&quot;Cruz&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Nilda Cruz&quot;,&quot;age&quot;:45,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G5811605182773174466&quot;},{&quot;firstname&quot;:&quot;Dalia&quot;,&quot;middlename&quot;:null,&quot;lastname&quot;:&quot;Gutierrez&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Dalia Gutierrez&quot;,&quot;age&quot;:47,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G5047647197463083018&quot;},{&quot;firstname&quot;:&quot;Juan&quot;,&quot;middlename&quot;:&quot;A Molina&quot;,&quot;lastname&quot;:&quot;Gutierrez&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Juan A Molina Gutierrez&quot;,&quot;age&quot;:32,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G-1312867908717696400&quot;},{&quot;firstname&quot;:&quot;Ashley&quot;,&quot;middlename&quot;:null,&quot;lastname&quot;:&quot;Medellin&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Ashley Medellin&quot;,&quot;age&quot;:24,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G-6323109582209457728&quot;},{&quot;firstname&quot;:&quot;Marisol&quot;,&quot;middlename&quot;:null,&quot;lastname&quot;:&quot;Molina&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Marisol Molina&quot;,&quot;age&quot;:28,&quot;city&quot;:&quot;Los Angeles&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90001&quot;,&quot;tahoeId&quot;:&quot;G-3253876514926717310&quot;},{&quot;firstname&quot;:&quot;Roxana&quot;,&quot;middlename&quot;:&quot;B&quot;,&quot;lastname&quot;:&quot;Pomposo&quot;,&quot;prefix&quot;:null,&quot;suffix&quot;:null,&quot;fullname&quot;:&quot;Roxana B Pomposo&quot;,&quot;age&quot;:39,&quot;city&quot;:&quot;South Gate&quot;,&quot;state&quot;:&quot;CA&quot;,&quot;zip5&quot;:&quot;90280&quot;,&quot;tahoeId&quot;:&quot;G-3381500288434610179&quot;}]',
                    'requestPath': 'address/1423-e-78th-st_los-angeles-ca',
                    'isMobile': 'false',
                }

                # yield scrapy.Request('https://www.fastpeoplesearch.com/api/v1/adHandler',method="POST", callback=self.parse,
                                         # headers=self.headers, body=json.dumps(data), meta={'item': searchAddress, 'data': data,
                                         #                                 "handle_httpstatus_all": True})
                url = 'https://www.fastpeoplesearch.com/api/v1/adHandler'
                yield scrapy.FormRequest(
                    url=self.get_scrapeops_url(url),
                    headers=self.headers,
                    formdata=data,
                    callback=self.parse,
                    meta = {'item': searchAddress, 'data': data, 'handle_httpstatus_all': True}
                )
                # yield scrapy.Request(url=self.get_scrapeops_url(url), callback=self.parse, meta={'item': searchAddress, 'data': data,
                # yield scrapy.Request(url=url, callback=self.parse, meta={'item': searchAddress, 'data': data,
                #                                                          "handle_httpstatus_all": True})
                                                                         # "zyte_api_automap": {"browserHtml": True}})

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

        html = Selector(text=response.text)

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
        payload = {'api_key': 'e21c645a-361a-4874-8dcf-816e85a40c77', 'url': url, 'country': 'us', 'keep_headers': True}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url