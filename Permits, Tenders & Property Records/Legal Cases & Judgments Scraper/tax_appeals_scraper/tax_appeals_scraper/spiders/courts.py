import re
import os
import glob
from datetime import datetime

import hashlib
from math import ceil
from unidecode import unidecode
from scrapy import Spider, Request, FormRequest


class CourtSpider(Spider):
    name = "courts"
    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    custom_settings = {
        # "CONCURRENT_REQUESTS": 4,
        'DOWNLOAD_TIMEOUT': 250,  # Extend timeout for slow responses (in seconds)
        'RETRY_TIMES': 3,  # Number of retries for failed downloads
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Referer': '',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    def __init__(self):
        super().__init__()
        self.items_scraped = 0
        self.years_item_found = 0
        self.current_records = []

        # files & Records
        os.makedirs('output/courts_judgments', exist_ok=True)
        self.previous_pdfs = self.get_previous_records()

        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/{self.name.title()}_{self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'[INIT] Script started at {self.script_starting_datetime}')
        self.write_logs(f"Total Previous Judgment Files Found: {len(self.previous_pdfs)}")

    def start_requests(self):
        for year in range(2002, 2026):
            #for 100 records
            url = f'https://www.courts.ie/search/judgments/" type:Judgment" AND "filter:alfresco_radio.title" AND "filter:alfresco_Court.High court" AND "filter:alfresco_Court.Court of Appeal" AND "filter:alfresco_fromdate.01 Jan {year}" AND "filter:alfresco_todate.31 Dec {year}"'
            self.headers['Referer']= url
            yield Request(url, callback=self.parse, headers=self.headers, meta={'year_no':year})

    def parse(self, response, **kwargs):
        year = response.meta.get('year_no')
        total_records = response.css('.search-amount b::text').get('')
        self.write_logs(f"Processing Year: {year} | Total Courts Judgments Found: {total_records}")

        #judgments Pds links and name
        table_tr = response.css('.alfresco-table tbody tr')
        if table_tr:
            yield from self.pagination(response)

    def pagination(self, response):
        year = response.meta.get('year_no')
        total_records = response.css('.search-amount b::text').get('')
        table_tr = response.css('.alfresco-table tbody tr')
        for tr in table_tr:
            name = tr.css('td + td ::text').get('')
            name= name.replace('  ', ' ').replace('/', '-').strip() if name else ''
            formatted_name = unidecode(name)
            max_filename_length = 150  # Define a safe maximum length
            if len(formatted_name) > max_filename_length:
                formatted_name = formatted_name[:145]

            if formatted_name in self.previous_pdfs:
                print(f"[SKIP] Year:{year} ,'{formatted_name}' has already been scraped. Skipping to the next record...")
                self.items_scraped += 1
                continue

            url = tr.css('td.pdf a ::attr(href)').get('')
            url = f'https://www.courts.ie{url}' if url else ''
            if name and url:
                # Trigger file download using Scrapy Request
                yield Request(url, callback=self.download_pdf,
                    meta={'name': formatted_name, 'year': year}
                    # dont_filter=True  # Allows downloading duplicate URLs if necessary
                )

        #pagination
        if not response.meta.get('pagination', ''):
            total_pages = ceil(int(total_records) / 100)
            for pg_no in range(1, total_pages):
                print(pg_no)
                url = f'{response.url}?page={pg_no}'
                response.meta['pagination']= True
                self.headers['Referer'] = url
                yield Request(url, callback=self.pagination, headers=self.headers, meta=response.meta)

    def download_pdf(self, response):
        def save_file(file_path):
            """Helper function to save the file."""
            with open(file_path, 'wb') as f:
                f.write(response.body)

        # Extract metadata from the response
        name = response.meta.get('name', 'unknown_document')
        year = response.meta.get('year', 'unknown_year')

        # Prepare output directory
        output_dir = os.path.join('output', 'courts_judgments', str(year))
        os.makedirs(output_dir, exist_ok=True)
        # Initial attempt to save the file
        try:
            file_path = os.path.join(output_dir, f"{name}.pdf")
            save_file(file_path)
            print(f"Downloaded PDF: {name} | Saved to: {file_path}")
            self.items_scraped += 1
            print(f'Item Scraped: {self.items_scraped}')
        except Exception as e:
            # Log the failure of the first attempt
            self.write_logs(f"Failed to save PDF on first attempt: Year:{year} | Name:{name} | Error: {e}")

            # Fallback: sanitize the filename and try again
            try:
                sanitized_name = re.sub(r'[<>:"/\\|?*\[\]\n]', '_', name).strip()
                sanitized_name = re.sub(r'\s+', ' ', sanitized_name)  # Remove double spaces
                file_path = os.path.join(output_dir, f"{sanitized_name}.pdf")
                save_file(file_path)
                print(f"Downloaded PDF (sanitized): {sanitized_name} | Saved to: {file_path}")
                self.items_scraped += 1
                print(f'Item Scraped: {self.items_scraped}')
            except Exception as e:
                # Log the failure of the second attempt
                self.write_logs(f"Failed to save PDF after sanitization: Year:{year} | Name:{name} | Error: {e}")

    def get_previous_records(self):
        try:
            # Get all PDF file paths from 'courts_judgments' directory
            files = glob.glob('output/courts_judgments/*/*.pdf')

            # Extract only the file names (without the directory path and extension)
            names = [os.path.splitext(os.path.basename(file))[0].strip() for file in files]
            return names
        except Exception as e:
            print(f"Error in get_previous_records: {e}")
            return []

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)
