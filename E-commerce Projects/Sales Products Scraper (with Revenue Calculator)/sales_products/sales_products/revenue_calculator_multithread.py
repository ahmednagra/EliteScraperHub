import csv
import glob
import os
import threading
import time
from datetime import datetime
from time import sleep
from collections import OrderedDict
import logging

from scrapy import Selector
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

from discord_webhook import DiscordWebhook, DiscordEmbed


class AmazonSpider:
    base_url = 'https://quotes.toscrape.com'

    def __init__(self, files_pair, logger, chunk=None, chunk_index=None, **kwargs):
        super().__init__(**kwargs)

        edge_options = Options()
        edge_options.use_chromium = True  # Use Chromium-based Edge
        msedgedriver_path = r'input\msedgedriver.exe'
        edge_options = EdgeOptions()
        edge_service = EdgeService(msedgedriver_path)
        self.driver = webdriver.Edge(service=edge_service, options=edge_options)
        # self.driver = webdriver.ChromiumEdge(service=ChromiumService(EdgeChromiumDriverManager().install()))
        self.driver.maximize_window()

        self.discord_webhook_url = self.read_config_file().get('discord_webhook_url', '')
        self.input_file_name = None
        self.error = False
        self.logger = logger

        if chunk:
            self.parse_detail(file_path=files_pair, chunk_rows=chunk, chunk_index=chunk_index)
        else:
            self.parse(files_pair)

    def parse(self, files_pair):
        # for file_path in files_pair:
        try:
            self.parse_detail(files_pair)

        except Exception as exc:
            self.logger.error(f"Error in parsing from Parse Method {files_pair}: {exc}")

    def parse_detail(self, file_path, chunk_rows=None, chunk_index=None):
        input_data = chunk_rows or self.read_input_file(file_path)
        file_base_name = os.path.splitext(os.path.basename(file_path))[0]
        file_name = f'{file_base_name} part{chunk_index}.csv' if chunk_index else os.path.basename(file_path)

        scraped_items = []
        rev_calc_file_path = f'output/Revenue Calculator/{file_name}'
        previous_rev_calculator_products = self.get_rev_calc_products(file_base_name)

        less_profit_skipped_items = []
        less_profit_file_path = f'output/Less Profit/{file_name}'
        previous_less_profit_products = self.get_less_profit_products(file_base_name)

        bad_asins_items = []
        bad_asin_file_path = f'output/Bad Asins/{file_name}'
        previous_bad_asin_products = self.get_bad_asin_products(file_base_name)

        is_file_written = False
        for index, row in enumerate(input_data):
            rows_processed_msg = f'{index+1}/{len(input_data)} Rows Processed in {file_path}'

            if not index % 20:
                write_info_logs(rows_processed_msg)

            if index and index % 10000 == 0:
                if not is_file_written:
                    mode = 'w'
                    is_file_written = True
                else:
                    mode = 'a'

                self.write_to_csv(scraped_items, rev_calc_file_path, mode=mode)
                self.write_to_csv(less_profit_skipped_items, less_profit_file_path, mode=mode)
                self.write_bad_asins_to_csv(bad_asins_items, bad_asin_file_path, mode=mode)

                scraped_items = []
                bad_asins_items = []
                less_profit_skipped_items = []

            try:
                title = row.get('Product Title', '')
                ean = row.get('EAN', '')
                search_key = title if 'telekom.de' in row.get('URL', '') else ean

                price = row.get('Price', '') or '0.0'
                price = self.get_float_price(price)

                if not price:
                    continue

                cost_of_goods_sold = str(round(price / 1.19, 2)).replace('.', ',')

                # Skip Revenue Clac Products if the EAN already exists in previous file with the Same price
                if self.is_product_already_scraped(search_key, price, previous_rev_calculator_products, ):
                    scraped_items.append(previous_rev_calculator_products[search_key])
                    write_info_logs(
                        f'Product Skipped. Already exists in Revenue Calculator file with same price: {search_key}, - File: {rev_calc_file_path}')
                    continue

                #  Skip Less 10% Profit Products  if the EAN already exists in less profit file with the Same price
                if self.is_product_already_scraped(search_key, price, previous_less_profit_products):
                    less_profit_skipped_items.append(previous_less_profit_products[search_key])
                    write_info_logs(
                        f'Product Skipped. Already exists in less Profit file with same price: {search_key}, - File: {less_profit_file_path}')
                    continue

                #  Skip Bad Asins Products  if the EAN already exists in Bad Asin File with the Same price
                if self.is_product_already_scraped(search_key, price, previous_bad_asin_products):
                    bad_asins_items.append(previous_bad_asin_products[search_key])
                    write_info_logs(
                        f'Product Skipped. Already exists in Bad Asin file with same price: {search_key}, - File: {less_profit_file_path}')
                    continue

                self.driver.get('https://sellercentral.amazon.fr/hz/fba/profitabilitycalculator/index?lang=de_DE')
                sleep(3)

                guest_button_selector = 'kat-button.spacing-top-small'

                if self.is_element_exist(guest_button_selector):
                    self.driver.find_element(By.CSS_SELECTOR, guest_button_selector).click()
                    sleep(1)

                drop_down_selector = 'kat-tab #ProductSearchInput .dropdown-country'

                if not self.is_element_exist(drop_down_selector):
                    self.logger.error(f'Drop Down Element not found EAN :{ean}, - File: {file_path}')
                    self.error = True
                    continue

                sleep(1)
                self.driver.find_element(By.CSS_SELECTOR, drop_down_selector).click()
                sleep(1)

                select_country_selector = 'kat-option[value="DE"]'
                if not self.is_element_exist(css_selector=select_country_selector):
                    self.logger.error(f'Select Country Element not found EAN :{ean}, - File: {file_path}')
                    self.error = True

                    continue

                self.driver.find_element(By.CSS_SELECTOR, select_country_selector).click()
                sleep(2)

                input_asin_selector = 'kat-input.input-asin'

                if not self.is_element_exist(input_asin_selector, timeout=50):
                    self.logger.error(f'Input ASIN Element not found')
                    self.error = True

                    continue

                input_asin_field = self.driver.find_element(By.CSS_SELECTOR, input_asin_selector)
                input_asin_field.send_keys(search_key)
                time.sleep(3)

                input_asin_field.send_keys(Keys.ENTER)
                time.sleep(3)

                no_products_alert_selector = 'kat-alert[description]'
                item_ean = search_key

                if self.is_element_exist(no_products_alert_selector, timeout=3):
                    write_info_logs(f'No Products Found against EAN: {search_key}, - File: {file_path}')
                    bad_asins_items.append(row)
                    continue

                product_select_btn_selector = 'kat-button.select-button'

                # Select first product if there are many, otherwise the single product will be selected automatically
                if self.is_element_exist(product_select_btn_selector, timeout=5):
                    self.driver.find_element(By.CSS_SELECTOR, product_select_btn_selector).click()
                    sleep(2)

                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                time.sleep(2)

                enter_cost_of_sold_goods_selector = 'kat-input[unique-id="katal-id-29"]'

                try:
                    x = self.driver.find_element(By.CSS_SELECTOR,
                                                 enter_cost_of_sold_goods_selector).location_once_scrolled_into_view
                except:
                    pass

                if not self.is_element_exist(enter_cost_of_sold_goods_selector, timeout=50):
                    self.logger.error(f'Cost Of Sold Goods Element not found')
                    self.error = True

                    continue

                input_cost_field = self.driver.find_element(By.CSS_SELECTOR, enter_cost_of_sold_goods_selector)
                input_cost_field.send_keys(cost_of_goods_sold)
                sleep(3)

                response_sel = Selector(text=self.driver.page_source)

                net_profit = response_sel.css('kat-label[text="Nettogewinn"] + kat-label::attr(text)').get(
                    '').replace(',', '.').replace('€', '').strip('%')

                net_profit_float = self.get_float_price(net_profit)

                item = OrderedDict()
                item['EAN'] = item_ean
                item['Price'] = price
                item['ASIN'] = response_sel.css('kat-tab tbody tr td + td ::text').get('')
                item['Sales Rank'] = response_sel.css(
                    '#product-detail-right tbody tr + tr + tr td+td ::text').get('')
                item['Net Profit'] = net_profit
                item['Net Margin'] = response_sel.css(
                    'kat-label[text="Nettospanne"] + kat-label::attr(text)').get(
                    '')

                # Skip product if the Net Profit is less than 10%
                if net_profit_float <= 10:
                    write_info_logs(f'profit less then 10% of the EAN :{item_ean}, - File: {file_path}')
                    less_profit_skipped_items.append(item)
                    continue
                write_info_logs(f'Product profit More then 10% of the EAN :{item_ean}, - File: {file_path}')
                scraped_items.append(item)

            except WebDriverException:
                continue

            except Exception as exc:
                self.logger.error(f"Error in parsing from Parse Detail Method {file_path}, EAN: {ean}: {exc}")
                continue

        if not is_file_written:
            mode = 'w'
            self.write_to_csv(scraped_items, rev_calc_file_path, mode=mode)
            self.write_to_csv(less_profit_skipped_items, less_profit_file_path, mode=mode)
            self.write_bad_asins_to_csv(bad_asins_items, bad_asin_file_path, mode=mode)

        # self.send_to_discord(rev_calc_file_path, scraped_items, chunk_index=chunk_index)
        self.send_to_discord(rev_calc_file_path, scraped_items)
        sleep(3)

    def get_bad_asin_products(self, file_base_name):
        bad_asin_csv_files = glob.glob(f'output/Bad Asins/{file_base_name}*.csv')
        bad_asin_products = {}

        for file_path in bad_asin_csv_files:
            bad_asin_products.update(self.get_previous_revenue_products_from_csv(file_path))

        return bad_asin_products

    def get_rev_calc_products(self, file_base_name):
        rev_calc_csv_files = glob.glob(f'output/Revenue Calculator/{file_base_name}*.csv')
        rev_calc_products = {}

        for file_path in rev_calc_csv_files:
            rev_calc_products.update(self.get_previous_revenue_products_from_csv(file_path))

        return rev_calc_products

    def get_less_profit_products(self, file_base_name):
        less_profit_csv_files = glob.glob(f'output/Less Profit/{file_base_name}*.csv')
        less_profit_products = {}

        for file_path in less_profit_csv_files:
            less_profit_products.update(self.get_previous_revenue_products_from_csv(file_path))

        return less_profit_products

    def get_previous_revenue_products_from_csv(self, file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                products = list(csv.DictReader(csv_file))
                # if its a telecom.de file,then the Key will be Title instead of EAN as EAN in telecom.de is not correct
                return {product.get('EAN', '').strip() if 'telekom.de' not in product.get('URL', '') else product.get(
                    'Product Title', ''): product for product in products}
        except FileNotFoundError:
            return {}

    def is_element_exist(self, css_selector, timeout=100):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, css_selector)))
            return True

        except (NoSuchElementException, TimeoutException):
            return False

    def get_float_price(self, price_str):
        price_str = price_str.replace(',', '.')

        if price_str.count('.') > 1:
            price_str = price_str.replace('.', '', 1)

        try:
            return float(price_str)
        except ValueError:
            return None

    def send_to_discord(self, file_path, is_items_scraped):
        if not is_items_scraped:
            self.upload_discord_empty_file_message(file_path)

        else:
            webhook = DiscordWebhook(url=self.discord_webhook_url, username="Python Bot")
            file_name = os.path.splitext(os.path.basename(file_path))[0]  # Remove extension
            current_time = datetime.now().strftime("%d%m%Y%H%M%S")
            new_file_name = f"{file_name}_{current_time}.csv"

            with open(file_path, "rb") as f:
                webhook.add_file(file=f.read(), filename=new_file_name)

            response = webhook.execute()

            if response.status_code == 200:
                write_info_logs(f"File '{file_name}' uploaded successfully!")

            else:
                self.logger.error(f"Failed to upload the file '{file_name}'. Status code: {response.status_code}")
                print(f"Failed to upload the file '{file_name}'. Status code: {response.status_code}")

    def read_input_file(self, file_name):
        self.input_file_name = file_name
        with open(file_name, mode='r', encoding='utf8') as input_file:
            return list(csv.DictReader(input_file))

    def write_to_csv(self, scraped_items, revenue_calc_file, mode='a'):
        if not scraped_items:
            return

        with open(revenue_calc_file, mode=mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile,
                                    fieldnames=['EAN', 'Price', 'ASIN', 'Sales Rank', 'Net Profit', 'Net Margin'])

            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerows(scraped_items)

    def write_bad_asins_to_csv(self, bad_asins_items, bad_asin_path, mode='a'):

        with open(bad_asin_path, mode=mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile,
                                    fieldnames=['Product Title', 'Price', 'EAN', 'URL'])

            if csvfile.tell() == 0:
                writer.writeheader()

            writer.writerows(bad_asins_items)

    def upload_discord_empty_file_message(self, file_path):
        webhook = DiscordWebhook(url=self.discord_webhook_url, username="Python Bot")
        file_name = os.path.basename(file_path)
        payload = f"From {file_name} not matched any record from Amazon Revenue Calculator."
        webhook.add_embed(DiscordEmbed(description=payload))
        write_info_logs(f'{file_name} uploaded the empty file record to discord successfully')
        webhook.execute()

    def is_product_already_scraped(self, search_keyword, current_price, products):
        """
        - If a product (EAN) already exists in the file and if it's price is the same as the input price,
         Then we will not recheck that product in revenue calculator

        """

        previous_product = products.get(search_keyword, {})

        if not previous_product:
            return False

        previous_price = self.get_float_price(previous_product.get('Price', ''))

        if not previous_price:
            return False

        if current_price == previous_price:
            return True

        return False

    def read_config_file(self):

        file_path = 'input/config.txt'
        config = {}
        try:
            with open(file_path, mode='r') as txt_file:
                for line in txt_file:
                    line = line.strip()
                    if line and '==' in line:
                        key, value = line.split('==', 1)
                        config[key.strip()] = value.strip()

            return config

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []


def create_logger(name, level=logging.ERROR, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def read_input_file():
    input_file = 'input/scraper_status.csv'

    with open(input_file, mode='r', encoding='utf8') as input_file:
        return list(csv.DictReader(input_file))


def write_info_logs(log_message, mode='a'):
    with open("spiders/info_logs.txt", mode=mode) as txt_file:
        print(log_message)
        txt_file.write(f"{datetime.now()} -> {log_message}\n")


def worker(files_pair, logger, chunk=None, chunk_index=None):
    AmazonSpider(files_pair, logger, chunk, chunk_index)

def create_chunks(lst, num_chunks):
    chunk_size = len(lst) // num_chunks
    remainder = len(lst) % num_chunks
    chunked_list = []
    index = 0

    for _ in range(num_chunks):
        sublist_size = chunk_size + int(remainder > 0)
        sublist = lst[index:index + sublist_size]
        chunked_list.append(sublist)
        index += sublist_size
        remainder -= 1

    return chunked_list


def get_rows_from_input_file(file_name):
    with open(file_name, mode='r', encoding='utf8') as input_file:
        return list(csv.DictReader(input_file))


def process_file_pair(file_name, logger):
    threads = []

    # for file_name in files_pair:
    input_rows = get_rows_from_input_file(file_name)
    num_of_threads = 3
    chunks = create_chunks(input_rows, num_of_threads)

    write_info_logs(f'Total number of Rows in {file_name}: {len(input_rows)}')
    write_info_logs(f'Total Threads for Rows: {num_of_threads}')
    write_info_logs(
        f'Rows equally distributed among {num_of_threads} Threads to process their own list independently')

    for index, chunk in enumerate(chunks):

        t = threading.Thread(target=worker, args=(file_name, logger, chunk, index+1))
        threads.append(t)
        t.start()

    # Wait for all threads processing rows within files to complete
    for t in threads:
        t.join()


def main():
    logger = create_logger("error_logger", level=logging.ERROR, log_file="spiders/error.log")
    write_info_logs('Started!')
    csv_rows = read_input_file()
    dont_run_rev_calculator = [row['SpiderName'].strip() for row in csv_rows if
                               'true' not in row.get('Process', '').lower()]

    file_names = glob.glob('output/*.csv')

    filtered_filenames = [filename for filename in file_names if
                          any(name in filename for name in dont_run_rev_calculator)]

    filenames = [filename for filename in file_names if filename not in filtered_filenames]

    pairs = [filenames[i:i + 2] for i in range(0, len(filenames), 2)]
    # pairs = [[filename] for filename in filenames]

    num_of_threads = len(pairs)

    write_info_logs(f'Total number of File Pairs: {len(pairs)}')
    write_info_logs(f'Total Threads: {num_of_threads}')
    write_info_logs(f'Pairs of Files: {pairs}')

    threads = []

    for files_pair in pairs:
        for file in files_pair:
            keywords = ['flaconi', 'fahrrad', 'fahrrad_xxl']
            if any(keyword in file for keyword in keywords):
                t = threading.Thread(target=process_file_pair, args=(file, logger))
            else:
                t = threading.Thread(target=worker, args=(file, logger))
            threads.append(t)
            t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()


if __name__ == '__main__':
    main()
