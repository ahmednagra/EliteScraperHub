import os
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Request, signals, Spider


class FarmersRecordsSpider(Spider):
    name = "farmers_records"
    start_urls = ["http://20.198.83.63:9090/dashboard/"]
    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        # 'DOWNLOAD_DELAY': 2,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'DOWNLOAD_FAIL_ON_DATALOSS': False,  # Handle incomplete responses
        'DOWNLOAD_TIMEOUT': 600,  # Adjust the value as needed (in seconds)

        'FEEDS': {
            f'Output/Jeevik Farmer Records {current_dt}.csv': {
                'format': 'csv',
                # 'fields': ['Sr. no', 'DISTRICT NAME', 'BLOCK NAME', 'FY', 'Village Name', 'VO', 'SHG',
                #            'Farmer Name', 'Farmer ID', 'Husband Name', 'Crop Name', 'Area Cultivation']
                'fields': ''
            }
        }
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.years_options = []
        self.years_options_count = 0
        self.current_items_scraped_count = 0

        self.logs_filename = f'logs/logs {self.current_dt}.txt'
        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            years = response.css('#year-selector option::attr(value)').getall()[1:]
            self.years_options.extend(years)

            self.years_options_count = len(self.years_options)

        except Exception as e:
            self.error.append(f'Error occurred while parse function: {str(e)}')

    def parse_state(self, response):
        try:
            district_urls = response.css('table tr a::attr(href)').getall()

            for district_url in district_urls:
                url = urljoin(response.url, district_url)
                self.logger.info('district_url Called : %s', url)
                district_name = url.split('=')[-1]
                yield Request(url=url, callback=self.parse_district, headers=self.headers,
                              meta={'district_name': district_name})
        except Exception as e:
            self.error.append(f'Error occurred while parsing state: {str(e)}')

    def parse_district(self, response):
        # No Former Record in the Block:
        urls = [element.css('a::attr(href)').get() for element in response.css('a[href*="techReportEnggFarmer.html"]')
                if element.css('::text').get('') == '0']
        for url in urls:
            district_name = response.meta.get('district_name', '')
            sub_district_name = url.split('blockName=')[1:2][0].split('&')[0:1][0]
            self.mandatory_logs.append(
                f"District {district_name} , Sub District Name: {sub_district_name} Has Total Records : 0")

        try:
            # Has FARMER RECORDS IN THE BLOCK
            blocks_urls = [element.css('a::attr(href)').get() for element in
                           response.css('a[href*="techReportEnggFarmer.html"]') if element.css('::text').get('') != '0']

            for block_url in blocks_urls:
                url = urljoin(response.url, block_url)
                print('block_url Called : %s', url)
                yield Request(url=url, callback=self.parse_sub_district, headers=self.headers)
                # sleep(2)
        except Exception as e:
            self.error.append(f'Error occurred while parsing district: {str(e)}')

    def update_custom_settings_fields(self, new_fields):
        try:
            self.custom_settings['FEEDS'][f'Output/Jeevik Farmer Records {self.current_dt}.csv']['fields'] = new_fields
        except Exception as e:
            self.error.append(f'Error occurred while updating custom settings: {str(e)}')

    def parse_sub_district(self, response):
        header_row = response.css('table tr[valign="top"]:contains("Farmer Name")')
        if header_row:
            header_row = header_row[0]
        else:
            return
        header_columns = [header.strip() for header in header_row.css('span::text').getall()]

        table_rows = response.css('table tr[valign="top"]')[3:-1]
        all_rows = []
        for row in table_rows:
            row_values = [value.replace('Â', '') for value in row.css('span::text').extract()]
            if row_values:
                all_rows.append(row_values)

        zipped_rows = [dict(zip(header_columns, row)) for row in all_rows]

        for zipped_row in zipped_rows:
            # Update field names in custom_settings
            self.update_custom_settings_fields(header_columns)
            try:
                item = OrderedDict()
                for field_name in header_columns:

                    # Set item field names dynamically
                    item[field_name] = zipped_row.get(field_name, '')

                self.current_items_scraped_count += 1
                print('current_items_scraped_count :', self.current_items_scraped_count)
                yield item
            except Exception as e:
                self.error.append(f'Error Yield item : {response.url} error: {e}')

    def closed(self, reason):
        try:
            # Write error logs to file
            with open('logs/error_logs.txt', 'a') as log_file:
                log_file.write('\n'.join(self.error))
            self.logger.info('Error logs written to file.')

            # Write mandatory logs to file
            with open(f'logs/logs_{self.current_dt}.txt', 'a') as log_file:
                log_file.write('\n'.join(self.mandatory_logs))
            self.logger.info('Mandatory logs written to file.')
        except Exception as e:
            self.error.append(f'Error occurred while closing spider: {str(e)}')

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def close(spider, reason):
        spider.mandatory_logs.append(
            f'\nSpider "{spider.name}" was started at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"\n\n')
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" Scraped Total Products "{spider.current_items_scraped_count}"')

        spider.mandatory_logs.append(f'\n\nSpider Error:: \n')
        spider.mandatory_logs.extend(spider.error)

        spider.write_logs()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FarmersRecordsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next Year if available.
        """

        print(f'\n\n{len(self.years_options)}/{self.years_options_count} Categories left to Scrape\n\n')

        if self.years_options:
            year_option = self.years_options.pop(0)
            url = f'http://20.198.83.63:9090/dashboard/reports/farmer/farmermasterdistrict.html?fy={year_option}'
            self.logger.info('Year Called : %s', url)

            req = Request(url=url,
                          callback=self.parse_state, headers=self.headers,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
