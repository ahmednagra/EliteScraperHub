import csv
import glob
import os
import re
import urllib.parse
from time import sleep, time
from datetime import datetime
from collections import OrderedDict

import requests
from scrapy import Spider, Request, Selector, signals

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, Popularity, HardwareType

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value]
hardware_types = [HardwareType.COMPUTER.value]
popularity = [Popularity.POPULAR, Popularity.COMMON.value]

user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems,
                               hardware_types=hardware_types, popularity=popularity, limit=500)

available_user_agents = user_agent_rotator.get_user_agents()

# Get Random User Agent String.
try:
    user_agent = user_agent_rotator.get_random_user_agent()
except IndexError as e:
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'  # Fallback user agent


class NassauSpiderSpider(Spider):
    name = "deeds_spider"
    start_urls = ["https://i2f.uslandrecords.com/NY/Nassau/D/Default.aspx?AspxAutoDetectCookieSupport=1"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

    }

    post_headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://i2f.uslandrecords.com',
        'Pragma': 'no-cache',
        'Referer': 'https://i2f.uslandrecords.com/NY/Nassau/D/Default.aspx?AspxAutoDetectCookieSupport=1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': user_agent,
        'X-MicrosoftAjax': 'Delta=true',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    post_cookies = {
        'NY/Nassau_DontAllowPopupTips': 'False',
        'NY/Nassau_DoNotShowSearchCriteria': 'False',
        'NY/Nassau_DoNotShowPrintChooseCriteria': 'True',
        'NY/Nassau_DoNotShowOrderChooseCriteria': 'True',
        'NY/Nassau_AutoDownloadExtraPage': '0',
        'NY/Nassau_IsImageUndock': 'False',
        'NY/Nassau_PageSize': '100',
        'NY/Nassau_DetailsViewMode': 'True',
        'NY/Nassau_PrintCriteria': 'False|False|False|True|0||2',
        'NY/Nassau_DownloadCriteria': 'True|False|False|True|0||2',
        'NY/Nassau_ScreenArrangement': '1',
        'ASP.NET_SessionId': 'bamn1ao1j3h4j4dhtq2k2mzg',
        'NY/Nassau_GroupName': 'Deeds/Mortgages',
        'NY/Nassau_ModelName': 'Deeds/Mortgages Section Search',
    }

    def __init__(self):
        super().__init__()
        self.current_search = {}
        self.search_section = ''
        self.search_block = ''
        self.search_lot = ''
        self.total_scraped_count = 0
        self.current_search_scraped_count = 0
        self.current_search_total_results = 0

        self.search_list = self.read_input_csv_file()

        self.years_ranges = self.get_yearly_search_combinations()

        # Selenium Driver
        self.homepage_url = None
        self.driver = None

        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/Deeds_logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

        # Output Folders Folder
        self.output_folder = ''
        self.output_file_name = ''
        self.pdf_folder = ''

        self.start_date = '1/01/1980'
        self.end_date = '12/31/2024'

    def start_requests(self):
        yield Request(url='https://quotes.toscrape.com/', dont_filter=True, meta={'handle_httpstatus_all': True})

    def parse_home_page(self, response):
        try:
            cookies = self.get_cookies()
            if cookies == '':
                # this conditions true if year range found no Records
                return

            if not cookies.get('ASP.NET_SessionId', ''):
                self.write_logs(f'Session id not updated {self.current_search} Years Range')
                return

            self.post_cookies['ASP.NET_SessionId'] = cookies.get('ASP.NET_SessionId', '')
            self.post_headers['Referer'] = self.driver.current_url
            self.homepage_url = self.driver.current_url
            selenium_page_html = Selector(text=self.driver.page_source)

            rows_records = selenium_page_html.css('#SearchInfo1_ACSLabel_SearchResultCount::text').get('')

            if rows_records:
                rows_records = int(rows_records)

            limit_text = 'NOTE: Your search results have been limited to the first 1000 records. Please narrow search criteria.'

            if limit_text in self.driver.page_source or rows_records >= 1000:
                for year_range_dict in self.years_ranges:
                    self.start_date = year_range_dict.get('start_date', '')
                    self.end_date = year_range_dict.get('end_date', '')
                    year_range = year_range_dict.get('year_range', '')

                    search_request = requests.post(self.homepage_url, cookies=self.post_cookies,
                                                   headers=self.post_headers,
                                                   data=self.get_form_data(year=year_range_dict))

                    yield from self.parse_request_page_results(page_source=search_request.text, search_value=year_range)
                    yield from self.pagination(page_source=search_request.text, year=year_range_dict)
            else:
                yield from self.parse_request_page_results(page_source=self.driver.page_source, search_value=True)
                yield from self.pagination(page_source=self.driver.page_source)

        except Exception as e:
            self.write_logs(f'{self.current_search}  Error parsing home page: {e}')

    def pagination(self, page_source, year=None):
        try:
            year_range = year.get('year_range', '')
            html = Selector(text=page_source)
            next_page_value = html.css('.PagerNextPrevButton:contains("Next") ::attr(href)').re_first(
                r"Back\('(.*?)',''\)")

            while next_page_value:
                next_page_reqs = requests.post(self.homepage_url, cookies=self.post_cookies, headers=self.post_headers,
                                               data=self.get_form_data(next_page=next_page_value, year=True))

                if next_page_reqs.status_code == 200:
                    yield from self.parse_request_page_results(page_source=next_page_reqs.text, next_page=True,
                                                               search_value=year_range if year_range else False)
                    next_page_html = Selector(text=next_page_reqs.text)
                    next_page_value = next_page_html.css('.PagerNextPrevButton:contains("Next") ::attr(href)').re_first(
                        r"Back\('(.*?)',''\)")
                else:
                    print(f'No Next Page . Failed to load next page: {next_page_reqs.status_code}')
                    break
            return ''

        except Exception as e:
            self.write_logs(f'year Range: {year} Pagination error : {e}')
        return ''

    def parse_request_page_results(self, page_source, search_value=None, next_page=None):
        try:
            html = Selector(text=page_source)
            records = html.css('.DataGridRow, .DataGridAlternatingRow')

            if not records:
                self.write_logs(f'{self.current_search}  No records found on the home page')
                return ''

            for record in records:
                try:
                    file_date = record.css("td a[id*='ButtonRow_File Date']::text").get('').strip()
                    date_id = ''.join(record.css('td a::attr(href)').get('').split("'")[1:2])
                    view_img = record.css("input[name*='ImgBut']::attr(name)").get('').strip()

                    if file_date:
                        deed_detail_dict = self.get_deed_detail(date_id)

                        deed_file_date = deed_detail_dict.get('File Date', '')
                        deed_type = deed_detail_dict.get('Type Desc.', '')

                        # Only Deeds None other types Yield
                        if 'deed' in deed_type.lower():
                            self.current_search_total_results += 1

                            grantors = deed_detail_dict.get('grantors', [])
                            sanitized_date = self.sanitize_filename(deed_file_date)

                            section = deed_detail_dict.get('Section', '')
                            block = deed_detail_dict.get('Block', '')
                            lot = deed_detail_dict.get('Lot', '')
                            deed_page_numbers = deed_detail_dict.get('# of Pgs.', '')
                            deed_book = deed_detail_dict.get('Book/Page', '')

                            item = OrderedDict()
                            item['Date'] = deed_file_date
                            item['Deed Type'] = deed_type
                            item['Deed Book'] = deed_book
                            item['Deed Page'] = deed_page_numbers
                            item['Section'] = section
                            item['Block'] = block
                            item['Lot'] = lot
                            item['Grantor 1'] = ''
                            item['Grantor 2'] = ''
                            item['Grantor 3'] = ''

                            # Ensure grantor fields are populated correctly
                            for index, grantor in enumerate(grantors, start=1):
                                if index > 3:  # Limit to 3 grantors
                                    break
                                item[f'Grantor {index}'] = grantor

                            item['Image Url'] = ''

                            name = f'{section}-{block}-{lot}'
                            csv_name = f'{name} - {sanitized_date}.csv'
                            csv_file_path = os.path.join(self.output_folder, csv_name)

                            if view_img:
                                images_contents, urls_list = self.get_deed_image_content(view_img, file_date)
                                item['Image Url'] = '\n'.join(urls_list)

                                # Create pdf file
                                deed_book_value = ''.join(deed_book.split('/')[:-1]).replace('D', '')
                                deed_book_page_value = ''.join(deed_book.split('/')[-1])
                                pdf_file_name = f'N-{name} - Deed - D_{deed_book_value} - P_{deed_book_page_value} - {deed_file_date}'
                                pdf_file_name = f'{self.sanitize_filename(pdf_file_name)}.pdf'
                                pdf_file_path = os.path.join(self.pdf_folder, pdf_file_name)

                                # Check if the file already exists and get a unique filename add Number
                                pdf_file_path = self.get_unique_filename(pdf_file_path)

                                self.create_pdf_from_deed_images(images_contents, pdf_file_path)
                                print(f"PDF created successfully: {pdf_file_path}")

                            self.write_to_csv(item, csv_file_path)

                            self.total_scraped_count += 1
                            self.current_search_scraped_count += 1
                            print('Current_Search_scraped_count', self.current_search_scraped_count)
                            print('total_scraped_count', self.total_scraped_count)

                            main_csv_file = os.path.join(self.output_folder,  f'{ self.search_section}-{self.search_block}-{self.search_lot}.csv')
                            self.write_to_csv(item, csv_file_path=main_csv_file)

                except Exception as e:
                    self.write_logs(f'Error Yield Item : {e}')
                    continue

            return ''
        except Exception as e:
            self.write_logs(f' Error From parse_request_page_results : {e} ')
            return ''

    def get_deed_detail(self, date_id):
        try:
            deed_detail_req = requests.post(self.homepage_url,
                                            cookies=self.post_cookies, headers=self.post_headers,
                                            data=self.get_form_data(date_id=date_id))

            html = Selector(text=deed_detail_req.text)
            tables_ids_list = ['DocDetails1_GridView_Details', 'DocDetails1_GridView_Property']
            deed_detail = {}

            for table_id in tables_ids_list:
                headers = html.css(f'#{table_id} .DataGridHeader th::text').getall()
                rows = html.css(f'#{table_id} .DataGridRow td::text').getall()
                table_dict = dict(zip(headers, rows))
                deed_detail.update(table_dict)

            grantors = [grantor.strip() for grantor in
                        html.css('#DocDetails1_GridView_GrantorGrantee tr:contains("Grantor") a::text ').getall()]
            deed_detail['grantors'] = grantors

            return deed_detail

        except Exception as e:
            self.write_logs(f'Error getting plat name for date_id {date_id}: {e}')
            return ''

    # Selenium Function open home page and load result, Update cookies
    def get_deed_image_content(self, view_img, file_date):
        current_search_date = f'{self.current_search} File Date: {file_date}'
        urls_list = []
        try:
            session = requests.session()
            homepage_data = self.get_form_data(view_img=view_img)
            homepage_resp = session.post(url=self.homepage_url, headers=self.post_headers, cookies=self.post_cookies,
                                         data=homepage_data)
            image_viewer_url = f"{''.join(self.homepage_url.split('Default')[0:1])}ImageViewerEx.aspx"
            view_image_resp = session.get(url=image_viewer_url, headers=self.post_headers, cookies=self.post_cookies)

            img_url, total_images = '', 0
            if 'preInit' in homepage_resp.text:
                img_url, total_images = self.get_acs_resource_url(homepage_resp.text)
            elif 'preInit' in view_image_resp.text:
                img_url, total_images = self.get_acs_resource_url(view_image_resp.text)

            if img_url:
                urls_list.append(img_url)

            if not img_url or not total_images:
                self.write_logs(f"{current_search_date} Error: Could not find image URL or total images.")
                return '', ''

            if total_images:
                self.write_logs(f"{current_search_date} Found Total Images: {total_images}")

            images_list = []
            successful_downloads = 0

            for i in range(int(total_images)):
                img_resp = requests.get(img_url, cookies=self.post_cookies, headers=self.post_headers)
                if img_resp.status_code == 200:
                    images_list.append({f'image_{i + 1}': img_resp.content})
                    successful_downloads += 1
                else:
                    self.write_logs(f"{current_search_date} Failed to download image No: {i + 1}")

                if i < int(total_images) - 1:  # Prepare for the next image
                    homepage_next_resp = session.post(url=self.homepage_url, headers=self.post_headers,
                                                      cookies=self.post_cookies,
                                                      data=self.get_form_data(view_img=view_img))
                    view_next_resp = session.post(url=image_viewer_url, headers=self.post_headers,
                                                  cookies=self.post_cookies, data=self.get_form_data(next_img=True))

                    if 'preInit' in homepage_next_resp.text:
                        img_url, total_images = self.get_acs_resource_url(homepage_next_resp.text)
                    elif 'preInit' in view_next_resp.text:
                        img_url, total_images = self.get_acs_resource_url(view_next_resp.text)

                    if img_url:
                        urls_list.append(img_url)

            self.write_logs(f"{current_search_date} Total images downloaded successfully: {successful_downloads}")

            return images_list, urls_list

        except Exception as e:
            self.write_logs(f"{current_search_date} Error getting the image: {e}")
            return '', ''

    def get_cookies(self):
        try:
            # Setup Chrome options for incognito mode
            chrome_options = Options()
            chrome_options.add_argument("--incognito")

            chrome_driver_path = glob.glob('input/chromedriver.exe')[0]  # Replace with the actual path

            # Initialize the Chrome driver with options
            self.driver = webdriver.Chrome(service=ChromeService(chrome_driver_path), options=chrome_options)

            # Open the website
            self.driver.get(self.start_urls[0])

            # Wait for the page to load completely
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )

            # Wait until the "Office" dropdown is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
            )
            sleep(1)

            # Wait until the "Search Type" dropdown is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchCriteriaName1_DDL_SearchName"))
            )
            sleep(1)

            # Select "Deeds/Mortgages" from the "Office" dropdown
            office_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
            office_dropdown.select_by_visible_text("Deeds/Mortgages")

            # Validate that "deeds" is selected
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"),
                                                       "Deeds/Mortgages")
            )

            sleep(3)

            # Select "Section Search" from the "Search Type" dropdown
            search_type_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaName1_DDL_SearchName"))
            search_type_dropdown.select_by_visible_text("Section Search")

            # Validate that "Recorded Date Search" is selected
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaName1_DDL_SearchName"),
                                                       "Section Search")
            )

            sleep(5)

            # Clear and set the "*Section" input
            try:
                # Try to find the input field by its ID
                section_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Section")
                validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Section")
            except NoSuchElementException:
                # If the input field by ID is not found, find it by name within the specified td
                section_input = self.driver.find_element(By.CLASS_NAME, "deftext")
                # from_date_input = from_date_cell.find_element(By.NAME, "SearchFormEx1$DRACSTextBox_DateFrom")
                validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Section")

            section_input.clear()
            section_input.send_keys(self.search_section)

            # Validate that the value is set correctly
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value(validation_condition, self.search_section)
            )

            sleep(1)

            # Clear and set the "Block" input
            try:
                # Try to find the input field by its ID
                block_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Block")
                validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Block")
            except NoSuchElementException:
                # If not found, try to find the input field by its name attribute
                block_input = self.driver.find_element(By.NAME, "SearchFormEx1$ACSTextBox_Block")
                validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Block")

            block_input.clear()
            # to_date_input.send_keys("12/31/1910")
            block_input.send_keys(self.search_block)

            # Validate that the value is set correctly
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value(validation_condition, self.search_block)
            )

            sleep(1)

            # Clear and set the "Lot" input
            try:
                # Try to find the input field by its ID
                lot_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Lot")
                validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Lot")
            except NoSuchElementException:
                # If not found, try to find the input field by its name attribute
                lot_input = self.driver.find_element(By.NAME, "SearchFormEx1$ACSTextBox_Lot")
                validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Lot")

            lot_input.clear()
            lot_input.send_keys(self.search_lot)

            # Validate that the value is set correctly
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value(validation_condition, self.search_lot)
            )

            sleep(1)

            # Wait until the "Search" button is present
            search_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchFormEx1_btnSearch"))
            )

            # Click the "Search" button
            search_button.click()

            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            sleep(4)

            if 'Search criteria resulted in 0 hits' in self.driver.page_source:
                self.write_logs(f'No Search results exist for {self.current_search} Years Range')
                self.driver.quit()
                # Return to spider_idle to continue with the next year
                self.spider_idle()
                return ''

            # Wait until the results are loaded and the page size selector is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "DocList1_PageView100Btn"))
            )

            # Select the maximum number of results per page {100}
            max_results_button = self.driver.find_element(By.ID, "DocList1_PageView100Btn")
            max_results_button.click()

            sleep(3)

            # Get the total number of results
            total_results_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchInfo1_ACSLabel_SearchResultCount"))
            )

            if int(total_results_element.text) < 1000:
                self.current_search_total_results = int(total_results_element.text)

            # Retrieve cookies
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

            return cookies

        except TimeoutException as e:
            self.write_logs(f'{self.current_search} Year Error: A TimeoutException occurred: {e}')
            self.write_logs(f'{self.current_search} Year Error: The page or one of the elements took too long to load.')
        except NoSuchElementException as e:
            self.write_logs(f'{self.current_search} Year Error: A NoSuchElementException occurred: {e}')
            self.write_logs(f'{self.current_search} Year Error: An element was not found on the page.')
        except Exception as e:
            self.write_logs(f'{self.current_search} Year Error: An error occurred: {e}')

        return None

    def get_form_data(self, next_page=None, year=None, date_id=None, view_img=None, next_img=None):
        try:
            data = {
                'ScriptManager1': 'SearchFormEx1$UpdatePanel|SearchFormEx1$btnSearch',
                'ScriptManager1_HiddenField': ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:effe2a26;;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:475a4ef5:5546a2b:497ef277:a43b07eb:d2e10b12:37e2e5c9:5a682656:1d3ed089:f9029856:d1a1d569:addc6819:c7029a2:e9e598a9;',
                'Navigator1$SearchOptions1$DocImagesCheck': 'on',
                'Navigator1$SearchOptions1$SavePrintCriteriaCheck': 'on',
                'Navigator1$SearchOptions1$SaveOrderCriteriaCheck': 'on',
                'SearchCriteriaOffice1$DDL_OfficeName': 'Deeds/Mortgages',
                'SearchCriteriaName1$DDL_SearchName': 'Deeds/Mortgages Section Search',
                'SearchFormEx1$ACSTextBox_Section': self.search_section,
                'SearchFormEx1$ACSTextBox_Block': self.search_block,
                'SearchFormEx1$ACSTextBox_Lot': self.search_lot,
                'SearchFormEx1$ACSTextBox_Unit': '',
                'SearchFormEx1$ACSTextBox_LastName': '',
                'SearchFormEx1$ACSTextBox_DateFrom': self.start_date,
                'SearchFormEx1$ACSTextBox_DateTo': self.end_date,
                'ImageViewer1$ScrollPos': '',
                'ImageViewer1$ScrollPosChange': '',
                'ImageViewer1$_imgContainerWidth': '0',
                'ImageViewer1$_imgContainerHeight': '0',
                'ImageViewer1$isImageViewerVisible': 'true',
                'ImageViewer1$hdnWidgetSize': '',
                'ImageViewer1$DragResizeExtender_ClientState': '',
                'CertificateViewer1$ScrollPos': '',
                'CertificateViewer1$ScrollPosChange': '',
                'CertificateViewer1$_imgContainerWidth': '0',
                'CertificateViewer1$_imgContainerHeight': '0',
                'CertificateViewer1$isImageViewerVisible': 'true',
                'CertificateViewer1$hdnWidgetSize': '',
                'CertificateViewer1$DragResizeExtender_ClientState': '',
                'PTAXViewer1$ScrollPos': '',
                'PTAXViewer1$ScrollPosChange': '',
                'PTAXViewer1$_imgContainerWidth': '0',
                'PTAXViewer1$_imgContainerHeight': '0',
                'PTAXViewer1$isImageViewerVisible': 'true',
                'PTAXViewer1$hdnWidgetSize': '',
                'PTAXViewer1$DragResizeExtender_ClientState': '',
                'DocList1$ctl12': '',
                'DocList1$ctl14': '',
                'RefinementCtrl1$ctl01': '',
                'RefinementCtrl1$ctl03': '',
                'NameList1$ScrollPos': '',
                'NameList1$ScrollPosChange': '',
                'NameList1$_SortExpression': '',
                'NameList1$ctl03': '',
                'NameList1$ctl05': '',
                'DocDetails1$PageSize': '',
                'DocDetails1$PageIndex': '',
                'DocDetails1$SortExpression': '',
                'BasketCtrl1$ctl01': '',
                'BasketCtrl1$ctl03': '',
                'OrderList1$ctl01': '',
                'OrderList1$ctl03': '',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__VIEWSTATE': '',
                '__ASYNCPOST': 'true',
                'SearchFormEx1$btnSearch': 'Search',
            }

            if date_id:
                data['ScriptManager1'] = f'DocList1$UpdatePanel|{date_id}'
                data['__EVENTTARGET'] = date_id
                if 'SearchFormEx1$btnSearch' in data:
                    del data['SearchFormEx1$btnSearch']

            if next_page:
                data['ScriptManager1'] = f'DocList1$UpdatePanel|{next_page}'
                data['__EVENTTARGET'] = next_page
                if 'SearchFormEx1$btnSearch' in data:
                    del data['SearchFormEx1$btnSearch']

            if view_img:
                data['ScriptManager1'] = f'DocList1$UpdatePanel|{view_img}'
                data[view_img] = ''
                if 'SearchFormEx1$btnSearch' in data:
                    del data['SearchFormEx1$btnSearch']

            if next_img:
                next_img_data = {
                    'ScriptManager1': 'ImageViewer1$UpdatePanel1|ImageViewer1$BtnNext',
                    'ScriptManager1_HiddenField': ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:effe2a26;;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:475a4ef5:5546a2b:497ef277:a43b07eb:3ac3e789;',
                    'ImageViewer1$ScrollPos': '',
                    'ImageViewer1$ScrollPosChange': '',
                    'ImageViewer1$_imgContainerWidth': '0',
                    'ImageViewer1$_imgContainerHeight': '0',
                    'ImageViewer1$isImageViewerVisible': 'true',
                    'ImageViewer1$hdnWidgetSize': '',
                    'ImageViewer1$tbPageNum': '',
                    'ImageViewer1$TextBox_GoTo': '',
                    'ImageViewer1$imWidth': '',
                    'ImageViewer1$imHeight': '',
                    'ImageViewer1$DragResizeExtender_ClientState': '',
                    '__EVENTTARGET': '',
                    '__EVENTARGUMENT': '',
                    '__VIEWSTATE': '',
                    '__ASYNCPOST': 'true',
                    'ImageViewer1$BtnNext': '',
                }

                return next_img_data

            if not date_id and not next_page and not view_img and not year and not next_img:
                return ''

            formdata = urllib.parse.urlencode(data)
            return formdata

        except Exception as e:
            self.write_logs(f'Form Data Error: {e}')
            return ''

    def get_yearly_search_combinations(self):
        start_year = 1980
        end_year = 2024
        gap = 5

        year_combinations = []

        while start_year <= end_year:
            range_end_year = min(start_year + gap - 1, end_year)

            year_start_date = f"1/01/{start_year}"
            year_end_date = f"12/31/{range_end_year}"

            current_year = f"{start_year}-{range_end_year}"

            year_combinations.append({
                'start_date': year_start_date,
                'end_date': year_end_date,
                'year_range': current_year
            })

            # Move to the next range
            start_year += gap

        return year_combinations

    def sanitize_filename(self, filename):
        # Replace invalid characters with underscores
        return re.sub(r'[\\/*?:"<>|]', '-', filename)

    def read_input_csv_file(self):
        input_file = glob.glob('input/search_records.csv')[0]
        try:
            with open(input_file, 'r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                return list(csv_reader)

        except FileNotFoundError:
            self.write_logs(f"File '{input_file}' not found.")
            return
        except Exception as e:
            self.write_logs(f"An error occurred while reading the file: {str(e)}")
            return

    def write_to_csv(self, item, csv_file_path):
        try:
            headers = item.keys()
            file_exists = os.path.exists(csv_file_path)

            if file_exists:
                # Read existing headers if the file exists
                with open(csv_file_path, 'r') as csvfile:
                    existing_headers = csvfile.readline().strip().split(',')
                    headers = existing_headers if existing_headers else list(headers)

            # Write data to the file
            with open(csv_file_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header if the file was empty
                if not file_exists or os.path.getsize(csv_file_path) == 0:
                    writer.writerow(headers)

                # Write the data row
                row = [item.get(header, '') for header in headers]
                writer.writerow(row)

            # Print success message
            print(f'Successfully wrote item to {csv_file_path}')

        except IOError as e:
            self.write_logs(f'IOError while writing to CSV: {e}')
        except Exception as e:
            self.write_logs(f'Unexpected error while writing to CSV: {e}')

    def get_acs_resource_url(self, request_text):
        html = Selector(text=request_text)
        try:
            preinit_value = html.css('script:contains("preInit") ::text').re_first(r"preInit\('(.*?)','ImageViewer1_docImage'")
            if not preinit_value:
                preinit_match = re.search(r"preInit\('([^']+)'",
                                          html.css('script:contains("preInit") ::text').get(''))
                if preinit_match:
                    preinit_value = preinit_match.group(1)

            # Next Image Acs Resource value
            if not preinit_value:
                preinit_value = ''.join(''.join(html.get().split("preInit('")[1:]).split("','Image")[0:1])

            img_url = f"{''.join(self.homepage_url.split('Default')[0:1])}{preinit_value}&CNTWIDTH=2557&CNTHEIGHT=963&FITTYPE=Height&ZOOM=4.5"
            total_images = html.css('#ImageViewer1_lblPageNum ::text').re_first(r'of (\d+)')

            if not img_url:
                self.write_logs('Error: Could not find the ACS resource value for the image URL.')
                return '', ''

            # If total_images is None, set it to an empty string
            total_images = total_images.strip() if total_images is not None else ''

            return img_url, total_images

        except Exception as e:
            self.write_logs(f"Error parsing ACS resource URL: {e}")
            return '', ''

    def create_pdf_from_deed_images(self, images_contents, pdf_file_path):
        try:
            c = canvas.Canvas(pdf_file_path, pagesize=letter)
            width, height = letter

            for image_dict in images_contents:
                for title, image_content in image_dict.items():
                    image = ImageReader(BytesIO(image_content))  # Use BytesIO to create a file-like object
                    c.setFont("Helvetica", 12)
                    c.drawString(100, height - 20, title)  # Title as header
                    c.drawImage(image, 0, 0, width, height - 40)
                    c.showPage()

            c.save()
        except Exception as e:
            self.write_logs(
                f"{self.current_search} File Path :{pdf_file_path} Pdf File Not created Successfully, Error: {e}")

    def get_unique_filename(self, file_path):
        """
        Generate a unique file name if the file already exists by appending a counter.
        """
        base, ext = os.path.splitext(file_path)
        counter = 1
        unique_file_path = file_path

        while os.path.exists(unique_file_path):
            unique_file_path = f"{base}_{counter}{ext}"
            counter += 1

        return unique_file_path

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NassauSpiderSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.current_search and self.current_search_total_results:
            # sec_bl_lot = f'Section: {self.search_section} Block: {self.search_block} Lot: {self.search_lot}'
            self.write_logs(f'{self.current_search} Total Record Found {self.current_search_total_results}')
            self.write_logs(f'{self.current_search} Total Record Scraped {self.current_search_scraped_count}')

            self.current_search = {}
            self.search_section = ''
            self.search_block = ''
            self.search_lot = ''
            self.output_file_name = ''
            self.current_search_scraped_count = 0
            self.current_search_total_results = 0
            self.write_logs('\n')

            # Clear cookies before quitting the driver
            if self.driver:
                self.driver.delete_all_cookies()
                self.driver.quit()

        self.write_logs(f'Search Combinations Left to Search: {len(self.search_list)}')

        if self.search_list:
            self.current_search = self.search_list.pop(0)
            self.search_section = self.current_search.get('section', '')
            self.search_block = self.current_search.get('block', '')
            self.search_lot = self.current_search.get('lots', '')

            self.output_folder = f'Deeds_output/{f"N-{self.search_section}-{self.search_block}-{self.search_lot}"}'
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

            self.pdf_folder = f'{self.output_folder}/PDF'
            if not os.path.exists(self.pdf_folder):
                os.makedirs(self.pdf_folder)

            self.write_logs(f'Row : {self.current_search} started for scraping')

            req = Request(url='https://quotes.toscrape.com/',
                          callback=self.parse_home_page,
                          dont_filter=True,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        spider.write_logs(f'Total Results Scraped: {spider.total_scraped_count}')
        # Clear cookies before quitting the driver
        if spider.driver:
            spider.driver.delete_all_cookies()
            spider.driver.quit()
