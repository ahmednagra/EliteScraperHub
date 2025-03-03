import csv
import glob
import os
import re
from time import sleep
from datetime import datetime
from collections import OrderedDict

import requests
from scrapy import Spider, Request, Selector, signals
from scrapy.exceptions import CloseSpider
from user_agent import generate_user_agent


class GobbcountySpiderSpider(Spider):
    name = "building_permits"
    start_urls = ["https://cobbca.cobbcounty.org/CitizenAccess/Login.aspx"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_user_agent = generate_user_agent(os='win', navigator='chrome', platform=None, device_type='desktop')

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    search_headers = {
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://cobbca.cobbcounty.org',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://cobbca.cobbcounty.org/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building&TabList=HOME%7C0%7CEnforce%7C1%7CDOT%7C2%7CBuilding%7C3%7CLicenses%7C4%7CPermits%7C5%7CPlanning%7C6%7CCurrentTabIndex%7C3',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': custom_user_agent,
        'x-microsoftajax': 'Delta=true',
        'x-requested-with': 'XMLHttpRequest',
    }

    login_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://cobbca.cobbcounty.org',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    def __init__(self):
        super().__init__()
        self.cookies = {}
        self.headers = {}

        self.all_items_counter = 0

        self.current_year_scraped_permits_list = []
        self.current_year_scraped_permits_count = 0
        self.current_scraped_permit_urls = []

        self.skipped_building_permits_list = []
        self.skipped_building_permits_count = 0

        self.skipped_permits_filepath = f'output/GobbCounty Skipped building permits records {self.current_dt}.csv'
        self.scraped_permits_filepath = f'output/GobbCounty Building Permits Records {self.current_dt}.csv'

        self.skipped_permits_fieldnames = ['Date', 'Building Number', 'Project Name', 'Address', 'Status', 'Url']
        self.scraped_permits_fieldnames = ['Permit No', 'Type', 'Status', 'Work Location', 'Licensed Person Name',
                                           'Licensed Person E-Mail', 'Licensed Person Company',
                                           'Licensed Person Phone No', 'Licensed Person Address', 'Project Description',
                                           'Owner Name', 'Owner Address', 'Additional Information',
                                           'Parcel Information', 'Application Information', 'Url']

        self.user_creds = self.read_user_cred_from_input_file()

        self.error = []
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

        # self.year_filter = [1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
        self.year_filter = [2006]
        self.session = requests.Session()
        self.aca_cs_field = ''
        self.viewstate_id = ''
        self.building_permit_url = 'https://cobbca.cobbcounty.org/CitizenAccess/Cap/CapHome.aspx?module=Building&TabName=Building&TabList=HOME|0|Enforce|1|DOT|2|Building|3|Licenses|4|Permits|5|Planning|6|CurrentTabIndex|3'

    def start_requests(self):
        try:
            # User Login with retries handled inside
            user_login = self.get_user_login()

            # Make a request to the Building Permit using the session
            building_permit_res = self.session.get(self.building_permit_url)

            if building_permit_res.status_code == 200:
                self.session.cookies.update(building_permit_res.cookies.get_dict())
                yield from self.parse_building_permit_page(building_permit_res)
            else:
                self.error.append('Failed to redirect Building Permit Page after Login')
                raise CloseSpider('Failed to redirect Building Permit Page after Login')
        except CloseSpider as e:
            print(f'Spider closed: {e}')
            self.error.append('Failed to User Login after maximum retries')
            raise e
        except requests.exceptions.RequestException as e:
            self.error.append(f'Error during Building Permit request: {e}')
            raise CloseSpider(f'Error during Building Permit request: {e}')

    def parse_building_permit_page(self, response):
        if 'shah' in response.text.lower():
            html_selector = Selector(text=response.content)

            # Update self.  fields  from the Building Permit Page before the search Results
            self.aca_cs_field = html_selector.css('#ACA_CS_FIELD::attr(value)').get('')
            self.viewstate_id = html_selector.css('#__VIEWSTATE::attr(value)').get('')
            self.session.headers.update(self.search_headers)
            self.session.cookies[
                'TabNav'] = 'HOME|0|Enforce|1|DOT|2|Building|3|Licenses|4|Permits|5|Planning|6|CurrentTabIndex|3'
        else:
            self.error.append('User logged out after redirect to permit page')
            raise CloseSpider

    def parse_search_building_permits_results(self, response):
        # Get Year range from meta and make search request for year base
        year = response.meta.get('select_year', '')

        formdata = self.get_search_permit_formdata(self.aca_cs_field, next_page=None, select_year=year)
        search_results = self.session.post(self.building_permit_url, data=formdata)

        # second page no
        page_no = 3

        while True:
            if search_results.status_code == 200:
                self.session.cookies.update(search_results.cookies.get_dict())
                if 'ACA_TabRow_Even_FontSize' in search_results.text or 'ACA_TabRow_Odd_FontSize' in search_results.text:
                    yield from self.parse_search_results(search_results)

                    html_selector = Selector(text=search_results.text)
                    viewstate = re.search(
                        r'hiddenField\|__VIEWSTATE\|(.+?)(?=\|8\|hiddenField\|__VIEWSTATEGENERATOR\|)',
                        search_results.text)
                    if viewstate:
                        self.viewstate_id = viewstate.group(1)
                    next_page_selector = html_selector.css('tr .aca_pagination_PrevNext')[-1]
                    next_page_value = next_page_selector.css('a::attr(href)').re_first(
                        r"javascript:__doPostBack\('([^']*)',''\)")

                    print('Page index No', page_no)

                    if next_page_value:
                        formdata = self.get_search_permit_formdata(self.aca_cs_field, next_page=next_page_value,
                                                                   select_year=year)

                        search_results = self.session.post(self.building_permit_url, data=formdata)
                        page_no += 1
                        self.viewstate_id = ''

                    else:
                        break  # Break the loop if no next page link is found
                else:
                    self.mandatory_logs.append(f'No Result found in the year range {year}')
                    break  # Break the loop if no permit results are found
            else:
                self.error.append('Failed to get the Building Permit Page Results')
                break  # Break the loop if request fails

    def parse_search_results(self, response):
        # After the results fetched , Indexing section of Search Result
        html_selector = Selector(text=response.text)
        building_permits = html_selector.css('.ACA_TabRow_Even_FontSize, .ACA_TabRow_Odd_FontSize')

        for permit in building_permits:
            self.all_items_counter += 1
            # print(f"Total Permits Counter :{self.all_items_counter} ")
            self.current_year_scraped_permits_count += 1

            url = permit.css('[id*="PermitNumber"] ::attr(href)').get('')
            if url:
                url = f"https://cobbca.cobbcounty.org{url}"

            if url in self.current_scraped_permit_urls:
                print('Url Already Scraped :', url)
                continue

            self.current_scraped_permit_urls.append(url)
            date = permit.css('[id*="lblUpdatedTime"]::text').get('')
            address = permit.css('[id*="lblAddress"]::text').get('')
            permit_id = ''.join([text for text in permit.css('[id*="PermitNumber"] ::text').getall() if text.strip()])
            name = permit.css('[id*="lblProjectName"]::text').get('')
            print(f'Name of permit :{name} Address : {address}')
            address = permit.css('[id*="lblAddress"]::text').get('')
            status = permit.css('[id*="lblStatus"]::text').get('')

            try:
                # Check if 'HVAC' is in the project name
                if 'HVAC' in name:
                    self.session.cookies.update(response.cookies.get_dict())
                    search_cookies = self.session.cookies.get_dict()
                    headers = dict(self.session.headers)
                    yield Request(url=url, headers=headers, cookies=search_cookies,
                                  callback=self.parse_permit_detail)
                else:
                    item = OrderedDict()
                    item['Date'] = date
                    item['Building Number'] = permit_id
                    item['Url'] = url
                    item['Project Name'] = name
                    item['Address'] = address
                    item['Status'] = status

                    self.skipped_building_permits_count += 1
                    self.write_item_into_csv(filename=self.skipped_permits_filepath, row=item,
                                             fieldnames=self.skipped_permits_fieldnames)
                    # print(f"Skipped items Without having Hvac in name : {self.skipped_building_permits_count}")

            except Exception as e:
                self.error.append(f"Error processing Name: {name}: {e}")

    def parse_permit_detail(self, response):
        permit_id = response.css('[id*="PermitNumber"]::text').get('')
        try:
            project_desc = response.xpath(
                '//span[contains(text(), "Project Description:")]/ancestor::div[1]//span[not(contains(text(), "Project Description:"))]//text()').getall()

            item = OrderedDict()
            item['Permit No'] = permit_id
            item['Type'] = response.css('[id*="PermitType"]::text').get('')
            item['Status'] = response.css('span#ctl00_PlaceHolderMain_lblRecordStatus ::text').get('')
            item['Work Location'] = response.css('#tbl_worklocation ::text').get('')
            item['Project Description'] = '\n'.join([line.strip() for line in project_desc if line.strip()])
            item['Additional Information'] = ' '.join(
                [text.strip() for text in response.css('#trADIList ::text').getall() if text.strip()])
            item['Parcel Information'] = self.get_parcel_info(response)
            item['Application Information'] = self.get_application_info(response)
            item['Url'] = response.url

            self.get_license_information(response, item)
            self.get_owner_info(response, item)

            self.current_year_scraped_permits_count += 1
            self.write_item_into_csv(filename=self.scraped_permits_filepath, row=item,
                                     fieldnames=self.scraped_permits_fieldnames)

            self.current_year_scraped_permits_list.append(item)
            print(f"Current Building Permits scraped Counter : {self.current_year_scraped_permits_count}")
        except Exception as e:
            self.error.append(f'Unable to yield {permit_id}  building Permit Detail  error : {e}')

    def get_search_permit_formdata(self, aca_cs_field, next_page, select_year):
        year = str(select_year)
        viewstate_id = self.viewstate_id.replace('/', '%2F').replace('+', '%2B')

        if not next_page:
            data = f'ctl00%24ScriptManager1=ctl00%24PlaceHolderMain%24updatePanel%7Cctl00%24PlaceHolderMain%24btnNewSearch&ctl00%24HeaderNavigation%24hdnShoppingCartItemNumber=&ctl00%24HeaderNavigation%24hdnShowReportLink=N&ctl00%24PlaceHolderMain%24addForMyPermits%24collection=rdoNewCollection&ctl00%24PlaceHolderMain%24addForMyPermits%24txtName=name&ctl00%24PlaceHolderMain%24addForMyPermits%24txtDesc=&ctl00%24PlaceHolderMain%24PermitList%24lblNeedReBind=&ctl00%24PlaceHolderMain%24PermitList%24gdvPermitList%24hfSaveSelectedItems=&ctl00%24PlaceHolderMain%24PermitList%24inpHideResumeConf=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSPermitNumber=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSStartDate=01%2F01%2F{year}&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSStartDate_ext_ClientState=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSEndDate=12%2F31%2F{year}&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSEndDate_ext_ClientState=&ctl00%24PlaceHolderMain%24hfASIExpanded=&ctl00%24PlaceHolderMain%24txtHiddenDate=&ctl00%24PlaceHolderMain%24txtHiddenDate_ext_ClientState=&ctl00%24PlaceHolderMain%24hfGridId=&ctl00%24HDExpressionParam=&Submit=Submit&__EVENTTARGET=ctl00%24PlaceHolderMain%24btnNewSearch&__EVENTARGUMENT=&__VIEWSTATE={viewstate_id}&__VIEWSTATEGENERATOR=A9414CD7&__VIEWSTATEENCRYPTED=&ACA_CS_FIELD={aca_cs_field}&__AjaxControlToolkitCalendarCssLoaded=&__ASYNCPOST=true&'

        else:
            next_page_value_encoded = next_page.replace('$', '%24')
            data = f'ctl00%24ScriptManager1=ctl00%24PlaceHolderMain%24dgvPermitList%24updatePanel%7C{next_page_value_encoded}&ctl00%24HeaderNavigation%24hdnShoppingCartItemNumber=&ctl00%24HeaderNavigation%24hdnShowReportLink=N&ctl00%24PlaceHolderMain%24addForMyPermits%24collection=rdoNewCollection&ctl00%24PlaceHolderMain%24addForMyPermits%24txtName=name&ctl00%24PlaceHolderMain%24addForMyPermits%24txtDesc=&ctl00%24PlaceHolderMain%24PermitList%24lblNeedReBind=&ctl00%24PlaceHolderMain%24PermitList%24gdvPermitList%24hfSaveSelectedItems=&ctl00%24PlaceHolderMain%24PermitList%24inpHideResumeConf=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSPermitNumber=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSStartDate=01%2F01%2F{year}&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSStartDate_ext_ClientState=&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSEndDate=12%2F31%2F{year}&ctl00%24PlaceHolderMain%24generalSearchForm%24txtGSEndDate_ext_ClientState=&ctl00%24PlaceHolderMain%24hfASIExpanded=&ctl00%24PlaceHolderMain%24txtHiddenDate=&ctl00%24PlaceHolderMain%24txtHiddenDate_ext_ClientState=&ctl00%24PlaceHolderMain%24dgvPermitList%24lblNeedReBind=&ctl00%24PlaceHolderMain%24dgvPermitList%24gdvPermitList%24hfSaveSelectedItems=&ctl00%24PlaceHolderMain%24dgvPermitList%24inpHideResumeConf=&ctl00%24PlaceHolderMain%24hfGridId=&ctl00%24HDExpressionParam=&Submit=Submit&__EVENTTARGET={next_page_value_encoded}&__EVENTARGUMENT=&__VIEWSTATE={viewstate_id}&__VIEWSTATEGENERATOR=A9414CD7&__VIEWSTATEENCRYPTED=&ACA_CS_FIELD={aca_cs_field}&__AjaxControlToolkitCalendarCssLoaded=&__ASYNCPOST=true&'
        return data

    def get_parcel_info(self, html_selector):
        table_rows = html_selector.css('#trParcelList tr')
        info = []
        for row in table_rows:
            text = ' '.join([text.strip() for text in row.css('::text').getall() if text.strip()])
            info.append(text)

        return '\n'.join(info)

    def get_user_login(self):
        if not self.get_login_data():
            print('Credentials Not found Now scraper is closed')
            self.error.append('Credentials Not found')
            raise CloseSpider('Credentials Not found')

        max_retries = 2
        attempt = 0

        while attempt <= max_retries:
            try:
                res = self.session.post('https://cobbca.cobbcounty.org/CitizenAccess/api/PublicUser/SignIn',
                                        cookies=self.cookies,
                                        headers=self.login_headers,
                                        json=self.get_login_data())

                if res.status_code == 200 and res.json().get('type') == 'success':
                    print("Login successful")
                    self.session.cookies.update(res.cookies.get_dict())
                    return res
                else:
                    print(f'Login request failed with status: {res.status_code}')
                    self.error.append(f'Failed to User Login on attempt {attempt + 1}')
                    attempt += 1
            except requests.exceptions.RequestException as e:
                print(f'Login request encountered an error: {e}')
                self.error.append(f'Login request encountered an error: {e}')
                attempt += 1

        print('Failed to User Login after maximum retries')
        raise CloseSpider('Failed to User Login after maximum retries')

    def get_license_information(self, response, item):
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

        item['Licensed Person Name'] = licensed_name
        item['Licensed Person E-Mail'] = licensed_email
        item['Licensed Person Company'] = licensed_company
        item['Licensed Person Phone No'] = licensed_phone
        item['Licensed Person Address'] = licensed_address

        return item

    def get_owner_info(self, response, item):
        owner_desc = response.xpath(
            '//span[contains(text(), "Owner:")]/ancestor::div[1]//span[not(contains(text(), "Owner:"))]//text()').getall()
        owner_info_text = [line.strip() for line in owner_desc if line.strip()]

        item['Owner Name'] = ''.join(''.join(owner_info_text).split('*')[0:1])
        item['Owner Address'] = ''.join(''.join(owner_info_text).split('*')[1:])

        return item

    def get_application_info(self, response):
        table_rows = response.css('#trASIList .ACA_TabRow ')
        info = []
        for row in table_rows:
            text = ' '.join([text.strip() for text in row.css('::text').getall() if text.strip()])
            info.append(text)

        return '\n'.join(info)

    def read_user_cred_from_input_file(self):
        """
        Reads a text file and returns its contents as a dictionary.
        :return: Dictionary containing the text file data.
        """
        file_path = ''.join(glob.glob('input/user_creds.txt'))
        data = {}
        with open(file_path, mode='r', encoding='utf-8-sig') as text_file:
            for line in text_file:
                key, value = line.strip().split('==', maxsplit=1)
                data[key.strip()] = value.strip()
        return data

    def write_item_into_csv(self, filename, row, fieldnames):
        os.makedirs('output', exist_ok=True)
        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                file_empty = csv_file.tell() == 0
                if file_empty:
                    writer.writeheader()

                writer.writerow(row)

        except Exception as e:
            self.error.append(f"file Name :{filename} __Building Permit :{row.get('Building Number', '')} Error:{e}")

    def get_login_data(self):
        name = self.user_creds.get('email', '')
        password = self.user_creds.get('password', '')

        if not name or not password:
            self.error.append(f"Kindly add the user credentials in the user_creds.txt file in input folder")
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
                'IsRemember': 0,
            },
        }

        return login_json_data

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def close(spider, reason):
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" Total Permits Found on the website are: "{spider.all_items_counter}"')
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%d%m%Y%H%M")}"\n\n')

        spider.mandatory_logs.append(f'Spider Error:: \n')
        spider.mandatory_logs.extend(spider.error)
        spider.write_logs()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GobbcountySpiderSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        self.mandatory_logs.append(
            f'Spider "{self.name}" Permits Scrapped : "{self.current_year_scraped_permits_count}"')
        self.mandatory_logs.append(
            f'Spider "{self.name}" Skipped Building Permits  : "{self.skipped_building_permits_count}"')

        self.skipped_building_permits_list = []
        self.current_year_scraped_permits_list = []
        self.current_year_scraped_permits_count = 0

        if self.year_filter and self.session.cookies.get_dict():
            select_year = self.year_filter.pop()
            self.mandatory_logs.append(f"\n\n Year range {select_year} now start scraping")

            req = Request(url='http://books.toscrape.com/',
                          callback=self.parse_search_building_permits_results,
                          dont_filter=True,
                          meta={'handle_httpstatus_all': True, 'select_year': select_year})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
