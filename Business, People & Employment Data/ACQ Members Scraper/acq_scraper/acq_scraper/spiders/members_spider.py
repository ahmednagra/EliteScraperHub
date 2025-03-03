import os
import json
import urllib.parse
from datetime import datetime
from collections import OrderedDict

import pandas as pd
from scrapy import Request, Spider

from slugify import slugify


class MembersSpiderSpider(Spider):
    name = "members_spider"
    start_urls = ["https://www.acq.org/repertoire-des-membres/"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    cookies = {
        'REGIONAL_ACQ': '0',
        'cmplz_consented_services': '',
        'cmplz_policy_id': '34',
        'cmplz_marketing': 'allow',
        'cmplz_statistics': 'allow',
        'cmplz_preferences': 'allow',
        'cmplz_functional': 'allow',
        'cmplz_banner-status': 'dismissed',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.acq.org',
        'Pragma': 'no-cache',
        'Referer': 'https://www.acq.org/repertoire-des-membres/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    def __init__(self):
        super().__init__()
        self.total_scraped_count = 0
        self.all_scraped_records = {}
        self.required_regions = self.read_input_regions_file()

        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/acq_log {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

    def parse(self, response, **kwargs):
        try:
            regions = json.loads(response.css('#acqRegionGeoloc-js-before').re_first(r'regions:(.*),'))
        except json.JSONDecodeError as e:
            regions = {}
            print('Regions parse Error: ', e)
            return

        for region in regions:
            region_name = region.get('name', '').replace('·', '')
            region_value = region_name.replace('·', '')
            if slugify(region_value).lower() in self.required_regions:
                print(region_name)
                region_id = region.get('external_id', '')
                yield Request(url='https://www.acq.org/wp-admin/admin-ajax.php', headers=self.headers, cookies=self.cookies,
                              body=self.get_formdata(region_id), callback=self.parse_region, dont_filter=True,
                              method='POST', meta={'handle_httpstatus_all': True, 'region_name': region_name})

    def parse_region(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            data = {}
            print(f'Response not in jSonFormat :{e}')
            return

        results = data.get('items', [])

        records = []
        try:
            for result in results:
                website_url = result.get('Website', '')
                item = OrderedDict()
                item['Business Name'] = result.get('UsualName', '')
                item['Person Name'] = result.get('LegalName', '')
                item['Phone Number 1'] = result.get('Phone', '')
                item['Phone Number 2'] = result.get('TollFreePhone', '')
                item['Fax Number'] = result.get('Fax', '')
                item['E - mail'] = result.get('Email', '')
                item['Address'] = result.get('Address', '').replace('\n', '')
                item['License Number'] = result.get('RbqNumber', '')

                if website_url:
                    if not (website_url.startswith('http://') or website_url.startswith('https://')):
                        website_url = f'http://{website_url}'
                    item['Website URL'] = website_url

                self.total_scraped_count += 1
                records.append(item)
        except Exception as e:
            print('Error Yield Item : ', e)

        region_name = response.meta.get('region_name', '').upper()

        # Ensure the region name key exists in the dictionary
        if region_name not in self.all_scraped_records:
            self.all_scraped_records[region_name] = []

        # Append records to the corresponding region name key
        self.all_scraped_records[region_name].extend(records)

    def read_input_regions_file(self):
        file_path = 'input/regions.txt'

        try:
            with open(file_path, mode='r') as txt_file:
                regions = [line.strip().lower().replace('·', '') for line in txt_file.readlines() if line.strip()]
                regions = [slugify(region) for region in regions]
                return regions
        except FileNotFoundError:
            self.write_logs(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.write_logs(f"An error occurred: {str(e)}")
            return []

    def write_to_excel(self):
        try:
            # Create the directory if it doesn't exist
            output_dir = 'output'
            os.makedirs(output_dir, exist_ok=True)

            # Save the workbook
            file_name = f'{output_dir}/ACQ Members Records {datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx'

            # Define headers for each sheet
            headers = ['Business Name', 'Person Name', 'Phone Number 1', 'Phone Number 2', 'Fax Number',
                       'E - mail', 'Address', 'License Number', 'Website URL']

            # Create a Pandas Excel writer using XlsxWriter as the engine
            with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
                for sheet_name, records in self.all_scraped_records.items():
                    # Truncate sheet names longer than 31 characters
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:25]

                    # Create a DataFrame for each sheet
                    df = pd.DataFrame(records, columns=headers)

                    # Write the DataFrame to the specified sheet
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            self.write_logs(f"Data saved to {file_name}")
        except Exception as e:
            self.write_logs(f"An error occurred while saving the data in output File Error: {str(e)}")

    def get_formdata(self, region_id):
        data = {
            'action': 'get_member_directory_members_ajax',
            'filters[keywords]': '',
            'filters[region]': region_id,
            'filters[city]': '',
        }

        encoded_data = urllib.parse.urlencode(data)
        return encoded_data

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def close(spider, reason):
        spider.write_to_excel()
        spider.write_logs(f'Total Items Scraped : {spider.total_scraped_count}')
