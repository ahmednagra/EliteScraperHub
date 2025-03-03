import os
import re
import csv
import json
from math import ceil
from collections import OrderedDict
from datetime import datetime, timedelta

from scrapy import Request, Spider


class FilesDownloadSpider(Spider):
    name = "fwc_files_download"
    start_urls = [
        'https://www.fwc.gov.au/document-search?options=SearchType_3,SortOrder_agreement-date-desc,DocFromDate_01/01/2020&q=*&pagesize=50']
    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_products_count = 0
        self.current_scraped_item = []
        self.duplicates_product_count = 0
        self.current_items_scraped_count = 0
        self.previously_duplicates_product_count = 0

        self.logs_filename = f'logs/logs {self.current_dt}.txt'
        self.output_filename = 'FWC Documents Data.csv'

        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

        self.fieldnames = ['agmnt_id', 'agmnt_title', 'matter_no', 'operative_date',
                           'expiry_date', 'approval_date', 'company_name abn', 'industry', 'storage_name',
                           'party_name', 'agmnt_type', 'fwc_text']

        self.previously_scraped_items = {item.get('agmnt_id', '').lower(): item for item in
                                         self.get_previous_scarped_cars_from_file()}

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_pagination, headers=self.headers)

    def parse_pagination(self, response):
        try:
            data_dict = json.loads(
                response.css('script:contains("urlFacets") ::text').re_first(r'aspViewModel = (.*);'))
        except json.JSONDecodeError as e:
            data_dict = {}
            self.error.append(f'Error Dictionary at Pagination url: {response.url}  Error: {e}')

        self.total_products_count = data_dict.get('documentResult', {}).get('count', 0)
        total_pages = ceil(int(self.total_products_count) / 50)

        for page_no in range(1, total_pages):
            url = f'{response.url}&page={page_no}'
            yield Request(url=url, callback=self.parse_products, headers=self.headers)

    def parse_products(self, response):
        try:
            data_dict = json.loads(
                response.css('script:contains("urlFacets") ::text').re_first(r'aspViewModel = (.*);'))
        except json.JSONDecodeError as e:
            data_dict = {}
            self.error.append(f'Error Parse Dictionary at Products url: {response.url} Error: {e}')

        products = data_dict.get('documentResult', {}).get('results', [{}])

        for product in products:
            try:
                product_dict = product.get('document', {})
                item = OrderedDict()
                document_id = product_dict.get('PublicationID', '')

                # test
                error_list = ['AE507378', 'AE507371', 'AE507372', 'AE507373', 'AE507375', 'AE507377', 'AE507379',
                              'AE507384', 'AE507376', 'AE507370', 'AE508361', 'AE508357', 'AE508220', 'AE508210',
                              'AE508261', 'AE508220']
                for error in error_list:
                    if error in document_id:
                        a=1

                # Current Scraping Revoke Duplication
                if document_id in [doc.get('agmnt_id') for doc in self.current_scraped_item]:
                    self.duplicates_product_count += 1
                    continue

                # Previously Scraping items from File Duplication Revoke
                if document_id.lower() in self.previously_scraped_items:
                    self.previously_duplicates_product_count += 1
                    continue

                item['agmnt_id'] = document_id
                item['agmnt_title'] = product_dict.get('AgreementTitle', '').replace('\u2013', '-')
                item['matter_no'] = ''.join(product_dict.get('MatterName', []))
                item['expiry_date'] = self.get_date(product_dict, 'NominalExpiryDate')
                item['approval_date'] = self.get_date(product_dict, 'DocumentDates')
                item['company_name abn'] = product_dict.get('ABN', '').replace(' ', '') if product_dict.get('ABN',
                                                                                                            '') != 'Other' else ''
                item['industry'] = ''.join(product_dict.get('AgreementIndustry', []))
                item['storage_name'] = product_dict.get('metadata_storage_name', '')
                item['party_name'] = product_dict.get('PartyName', '')
                item['agmnt_type'] = ''.join(product_dict.get('AgreementType', []))
                item['fwc_text'] = self.get_document_text(product_dict)

                url = f"https://www.fwc.gov.au/document-search/view/3/{product_dict.get('metadata_storage_path', '')}"
                #yield Request(url=url, callback=self.parse_document_detail, headers=self.headers, meta={'item': item})

                # test
                self.current_items_scraped_count += 1
                print('Current Scraped Items Counter :', self.current_items_scraped_count)
                self.current_scraped_item.append(item)


            except Exception as e:
                self.error.append(
                    f"Document ID :{product.get('document', {}).get('PublicationID', '')}  Error in yield Document :{e}")

    def parse_document_detail(self, response):
        document_download = self.download_document(response)
        if document_download:
            yield Request(url=document_download[0], callback=self.request_download_file,
                          meta={'output_path': document_download[1], 'document_name': document_download[2]})

        item = OrderedDict()
        item.update(response.meta.get('item', {}))
        item['operative_date'] = self.get_operative_date(item, response)

        self.current_items_scraped_count += 1
        print('Current Scraped Items Counter :', self.current_items_scraped_count)
        self.current_scraped_item.append(item)

    def get_date(self, product_dict, key):
        expiry_date_string = product_dict.get(f'{key}', '')  # Assuming product is a dictionary
        if expiry_date_string:
            expiry_date = datetime.strptime(expiry_date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%d %B %Y')
        else:
            expiry_date = ''

        return expiry_date

    def download_document(self, response):
        try:
            data_dict = json.loads(response.css('script:contains("docresult ")::text').re_first(r'docresult = (.*);'))
        except json.JSONDecodeError as e:
            data_dict = {}
            self.error.append(f'Error Reading Script Dictionary {response.url}  Error: {e}')

        output_folder = 'output/Documents'
        document_name = data_dict.get('result', {}).get('metadata_storage_name', '')

        # Path to save the downloaded document
        output_path = os.path.join(output_folder, document_name)

        # Check if the document already downloaded and exist in the output folder
        if os.path.exists(output_path):
            return

        # Check if the output folder exists, create it if it doesn't
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        download_link = f"{data_dict.get('decodedPath')}{data_dict.get('token')}"
        return download_link, output_path, document_name

    def request_download_file(self, response):
        output_path = response.meta.get('output_path', '')
        document_name = response.meta.get('document_name', '')
        try:
            with open(output_path, 'wb') as f:
                f.write(response.body)
            return

        except Exception as e:
            self.error.extend(f'Error downloading document {document_name}: {e}')

    def get_operative_date(self, item, response):
        try:
            approve_date = item.get('approval_date', '')

            operative_date = ''.join(
                re.findall(r'will operate from\s*([^.]*)', response.text, re.IGNORECASE)[0:1]).replace('\n',
                                                                                                       '').replace(
                '\\n', '').strip()

            # if 'day' in operative_date or '7' in operative_date or 'days' in operative_date or 'seventh day' in operative_date:
            if 'day' in operative_date or '7' in operative_date or 'days' in operative_date or 'seventh day' in operative_date:

                if '17' in operative_date and 'as' not in operative_date:
                    return operative_date

                # Convert approve_date string to datetime object
                approve_date = datetime.strptime(approve_date, '%d %B %Y')
                # Add 7 days to the approved date
                approve_date += timedelta(days=7)
                # Format the resulting date back into the desired string format
                operative_date = approve_date.strftime('%d %B %Y')

            # remove "as required by section 54 of the Act"
            operative_date = ''.join(operative_date.split('as')[0:1]).strip()

            # Just get Digit to last digit value example: 06 May 2024
            matches = re.search(r'\b\d+(?:\s+[A-Za-z]+){1,2}\s+\d{4}\b', operative_date)

            if matches:
                operative_date = matches.group()

            if not any(char.isdigit() for char in operative_date):
                operative_date = ''

            if 'period' in operative_date or 'beginning' in operative_date or 'commence' in operative_date:
                operative_date = ''

            return operative_date
        except Exception as e:
            self.error.append(
                f"Product Id: {response.meta.get('item', {}).get('agmnt_id')}  error in getting Operative Date :{e}")
            return ''

    def get_document_text(self, product_dict):
        try:
            text = '\n'.join(product_dict.get('text', []))
            decoded_text = text.encode('latin1').decode('utf-8')
            cleaned_text = decoded_text.replace('â€º', '_').replace('-', '_')
            return cleaned_text[:32000]
        except Exception as e:
            return '\n'.join(product_dict.get('text', []))[:32000]

    def get_previous_scarped_cars_from_file(self):
        try:
            file_path = os.path.join('output', self.output_filename)

            with open(file_path, 'r') as csv_file:
                all_records = list(csv.DictReader(csv_file))

            print('Total Records Loaded:', len(all_records))
            self.mandatory_logs.append(f'Total Previous Scraped Records Loaded: {len(all_records)}')
            return all_records
        except Exception as e:
            return []

    def write_current_scraped_items_into_csv(self):
        if not self.current_scraped_item:
            self.mandatory_logs.append(
                f'{len(self.current_scraped_item)} : No new Record scraped.')
            return

        # Write the car_sold_records to a new CSV file
        file_path = os.path.join('output', self.output_filename)

        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)

            if csv_file.tell() == 0:
                writer.writeheader()

            # Write data to CSV
            writer.writerows(self.current_scraped_item)

        self.mandatory_logs.append(
            f'Records Inserted In output file "Fair Work Commission" Successfully: {len(self.current_scraped_item)} ')

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def close(spider, reason):
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"\n\n')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Found Total Products "{spider.total_products_count}"')
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" Scraped Total Products "{spider.current_items_scraped_count}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Duplicates Products "{spider.duplicates_product_count}"')
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" Previously Scraped Duplicates Products "{spider.previously_duplicates_product_count}"')

        spider.write_current_scraped_items_into_csv()

        spider.mandatory_logs.append(f'\n\nSpider Error:: \n')
        spider.mandatory_logs.extend(spider.error)

        spider.write_logs()
