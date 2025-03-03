import glob
import os
import re
import urllib.parse
from time import sleep
from datetime import datetime
from collections import OrderedDict

import requests
from scrapy import Spider, Request, Selector, signals

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, Popularity, HardwareType


class NassauSpiderSpider(Spider):
    name = "nassau_spider"
    start_urls = ["https://i2f.uslandrecords.com/NY/Nassau/D/Default.aspx?AspxAutoDetectCookieSupport=1"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

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

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'Maps_output/Nassau County Map Records {current_dt}.csv': {
                'format': 'csv',
                'fields': ['File Date', 'Map Title', 'Map No', 'Type Desc', 'Doc', 'Image']
            }
        }
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
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'User-Agent': user_agent,
        'X-MicrosoftAjax': 'Delta=true',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    post_cookies = {
        'NY/Nassau_DetailsViewMode': 'True',
        'NY/Nassau_DontAllowPopupTips': 'False',
        'NY/Nassau_DoNotShowSearchCriteria': 'False',
        'NY/Nassau_DoNotShowPrintChooseCriteria': 'True',
        'NY/Nassau_DoNotShowOrderChooseCriteria': 'True',
        'NY/Nassau_AutoDownloadExtraPage': '0',
        'NY/Nassau_IsImageUndock': 'False',
        'NY/Nassau_GroupName': 'Maps',
        'NY/Nassau_ModelName': 'Maps Recorded Date Search',
        'ASP.NET_SessionId': 'cd3121jo3whce3hqsf5indux',
        'NY/Nassau_PageSize': '100',
    }

    def __init__(self):
        super().__init__()
        self.current_year = ''
        self.search_from_date = ''
        self.search_to_date = ''
        self.total_scraped_count = 0
        self.current_year_scraped_count = 0
        self.current_year_total_results = 0

        self.years = self.get_yearly_search_combinations()

        # Selenium Driver
        self.homepage_url = None
        self.driver = None

        # Logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/Maps_logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

        # Images Folder
        self.images_folder = 'Maps_output/image'
        # Check if images_folder exists, create if not
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)

        # Url Text FIle
        self.url_folder = 'Maps_output/url'
        self.url_file = os.path.join(self.url_folder, f'urls_{self.current_dt}.txt')
        if not os.path.exists(self.url_folder):
            os.makedirs(self.url_folder)

    def start_requests(self):
        yield from self.spider_idle()

    def parse_home_page(self, response):
        try:
            cookies = self.get_cookies()
            # this conditions true if year range found no Records
            if cookies == '' or cookies is None:
                return

            if not cookies.get('ASP.NET_SessionId', ''):
                self.write_logs(f'Session id not updated {self.current_year} Years Range')
                return

            self.post_cookies['ASP.NET_SessionId'] = cookies.get('ASP.NET_SessionId', '')
            self.post_headers['Referer'] = self.driver.current_url
            self.homepage_url = self.driver.current_url
            selenium_page_html = Selector(text=self.driver.page_source)

            rows_records = selenium_page_html.css('#SearchInfo1_ACSLabelParam_SearchResultCount::text').get('')

            if rows_records:
                rows_records = int(rows_records)

            limit_text = 'NOTE: Your search results have been limited to the first 1000 records. Please narrow search criteria.'

            if limit_text in self.driver.page_source or rows_records >= 1000:

                # Extract Maps option elements that are not selected and create a list of dictionaries
                option_list = [
                    {option.css('::text').get(): option.css('::attr(value)').get()}
                    for option in selenium_page_html.css('.lst option:not([selected])')
                ]
                for option in option_list:
                    for value in option.values():
                        data = self.get_form_data(search_type=value)
                        search_request = requests.post(self.homepage_url, cookies=self.post_cookies,
                                                       headers=self.post_headers, data=data)

                        yield from self.parse_search_results(page_source=search_request.text, search_value=option)
                        yield from self.pagination(page_source=search_request.text, search_option=option)
            else:
                yield from self.parse_search_results(page_source=self.driver.page_source)
                yield from self.pagination(page_source=self.driver.page_source)

        except Exception as e:
            self.write_logs(f'Year Range :{self.current_year} Error parsing home page: {e}')

    def pagination(self, page_source, search_option=None):
        try:
            html = Selector(text=page_source)
            next_page_value = html.css('.PagerNextPrevButton:contains("Next") ::attr(href)').re_first(
                r"Back\('(.*?)',''\)")
            search_value = search_option
            search_option = list(search_option.keys())[0] if search_option else ''
            while next_page_value:
                try:
                    data = self.get_form_data(next_page=next_page_value,
                                              search_type=search_option) if search_option else self.get_form_data(
                        next_page=next_page_value)
                    next_page_reqs = requests.post(self.homepage_url, headers=self.post_headers,
                                                   cookies=self.post_cookies, data=data)

                    if next_page_reqs.status_code == 200:
                        if search_option:
                            yield from self.parse_search_results(page_source=next_page_reqs.text, search_value=search_value)
                        else:
                            yield from self.parse_search_results(page_source=next_page_reqs.text)

                        next_page_html = Selector(text=next_page_reqs.text)
                        next_page_value = next_page_html.css(
                            '.PagerNextPrevButton:contains("Next") ::attr(href)').re_first(r"Back\('(.*?)',''\)")
                    else:
                        self.write_logs(f'Failed to load next page: {next_page_reqs.status_code}')
                        break

                except Exception as e:
                    self.write_logs(f'Error processing next page: {e}')
                    break

        except Exception as e:
            self.write_logs(f'Error initializing pagination: {e}')

        return

    def parse_search_results(self, page_source, search_value=None):
        try:
            html = Selector(text=page_source)
            records = html.css('.DataGridRow, .DataGridAlternatingRow')
            search_key = list(search_value.keys())[0] if search_value else ''

            if not records:
                self.write_logs(
                    f'Year Range: {self.current_year} has No records found on the home page.')
                return

            if search_value:
                rows_records = html.css('#SearchInfo1_ACSLabelParam_SearchResultCount::text').get('0')
                self.write_logs(
                    f'Year Range: {self.current_year} ,  Search Option "{search_key}" has "{rows_records}" records found on the home page.')
                self.current_year_total_results += int(rows_records)

            for record in records:
                try:
                    file_date = record.css("td a[id*='ButtonRow_File Date']::text").get('').strip()
                    date_id = ''.join(record.css('td a::attr(href)').get('').split("'")[1:2])
                    type_desc = record.css("td a[id*='ButtonRow_Type Desc.']::text").get('').strip()
                    doc_number = record.css("td a[id*='ButtonRow_Doc. #']::text").get('').strip()
                    rec_time = record.css("td a[id*='ButtonRow_Rec. Time']::text").get('').strip()
                    num_pages = record.css("td a[id*='ButtonRow_# of Pgs']::text").get('').strip()
                    view_img = record.css("input[name*='ImgBut']::attr(name)").get('').strip()
                    add_to_basket = record.css("input[name*='AddToBskBut']::attr(name)").get('').strip()

                    if file_date:
                        plat_desc, map_no = self.get_plat_name(date_id, file_date)

                        image_name = f'NM-{self.sanitize_filename(map_no)} - {self.sanitize_filename(plat_desc)} - {self.sanitize_filename(file_date)}.jpg'
                        image_file_path = os.path.join(self.images_folder, image_name)

                        item = OrderedDict()
                        item['File Date'] = file_date
                        item['Map Title'] = plat_desc
                        item['Map No'] = map_no
                        item['Type Desc'] = type_desc
                        item['Doc'] = doc_number
                        item['Search Option'] = search_key
                        item['Image'] = image_name

                        self.total_scraped_count += 1
                        self.current_year_scraped_count += 1
                        print('Current_year_scraped_count', self.current_year_scraped_count)
                        print('total_scraped_count', self.total_scraped_count)

                        if view_img:
                            images_list = self.get_map_image_content(view_img, file_date, image_name)
                            if len(images_list) == 1:
                                image_content = list(images_list[0].values())[0]
                                with open(image_file_path, 'wb') as f:
                                    f.write(image_content)
                                print(f"Image downloaded successfully to: {image_file_path}")
                            else:
                                for image_dict in images_list:
                                    for key, image_content in image_dict.items():
                                        file_path = os.path.join(self.images_folder, f"{key}.jpg")
                                        with open(file_path, 'wb') as f:
                                            f.write(image_content)
                                        print(f"Image downloaded successfully to: {file_path}")

                        yield item

                except Exception as e:
                    self.write_logs(f'Error Yield Item : {e}')
                    continue

        except Exception as e:
            self.write_logs(f' Error From parse_request_page_results : {e} ')
            return

    def get_plat_name(self, date_id, file_date):
        try:
            self.post_cookies.update({'NY/Nassau_IsImageUndock': 'False'})
            session = requests.session()
            session_req = session.post(self.homepage_url,
                                       cookies=self.post_cookies, headers=self.post_headers,
                                       data=self.get_form_data(date_id=date_id))

            html = Selector(text=session_req.text)

            file_date_formatted = '/'.join(file_date.split('/')[:-1])

            # Extract the value from the matching row
            texts = [tr.css('a::text').get('').strip() for tr in html.css('#DocDetails1_GridView_GrantorGrantee tr')]
            plat_desc = next((text for text in texts if file_date_formatted in text.replace('0', '')), '')
            plat_desc = re.findall(r'\d[\d\s/\-]*([A-Za-z].*)', plat_desc)[0] if re.findall(r'\d[\d\s/\-]*([A-Za-z].*)',
                                                                                            plat_desc) else plat_desc
            if not plat_desc:
                plat_desc = ''.join(
                    html.css('#DocDetails1_GridView_GrantorGrantee tr:contains("Plat Desc") a::text').getall()[
                    -1:]).strip()
            if not plat_desc:
                plat_desc = re.sub(r'\d', '', texts[0]).strip()
            if not plat_desc:
                plat_desc = file_date_formatted

            map_detail_row = html.css('#DocDetails1_GridView_Details .DataGridRow td::text').getall()
            map_no = map_detail_row[-1].lstrip('0').strip() if map_detail_row else ''

            return plat_desc, map_no

        except Exception as e:
            self.write_logs(f'Error getting plat name for date_id {date_id}: {e}')
            return '', '', ''

    def get_map_image_content(self, view_img, file_date, image_name):
        current_search_date = f'Year: {self.current_year}  File Date: {file_date}'
        try:
            session = requests.session()
            image_viewer_url = f"{''.join(self.homepage_url.split('Default')[0:1])}ImageViewerEx.aspx"

            homepage_data = self.get_form_data(view_img=view_img)
            homepage_resp = session.post(url=self.homepage_url, headers=self.post_headers, cookies=self.post_cookies, data=homepage_data)
            view_image_resp = session.get(url=image_viewer_url, headers=self.post_headers, cookies=self.post_cookies)

            image_urls = []
            img_url, total_images = '', 0
            if 'preInit' in homepage_resp.text:
                img_url, total_images = self.get_acs_resource_url(homepage_resp.text)
                image_urls.append(img_url)
            elif 'preInit' in view_image_resp.text:
                img_url, total_images = self.get_acs_resource_url(view_image_resp.text)
                image_urls.append(img_url)

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
                        image_urls.append(img_url)
                    elif 'preInit' in view_next_resp.text:
                        img_url, total_images = self.get_acs_resource_url(view_next_resp.text)
                        image_urls.append(img_url)

            self.write_logs(f"{current_search_date} Total images downloaded successfully: {successful_downloads}")

            # urls = [''.join(''.join(url.split('SCTKEY=')[1:2]).split('/')[0:1]) for url in image_urls]
            urls = ', '.join(image_urls)
            # image name, image URL
            img_and_url = f'{image_name}, {urls}\n'
            with open(self.url_file, 'a') as file:

                file.write(img_and_url)

            return images_list

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

            # Select "Maps" from the "Office" dropdown
            office_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
            office_dropdown.select_by_visible_text("Maps")

            # Validate that "Maps" is selected
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"), "Maps")
            )

            sleep(5)

            # Select "Recorded Date Search" from the "Search Type" dropdown
            search_type_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaName1_DDL_SearchName"))
            search_type_dropdown.select_by_visible_text("Recorded Date Search")

            try:
                # Validate that "Recorded Date Search" is selected
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaName1_DDL_SearchName"),
                                                           "Recorded Date Search")
                )
            except:
                # If the text validation fails, select by value
                search_type_dropdown.select_by_value("Maps Recorded Date Search")

                # Validate that the "Recorded Date Search" option is selected by value
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaName1_DDL_SearchName"),
                                                           "Maps Recorded Date Search")
                )

            sleep(5)

            # Clear and set the "From Date" input
            try:
                # Try to find the input field by its ID
                from_date_input = self.driver.find_element(By.ID, "SearchFormEx1_DRACSTextBox_DateFrom")
                validation_condition = (By.ID, "SearchFormEx1_DRACSTextBox_DateFrom")
            except NoSuchElementException:
                # If the input field by ID is not found, find it by name within the specified td
                from_date_cell = self.driver.find_element(By.ID, "SearchFormEx1_DataRange_Cell21")
                from_date_input = from_date_cell.find_element(By.NAME, "SearchFormEx1$DRACSTextBox_DateFrom")
                validation_condition = (By.NAME, "SearchFormEx1$DRACSTextBox_DateFrom")

            from_date_input.clear()
            # from_date_input.send_keys("1/01/1900")
            from_date_input.send_keys(self.search_from_date)

            # Validate that the value is set correctly
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value(validation_condition, self.search_from_date)
            )

            sleep(1)

            # Clear and set the "To Date" input
            try:
                # Try to find the input field by its ID
                to_date_input = self.driver.find_element(By.ID, "SearchFormEx1_DRACSTextBox_DateTo")
            except NoSuchElementException:
                # If not found, try to find the input field by its name attribute
                to_date_input = self.driver.find_element(By.NAME, "SearchFormEx1$DRACSTextBox_DateTo")

            to_date_input.clear()
            # to_date_input.send_keys("12/31/1910")
            to_date_input.send_keys(self.search_to_date)

            # Validate that the value is set correctly
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element_value((By.ID, "SearchFormEx1_DRACSTextBox_DateTo"),
                                                       self.search_to_date)
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

            if 'resulted in 0 hits' in self.driver.page_source:
                self.write_logs(f'No Search results exist for {self.current_year} Years Range')
                self.driver.quit()
                self.spider_idle()
                return ''

            # Wait until the results are loaded and the page size selector is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "DocList1_PageView100Btn"))
            )

            # Select the maximum number of results per page
            max_results_button = self.driver.find_element(By.ID, "DocList1_PageView100Btn")
            max_results_button.click()

            sleep(5)

            # Get the total number of results
            total_results_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchInfo1_ACSLabelParam_SearchResultCount"))
            )
            if int(total_results_element.text) < 1000:
                self.current_year_total_results = int(total_results_element.text)

            # Retrieve cookies
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

            return cookies

        except TimeoutException as e:
            self.write_logs(f'{self.current_year} Year Error: A TimeoutException occurred: {e}')
            self.write_logs(f'{self.current_year} Year Error: The page or one of the elements took too long to load.')
        except NoSuchElementException as e:
            self.write_logs(f'{self.current_year} Year Error: A NoSuchElementException occurred: {e}')
            self.write_logs(f'{self.current_year} Year Error: An element was not found on the page.')
        except Exception as e:
            self.write_logs(f'{self.current_year} Year Error: An error occurred: {e}')

        return None

    def get_form_data(self, view_img=None, date_id=None, tab_image=None, next_page=None, search_type=None, next_img=None):
        try:
            data_dict = {
                'ScriptManager1': 'DocList1$UpdatePanel|DocList1$GridView_Document$ctl02$ButtonRow_File Date_0',
                'ScriptManager1_HiddenField': ';;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:effe2a26;;;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:1547e793-5b7e-48fe-8490-03a375b13a33:475a4ef5:5546a2b:497ef277:a43b07eb:d2e10b12:37e2e5c9:5a682656:1d3ed089:f9029856:d1a1d569:addc6819:c7029a2:e9e598a9;',
                'Navigator1$SearchOptions1$DocImagesCheck': 'on',
                'Navigator1$SearchOptions1$SavePrintCriteriaCheck': 'on',
                'Navigator1$SearchOptions1$SaveOrderCriteriaCheck': 'on',
                'SearchCriteriaOffice1$DDL_OfficeName': 'Maps',
                'SearchCriteriaName1$DDL_SearchName': 'Maps Recorded Date Search',
                'SearchFormEx1$DRACSTextBox_DateFrom': self.search_from_date,
                'SearchFormEx1$DRACSTextBox_DateTo': self.search_to_date,
                'SearchFormEx1$ACSDropDownList_DocumentType': '-2',
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
                'DocList1$ctl14': '0',
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
                '__ASYNCPOST': 'true'
            }

            if date_id and not view_img:
                data_dict['ScriptManager1'] = f'DocList1$UpdatePanel|{date_id}'
                data_dict['__EVENTTARGET'] = date_id
            elif not date_id and view_img:
                data_dict['ScriptManager1'] = f'DocList1$UpdatePanel|{view_img}'
                data_dict[view_img] = ''
            elif tab_image:
                data_dict['ScriptManager1'] = 'TabController1$UpdatePanel1|TabController1$ImageViewertabitem'
                data_dict['__EVENTTARGET'] = 'TabController1$ImageViewertabitem'
            elif next_page:
                data_dict['ScriptManager1'] = f'DocList1$UpdatePanel|{next_page}'
                data_dict['__EVENTTARGET'] = next_page
            elif search_type:
                data_dict['ScriptManager1'] = 'SearchFormEx1$UpdatePanel|SearchFormEx1$btnSearch'
                data_dict['SearchFormEx1$ACSDropDownList_DocumentType'] = search_type
                data_dict['Options1_TabContainer1_ClientState'] = '{"ActiveTabIndex":0,"TabState":[true,true,true]}'
                data_dict['SearchFormEx1$btnSearch'] = 'Search'
            elif next_img:
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

            elif not date_id and not view_img and not tab_image and not next_page and not search_type:
                # this empty form data for second request for image
                return None

            formdata = urllib.parse.urlencode(data_dict)
            return formdata
        except Exception as e:
            self.write_logs(f'Form Data Error: {e}')
            return None

    def get_yearly_search_combinations(self):
        start_year = 1900
        end_year = 2024
        gap = 5

        year_combinations = []

        while start_year <= end_year:
            # Calculate the end year for the current range
            range_end_year = min(start_year + gap - 1, end_year)

            # Define the start and end dates for this range
            year_start_date = f"1/01/{start_year}"
            year_end_date = f"12/31/{range_end_year}"

            # Create the current year range string
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
        return re.sub(r'[\\/*?:"<>|]', '_', filename)

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

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

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NassauSpiderSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.current_year and self.current_year_total_results:
            self.write_logs(f'Year: {self.current_year} Total Record Found {self.current_year_total_results}')
            self.write_logs(f'Year: {self.current_year} Total Record scraped {self.current_year_scraped_count}')

            self.current_year = ''
            self.current_year_total_results = 0
            self.current_year_scraped_count = 0

            # Clear cookies before quitting the driver
            if self.driver:
                self.driver.delete_all_cookies()
                self.driver.quit()

        self.write_logs('\n')
        self.write_logs(f'Search Combinations Left to Search: {len(self.years)}')

        if self.years:
            year = self.years.pop(0)
            self.current_year = year.get('year_range', '')
            self.search_from_date = year.get('start_date', '')
            self.search_to_date = year.get('end_date', '')

            self.write_logs(f'Year: {self.current_year} started for scraping')

            req = Request(url='https://quotes.toscrape.com/',
                          callback=self.parse_home_page,
                          dont_filter=True,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        spider.write_logs(f'{spider.total_scraped_count} Total Maps Are Scrapped ')
        if spider.driver:
            spider.driver.quit()
