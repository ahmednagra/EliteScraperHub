import csv
import os
import ssl
import time
import urllib.parse
from collections import OrderedDict
from datetime import datetime, timedelta

import requests
from scrapy import Spider, Request, Selector, signals
from scrapy.exceptions import CloseSpider

ssl._create_default_https_context = ssl._create_unverified_context

from .merger_data import main


class CobbCountySpider(Spider):
    name = "permits"
    base_url = 'https://cobbca.cobbcounty.org/'
    start_urls = ["https://cobbca.cobbcounty.org/CitizenAccess/Login.aspx"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    request_headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://cobbca.cobbcounty.org',
        'priority': 'u=1, i',
        'referer': 'https://cobbca.cobbcounty.org/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building&TabList=HOME%7C0%7CEnforce%7C1%7CDOT%7C2%7CBuilding%7C3%7CLicenses%7C4%7CPermits%7C5%7CPlanning%7C6%7CCurrentTabIndex%7C3',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'x-microsoftajax': 'Delta=true',
        'x-requested-with': 'XMLHttpRequest',
    }

    def __init__(self):
        super().__init__()
        self.cookies = {}

        self.total_items_scraped_count = 0
        self.current_month_permits_scraped_count = 0
        self.current_month_building_permits_skipped_count = 0

        self.skipped_permits_filepath = ''
        self.scraped_permits_filepath = ''

        self.skipped_permits_fieldnames = ['Date', 'Building Number', 'Project Name', 'Address', 'Status', 'Url']

        self.scraped_permits_fieldnames = ['Date', 'Building Number', 'Project Name', 'Address', 'Type', 'Status',
                                           'Work Location', 'Licensed Person Name',
                                           'Licensed Person E-Mail', 'Licensed Person Company',
                                           'Licensed Person Phone No', 'Licensed Person Address', 'Project Description',
                                           'Owner Name', 'Owner Address', 'Additional Information',
                                           'Parcel Information', 'Application Information', 'Url']

        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')
        self.login_failed = False

        # scraped data onward 2004 years till 2024
        years_scraped = [1999, 2000, 2001, 2002, 2003, 2004]

        self.current_searching_year = None

        self.monthly_date_filters = self.get_monthly_search_combinations()
        self.monthly_date_filters = [row for row in self.monthly_date_filters if row.get('year') not in years_scraped]
        self.current_searching_month_dates = {}
        self.current_searching_month_name = ''

        self.month_wise_seen_building_urls = []
        self.month_wise_duplicates_count = 0

        self.session = None
        self.building_permit_url = 'https://cobbca.cobbcounty.org/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building&TabList=HOME%7C0%7CEnforce%7C1%7CDOT%7C2%7CBuilding%7C3%7CLicenses%7C4%7CPermits%7C5%7CPlanning%7C6%7CCurrentTabIndex%7C3'

    def start_requests(self):
        yield Request(url='https://quotes.toscrape.com/', meta={'handle_httpstatus_all': True})

    def parse(self, response, **kwargs):
        self.month_wise_seen_building_urls = []
        self.current_month_permits_scraped_count = 0
        self.current_month_building_permits_skipped_count = 0

        self.current_searching_month_dates = self.monthly_date_filters.pop(0)

        self.current_searching_year = self.current_searching_month_dates.get('year')
        month = self.current_searching_month_dates.get('month')
        self.current_searching_month_name = f'{month}_{self.current_searching_year}'

        # Create output directories
        non_hvac_items_folder = f'output/Non HVAC Permits/{self.current_searching_year}'
        hvac_items_folder = f'output/Permits Details/{self.current_searching_year}'

        os.makedirs(non_hvac_items_folder, exist_ok=True)
        os.makedirs(hvac_items_folder, exist_ok=True)

        self.skipped_permits_filepath = f'{non_hvac_items_folder}/{self.current_searching_month_name}.csv'
        self.scraped_permits_filepath = f'{hvac_items_folder}/{self.current_searching_month_name}.csv'

        # User Login
        logged_in = self.do_user_login()
        if not logged_in:
            self.login_failed = True
            self.write_logs('Login Failed')

            return

        self.write_logs('Login Successful!')

        self.write_logs(f'\nStart Searching and Scraping Month: {self.current_searching_month_name}\n\n')

        # Make a request to the Building Permit using the session just to refresh and update the cookies
        building_permit_res = self.session.get(self.building_permit_url, timeout=100)

        if building_permit_res.status_code != 200:
            self.write_logs('Failed to redirect Building Permit Page after Login')
            raise CloseSpider('Failed to redirect Building Permit Page after Login')

        self.session.cookies.update(building_permit_res.cookies.get_dict())
        html_selector = Selector(text=building_permit_res.content)

        self.session.headers.update(self.request_headers)

        # Page indexing starts from "2". 02 is the first page, 03 is the 2nd and so on...
        page_num = 2

        form_data = self.get_request_formdata(html_selector=html_selector)

        while True:

            self.write_logs(f'\nRequesting Page "{page_num - 1}" Data for Year "{self.current_searching_month_name}"')

            try:
                post_response = self.session.post(self.building_permit_url, data=form_data,
                                                  headers=self.request_headers, timeout=100)
            except requests.exceptions.ConnectionError as e:
                time.sleep(10)
                continue

            self.write_logs(
                f'Got "{post_response.status_code}" response for page "{page_num - 1}" for Month "{self.current_searching_month_name}"')

            if post_response.status_code != 200:
                self.write_logs(
                    f'More Pages scraping stopped. Due to non 200 response for Month "{self.current_searching_month_name}"')
                break

            self.session.cookies.update(post_response.cookies.get_dict())

            # add condition the response has appropriate results
            html_selector = Selector(text=post_response.text)
            building_permits = html_selector.css('.ACA_TabRow_Even_FontSize, .ACA_TabRow_Odd_FontSize')

            self.parse_listings(building_permits, page_num)

            ###################################################
            # #         HANDLE NEXT PAGE REQUEST            # #
            ###################################################

            page_num += 1
            # print(f"Page request : {next_page_num - 2}")

            next_page_url = html_selector.css('.aca_pagination_td + .aca_pagination_PrevNext a::attr(href)').re_first(
                r"PostBack\(\'(.*)\',")

            form_data = self.get_request_formdata(html_selector, page_url=next_page_url)

            if not next_page_url:  # Skip next pages requests if next page is not there
                self.write_logs(
                    f'No more building permits Pages found for year {self.current_searching_year}, stopping at Page: {page_num - 1}')
                break

    def parse_listings(self, building_permits_rows, page_num):
        current_page_num = page_num or 2  # Page num of response request. Default is 2 as first page

        for permit_row in building_permits_rows:
            url = permit_row.css('[id*="PermitNumber"] ::attr(href)').get('')

            if not url:
                print('Project URL not found')
                continue

            url = f"https://cobbca.cobbcounty.org{url}" if url else url
            project_name = permit_row.css('[id*="lblProjectName"]::text').get('') or ''

            partial_item = dict()  # fields on listing page
            partial_item['Date'] = permit_row.css('[id*="lblUpdatedTime"]::text').get('')
            partial_item['Building Number'] = permit_row.css('a [id*="lblPermitNumber1"] ::text').get('')
            partial_item['Project Name'] = project_name
            partial_item['Address'] = permit_row.css('[id*="lblAddress"]::text').get('')
            partial_item['Status'] = permit_row.css('[id*="lblStatus"]::text').get('')
            partial_item['Url'] = url

            if url in self.month_wise_seen_building_urls:
                self.month_wise_duplicates_count += 1
                print(f'Duplicate row found. Total Duplicates: {self.month_wise_duplicates_count}')

            self.month_wise_seen_building_urls.append(url)

            print(f'Project Name: {project_name}')

            # Check if 'HVAC' is in the project name
            if 'hvac' not in project_name.lower():
                # self.write_logs(f'Project Name "{project_name}" skipped as HVAC not exists in the name')
                print(f'Project Name "{project_name}" skipped as "HVAC" not exists in the name')
                self.write_non_hvac_items_into_csv(partial_item)
                continue

            try:
                self.parse_permit_details(partial_item)

            except Exception as e:
                self.write_logs(
                    f"Error processing Details Page Request for URL: '{url}'. \nError: {e}")

    def parse_permit_details(self, partial_item):
        permit_url = partial_item.get('Url')

        retries_counter = 0
        details_response = None

        while retries_counter < 5:
            try:
                details_response = self.session.get(permit_url, timeout=100)
                break
            except requests.exceptions.ConnectionError:
                retries_counter += 1
                details_response = None
                time.sleep(5)
                continue

        if not details_response:
            self.write_non_hvac_items_into_csv(partial_item)
            self.write_logs(
                f'\n\nDetails page request failed after {retries_counter} times Retrying. Item inserted into Non HVAC file: "{self.skipped_permits_filepath}"\n\n')
            return

        response = Selector(text=details_response.text)

        permit_id = response.css('[id*="PermitNumber"]::text').get('')
        try:
            project_desc = response.xpath(
                '//span[contains(text(), "Project Description:")]/ancestor::div[1]//span[not(contains(text(), "Project Description:"))]//text()').getall()

            item = OrderedDict()
            item.update(partial_item)
            item['Building Number'] = permit_id
            item['Type'] = response.css('[id*="PermitType"]::text').get('')
            item['Status'] = response.css('span#ctl00_PlaceHolderMain_lblRecordStatus ::text').get(
                '') or partial_item.get('Status')
            item['Work Location'] = response.css('#tbl_worklocation ::text').get('')
            item.update(self.get_license_information(response))
            item['Project Description'] = '\n'.join([line.strip() for line in project_desc if line.strip()])
            item.update(self.get_owner_info(response))
            item['Additional Information'] = ' '.join(
                [text.strip() for text in response.css('#trADIList ::text').getall() if text.strip()])
            item['Parcel Information'] = self.get_parcel_info(response)
            item['Application Information'] = self.get_application_info(response)

            self.current_month_permits_scraped_count += 1
            self.total_items_scraped_count += 1

            self.write_item_into_csv(file_path=self.scraped_permits_filepath, item=item)
            print(
                f"\n\nBuilding Permits Scraped Count for Month {self.current_searching_month_name}: {self.current_month_permits_scraped_count}")
            print(f"All Total items Scraped Count: {self.total_items_scraped_count}\n\n")

            print(item)

        except Exception as e:
            log_msg = f'Error in Getting Details for permit ID "{permit_id}". \nError: {e}'
            self.write_logs(log_msg)

    def write_non_hvac_items_into_csv(self, item):
        self.current_month_building_permits_skipped_count += 1
        self.write_item_into_csv(file_path=self.skipped_permits_filepath, item=item)
        print(
            f"Non HVAC Items Skipped Count for Month {self.current_searching_month_name}: {self.current_month_building_permits_skipped_count}\n")

    def get_request_formdata(self, html_selector, page_url=None):
        is_first_page_request = True if not page_url else False

        viewstate = self.get_element_value(html_selector, element_name='__VIEWSTATE')
        if not viewstate:
            a = 0

        # start_date = f"06/01/2005"
        # end_date = f"06/30/2005"

        start_date = self.current_searching_month_dates.get('start_date')
        end_date = self.current_searching_month_dates.get('end_date')

        next_page_event = f"ctl00$PlaceHolderMain$dgvPermitList$gdvPermitList$ctl13$ctl2" if is_first_page_request else page_url

        data = {
            "ctl00$ScriptManager1": 'ctl00$PlaceHolderMain$updatePanel|ctl00$PlaceHolderMain$btnNewSearch' if is_first_page_request else f'ctl00$PlaceHolderMain$dgvPermitList$updatePanel|{next_page_event}',
            "ctl00$HeaderNavigation$hdnShoppingCartItemNumber": "",
            "ctl00$HeaderNavigation$hdnShowReportLink": "N",
            "ctl00$PlaceHolderMain$addForMyPermits$collection": "rdoNewCollection",
            "ctl00$PlaceHolderMain$addForMyPermits$txtName": "name",
            "ctl00$PlaceHolderMain$addForMyPermits$txtDesc": "",
            "ctl00$PlaceHolderMain$PermitList$lblNeedReBind": "",
            "ctl00$PlaceHolderMain$PermitList$gdvPermitList$hfSaveSelectedItems": "",
            "ctl00$PlaceHolderMain$PermitList$inpHideResumeConf": "",
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSPermitNumber": "",
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate": start_date,
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSStartDate_ext_ClientState": "",
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSEndDate": end_date,
            "ctl00$PlaceHolderMain$generalSearchForm$txtGSEndDate_ext_ClientState": "",
            "ctl00$PlaceHolderMain$hfASIExpanded": "",
            "ctl00$PlaceHolderMain$txtHiddenDate": "",
            "ctl00$PlaceHolderMain$txtHiddenDate_ext_ClientState": "",
            "ctl00$PlaceHolderMain$hfGridId": "",
            "ctl00$HDExpressionParam": "",
            "Submit": "Submit",
            "__EVENTTARGET": 'ctl00$PlaceHolderMain$btnNewSearch' if is_first_page_request else next_page_event,
            "__EVENTARGUMENT": self.get_element_value(html_selector, element_name='__EVENTARGUMENT'),
            "__VIEWSTATE": self.get_element_value(html_selector, element_name='__VIEWSTATE'),
            "__VIEWSTATEGENERATOR": self.get_element_value(html_selector, element_name='__VIEWSTATEGENERATOR'),
            "__VIEWSTATEENCRYPTED": "",
            "ACA_CS_FIELD": self.get_element_value(html_selector, element_name='ACA_CS_FIELD'),
            "__AjaxControlToolkitCalendarCssLoaded": "",
            "__ASYNCPOST": "true"
        }

        formdata = urllib.parse.urlencode(data)
        return formdata

    def get_parcel_info(self, html_selector):
        table_rows = html_selector.css('#trParcelList tr')
        info = []
        for row in table_rows:
            text = ' '.join([text.strip() for text in row.css('::text').getall() if text.strip()])
            info.append(text)

        return '\n'.join(info)

    def get_element_value(self, response, element_name):
        # Element name could be the ID of the element. For example: __VIEWSTATE

        value = response.css(f'#{element_name}::attr(value)').get('') or \
                response.css(f'body:contains("|{element_name}|")::text').re_first(r'hiddenField\|__VIEWSTATE\|(.*)\|',
                                                                                  '').split('|')[0]

        if not value:
            a = 0

        return value

    def do_user_login(self):
        if not self.get_login_request_formdata():
            self.write_logs('Login Credentials Not found. Scraper closed')
            # return False
            raise CloseSpider('Credentials Not found')

        login_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://cobbca.cobbcounty.org',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        self.session = requests.Session()

        retries_counter = 0
        login_response = None

        # Retry failed requests
        while retries_counter < 5:
            try:
                login_response = self.session.post('https://cobbca.cobbcounty.org/CitizenAccess/api/PublicUser/SignIn',
                                                   cookies=self.cookies,
                                                   headers=login_headers,
                                                   json=self.get_login_request_formdata(),
                                                   timeout=100)

                break
            except requests.exceptions.ConnectionError as e:
                retries_counter += 1
                self.write_logs(f'Retying login request for {retries_counter} Times.')
                login_response = None
                time.sleep(5)
                continue
        try:
            if login_response.status_code == 200 and login_response.json().get('type') == 'success':
                # print("Login successful")
                self.session.cookies.update(login_response.cookies.get_dict())
                return login_response
            else:
                self.write_logs('Login request failed')
                # return False
                raise CloseSpider('Login request failed')
        except:
            raise CloseSpider('Login request failed')

    def get_license_information(self, response):
        license_info = [text.strip() for text in response.css("#tbl_licensedps ::text").getall() if text.strip()]
        mail_text_string = [text.strip() for text in license_info if '@' in text]

        licensed_email = ' '.join([word for word in ''.join(mail_text_string).split() if '@' in word])
        licensed_name = ' '.join([word for word in ''.join(mail_text_string).split() if '@' not in word]) or ''.join(
            license_info[0:1])
        licensed_company = next(
            (license_info[i + 1] for i, text in enumerate(license_info) if '@' in text and i + 1 < len(license_info)),
            None) or ''.join(license_info[1:2])
        licensed_phone = next((license_info[i + 1] for i, text in enumerate(license_info) if
                               'phone' in text.lower() and i + 1 < len(license_info)), None)

        # Extract the address by excluding already fetched items
        address_parts = []
        for text in license_info:
            if text not in {licensed_email, licensed_name, licensed_company, licensed_phone}:
                if 'phone' in text.lower() or '@' in text.lower():
                    continue
                address_parts.append(text)

        licensed_address = ' '.join(address_parts)

        license_info_item = dict()

        license_info_item['Licensed Person Name'] = licensed_name
        license_info_item['Licensed Person E-Mail'] = licensed_email
        license_info_item['Licensed Person Company'] = licensed_company
        license_info_item['Licensed Person Phone No'] = licensed_phone
        license_info_item['Licensed Person Address'] = licensed_address

        return license_info_item

    def get_owner_info(self, response):
        owner_desc = response.xpath(
            '//span[contains(text(), "Owner:")]/ancestor::div[1]//span[not(contains(text(), "Owner:"))]//text()').getall()
        owner_info_text = [line.strip() for line in owner_desc if line.strip()]

        owner_info_item = dict()
        owner_info_item['Owner Name'] = ''.join(''.join(owner_info_text).split('*')[0:1])
        owner_info_item['Owner Address'] = ''.join(''.join(owner_info_text).split('*')[1:])

        return owner_info_item

    def get_application_info(self, response):
        table_rows = response.css('#trASIList .ACA_TabRow ')
        info = []
        for row in table_rows:
            text = ' '.join([text.strip() for text in row.css('::text').getall() if text.strip()])
            info.append(text)

        return '\n'.join(info)

    def get_login_creds_from_file(self):
        file_path = 'input/login.txt'
        data = {}

        with open(file_path, mode='r', encoding='utf-8-sig') as text_file:
            for line in text_file:
                key, value = line.strip().split('==', maxsplit=1)
                data[key.strip()] = value.strip()

        return data

    def write_item_into_csv(self, file_path, item):
        fieldnames = self.skipped_permits_fieldnames if 'Non HVAC' in file_path else self.scraped_permits_fieldnames

        try:
            with open(file_path, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                # Write Columns Headers Row if file is empty
                if csv_file.tell() == 0:
                    writer.writeheader()

                # Prepare item-row with default values for missing fields
                row_to_write = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row_to_write)

        except Exception as e:
            self.write_logs(f'Error in writing item to csv file. Error : {e}')

    def get_login_request_formdata(self):
        login_creds = self.get_login_creds_from_file()
        name = login_creds.get('email', '')
        password = login_creds.get('password', '')

        if not name or not password:
            self.write_logs(f"Kindly add the user login credentials in the 'input/login.txt' file")
            return ''

        login_json_data = {
            'headers': {
                'normalizedNames': {},
                'lazyUpdate': None,
                'headers': {},
            },
            'body': {
                # 'Name': 'shahmuhammad.gulzarsoft@gmail.com',
                'Name': name,
                # 'Pwd': 'abcd_1234',
                'Pwd': password,
                'IsRemember': 1,
            },
        }

        return login_json_data

    def get_monthly_search_combinations(self):
        # List of years from 2007 to 2024
        years = list(range(2005, 2024 + 1))

        # Function to get the end date of a month
        def get_month_end_date(year, month):
            if month == 12:
                return datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                return datetime(year, month + 1, 1) - timedelta(days=1)

        # Create combinations of years and months in a list of dictionaries
        year_month_combinations = []

        for year in years:
            for month in range(1, 13):
                month_start_date = datetime(year, month, 1).strftime("%m-%d-%Y")
                month_end_date = get_month_end_date(year, month).strftime("%m-%d-%Y")

                year_month_combinations.append({
                    'year': year,
                    'month': month,
                    'start_date': month_start_date,
                    'end_date': month_end_date
                })

        return year_month_combinations

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CobbCountySpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.current_searching_month_dates:
            self.write_logs(
                f'\nTotal "HVAC" items Scraped for Month "{self.current_searching_month_name}": {self.current_month_permits_scraped_count}')
            self.write_logs(
                f'Total "Non HVAC" items skipped for Month "{self.current_searching_month_name}": {self.current_month_building_permits_skipped_count}')

        self.current_month_permits_scraped_count = 0
        self.current_month_building_permits_skipped_count = 0

        self.write_logs('\n\n')
        self.write_logs('#' * 60)
        self.write_logs(f'\n\nSearch Combinations Left to Search: {len(self.monthly_date_filters)}')

        if self.login_failed:
            raise CloseSpider('Login Failed')

        if not self.monthly_date_filters:
            return

        req = Request(url='http://books.toscrape.com/',
                      callback=self.parse,
                      dont_filter=True,
                      meta={'handle_httpstatus_all': True})

        try:
            self.crawler.engine.crawl(req)  # For latest Python version
        except TypeError:
            self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        spider.write_logs(f'\nOverall Total Items Scraped Count: {spider.total_items_scraped_count}')
        spider.write_logs(f'\nLast Month Searched: {spider.current_searching_month_name}')
        spider.write_logs(f'\n\nScraper was started at "{spider.script_starting_datetime}"')
        spider.write_logs(f'Scraper closed at "{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}"\n\n')

        # call the merge data script
        main()
