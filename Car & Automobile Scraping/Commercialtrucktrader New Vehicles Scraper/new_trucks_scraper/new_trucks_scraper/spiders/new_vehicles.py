import os
import csv
import json
import random
from math import ceil
from datetime import datetime
from collections import OrderedDict
from urllib.parse import unquote
import requests

from scrapy import Spider, Request, signals


class TruckTradeSpider(Spider):
    name = "new_vehicles"
    base_urls = 'https://www.commercialtrucktrader.com/'
    start_urls = ["https://www.commercialtrucktrader.com/dealers/"]

    csv_headers = ['Title', 'Make', 'Model', 'Year', 'Vin',
                   'Location', 'Condition', 'Price',
                   'Average Market Price', 'Main Image', 'Options',
                   'Mileage', 'Trim', 'Color', 'Body Type', 'Fuel Type', 'Engine',
                   'Deal Rating', 'Days on Market', 'Drive Train', 'City Fuel Economy',
                   'Highway Fuel Economy', 'Combined Fuel Economy', 'Dealer Name',
                   'Dealer City', 'Dealer State', 'Dealer Zip', 'Dealer Phone', 'Dealer Rating',
                   'URL', 'Scraped Date']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
    }

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.state_name = ''
        self.all_vehicles_count = 0
        self.state_vehicles_count = 0
        self.new_scraped_vehicles_counter = 0

        self.errors = []
        self.states_urls = []
        self.duplicates_urls = []
        self.current_scraped_items = []

        self.current_date_time = datetime.now().strftime("%Y-%m-%d %H%M%S")
        self.mandatory_logs = []

        self.used_output_filename = f'output/New Commercial Trucks Details {self.current_date_time}.csv'
        self.previously_scraped_items = {item.get('URL'): item for item in self.get_previous_scarped_cars_from_file()}

        self.config = self.read_input_file(file_path='input/scrapeops_proxy_key.txt', file_type='config')
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('use_proxy', '')
        a=1

    def start_requests(self):
        yield Request(url=self.start_urls[0],
                      callback=self.parse,
                      meta={'handle_httpstatus_list': [400, 401, 429]})

    def parse(self, response, **kwargs):
        # Extract state URLs from the webpage
        states_urls = response.css('.list-unstyled.lfloat a::attr(href)').getall()

        # Log the total number of states found
        self.mandatory_logs.append(f'Total States found in the website : {len(states_urls)}\n')

        if not states_urls:
            self.mandatory_logs.append('No states found')
            return

        # Add the extracted state URLs to the list
        self.states_urls.extend(states_urls)

    def pagination(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.errors.append(f'Json Parsing Error State : {self.state_name}\n')
            return

        dealers = data.get('meta', {}).get('page', {}).get('total_results', 0)
        self.mandatory_logs.append(f'Total No of Dealers: "{dealers}" exists in the state : "{self.state_name}"\n')

        # Limitation Check condition
        if len(str(dealers)) >= 2400:
            self.errors.append(f"Found More Than 2400 Dealers url:{''.join(unquote(''.join(unquote(response.url).split('url=')[1:])).split('url=')[1:])}")
            return

        if not dealers:
            self.mandatory_logs.append(f'No dealer found on the State: {self.state_name} ')
            return

        total_pages = ceil(dealers / 24)
        # self.mandatory_logs.append(f'Found {dealers} dealers in state "{self.state_name}"\n')

        for page_no in range(1, total_pages + 1):
            url = f"{''.join(unquote(response.url).split('url=')[1:])}&page={page_no}"
            yield Request(url=url, callback=self.parse_dealers, meta=response.meta)

    def parse_dealers(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.errors.append(f"Json Parsing Error Parse Dealers : {''.join(unquote(''.join(unquote(response.url).split('url=')[1:])).split('url=')[1:])}\n")
            return

        dealers = data.get('results', {})

        for dealer in dealers:
            d_id = dealer.get('id', {}).get('raw', '')
            d_name = dealer.get('name', {}).get('raw', '')
            url = f'{self.base_urls}search-results-data?dealerid={d_id}&condition=N&dealer_id={d_id}&priceFilterType=cash'
            response.meta['dealer_name'] = d_name
            response.meta['dealer_id'] = d_id
            yield Request(url=url, callback=self.parse_dealer_vehicles_pagination, meta=response.meta)

    def parse_dealer_vehicles_pagination(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.errors.append(f"Json Parsing Error parse_dealer_vehicles_pagination: {''.join(unquote(''.join(unquote(response.url).split('url=')[1:])).split('url=')[1:])}\n")
            return

        dealer_vehicles = data.get('meta', {}).get('page', {}).get('total_results', 0)
        self.all_vehicles_count += int(dealer_vehicles)
        self.state_vehicles_count += int(dealer_vehicles)
        print(f'State : "{self.state_name} Vehicles Count : {self.state_vehicles_count}')
        print(f'Total Vehicles Counter : {self.all_vehicles_count}')

        if not dealer_vehicles:
            self.mandatory_logs.append(
                f'State: "{self.state_name}", Dealer Name: "{response.meta.get("dealer_name")}" has no vehicles')
            return

        self.mandatory_logs.append(
            f'State: "{self.state_name}", Dealer Name: "{response.meta.get("dealer_name")}" has {dealer_vehicles} vehicles')

        if dealer_vehicles <= 38:
            yield from self.parse_dealer_vehicles(response)
        else:
            dealer_id = response.meta.get('dealer_id', '')
            total_pages = ceil(dealer_vehicles / 38)
            for page_no in range(1, total_pages + 1):
                page_no = 1
                url = f'{self.base_urls}search-results-data?dealerid={dealer_id}&page={page_no}&condition=N&dealer_id={dealer_id}&priceFilterType=cash'
                yield Request(url=url, callback=self.parse_dealer_vehicles, meta=response.meta)

    def parse_dealer_vehicles(self, response):
        # dealer response has 38 records
        try:
            data = response.json()
        except json.JSONDecodeError:
            self.errors.append(f"Json Parsing Error parse_dealer_vehicles : {''.join(unquote(response.url).split('url=')[1:])}\n")
            return

        vehicles = data.get('results', [])

        # Extract vehicle information
        for vehicle in vehicles:
            city = vehicle.get('city', {}).get('raw', '')
            state = vehicle.get('state_code', {}).get('raw', '')
            v_year = vehicle.get('year', {}).get('raw', 0)
            v_make_name = ''.join(vehicle.get('make_name', {}).get('raw', []))
            v_model_name = ''.join(vehicle.get('model_name', {}).get('raw', []))
            v_id = vehicle.get('id', {}).get('raw', '')
            fuel_type = vehicle.get('fuel_type', {}).get('raw', '')
            days_on_market = vehicle.get('create_date', {}).get('raw', '')

            url = f'{self.base_urls}listing/{v_year}-{v_make_name}-{v_model_name}-{v_id}'

            # current if already exists in latest previous scrape vehicle file
            if url in self.previously_scraped_items:
                item = self.previously_scraped_items.get(url)
                self.current_scraped_items.append(item)
                self.new_scraped_vehicles_counter += 1
                print('Used Vehicles Scraped Counter : ', self.new_scraped_vehicles_counter)
                continue

            if url in self.duplicates_urls:
                self.errors.append(f'Already Scraped Url: {url}')
                continue

            info = {
                'v_year': v_year,
                'v_make_name': v_make_name,
                'v_model_name': v_model_name,
                'city': city,
                'state': state,
                'fuel_type': fuel_type,
                'days_on_market': days_on_market,
                'milage': vehicle.get('mileage', {}).get('raw', 0)
            }

            yield Request(url=url, callback=self.parse_vehicle_detail, meta=info)

    def parse_vehicle_detail(self, response):
        try:
            data = json.loads(response.css('script[type="application/json"]:contains("id")::text').get(''))
        except json.JSONDecodeError:
            self.errors.append(f"Json Parsing Error Vehicle detail Function : {''.join(unquote(response.url).split('url=')[1:])}\n")
            return

        try:
            title = response.css('.dealer-details-subtitle::text').get('').strip()
            year = (response.css('.detailsListItemLeft:contains("Year") + span ::text').get('').strip()
                    or response.meta.get('v_year', 0)) or data.get('year', 0)
            make = response.css('[data-track="vdp specs make"]::text').get('') or response.meta.get('v_make_name', '')
            trim_name = data.get('trimName', '')
            color = data.get('details', {}).get('Color', '')
            condition = data.get('condition', '')

            item = OrderedDict()
            item['Title'] = title
            item['Make'] = make or data.get('makeDisplayName', '')
            item['Model'] = response.meta.get('v_model_name', '') or data.get('modelDisplayName', '')
            item['Year'] = str(year).strip() if year else ''
            item['Vin'] = data.get('details', {}).get('VIN', '')
            item['Location'] = self.get_location(response, data)
            item['Condition'] = condition
            item['Price'] = data.get('price', '')
            item['Average Market Price'] = ''
            item['Main Image'] = self.get_main_image(response)
            item['Options'] = self.get_options(response, data)
            item['Mileage'] = self.get_mileage(response, data)
            item['Trim'] = trim_name if trim_name is not None else ''
            item['Color'] = color if color is not None else ''
            item['Body Type'] = data.get('details', {}).get('Cab Type', '')
            item['Fuel Type'] = response.meta.get('fuel_type', '') or data.get('details', {}).get('Fuel Type', '')
            item['Engine'] = data.get('details', {}).get('Engine Model', '')
            item['Deal Rating'] = ''
            item['Days on Market'] = self.get_days_on_market(response)
            item['Drive Train'] = data.get('details', {}).get('Drivetrain', '')
            item['City Fuel Economy'] = ''
            item['Highway Fuel Economy'] = ''
            item['Combined Fuel Economy'] = ''
            item['Dealer Name'] = data.get('dealerName', '').title()
            item['Dealer City'] = response.meta.get('city', '').title()
            item['Dealer State'] = response.meta.get('state', '')
            item['Dealer Zip'] = data.get('zip', '')
            item['Dealer Phone'] = data.get('formattedPhone', '')
            item['Dealer Rating'] = ''
            item['URL'] = unquote(''.join(unquote(response.url).split('url=')[1:]))
            item['Scraped Date'] = self.current_date_time

            self.duplicates_urls.append(item['URL'])

            self.current_scraped_items.append(item)
            self.new_scraped_vehicles_counter += 1
            print('Used Vehicles Scraped Counter : ', self.new_scraped_vehicles_counter)

        except Exception as e:
            self.errors.append(f"Error from Detail Vehicle Page Url: {''.join(unquote(response.url).split('url=')[1:])}, Error {e}\n")
            return

    def get_options(self, response, data):
        options = data.get('details', {})
        options_list = []

        for key, value in options.items():
            if isinstance(value, list):
                values = [item[next(iter(item))] for item in value]
                options_list.extend(values)
            else:
                options_list.append(str(value))

        options_string = ', '.join(options_list)

        specifications_selector = response.css('#info-list-seller li')
        specifications_list = []

        for specification_selector in specifications_selector:
            value = specification_selector.css('.detailsListItemRight ::text').getall()
            value = ', '.join([ele for ele in value if ele.strip()])

            if value:
                specifications_list.append(value)

        specifications = ', '.join(specifications_list)
        return options_string or specifications

    def get_days_on_market(self, response):
        try:
            days_on_market = response.meta.get('days_on_market', '')

            # Convert days_on_market to a datetime object
            days_on_market_date = datetime.fromisoformat(days_on_market.split('+')[0])

            current_date = datetime.now()
            time_difference = current_date - days_on_market_date
            total_days = time_difference.days

            return total_days if total_days else ''
        except Exception as e:
            self.errors.append(f"Error from Get Days on Market Url: {''.join(unquote(response.url).split('url=')[1:])}, Error {e}\n")
            return ''

    def get_location(self, response, data):
        location = data.get('location', '')
        if not location:
            selector = response.css('.seller-features .directionsLink ::text').getall()
            location = ''.join([ele.strip() for ele in selector if ele.strip()])
        distance = data.get('locationDistance', '')

        address = f"{location} {distance}".strip()

        return address if address else ''

    def get_main_image(self, response):
        image_list = response.css('.rsTmb::attr(src)').getall()
        if image_list:
            image = image_list[0]
            image = image.split('?width')[0]

            return image

    def get_mileage(self, response, data):
        milage = data.get('miles', '') or response.meta.get('milage', '')
        milage = f'{milage} Miles' if milage else ''
        return milage

    def get_previous_scarped_cars_from_file(self):
        """
        - Get the cars from the latest previously run file.
        - There could be many files, but we need the latest one to compare the cars
        """

        try:
            rows = []
            output_files = self.get_latest_files_path()

            if not output_files:
                return []

            while True:
                latest_output_filename = output_files.pop(0)

                with open(latest_output_filename, mode='r', encoding='utf-8') as csv_file:
                    rows = list(csv.DictReader(csv_file))

                    if rows:
                        break

                self.mandatory_logs.append(
                    f'Last Scraped file "{latest_output_filename}" has "{len(rows)}" rows to be compared with Current file to find out the Sold Cars')

            return rows

        except FileNotFoundError:
            self.errors.append('No previous output files found')
            return []
        except Exception as e:
            self.errors.append(f'Error accessing previous output files: {str(e)}')
            return []

    def get_latest_files_path(self):
        folder_path = 'output'

        # Get a list of all files in the directory
        files = os.listdir(folder_path)
        # Filter the list to include only CSV files
        # csv_files = [f for f in files if f.endswith('.csv')]
        csv_files = [f for f in files if f.endswith('.csv') and 'New' in f]

        # Sort the CSV files by their last created time (most recent first)
        csv_files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)

        # return os.path.join(folder_path, csv_files[1]) if len(csv_files) > 1 else None
        return [os.path.join(folder_path, csv_file) for csv_file in csv_files] if len(csv_files) > 0 else None

    def find_sold_cars(self):
        # if not self.all_current_scraped_items or not self.previously_scraped_items:
        if not self.current_scraped_items:
            return

        # Specify the file name and output folder
        sold_output_folder = 'output/Sold'

        # Create the output folder if it doesn't exist
        os.makedirs(sold_output_folder, exist_ok=True)

        file_name = f'Sold Cars {self.current_date_time}.csv'
        sold_cars_filepath = os.path.join(sold_output_folder, file_name)
        master_sold_cars_filepath = os.path.join(sold_output_folder, 'Master SoldCars.csv')

        sold_cars = []

        # Get the list of VINs from current_scraped_items
        current_scraped_url = [item.get('URL') for item in self.current_scraped_items]

        # Iterate through previous items, and append to sold_car sheet if URL not in current_scraped_url
        if self.previously_scraped_items:
            for previous_url, previous_item in self.previously_scraped_items.items():
                if previous_url not in current_scraped_url:
                    sold_cars.append(previous_item)
        else:
            # Current Scraped items
            self.write_item_into_csv(filename=self.used_output_filename, rows=self.current_scraped_items)
            return

        # Save the Sold cars into the new CSV
        self.write_item_into_csv(filename=sold_cars_filepath, rows=sold_cars)

        # Append these sold cars into the master file of sold cars
        self.write_item_into_csv(filename=master_sold_cars_filepath, rows=sold_cars)

        # Current Used Scraped items
        self.write_item_into_csv(filename=self.used_output_filename, rows=self.current_scraped_items)

        self.mandatory_logs.append(
            f'{len(sold_cars)} Cars found as Sold Cars as those were exists last time but not exists today')
        self.mandatory_logs.append(
            f'{len(sold_cars)} Sold Cars written into file: {sold_cars_filepath} as well as added in to the Master Sold cars file: {master_sold_cars_filepath}')

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        log_filename = f'{log_folder}/logs_{self.current_date_time}.txt'

        # Write informative logs
        with open(log_filename, mode='a', encoding='utf-8') as log_file:
            log_file.write(f'Spider "{self.name}" Started at "{self.current_date_time}"\n\n')
            # Write errors logs
            if self.errors:
                log_file.write('Error Logs:\n\n')
                for error in self.errors:
                    log_file.write(f'{error}\n')
                log_file.write('End of Error Logs:\n')
                log_file.write('\n\n')
            else:
                log_file.write('No error occurred during the project run.\n')

            # Write Mandatory logs
            log_file.write('Informative Logs:\n')
            if self.mandatory_logs:
                for log in self.mandatory_logs:
                    log_file.write(f'{log}\n')

    def read_input_file(self, file_path, file_type):
        """
        Read URLs or configuration from a text file.
        """
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                if file_type == 'urls':
                    return [line.strip() for line in file.readlines() if line.strip()]
                elif file_type == 'config':
                    return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file if '==' in line}
        except FileNotFoundError:
            self.errors.append(f"File not found: {file_path}")
            return [] if file_type == 'urls' else {}
        except Exception as e:
            self.errors.append(f"An error occurred while reading {file_path} file: {str(e)}")
            return [] if file_type == 'urls' else {}

    def write_item_into_csv(self, filename, rows):
        if not rows:
            return

        # Determine the mode (write or append)
        mode = 'a' if 'Master SoldCars' in filename else 'w'
        try:
            with open(filename, mode=mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)

                # Write header only if file is newly created
                if csvfile.tell() == 0:
                    writer.writeheader()

                # Write rows
                for row in rows:
                    # Filter out any keys not in csv_headers
                    row_to_write = {key: row[key] for key in self.csv_headers if key in row}
                    writer.writerow(row_to_write)

            self.mandatory_logs.append(f'{len(rows)} rows inserted into file "{filename}"')
        except Exception as e:
            self.errors.append(f'Error writing to file "{filename}": {str(e)}')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TruckTradeSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        if self.state_name:
            self.mandatory_logs.append(
                f"\n\n State {self.state_name}, has Total Vehicles : {self.state_vehicles_count}\n\n")
            self.state_name = ''
            self.state_vehicles_count = 0

        if self.states_urls:
            state = self.states_urls.pop(0)
            self.state_name = state.split('=')[1]
            url = f'https://www.commercialtrucktrader.com/dealers/results/ajax?state={self.state_name}'
            print('State Url : ', url)

            req = Request(url=url,
                          callback=self.pagination,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        # spider.mandatory_logs.append(f'\n\n\nVehicles are found: "{spider.all_vehicles_count}" , New vehicle are scraped "{spider.new_scraped_vehicles_counter}" for spider "{spider.name}"')
        spider.mandatory_logs.append(
            f'\n\n\nVehicles are found: "{spider.all_vehicles_count}" , for spider "{spider.name}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" was started at "{spider.current_date_time}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')

        spider.find_sold_cars()
        spider.write_logs()

