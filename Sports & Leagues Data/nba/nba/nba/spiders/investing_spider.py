import glob
from datetime import datetime
from time import sleep
from typing import Iterable

import requests
import scrapy
import json
import os
import csv

from openpyxl import Workbook
from collections import OrderedDict

from scrapy import Spider, Request, Selector
from urllib3.filepost import writer

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import scrapy_xlsx

class InvestingSpider(Spider):
    name = 'currency'
    base_url = 'https://www.investing.com/rates-bonds/forward-rates'

    # player_csv_headers = ['Name', 'Bid', 'Ask', 'High', 'Low', 'Chg.', 'Time']

    custom_settings = {
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'CONCURRENT_REQUESTS': 4,
        # 'DOWNLOAD_DELAY': 1,
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },
        'FEEDS': {
            f'output/EUR_USD Currency {datetime.now().strftime("%d%m%Y%H%M")}.xlsx': {
                'format': 'xlsx',
                'fields': ['Name', 'Bid', 'Ask', 'High', 'Low', 'Chg.', 'Time']
            }
        }

    }

    headers = {
    'accept': 'text/html, */*; q=0.01',
    'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
    # 'cookie': 'PHPSESSID=lgcotn262ptqovgs9mkfkf4dvj; geoC=PK; page_equity_viewed=0; browser-session-counted=true; user-browser-sessions=1; adBlockerNewUserDomains=1729709794; gtmFired=OK; udid=6a0df84ba1e4c866b14cfd0cc278ff34; smd=6a0df84ba1e4c866b14cfd0cc278ff34-1729709794; __cflb=02DiuGRugds2TUWHMkimYPAcC3JQrXKkBcWu2HtfC9CEQ; _imntz_error=0; _gid=GA1.2.1993591719.1729709807; __eventn_id=6a0df84ba1e4c866b14cfd0cc278ff34; adsFreeSalePopUp=3; nyxDorf=NTI3YGI0ZDo0aGE4bj1mZDBhYzJhYjAyPWhjajdlM29lMmFlYGxhNzY1YDowOjk9MGFlYjY2MmVnbjI4NmFnZzVlN25iNWRqNDRhZQ%3D%3D; page_view_count=2; invpc=2; cf_clearance=cwLKjcg4neNZsFAlFWfoQkqhULF5odorOGWEQYDLeBI-1729710935-1.2.1.1-SELZza06mDNlijRkWonD43js52kS0rOO8z0PY0q16H7GyeMKjGCIuVXqjDYGmPU8awI0XGALJvdZFdh0.KkManpbct39Jdwcd0bYgfFja6mVbHcbo3MapGMdIMXaYr7Gu5md.Ni.KgOwm_fj_NTDHb7vuRTy0DhROwEQRc7deZHNwyBBy6osWCLe.dIF9EQeRibjt.Xq3c7ZDkWfxhaF0A25rbMNNX433Oa9GkVsep5fly5e7mKQVTWPVlRX8plrS2gxXsCNRIhA81K3USuLfd9TAhzuMQp0IpkYo6MVMNd8agA5R_WYkaNX97fX1tXm0eUGez430Quw9FHYU2kxuRAvlSdZAYBsJS0PGSW0suN1xjxfdnFEuqfdEXC5kIr1oWpTRugDnXi6w3c8zYdbqw; _ga=GA1.1.122462669.1729709807; _ga_C4NDLGKVMK=GS1.1.1729709815.1.1.1729712602.60.0.0; __cf_bm=Hn2vfgtdvmogreSSWi7IpmjdHA5FjowIp50A1vOA7cg-1729712615-1.0.1.1-eGdpv95JCkKR2bnscB3pW2wUtcXd8pF5jgCLRzSE_weW7UzufdjEA5fjzGdowt6xOUMfnbfoXkUc1MbYkbgDj.LWRMOvYuEGWs7SnXs3j90',
    'priority': 'u=1, i',
    'referer': 'https://www.investing.com/rates-bonds/forward-rates',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

    def __init__(self):
        super().__init__()
        self.cookies = {}

        # Selenium Driver
        self.homepage_url = None
        self.driver = None

        self.data = []  # Collect data into this list

    def start_requests(self) -> Iterable[Request]:
        self.cookies = self.get_cookies()
        yield from self.parse()

    def parse(self):

        # response = Selector(text=self.driver.page_source)
        # currency_name = response.css('#leftColumn table ::text').get('')
        # headers = [header.strip() for header in response.css('#curr_table thead tr ::text').getall() if header.strip() != '']
        # raw_records = response.css('#curr_table tbody tr')
        # for row in raw_records:
        #     td = row.css('td:not(.icon)')
        #     item = OrderedDict()
        #     item['Name'] = td.css(' ::text').getall()[0]
        #     item['Bid'] = td.css(' ::text').getall()[1]
        #     item['Ask'] = td.css(' ::text').getall()[2]
        #     item['High'] = td.css(' ::text').getall()[3]
        #     item['Low'] = td.css(' ::text').getall()[4]
        #     item['Chg.'] = td.css(' ::text').getall()[5]
        #     item['Time'] = td.css(' ::text').getall()[6]
        #
        #     yield item
        # Get the page source and parse with Scrapy's Selector
        response = Selector(text=self.driver.page_source)

        # Extract headers and table rows
        headers = [header.strip() for header in response.css('#curr_table thead tr ::text').getall() if
                   header.strip() != '']
        raw_records = response.css('#curr_table tbody tr')

        # Iterate over each row and yield items
        for row in raw_records:
            td = row.css('td:not(.icon)')

            # Make sure to handle cases where some columns may be missing
            td_texts = td.css(' ::text').getall()

            item = OrderedDict()
            item['Name'] = td_texts[0] if len(td_texts) > 0 else None
            item['Bid'] = td_texts[1] if len(td_texts) > 1 else None
            item['Ask'] = td_texts[2] if len(td_texts) > 2 else None
            item['High'] = td_texts[3] if len(td_texts) > 3 else None
            item['Low'] = td_texts[4] if len(td_texts) > 4 else None
            item['Chg.'] = td_texts[5] if len(td_texts) > 5 else None
            item['Time'] = td_texts[6] if len(td_texts) > 6 else None

            # yield item  # Yield the item, not a request
            self.data.append(item)  # Collect the data into the list

    def close(self, reason):
        # When the spider finishes, write the data to an Excel file
        self.write_to_xlsx()

    def write_to_xlsx(self):
        # Ensure the output directory exists
        output_dir = 'Currency_Output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create a new Excel workbook and add a sheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Currency Data"

        # Write the headers to the first row
        headers = ['Name', 'Bid', 'Ask', 'High', 'Low', 'Chg.', 'Time']
        ws.append(headers)

        # Write the data rows
        for record in self.data:
            ws.append([record.get(header) for header in headers])

        # Save the workbook to a file
        filename = f'{output_dir}/EUR_USD_Currency_{datetime.now().strftime("%d%m%Y%H%M")}.xlsx'
        wb.save(filename)

        self.log(f"Data saved to {filename}")
        a=1


        # session_id = response._text.split("'session_uniq_id=")[1].split("&currencies=' + symbol+")[0]
        #
        # params = {
        #     'session_uniq_id': session_id,
        #     'currencies': '9',
        #     'table_width': '636',
        # }
        #
        # resp = requests.get('https://www.investing.com/center_forward_rates.php', params=params, cookies=self.cookies,
        #                         headers=self.headers)
        # # url = 'https://www.investing.com/center_forward_rates.php?session_uniq_id=e9f06e9abaa682c6f68f49bc0182afcc&currencies=9&table_width=636'
        # url = f'https://www.investing.com/center_forward_rates.php?session_uniq_id={session_id}&currencies=1&table_width=636'
        # file_name = 'EUR/USD.csv'
        # filename = os.path.join('TEAM', file_name)
        #
        # # Check if the file exists to append or create a new one
        # file_exists = os.path.isfile(filename)
        #
        # with open(filename, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
        #     csv_writer = csv.DictWriter(csvfile, fieldnames=self.team_csv_headers)
        #
        #     # Write headers if the file is new
        #     if not file_exists or csvfile.tell() == 0:
        #         csv_writer.writeheader()
        #
        #     # Write the player's data (ensure it's in the correct format)
        #     csv_writer.writerow(team_record)
        #
        #     # self.logger.info(f"Saved data for {item.get('Name')} to {filename}")
        #     print(f"Saved data for {team_name} to {filename}")
        #
        # yield Request(url='https://www.investing.com/center_forward_rates.php', body=json.dumps(params), headers=self.headers, cookies=self.cookies, callback=self.parse)


    # def parse(self, response, **kwargs):
    #     a=1

    def get_cookies(self):
        try:
            # Setup Chrome options for incognito mode
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Run browser in headless mode
            chrome_options.add_argument('--no-sandbox')  # Disable sandbox
            chrome_options.add_argument('--incognito')  # Enable incognito mode
            chrome_options.add_argument('--disable-dev-shm-usage')  # Disable /dev/shm usage for performance

            # Automatically download the appropriate ChromeDriver using webdriver-manager
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                           options=chrome_options)

            # Maximize the browser window
            self.driver.maximize_window()

            # Now you can proceed with your operations, such as navigating to a website
            print("Driver initialized successfully.")

            # Open the website
            self.driver.get(self.base_url)

            # Wait for the page to load completely
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script(
                    'return document.readyState') == 'complete' or 'session_uniq_id' in d.page_source
            )
            # sleep(10)
            # if 'session_uniq_id' in self.driver.page_source:
            #     print('id found')
            #     cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            #     return cookies
            #
            # sleep(10)
            # print("Page loaded or 'session_uniq_id' found.")


            #
            # # Wait until the "Search Type" dropdown is present
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.ID, "SearchCriteriaName1_DDL_SearchName"))
            # )
            # sleep(1)
            #
            # # Select "Deeds/Mortgages" from the "Office" dropdown
            # office_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaOffice1_DDL_OfficeName"))
            # office_dropdown.select_by_visible_text("Deeds/Mortgages")
            #
            # # Validate that "deeds" is selected
            # WebDriverWait(self.driver, 10).until(
            #     EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaOffice1_DDL_OfficeName"),
            #                                            "Deeds/Mortgages")
            # )
            #
            # sleep(3)
            #
            # # Select "Section Search" from the "Search Type" dropdown
            # search_type_dropdown = Select(self.driver.find_element(By.ID, "SearchCriteriaName1_DDL_SearchName"))
            # search_type_dropdown.select_by_visible_text("Section Search")
            #
            # # Validate that "Recorded Date Search" is selected
            # WebDriverWait(self.driver, 10).until(
            #     EC.text_to_be_present_in_element_value((By.ID, "SearchCriteriaName1_DDL_SearchName"),
            #                                            "Section Search")
            # )
            #
            # sleep(5)
            #
            # # Clear and set the "*Section" input
            # try:
            #     # Try to find the input field by its ID
            #     section_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Section")
            #     validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Section")
            # except NoSuchElementException:
            #     # If the input field by ID is not found, find it by name within the specified td
            #     section_input = self.driver.find_element(By.CLASS_NAME, "deftext")
            #     # from_date_input = from_date_cell.find_element(By.NAME, "SearchFormEx1$DRACSTextBox_DateFrom")
            #     validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Section")
            #
            # section_input.clear()
            # section_input.send_keys(self.search_section)
            #
            # # Validate that the value is set correctly
            # WebDriverWait(self.driver, 10).until(
            #     EC.text_to_be_present_in_element_value(validation_condition, self.search_section)
            # )
            #
            # sleep(1)
            #
            # # Clear and set the "Block" input
            # try:
            #     # Try to find the input field by its ID
            #     block_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Block")
            #     validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Block")
            # except NoSuchElementException:
            #     # If not found, try to find the input field by its name attribute
            #     block_input = self.driver.find_element(By.NAME, "SearchFormEx1$ACSTextBox_Block")
            #     validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Block")
            #
            # block_input.clear()
            # # to_date_input.send_keys("12/31/1910")
            # block_input.send_keys(self.search_block)
            #
            # # Validate that the value is set correctly
            # WebDriverWait(self.driver, 10).until(
            #     EC.text_to_be_present_in_element_value(validation_condition, self.search_block)
            # )
            #
            # sleep(1)
            #
            # # Clear and set the "Lot" input
            # try:
            #     # Try to find the input field by its ID
            #     lot_input = self.driver.find_element(By.ID, "SearchFormEx1_ACSTextBox_Lot")
            #     validation_condition = (By.ID, "SearchFormEx1_ACSTextBox_Lot")
            # except NoSuchElementException:
            #     # If not found, try to find the input field by its name attribute
            #     lot_input = self.driver.find_element(By.NAME, "SearchFormEx1$ACSTextBox_Lot")
            #     validation_condition = (By.NAME, "SearchFormEx1$ACSTextBox_Lot")
            #
            # lot_input.clear()
            # lot_input.send_keys(self.search_lot)
            #
            # # Validate that the value is set correctly
            # WebDriverWait(self.driver, 10).until(
            #     EC.text_to_be_present_in_element_value(validation_condition, self.search_lot)
            # )
            #
            # sleep(1)
            #
            # # Wait until the "Search" button is present
            # search_button = WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.ID, "SearchFormEx1_btnSearch"))
            # )
            #
            # # Click the "Search" button
            # search_button.click()
            #
            # cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            # sleep(4)
            #
            # if 'Search criteria resulted in 0 hits' in self.driver.page_source:
            #     self.write_logs(f'No Search results exist for {self.current_search} Years Range')
            #     self.driver.quit()
            #     # Return to spider_idle to continue with the next year
            #     self.spider_idle()
            #     return ''
            #
            # # Wait until the results are loaded and the page size selector is present
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.ID, "DocList1_PageView100Btn"))
            # )
            #
            # # Select the maximum number of results per page {100}
            # max_results_button = self.driver.find_element(By.ID, "DocList1_PageView100Btn")
            # max_results_button.click()
            #
            # sleep(3)
            #
            # # Get the total number of results
            # total_results_element = WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.ID, "SearchInfo1_ACSLabel_SearchResultCount"))
            # )
            #
            # if int(total_results_element.text) < 1000:
            #     self.current_search_total_results = int(total_results_element.text)

            # Retrieve cookies

            # Maximize the browser window
            self.driver.minimize_window()
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            return cookies

        except TimeoutException as e:
            return None


