import csv
import os
import glob
import json
import threading
from math import ceil
from datetime import datetime
from collections import OrderedDict

from scrapy import Spider, Request


class NewcarsSpider(Spider):
    name = "new_cars"
    start_urls = [
        'https://www.cargurus.com/Cars/getCarPickerReferenceDataAJAX.action?localCountryCarsOnly=true&outputFormat=REACT&showInactive=false&useInventoryService=true&quotableCarsOnly=true']

    headers = {
        'authority': 'www.cargurus.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.cargurus.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    csv_headers = ['Title', 'Make', 'Model', 'Year', 'Vin',
                   'Location', 'Condition', 'Price',
                   'Average Market Price', 'Main Image', 'Options',
                   'Mileage', 'Trim', 'Color', 'Body Type', 'Fuel Type', 'Engine',
                   'Deal Rating', 'Days on Market', 'Drive Train', 'City Fuel Economy',
                   'Highway Fuel Economy', 'Combined Fuel Economy', 'Dealer Name',
                   'Dealer City', 'Dealer State', 'Dealer Zip', 'Dealer Rating',
                   'Dealer Phone', 'URL'
                   ]

    main_start_datetime_str = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'DOWNLOAD_DELAY': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,

        'FEEDS': {
            f'output/CarGurus New Cars {main_start_datetime_str}.csv': {
                'format': 'csv',
                'fields': csv_headers,
            }
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zipcodes = self.read_uszip_file()

        self.scraped_product_counter = 0
        self.error_in_filter = []
        self.csv_lock = threading.Lock()
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.main_start_datetime_str}"\n']
        self.scraper_started_at = datetime.now()

        self.current_scraped_items = []
        self.scraping_datetime = datetime.now().strftime('%Y-%m-%d %H%M%S')
        self.previously_scraped_items = {item.get('Vin'): item for item in self.get_previous_scarped_cars_from_file()}

    def parse(self, response, **kwargs):
        data = response.json().get('allMakerModels', []).get('makers', [{}])

        for zipcode in self.zipcodes:
            for maker in [x.get('id') for x in data]:
                url = f'https://www.cargurus.com/Cars/preflightResults.action?searchId=842cfc71-84f0-44a1-9ca9-0f565e9a95ec&zip={zipcode}&distance=50&entitySelectingHelper.selectedEntity={maker}&sourceContext=untrackedExternal_false_0&isNewCarSearch=true&newUsed=1&inventorySearchWidgetType=NEW_CAR&sortDir=ASC&sortType=PRICE&shopByTypes=MIX&srpVariation=NEW_CAR_SEARCH&nonShippableBaseline=0'
                yield Request(url=url, callback=self.pagination)

    def pagination(self, response):
        try:
            res = response.json()
        except json.JSONDecodeError as e:
            res = {}
            self.logger.error(f'Function Pagination Error in Response Json : {e}')
            return

        total_results = res.get('totalListings', 0)
        print('Total Cars Found :', total_results)

        if total_results == 0:
            return

        if total_results > 0:
            total_pages = ceil(total_results / 15)
            print('Total Pages are :', total_pages)

            for page_number in range(total_pages):
                offset = page_number * 15
                maker = res.get('search', {}).get('selectedEntity', '')
                zip_no = res.get('search', {}).get('zip', '')
                page_url = f'https://www.cargurus.com/Cars/preflightResults.action?searchId=b16cd2aa-db81-45cd-a700-617cbe7f6e36&zip={zip_no}&distance=50&entitySelectingHelper.selectedEntity={maker}&sourceContext=untrackedWithinSite_false_0&isNewCarSearch=true&newUsed=1&inventorySearchWidgetType=NEW_CAR&sortDir=ASC&sortType=PRICE&shopByTypes=MIX&srpVariation=NEW_CAR_SEARCH&nonShippableBaseline={total_results}&offset={offset}&maxResults=15&filtersModified=true'

                yield Request(url=page_url, callback=self.parse_newcars, dont_filter=True)
        else:
            return

    def parse_newcars(self, response):
        if response.text.strip() == 'null':
            print('No result founded in url :', response.url)
            return

        # get response and load into json then get records one by one
        try:
            data = response.json()
            desired_keys = ['listings', 'priorityListings', 'highlightListings', 'newCarFeaturedListings']

            combine_dict = {key: data.get(key, {}) for key in desired_keys}
            new_list = []
            [new_list.extend(value) for value in combine_dict.values()]

            for car in new_list:
                try:
                    item = OrderedDict()
                    car_id = car.get('id', 0)

                    title = car.get('listingTitle', '')
                    if not title:
                        continue

                    vin_number = car.get('vin', '')
                    if any(item.get('Vin No', '') == vin_number for item in self.current_scraped_items):
                        print(vin_number, 'product already exists')
                        continue

                    item['Title'] = car.get('listingTitle', '')
                    item['Make'] = car.get('makeName', '')
                    item['Model'] = car.get('modelName', '')
                    item['Year'] = car.get('carYear', 0)
                    item['Vin'] = car.get('vin', '')

                    item['Location'] = car.get('sellerCity', '')
                    item['Condition'] = 'New'
                    item['Price'] = car.get('priceString', '')
                    # item['Average Market Price'] = f"${car.get('msrp', 0)}"
                    item['Average Market Price'] = f"${car['msrp']}" if car.get('msrp') is not None else ''
                    item['Main Image'] = car.get('originalPictureData', {}).get('url', '')
                    item['Options'] = ', '.join([x for x in car.get('options', '')])

                    item['Mileage'] = f"{car.get('mileageString', '')} Miles"
                    item['Trim'] = car.get('trimName', '')

                    item['Color'] = car.get('normalizedExteriorColor', '')
                    item['Body Type'] = car.get('bodyTypeName', '')
                    item['Fuel Type'] = car.get('localizedFuelType', '')
                    item['Engine'] = car.get('localizedEngineDisplayName', '')

                    item['Deal Rating'] = car.get('dealRating', '')
                    item['Days on Market'] = car.get('daysOnMarket', '')

                    item['Drive Train'] = car.get('driveTrain', '')
                    item['City Fuel Economy'] = ' '.join(
                        [str(value) for value in list(car.get('cityFuelEconomy', {}).values())])
                    item['Highway Fuel Economy'] = ' '.join(
                        [str(value) for value in list(car.get('highwayFuelEconomy', {}).values())])
                    item['Combined Fuel Economy'] = ' '.join(
                        [str(value) for value in list(car.get('combinedFuelEconomy', {}).values())])

                    item['Dealer Name'] = car.get('serviceProviderName', '')
                    item['Dealer City'] = car.get('sellerCity', '').split(',')[0].strip()
                    item['Dealer State'] = car.get('sellerRegion', '')
                    item['Dealer Zip'] = car.get('sellerPostalCode', '')
                    item['Dealer Rating'] = round(car.get('sellerRating', 0), 2)
                    item['Dealer Phone'] = car.get('phoneNumberString', '')
                    item[
                        'URL'] = f'https://www.cargurus.com/Cars/inventorylisting/vdp.action?listingId={car_id}&entitySelectingHelper.selectedEntity=NEW_CAR#listing={car_id}/NEWCAR_FEATURED/DEFAULT'

                    self.current_scraped_items.append(item)
                    self.scraped_product_counter += 1

                    yield item

                except Exception as e:
                    a = 1
                    continue

        except Exception as e:
            self.logger.error(f"Error while parsing new cars: {e} : Url {response.url}")

    def find_sold_cars(self):
        if not self.current_scraped_items or not self.previously_scraped_items:
            return

        # Specify the file name and output folder
        sold_output_folder = 'output/Sold'

        # Create the output folder if it doesn't exist
        if not os.path.exists(sold_output_folder):
            os.makedirs(sold_output_folder)

        file_name = f'Sold Cars {datetime.now().strftime("%Y-%m-%d %H%M%S")}.csv'
        sold_cars_filepath = os.path.join(sold_output_folder, file_name)
        master_sold_cars_filepath = os.path.join(sold_output_folder, 'Master SoldCars.csv')

        sold_cars = []

        # Get the list of VINs from current_scraped_items
        current_scraped_vin = [item.get('Vin') for item in self.current_scraped_items]

        # Iterate through previous items, and append to sold_car sheet if VIN not in current_scraped_vin
        for previous_vin, previous_item in self.previously_scraped_items.items():
            if previous_vin not in current_scraped_vin:
                sold_cars.append(previous_item)

        # Save the Sold cars into the new CSV
        self.write_item_into_csv(filename=sold_cars_filepath, rows=sold_cars)

        # Append these sold cars into the master file of sold cars
        self.write_item_into_csv(filename=master_sold_cars_filepath, rows=sold_cars)

        self.mandatory_logs.append(f'{len(sold_cars)} Cars found as Sold Cars as those were exists last time but not exists today')
        self.mandatory_logs.append(f'{len(sold_cars)} Sold Cars written into file: {sold_cars_filepath} as well as added in to the Master Sold cars file: {master_sold_cars_filepath}')

    def write_item_into_csv(self, filename, rows):
        if not rows:
            return

        # Acquire a file lock
        try:
            with self.csv_lock:  # Check with the Lock
                with open(filename, mode='a', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=self.csv_headers)

                    if csv_file.tell() == 0:
                        writer.writeheader()

                    # Write data to CSV
                    writer.writerows(rows)

        except:
            self.logger.error('Error in Adding Sold cars to Sold File')

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

                self.mandatory_logs.append(f'Last Scraped file "{latest_output_filename}" has "{len(rows)}" rows to be compared with Current file to find out the Sold Cars')

            return rows

        except:
            self.mandatory_logs.append(f'No previous output file found')
            return []

    def get_latest_files_path(self):
        folder_path = 'output'

        # Get a list of all files in the directory
        files = os.listdir(folder_path)

        # Filter the list to include only CSV files
        csv_files = [f for f in files if f.endswith('.csv')]

        # Sort the CSV files by their last created time (most recent first)
        csv_files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)

        return [os.path.join(folder_path, csv_file) for csv_file in csv_files] if len(csv_files) > 0 else None

    def write_logs(self):
        log_folder = 'logs/info-logs'
        logs_filename = f'{log_folder}/logs {self.main_start_datetime_str}.txt'
        os.makedirs(log_folder, exist_ok=True)

        with open(logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                # print(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

        self.mandatory_logs = []

    def read_uszip_file(self):
        file_path = ''.join(glob.glob('input/uszip.txt'))
        rows = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                rows.append(line.strip())
        return rows

    def close(spider, reason):
        spider.find_sold_cars()

        spider.mandatory_logs.append(f'Total "{spider.scraped_product_counter}" Cars scraped for spider "{spider.name}"')

        spider.mandatory_logs.append(f'Spider "{spider.name}" was started at "{spider.main_start_datetime_str}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')

        if spider.error_in_filter:
            spider.mandatory_logs.append(f'\n\nERRORS in spider "{spider.name}"\n')
            spider.mandatory_logs += spider.error_in_filter  # Add all the errors in the logs list and then write into file

        spider.write_logs()
