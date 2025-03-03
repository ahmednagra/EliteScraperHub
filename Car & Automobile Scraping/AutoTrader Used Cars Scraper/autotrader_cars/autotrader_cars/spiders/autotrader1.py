import csv
import json
from collections import OrderedDict
from datetime import datetime
from time import sleep
import threading

import requests
from scrapy import Spider, Request, signals


class AutotraderSpider(Spider):
    name = 'autotrader'
    base_url = 'https://www.autotrader.com/'

    csv_headers = ['Title', 'Make', 'Model', 'Year', 'Vin', 'Location', 'Condition', 'Price', 'Average Market Price',
                   'Main Image', 'Options', 'Mileage', 'Trim', 'Color', 'Body Type', 'Fuel Type', 'Engine',
                   'Drive Train', 'City Fuel Economy', 'Highway Fuel Economy', 'Combined Fuel Economy', 'Dealer Name',
                   'Dealer City', 'Dealer State', 'Dealer Zip', 'Dealer Rating', 'Dealer Phone', 'URL', 'Status',
                   'Scraped Date']

    custom_settings = {

        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 3,

        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
    }

    headers = {
        'authority': 'www.autotrader.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_start_datetime_str = kwargs.get(
            'dt')  # Get the datetime object from the main.py file to make the time same for both the spiders
        self.start_time = self.main_start_datetime_str

        print('start time :', self.start_time)

        self.csv_lock = threading.Lock()
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.start_time}"\n']
        self.logs_filename = f'logs/logs {self.main_start_datetime_str}.txt'
        self.output_filename = f'output/Autotrader Used Cars {self.main_start_datetime_str}.csv'  # This file is created with headers row inside the main.py file with exact name. If the name required to change, then it should be changed there as well

        self.unwanted_makes = []
        self.unwanted_models = []
        self.unwanted_years = []
        self.set_unwanted_makesModlesYears()  # assign above three unwanted variables values

        self.error_in_filter = []
        self.skipped_cars = 0
        self.makes = None
        self.blocked_urls = []

        self.current_scraped_items_p_ids = []
        self.make_wise_current_items = []  # it contains the current single make items and will be empty in idle method
        self.all_current_scraped_items = []  # it will contain all maker items and will carry them till the end
        self.scraped_product_counter = 0

    def start_requests(self):
        yield Request(url=self.base_url, headers=self.headers)

    def parse(self, response, **kwargs):
        makes = self.get_makes_names(response)
        self.makes = makes[:35]  # Next makes are processing in the other spider

    def get_makes_names(self, response):
        makes = response.css('[label="All Makes"] option')

        # Remove those makes which are added inside the unwanted.txt file

        filtered_makes = []

        for make in makes:
            make_value = make.css('::attr(value)').get('')
            make_name = make.css('::attr(label)').get('').lower()

            if make_name in self.unwanted_makes:
                self.mandatory_logs.append(f'Make "{make_name}" Skipped as it was added inside the unwanted.txt file')
                continue

            filtered_makes.append(make_value)

        return filtered_makes

    def search_make(self, response):
        maker = self.makes.pop(0)
        self.mandatory_logs.append(f'Searching make "{maker}" for Cars to scrape')

        url = f'https://www.autotrader.com/rest/lsc/listing?makeCode={maker}&firstRecord=0&newSearch=false&numRecords=2000&listingType=USED'
        yield Request(url=url, headers=self.headers, callback=self.parse_by_makes, meta={'make': maker})

    def parse_by_makes(self, response):
        make = response.meta.get('make')
        json_data, total_results = self.get_json_data(response)

        self.mandatory_logs.append(f'Make "{make}" have total "{total_results}" Used cars on web')

        if total_results > 2000:
            url = f'https://www.autotrader.com/collections/ccServices/rest/ccs/models?makeCode={make}'
            yield Request(url=url, headers=self.headers, callback=self.parse_by_models,
                          meta={'search_url': response.url})
        else:
            yield from self.parse_products(json_data)

    def parse_by_models(self, response):
        json_data, total_results = self.get_json_data(response)

        try:
            maker_models = {model.get('label', '').replace('-', '').strip().lower(): model.get('value') for model in
                            json_data if model.get('value')}
        except:
            maker_models = {}

        for model_label, model_value in maker_models.items():
            # Skip those models which are added inside the unwanted.txt file. Those models are not needed to scrape
            if model_label in self.unwanted_models:
                self.logger.info(f'\n\nSkipped {model_label} Model\n')
                self.mandatory_logs.append(
                    f'Model "{model_label.title()}" Skipped as it was added inside the unwanted.txt file')
                continue

            url = f'{response.meta.get("search_url")}&modelCode={model_value}'
            yield Request(url=url, headers=self.headers, callback=self.parse_by_years)

    def parse_by_years(self, response):
        json_data, total_results = self.get_json_data(response)

        if total_results > 2000:
            try:
                year_range = [year.get('value', '') for year in
                              json_data.get('filters', {}).get('yearRange', {}).get('options') if year.get('value')]
            except:
                self.error_in_filter.append(response.url)
                year_range = []

                yield from self.parse_products(json_data)

            for year in year_range:

                if year == '0':
                    continue

                # Skip those years which are added inside the unwanted.txt file. Those models are not needed to scrape
                if str(year) in self.unwanted_years:
                    self.mandatory_logs.append(f'Year "{year}" Skipped as it was added inside the unwanted.txt file')
                    continue

                yield Request(url=f'{response.url}&endYear={year}&startYear={year}', headers=self.headers,
                              callback=self.parse_by_colors)
        else:
            yield from self.parse_products(json_data)

    def parse_by_colors(self, response):
        json_data, total_results = self.get_json_data(response)

        if total_results > 2000:
            try:
                colors = [color.get('value') for color in
                          json_data.get('filters', {}).get('extColorSimple', {}).get('options', [{}])]
            except:
                self.error_in_filter.append(response.url)
                colors = []
                yield from self.parse_products(json_data)

            for color in colors:
                url = f"{response.url}&extColorSimple={color}"
                yield Request(url=url, headers=self.headers, callback=self.parse_by_body_styles)
        else:
            yield from self.parse_products(json_data)

    def parse_by_body_styles(self, response):
        json_data, total_results = self.get_json_data(response)

        if total_results > 2000:
            try:
                body_styles = [option.get('value') for option in
                               json_data.get('filters', {}).get('vehicleStyleCode', {}).get('options')]
            except:
                self.error_in_filter.append(response.url)
                body_styles = []
                yield from self.parse_products(json_data)

            for style in body_styles:
                url = f"{response.url}&vehicleStyleCode={style}"
                yield Request(url=url, headers=self.headers, callback=self.parse_by_fuel_type)

        else:
            yield from self.parse_products(json_data)

    def parse_by_fuel_type(self, response):
        json_data, total_results = self.get_json_data(response)

        if total_results > 2000:
            try:
                fuel_types = [option.get('value') for option in
                              json_data.get('filters', {}).get('fuelTypeGroup', {}).get('options')]
            except:
                self.error_in_filter.append(response.url)
                fuel_types = []
                yield from self.parse_products(json_data)

            for f_type in fuel_types:
                url = f"{response.url}&fuelTypeGroup={f_type}"
                yield Request(url=url, headers=self.headers, callback=self.parse_by_engine_displacement)

        else:
            yield from self.parse_products(json_data)

    def parse_by_engine_displacement(self, response):
        json_data, total_results = self.get_json_data(response)
        if total_results > 2000:

            engine_displacement = [option.get('value') for option in
                                   json_data.get('filters', {}).get('engineDisplacement', {}).get('options')]
            for engine_dis in engine_displacement:
                url = f"{response.url}&engineDisplacement={engine_dis}"
                yield Request(url=url, headers=self.headers, callback=self.parse_cars)

        else:
            yield from self.parse_products(json_data)

    def parse_cars(self, response):
        json_data, total_results = self.get_json_data(response)
        if total_results > 2000:
            for sort_option in ['derivedpriceASC', 'derivedpriceDESC']:
                url = f"{response.url}&sortBy={sort_option}"
                yield Request(url=url, headers=self.headers, callback=self.parse_by_price_sorting)
        else:
            yield from self.parse_products(json_data)

    def parse_by_price_sorting(self, response):
        json_data, total_results = self.get_json_data(response)
        yield from self.parse_products(json_data)

    def parse_products(self, json_data):
        products = json_data.get('listings', [])

        if not products:
            return

        for product in products:
            try:
                # Extract basic information from the JSON data
                p_id = product.get('id', '')
                if p_id in self.current_scraped_items_p_ids:
                    self.skipped_cars += 1
                    # print(f'{p_id} already Exist')
                    continue

                make = product.get('make', {}).get('name', '')
                model = product.get('model', {}).get('name', '')
                year = str(product.get('year', 0))

                model = model.replace(str(make), '').replace(year, '').strip()

                if make.lower() in self.unwanted_makes:
                    self.mandatory_logs.append(f'Make "{make}" Skipped as it was added inside the unwanted.txt file')
                    continue

                if model.replace('-', '').strip().lower() in self.unwanted_models:
                    self.mandatory_logs.append(f'Model "{model}" Skipped as it was added inside the unwanted.txt file')
                    continue

                if year in self.unwanted_years:
                    # self.mandatory_logs.append(f'Year "{year}" Skipped as it was added inside the unwanted.txt file')
                    continue

                condition = product.get('listingTypes', {})
                if condition:
                    condition = product.get('listingTypes', {})[0].get('name', '') or product.get('listingType', '')

                price = product.get('pricingDetail', {}).get('salePrice', 0)
                avg_market_price = product.get('pricingDetail', {}).get('kbbFppAmount', 0.0)
                milage = product.get('mileage', {}).get('value', '').strip()

                # Extract specific specifications
                body_styles = product.get('bodyStyles', [])
                if body_styles:
                    body_type = body_styles[0].get('code', '')
                else:
                    body_type = ''

                city_fuel = product.get('mpgCity', 0)
                highway_fuel = product.get('mpgHighway', 0)

                # Create an ordered dictionary to store item data
                item = OrderedDict()
                item['Title'] = product.get('title', '').replace(year, '').replace(condition, '').strip()
                item['Make'] = make
                item['Model'] = model
                item['Year'] = year if year else ''
                item['Vin'] = product.get('vin', '')

                # Populate additional fields
                item['Location'] = ''
                item['Condition'] = condition
                item['Price'] = price if price else ''
                item['Average Market Price'] = avg_market_price if avg_market_price else ''
                item['Main Image'] = ''.join(
                    [img.get('src', '') for img in product.get('images', {}).get('sources', [{}])][:1])
                item['Options'] = self.get_options(product)
                item['Mileage'] = milage if milage else ''
                item['Trim'] = product.get('trim', {}).get('code', '')
                item['Color'] = product.get('color', {}).get('exteriorColor', '')
                item['Body Type'] = body_type
                item['Fuel Type'] = product.get('fuelType', {}).get('name', '')
                item['Engine'] = product.get('engine', {}).get('name', '')
                item['Drive Train'] = product.get('driveType', {}).get('description', '')
                item['City Fuel Economy'] = city_fuel if city_fuel else ''
                item['Highway Fuel Economy'] = highway_fuel if highway_fuel else ''
                item['Combined Fuel Economy'] = ''

                # Extract dealer information
                dealer_address = product.get('owner', {}).get('location', {}).get('address', {})
                dealer_rating = product.get('owner', {}).get('rating', {}).get('value', 0.0)
                item['Dealer Name'] = product.get('owner', {}).get('name', '')
                item['Dealer City'] = dealer_address.get('city', '').strip()
                item['Dealer State'] = dealer_address.get('state', '')
                item['Dealer Zip'] = dealer_address.get('zip', '')
                item['Dealer Rating'] = dealer_rating if dealer_rating else ''
                item['Dealer Phone'] = product.get('owner', {}).get('phone', {}).get('value', '')
                item['URL'] = f'https://www.autotrader.com/cars-for-sale/vehicle/{p_id}'
                item['Status'] = product.get('pricingDetail', {}).get('dealIndicator', '')
                item['Scraped Date'] = self.main_start_datetime_str

                self.scraped_product_counter += 1
                print('Current Scraped Items Counter :', self.scraped_product_counter)
                self.current_scraped_items_p_ids.append(p_id)

                self.make_wise_current_items.append(item)
                self.all_current_scraped_items.append(item)
                # All the items for one complete make will be written into the output file at once inside idle methods

                yield item

            except:
                continue

    def get_options(self, product):
        specifications = product.get('specifications', {})
        options_string = ""

        for key, value in specifications.items():
            label = value.get('label', '')
            option_value = value.get('value', '')
            option_string = f"{label}: {option_value}"
            options_string += f"{key.title()} = [{option_string}]\n"

        return options_string.strip()

    def get_json_data(self, response):
        try:
            json_data = json.loads(response.text)
        except:
            # resp = requests.get(response.url, headers=self.headers)
            resp = self.retry_request(response.url)

            try:
                json_data = json.loads(resp.text)
            except:
                json_data = {}
                self.blocked_urls.append(response.url)

        try:
            total_results = json_data.get('totalResultCount', 0)
        except:
            total_results = 0

        return json_data, total_results

    def get_unwantedcarsfilters_from_file(self):
        try:
            with open(r'input\unwanted.txt', mode='r', encoding='utf-8') as input_file:
                data = {}

                for row in input_file.readlines():
                    if not row.strip():
                        continue

                    try:
                        key, value = row.strip().split('==')
                        data.setdefault(key.strip(), value.strip())
                    except ValueError:
                        pass

                return data
        except FileNotFoundError:
            return {}

    def set_unwanted_makesModlesYears(self):
        unwanted_cars_filters = self.get_unwantedcarsfilters_from_file()
        self.unwanted_makes = [maker.lower() for maker in unwanted_cars_filters.get('makes', '').split(',')]
        self.unwanted_models = [model.replace('-', '').lower().strip() for model in
                                unwanted_cars_filters.get('models', '').split(
                                    ',')]  # same format will be used where this model comparing
        self.unwanted_years = self.get_unwanted_years(unwanted_cars_filters.get('years', ''))

        self.mandatory_logs.append(f'Unwanted Makes to Skip: {", ".join(self.unwanted_makes)}')
        self.mandatory_logs.append(f'Unwanted Models to Skip: {", ".join(self.unwanted_models)}')
        self.mandatory_logs.append(f'Unwanted Years to Skip: {", ".join(self.unwanted_years)}\n\n')

    def get_unwanted_years(self, years_string):
        """
        - Separate the years based on comma
        - If there is a range set between any years with dash (-), then calculate those years in range
        - For example, user has put year in this format in the unwanted.txt file: "2000,2010,2017-2020, 2023"
            - The script should consider it these years: "2000,2010,2017,2018,2019,2020,2023"

        """

        unwanted_years = []

        years = years_string.split(',')

        for year in years:
            if '-' in year:
                start, end = map(int, year.split('-'))
                unwanted_years.extend(range(start, end + 1))
            else:
                unwanted_years.append(year)

        return [str(year) for year in unwanted_years]

    def retry_request(self, url):
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                # print(f"Attempt {attempt} failed. Retrying in 2 seconds. Error: {e}")
                sleep(2)

        raise Exception(f"Max retry attempts reached for URL: {url}")

    def write_item_into_csv(self, filename, rows):
        # File already through in main.py file with Header row
        if not rows:
            return

        # Acquire a file lock
        try:
            with self.csv_lock:  # Check with the Lock
                with open(filename, mode='a', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=self.csv_headers)

                    # # HEADER ROW ALREADY INSERTED INSIDE THE MAIN FILE
                    # # Check if the file is empty (no headers)
                    # csv_file.seek(0, 2)  # Move to the end of the file
                    # file_empty = csv_file.tell() == 0
                    #
                    # if file_empty:
                    #     # Write headers only if the file is empty
                    #     writer.writeheader()

                    # Write data to CSV
                    writer.writerows(rows)

        except:
            self.error_in_filter.append('Error in Adding Sold cars to Master File')

    def write_logs(self):
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                # print(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

        self.mandatory_logs = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AutotraderSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        # after every maker complete scraping, then write scraped items into csv file
        if self.make_wise_current_items:
            self.write_item_into_csv(filename=self.output_filename, rows=self.make_wise_current_items)
            self.make_wise_current_items = []  # after writing current scraped items into file then empty the list container

            self.write_logs()

        if self.makes:

            req = Request(url=self.base_url,
                          callback=self.search_make,
                          dont_filter=True,
                          headers=self.headers,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):

        spider.mandatory_logs.append(
            f'Total "{spider.scraped_product_counter}" Cars scraped for spider "{spider.name}"')
        spider.mandatory_logs.append(f'Total "{spider.skipped_cars}" Duplicate Cars Skipped for spider "{spider.name}"')

        spider.mandatory_logs.append(f'Spider "{spider.name}" was started at "{spider.start_time}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')

        if spider.error_in_filter:
            spider.mandatory_logs.append(f'\n\nERRORS in spider "{spider.name}"\n')
            spider.mandatory_logs += spider.error_in_filter  # Add all the errors in the logs list and then write into file

        spider.write_logs()
