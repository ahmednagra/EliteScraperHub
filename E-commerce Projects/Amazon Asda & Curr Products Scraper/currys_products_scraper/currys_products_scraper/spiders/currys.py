import os
import csv
import glob
import json
import re
from datetime import datetime
from collections import OrderedDict
from urllib.parse import urljoin, quote

import requests
from scrapy import Request, Spider


class CurrySpider(Spider):
    name = "curry"
    allowed_domains = ["www.currys.co.uk"]
    base_url = 'https://www.currys.co.uk'
    current_dt = datetime.now().strftime("%d%m%Y%H%M")
    api_url = "https://phplaravel-1369810-5049628.cloudwaysapps.com/api/push-data"

    custom_settings = {
        # Zyte API Configuration
        'ZYTE_API_KEY': "bae3c3b2c954411ba6d0d8c0bae1842a",
        'ZYTE_API_TRANSPARENT_MODE': True,

        # Default headers for Zyte API
        'DEFAULT_REQUEST_HEADERS': {
            "zyte_api": {
                "httpResponseBody": True,
                "httpResponseHeaders": True,
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
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        # 'CONCURRENT_REQUESTS': 3,
    }

    fields = [
        'retailer_id', 'retailer_name', 'retailer_country', 'retailer_website',
        'product_id', 'product_title', 'product_description', 'promotion_type',
        'promotion_description', 'promotion_price', 'promotion_discount',
        'promotion_conditions', 'promotion_start_date', 'promotion_expiry',
        'promotion_badge_type', 'rich_content_displayed', 'rich_content_images',
        'timestamp'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Logs
        logs_dir = '/app/logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Generate the log file path with timestamp
        self.current_dt = datetime.now().strftime("%d%m%Y%H%M")
        self.logs_filepath = f'{logs_dir}/Currys_logs_{self.current_dt}.txt'

        # Record script start time and write to log
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'[INIT] Script started at {self.script_starting_datetime}')

        # Initialize search keywords from the input file
        self.search_keywords = self.get_search_keywords_from_file()

        self.items_scrapped = 0
        self.total_items = 0
        self.scraped_urls = []
        self.duplicates_count = 0

    def start_requests(self):
        # Log the total number of search keywords available
        self.write_logs(f'[START_REQUESTS] Number of search keywords: {len(self.search_keywords)}')

        for keyword in self.search_keywords:
            print(f'Search Keyword: {keyword}')
            url = f'https://www.currys.co.uk/search?q={quote(keyword)}&search-button=&lang=en_GB'
            yield Request(url, callback=self.parse, meta={'Keyword': keyword, 'handle_httpstatus_all': True})

    def parse(self, response, **kwargs):
        keyword = response.meta.get('Keyword')

        # new url for get the 50 Products
        cgid = response.css('.page-next::attr("data-fullhref")').get('').split('&start=')[0]

        if cgid:
            url = f'https://www.currys.co.uk/search-update-grid?{cgid}&start=0&sz=50&viewtype=listView'
            yield Request(url, callback=self.pagination, dont_filter=True,
                              meta={'handle_httpstatus_all': True, 'Keyword': keyword})
        else:
            self.write_logs(f'Keyword:{keyword} Not Found the search Update Url value, Keyword scraping skipped.')

    def pagination(self, response):
        keyword = response.meta.get('Keyword')
        try:
            items= response.css('.page-result-count::text, .search-result-count::text').get('').strip()

            if not response.meta.get('next_page'):
                self.write_logs(f'Keyword: {keyword} Total "{items}" are found\n')

            if not items:
                self.write_logs(f'Keyword: {keyword} NO product found\n')
                return

            # Extract unique product URLs
            products_urls = list(set(response.css('.click-beacon[role="columnheader"] > a::attr(href)').getall()))
            if products_urls:
                self.total_items += len(products_urls)

            for product_url in products_urls[:2]:
                url = urljoin(self.base_url, product_url)

                #Avoiding Duplicate Records Scrape
                if url in self.scraped_urls:
                    self.duplicates_count += 1
                    self.write_logs(f'URL already scrapped, Skipped : {url} \n')
                    continue

                yield Request(url, callback=self.parse_product_detail, meta=response.meta)
        except Exception as e:
            self.write_logs(f'[PARSE] Error on listing page for keyword "{keyword}": {e}')

        # Because need first 50 Result so dont need pagination because on first page there 50 products available
        # next_page = response.css('.page-next.page-link::attr(href)').get('')
        # if next_page:
        #     response.meta['next_page'] = True
        #     yield Request(url=next_page, callback=self.pagination, meta=response.meta)

    def parse_product_detail(self, response):
        keyword = response.meta.get('Keyword', '')
        title = ''
        res = response
        url = response.url
        try:
            # Load product data from JSON-LD structured data script
            data_dict = json.loads(res.xpath('//script[@type="application/ld+json" and contains(text(), \'\"@type\":\"Product\"\')]/text()').get(''))

            discounted_price = data_dict.get('offers', {}).get('price', '')
            discounted_price = float(discounted_price) if discounted_price else 0.0
            regular_price = self.get_regular_price(res)
            promotion_disc = regular_price - discounted_price if regular_price > discounted_price else 0.0

            title = res.css('h1.product-name::text').get('').strip() or data_dict.get('name', '')
            print(response.url)
            # Create item dictionary with product details
            item = OrderedDict()
            item['retailer_id'] = 'currys_uk'
            item['retailer_name'] = 'currys_UK'
            item['retailer_country'] = 'UK'
            item['retailer_website'] = 'https://www.currys.co.uk/'
            item['product_id'] =  data_dict.get('sku', '')
            item['product_title'] = title
            item['product_description'] = self.get_desc(res, keyword, title, data_dict)
            item['promotion_type'] = data_dict.get('offers', {}).get('@type', '')
            item['promotion_description'] = None
            item['promotion_price'] = discounted_price if discounted_price else regular_price
            item['promotion_discount'] = promotion_disc
            item['promotion_start_date'] = self.get_pro_start_date(res)
            item['promotion_expiry'] = self.get_pro_exp_date(res)
            item['promotion_badge_type'] = None
            item['rich_content_displayed'] = False
            # item['rich_content_images'] = '\n'.join([img.replace('?$l-large$&fmt=auto', '') for img in data_dict.get('image', [])])
            item['rich_content_images'] = [img.replace('?$l-large$&fmt=auto', '') for img in data_dict.get('image', [])]

            iso_timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            # Convert ISO 8601 format to MySQL-compatible format
            item['timestamp'] = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")

            self.scraped_urls.append(url)
            self.post_to_api(item)

        except json.JSONDecodeError as e:
            self.write_logs(f'[PARSE_PRODUCT_DETAIL] JSON parsing error for keyword "{keyword}" - {e}')
        except Exception as e:
            self.write_logs(f'[PARSE_PRODUCT_DETAIL] Error for keyword "{keyword}" and title "{title}": {e}')

    def handle_post_response(self, response):
        """
        Handles successful POST request responses.
        """
        try:
            # Parse JSON response
            response_data = response.json()
            self.write_logs(f'[POST_TO_API] Successfully uploaded data. Response: {response_data}')
        except Exception as e:
            self.write_logs(f'[POST_TO_API] Error parsing response: {e}')

    def handle_post_error(self, failure):
        """
        Handles errors during the POST request.
        """
        self.write_logs(f'[POST_TO_API] Error occurred: {failure.value}')

    def get_search_keywords_from_file(self):
        return self.get_input_from_txt(glob.glob('input/curry_search_keywords.txt')[0])

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

    def get_product_specifications(self, response, keyword, title):
        try:
            # Initialize spec to collect all specifications as a formatted string
            spec = ''

            # Extract and add the main title of the product specifications
            main_title = ''.join(response.css('#tab2 .productSheet > h3 ::text').getall()).strip()
            spec += main_title + '\n\n'

            # Select all specification sections
            specs_sections = response.css('.tech-specification-table')

            # Loop through each section to process its title and details
            for section in specs_sections:
                section_content  = ''

                # Extract and add the title of each specification section
                section_title = section.css('h3::text').get('')
                section_content  += section_title + '\n'

                # Process each row in the section to extract heading and value
                rows = section.css('.tech-specification-body')
                for row in rows:
                    heading = row.css('.tech-specification-th::text').get('')
                    value = ''.join([text.strip() for text in row.css('.tech-specification-td ::text').getall()])

                    # Format the row as 'Heading: Value'
                    section_content  += f'{heading}: {value}\n'

                # Add the section content to the main spec with a separator
                spec += section_content + '\n'

            return spec
        except Exception as e:
            self.write_logs(f'[GET_PRODUCT_SPECIFICATIONS] Error for keyword "{keyword}" and title "{title}": {e}')
            return ''

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def write_csv(self, record):
        """Write a single record to the CSV file."""
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # output_file = f'{output_dir}/Currys Products Details {self.current_dt}.csv' # csv
        output_file = f'{output_dir}/Currys Products Details {self.current_dt}.json'

        try:
            # Check if file exists
            file_exists = os.path.exists(output_file)

            # Open the JSON file in append mode or create it if it doesn't exist
            with open(output_file, 'a' if file_exists else 'w', encoding='utf-8') as json_file:
                # If the file is new, write an opening bracket for the JSON array
                if not file_exists:
                    json_file.write('[')

                # If the file is not empty, add a comma to separate the records
                if file_exists and json_file.tell() > 1:
                    json_file.write(',\n')

                # Write the record as a JSON object (without a comma if it's the last record)
                json.dump(record, json_file, ensure_ascii=False, indent=4)

                # If the record is the last one, add a closing bracket to the JSON array
                if file_exists and json_file.tell() > 1:
                    json_file.write('\n]')
                else:
                    json_file.write('\n]')

                self.items_scrapped += 1
                print('Items ae Scrapped: ', self.items_scrapped)

            print(f"Record for '{record.get('product_title', '')}' written to CSV successfully.")
        except Exception as e:
            self.write_logs(f"Title: {record.get('product_title', '')} Url:{record.get('URL', '')} Error writing to the CSV file: {e}")

    def post_to_api(self, item):
        """
        Sends a POST request to the API with the item data.
        """
        try:
            # Convert item to JSON
            response = requests.post(self.api_url, json=item, headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                self.items_scrapped += 1
                print('Items ae Scrapped: ', self.items_scrapped)
                self.write_logs(f'[POST_TO_API] Successfully uploaded data for product ID {item.get("product_id")}. Response: {response.json()}')
            else:
                self.write_logs(f'[POST_TO_API] Failed to upload data for product ID {item.get("product_id", "")}. '
                                f'Status Code: {response.status_code}, Response: {response.text}')

        except requests.exceptions.RequestException as e:
            self.write_logs(f'[POST_TO_API] Request error while uploading data for product ID {item.get("product_id", "")}: {e}')
        except Exception as e:
            self.write_logs(f'[POST_TO_API] Unexpected error: {e}')

    def get_desc(self, res, keyword, title, data_dict):
        spec_list = []
        description = data_dict.get('description', '')
        if description:
            spec_list.append('Description\n')
            spec_list.append(description)

        features = '\n'.join(
            [item.strip() for item in res.css('.key-features-desktop-tab .item-title ::text').getall()])
        if features:
            spec_list.append('\n\nFeatures\n')
            spec_list.append(features)

        specification = self.get_product_specifications(res, keyword, title)
        if specification:
            spec_list.append('\n\nSpecification\n')
            spec_list.append(specification)

        return ''.join(spec_list) if spec_list else ''

    def get_regular_price(self, response):
        price_text = response.css('.price-date ::text').get('')
        if price_text:
            # Use regex to extract digits
            match = re.search(r'\d[\d,]*\.?\d*', price_text)
            if match:
                # Convert to float after removing commas
                price = float(match.group(0).replace(',', ''))
            else:
                price = 0.0  # If regex fails, fallback to 0.0
        else:
            price = 0.0  # If no price is found, return 0.0

        return price

    def get_pro_start_date(self, response):
        text = response.css('.row product-price.credit-offer-price .price-date ::text').get('')
        if text:
            text = ''.join(text.split('(')[1:])
            start_date = ''.join(text.split('to')[0:1]).replace('from', '').strip()
        else:
            start_date = ''

        return start_date

    def get_pro_exp_date(self, response):
        text = response.css('.row product-price.credit-offer-price .price-date ::text').get('')
        if text:
            text = ''.join(text.split('(')[1:])
            exp_date = ''.join(text.split('to')[1:]).replace(')', '').strip()
        else:
            exp_date = ''

        return exp_date

    def close(spider, reason):
        spider.write_logs(f'Spider Started at:{spider.script_starting_datetime}')
        spider.write_logs(f'Spider Stopped at:{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}')

        spider.write_logs(f'Total Items Found:{spider.total_items}')
        spider.write_logs(f'Total Items Scraped:{spider.items_scrapped}')
        spider.write_logs(f'Total Duplicate Items Found:{spider.duplicates_count}')

