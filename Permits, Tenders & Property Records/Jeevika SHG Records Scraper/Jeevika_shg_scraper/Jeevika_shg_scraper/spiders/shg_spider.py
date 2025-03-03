import os
from datetime import datetime
from collections import OrderedDict

from scrapy import Request, signals, Spider


class SHGRecordsSpider(Spider):
    name = "SHG_records"
    base_url = 'http://20.198.83.63:9090'
    start_urls = [
        "http://20.198.83.63:9090/dashboard/reports/getAllCountDefaultMember/totalCountDefaultMember.html"]  # JEEVIKA DASHBOARD Url
    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        # 'DOWNLOAD_DELAY': 2,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'DOWNLOAD_FAIL_ON_DATALOSS': False,  # Handle incomplete responses
        'DOWNLOAD_TIMEOUT': 6000,  # Adjust the value as needed (in seconds)
        'DOWNLOAD_WARNSIZE': 0,

        'FEEDS': {
            f'Output/Jeevik Farmer Records {current_dt}.csv': {
                'format': 'csv',
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
        self.current_items_scraped_count = 0
        self.district_options = []
        self.district_options_count = 0

        # logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        try:
            shg_formed_url = ''.join(
                [url for url in response.css('a::attr(href)').getall() if 'cbomappingforshg' in url][0:1])
            if shg_formed_url:
                shg_formed_url = f'{self.base_url}{shg_formed_url}'
                yield Request(url=shg_formed_url, headers=self.headers, callback=self.parse_shg)
        except Exception as e:
            self.write_logs(f'Error occurred while parse function: {str(e)}')

    def parse_shg(self, response):
        try:
            district_selectors = response.css('table tr[valign]')[3:]
            required_district = ['bhojpur', 'gaya', 'begusarai', 'purnia', 'jamui']

            for district in district_selectors:
                district_name = district.css('td:nth-child(2) a span::text').get('').strip()

                if district_name.lower() in required_district:
                    # district_url = district.css('td:nth-child(2) a::attr(href)').get('')
                    shg_url = district.css('td:nth-child(4) a::attr(href)').get('')
                    shg_url = f'{self.base_url}{shg_url}'
                    self.district_options.append({
                        'district_name': district_name,
                        'shg_url': shg_url
                    })

            self.district_options_count = len(self.district_options)

        except Exception as e:
            self.write_logs(f'Error occurred while parsing state: {str(e)}')

    def parse_district(self, response):
        district_name = response.meta.get('district_name', '')
        header_row = response.css('table tr[valign="top"]:contains("Serial No:")')
        if header_row:
            header_row = header_row[0]
            header_columns = [header.strip() for header in header_row.css('span::text').getall()]
        else:
            header_columns = [header.strip() for header in
                              response.css('table tr[valign="top"]:nth-child(4) td span::text').getall()]

        # Check if headers are found, if not log an error and return
        if not header_columns:
            self.write_logs('No headers Found')
            return

        # Include 'District Name' in the header columns
        header_columns.insert(0, 'District Name')

        table_rows = response.css('a[name="JR_PAGE_ANCHOR_0_1"] + table tr')[4:-1]
        all_rows = []
        for row in table_rows:
            row_values = [value.replace(')', '').strip() for value in row.css('span::text').extract()]
            if row_values:
                # Insert district name as the first value in each row
                row_values.insert(0, district_name)
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
                self.write_logs(f'Error occurred while parsing district: {str(e)}')

    def update_custom_settings_fields(self, new_fields):
        try:
            self.custom_settings['FEEDS'][f'Output/Jeevik Farmer Records {self.current_dt}.csv']['fields'] = new_fields
        except Exception as e:
            self.write_logs(f'Error occurred while updating custom settings: {str(e)}')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SHGRecordsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling Districts if available.
        """

        print(f'\n\n{len(self.district_options)}/{self.district_options_count} Districts left to Scrape\n\n')

        if self.district_options:
            district = self.district_options.pop(0)
            url = district.get('shg_url', '')
            name = district.get('district_name', '')

            req = Request(url=url,
                          callback=self.parse_district, headers=self.headers,
                          meta={'handle_httpstatus_all': True, 'district_name': name})

            # test
            self.district_options = []

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)
