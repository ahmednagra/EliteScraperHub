import csv
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from spiders.autotrader1 import AutotraderSpider


def create_csv_file(file_path, mode, rows):
    """
       Create or append to a CSV file with specified rows.

       Args:
           file_path (str): Path to the CSV file.
           mode (str): File mode ('w' for write, 'a' for append).
           rows (list): List of dictionaries representing rows to write.

       Returns:
           None
       """
    # If file already exists in write mode, return
    # Avoid override the Master File
    if os.path.exists(file_path) and mode == 'w':
        return

    with open(file_path, mode=mode, newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=AutotraderSpider.csv_headers)
        file_empty = csv_file.tell() == 0  # Check if file is empty

        if file_empty:
            writer.writeheader()  # Write headers only if file is empty

        # Write data to CSV
        writer.writerows(rows)


def create_output_csv_files():
    """
    - There are two spiders those are writing into the same file.
    - There was an issue that sometimes the headers were not written there.
    - So to handle that issue, the files are creating here in main method with the header row inserted
    - The same header names will be written which are defined in "csv_headers" inside the spider

    - These same names are used inside the spider as well.
    - So if a change requires, it needs to be done on both places

    - The files will be created (if not exists already) with the header rows only

    """

    sold_folder = 'output/Sold'

    daily_used_cars_filepath = f'output/Autotrader Used Cars {running_datetime}.csv'
    daily_sold_cars_filepath = f'{sold_folder}/Sold Cars {running_datetime}.csv'
    master_sold_cars_filepath = f'{sold_folder}/Master SoldCars.csv'

    if not os.path.isdir(sold_folder):
        os.makedirs(sold_folder)

    # Create CSV files if they don't exist
    create_csv_file(daily_used_cars_filepath, mode='w', rows=[])
    create_csv_file(daily_sold_cars_filepath, mode='w', rows=[])
    create_csv_file(master_sold_cars_filepath, mode='w', rows=[])


def get_previous_scarped_cars_from_file():
    """
        - Get the cars from the latest previously run file.
        - There could be many files, but we need the latest one to compare the cars
        """

    try:
        rows = []
        output_files = get_latest_files_path()

        if not output_files:
            return []

        for latest_output_filename in output_files:
            if running_datetime in latest_output_filename:
                continue

            with open(latest_output_filename, mode='r', encoding='utf-8') as csv_file:
                rows = list(csv.DictReader(csv_file))

                if rows:
                    return rows
                else:
                    pass
        return []

    except Exception as e:
        print(f'Error occurred: {str(e)}')
        return []


def get_latest_files_path():
    """
    Get paths of the latest CSV files.
    """

    folder_path = 'output'

    # Get a list of all files in the directory
    files = os.listdir(folder_path)
    # Filter the list to include only CSV files
    csv_files = [f for f in files if f.endswith('.csv')]

    # Sort the CSV files by their last created time (most recent first)
    csv_files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)), reverse=True)

    return [os.path.join(folder_path, csv_file) for csv_file in csv_files] if len(csv_files) > 0 else None


def get_current_scarped_cars_from_file():
    """
        - Get the cars from the latest Scrape run file.
        - There could be many files, but we need the latest one with Date time match to compare the cars
        """

    try:
        rows = []
        output_files = get_latest_files_path()

        if not output_files:
            return []

        for latest_output_filename in output_files:
            if running_datetime in latest_output_filename:
                with open(latest_output_filename, mode='r', encoding='utf-8') as csv_file:
                    rows = list(csv.DictReader(csv_file))

                    if rows:
                        return rows
                    else:
                        pass
        return []

    except Exception as e:
        print(f'Error occurred: {str(e)}')
        return []


def find_sold_cars():
    """
    Find and save sold cars to CSV files.
    """
    if not all_current_scraped_items:
        return

    sold_cars = []

    # Get the list of VINs from current_scraped_items
    current_scraped_vin = [item.get('Vin') for item in all_current_scraped_items]

    # Iterate through previous items, and append to sold_car sheet if VIN not in current_scraped_vin
    for previous_vin, previous_item in previously_scraped_items.items():
        if previous_vin not in current_scraped_vin:
            sold_cars.append(previous_item)

    # Specify the file name and output folder
    sold_folder = 'output/Sold'

    # Create the output folder if it doesn't exist
    if not os.path.exists(sold_folder):
        os.makedirs(sold_folder)

    # These sold files are created with headers row inside the main.py file with exact names.
    # If the name required to change, then it should be changed there as well

    daily_sold_cars_filepath = f'{sold_folder}/Sold Cars {running_datetime}.csv'
    master_sold_cars_filepath = f'{sold_folder}/Master SoldCars.csv'

    # Save the Sold cars into the new CSV
    create_csv_file(file_path=daily_sold_cars_filepath, mode='a', rows=sold_cars)

    # Append these sold cars into the master file of sold cars
    create_csv_file(file_path=master_sold_cars_filepath, mode='a', rows=sold_cars)


if __name__ == '__main__':
    running_datetime = datetime.now().strftime('%Y-%m-%d %H%M%S')
    create_output_csv_files()

    # Create the logs folder if not exists
    if not os.path.isdir('logs'):
        os.makedirs('logs')

    spiders = ['autotrader', 'autotrader2']

    def run_spider(spider_file):
        # Pass the current datetime to make the output file with same datetime
        subprocess.run(['scrapy', 'crawl', spider_file, '-a', f'dt={running_datetime}'])


    with ThreadPoolExecutor() as executor:
        executor.map(run_spider, spiders)

    previously_scraped_items = {item.get('Vin'): item for item in get_previous_scarped_cars_from_file()}
    all_current_scraped_items = get_current_scarped_cars_from_file()
    find_sold_cars()
