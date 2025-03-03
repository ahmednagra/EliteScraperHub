import os
import re
import csv
import json
from math import ceil
from collections import OrderedDict
from datetime import datetime, timedelta

from scrapy import Request, Spider


class FilesDownloadSpider(Spider):
    name = 'fwc'

    base_url = 'https://www.fwc.gov.au/'
    start_urls = []
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
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

        self.search_url = self.get_search_url_from_file()

        self.total_products_count = 0
        self.current_scraped_items = []
        self.duplicates_product_count = 0
        self.current_items_scraped_count = 0
        self.previously_duplicates_product_count = 0

        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.output_csv_filepath = 'output/FWC Documents Data.csv'
        self.documents_download_folder_path = 'output/Documents'

        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

        self.output_column_names = ['agmnt_id', 'agmnt_title', 'matter_no', 'operative_date',
                                    'expiry_date', 'approval_date', 'company_name abn', 'industry', 'storage_name',
                                    'party_name', 'agmnt_type', 'fwc_text']

        self.previously_scraped_items = {item.get('agmnt_id', ''): item for item in
                                         self.get_previous_scarped_items_from_file()}

        self.previously_downloaded_documents_names = os.listdir(self.documents_download_folder_path)

        a=0

    def start_requests(self):
        self.mandatory_logs.append(f'Search URL: {self.search_url}')

        yield Request(url=self.search_url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        json_data = self.get_json_from_html(response)

        self.total_products_count = json_data.get('documentResult', {}).get('count', 0)
        total_pages = ceil(int(self.total_products_count) / 50)

        for page_no in range(1, total_pages+1):
            url = f'{response.url}&page={page_no}'

            yield Request(url=url, callback=self.parse_products, headers=self.headers)

    def parse_products(self, response):
        json_data = self.get_json_from_html(response)
        documents = json_data.get('documentResult', {}).get('results', [{}])

        for document in documents:
            try:
                document_dict = document.get('document', {})
                document_id = document_dict.get('PublicationID', '')

                # Current Scraping Revoke Duplication
                if document_id in [doc.get('agmnt_id') for doc in self.current_scraped_items]:
                    self.duplicates_product_count += 1
                    continue

                storage_name = document_dict.get('metadata_storage_name', '') or f'{document_id}.pdf'

                # Previously Scraped items from File Duplication Revoke
                if self.previously_scraped_items.get(document_id) and storage_name in self.previously_downloaded_documents_names:
                    self.previously_duplicates_product_count += 1
                    continue

                item = OrderedDict()
                item['agmnt_id'] = document_id
                item['agmnt_title'] = self.get_document_title(document_dict)
                item['matter_no'] = ''.join(document_dict.get('MatterName', []))
                item['expiry_date'] = self.get_date(document_dict, 'NominalExpiryDate')
                item['approval_date'] = self.get_date(document_dict, 'DocumentDates')
                item['company_name abn'] = self.get_documnet_company_name(document_dict)
                item['industry'] = ''.join(document_dict.get('AgreementIndustry', []))
                item['storage_name'] = storage_name
                item['party_name'] = document_dict.get('PartyName', '')
                item['agmnt_type'] = ''.join(document_dict.get('AgreementType', []))
                # item['fwc_text'] = self.get_document_text(document_dict)

                url = f"https://www.fwc.gov.au/document-search/view/3/{document_dict.get('metadata_storage_path', '')}"
                # yield Request(url=url, callback=self.parse_document_detail, headers=self.headers, meta={'item': item})
                self.current_scraped_items.append(item)

            except Exception as e:
                self.error.append(f"Document ID :{document.get('document', {}).get('PublicationID', '')}  Error in yield Document :{e}")
        a = 1

    def get_document_title(self, document_dict):
        try:
            title = document_dict.get('AgreementTitle', '')

            if isinstance(title, str):
                return title.replace('\u2013', '-')

            # Get title from DocumentTitle if it's a non-empty list
            elif isinstance(title, list) and title:
                return title[0].replace('\u2013', '-')

            return ''
        except Exception as e:
            return ''

    def parse_document_detail(self, response):
        item = response.meta.get('item', {})
        document_id = item.get('agmnt_id', '')
        storage_name = item.get('storage_name', '')

        document_params = self.get_document_params(response) if storage_name not in self.previously_downloaded_documents_names else None
        if document_params:
            yield Request(url=document_params[0], callback=self.download_document,
                          meta={'output_path': document_params[1], 'document_name': document_params[2]})

        if not self.previously_scraped_items.get(document_id):
            item['operative_date'] = self.get_operative_date(item, response)

            self.write_item_to_csv(item)
            self.current_items_scraped_count += 1
            print(f'\nCurrent Items Scraped Count: {self.current_items_scraped_count}\n')
            self.current_scraped_items.append(item)

            yield item

    def get_documnet_company_name(self, document_dict):
        company_name = document_dict.get('ABN', '')

        # Check if company_name is None
        if company_name is None:
            company_name = ''
        else:
            # Remove spaces from company_name if it's not 'Other' or 'None'
            company_name = company_name.replace(' ', '') if company_name not in ['Other', 'None'] else ''

        return company_name

    def get_json_from_html(self, response):
        try:
            data_dict = json.loads(
                response.css('script:contains("urlFacets") ::text').re_first(r'aspViewModel = (.*);'))
        except json.JSONDecodeError as e:
            data_dict = {}
            self.error.append(f'Error in Getting JSON from url: {response.url}  Error: {e}')

        return data_dict

    def get_date(self, product_dict, key):
        expiry_date_string = product_dict.get(f'{key}', '')  # Assuming product is a dictionary
        if expiry_date_string:
            expiry_date = datetime.strptime(expiry_date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%d %B %Y')
        else:
            expiry_date = ''

        return expiry_date

    def get_document_params(self, response):
        try:
            data_dict = json.loads(response.css('script:contains("docresult ")::text').re_first(r'docresult = (.*);'))
        except json.JSONDecodeError as e:
            data_dict = {}
            self.error.append(f'Error Reading Script Dictionary {response.url}  Error: {e}')

        output_folder = 'output/Documents'
        doc = data_dict.get('result', {}) or {}
        document_name = doc.get('metadata_storage_name', '') or f"{doc.get('PublicationID', '').lower()}.pdf"

        # Path to save the downloaded document
        output_path = os.path.join(output_folder, document_name)

        # Check if the document already downloaded and exist in the output folder
        if os.path.exists(output_path):
            return False

        # Check if the output folder exists, create it if it doesn't
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        download_link = f"{data_dict.get('decodedPath')}{data_dict.get('token')}"
        return download_link, output_path, document_name

    def download_document(self, response):
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

    def get_previous_scarped_items_from_file(self):
        try:

            with open(self.output_csv_filepath, mode='r', encoding='utf-8') as csv_file:
                previous_documents = list(csv.DictReader(csv_file))

            print('Total Records Loaded from previous file:', len(previous_documents))
            self.mandatory_logs.append(f'Total Previous Scraped Records Loaded from File: {len(previous_documents)}')

            return previous_documents
        except Exception as e:
            return []

    def write_item_to_csv(self, item):
        with open(self.output_csv_filepath, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.output_column_names)

            if csv_file.tell() == 0:
                writer.writeheader()

            # Write data to CSV
            writer.writerow(item)

        self.mandatory_logs.append(
            f'Records Inserted In Output file "Fair Work Commission" Successfully: {len(self.current_scraped_items)} ')

    def get_search_url_from_file(self):
        with open('input/search_url.txt', mode='r', encoding='utf-8') as txt_file:
            return ''.join([x.strip() for x in txt_file.readlines() if x.strip()][:1]).strip().split('&page=')[0]

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
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

        spider.mandatory_logs.append(f'\n\nSpider Error:: \n')
        spider.mandatory_logs.extend(spider.error or ['None'])

        spider.write_logs()