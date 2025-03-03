import re
import json
from scrapy import Spider, Request, Selector


class SearchSpider(Spider):
    name = "search_scraper"
    allowed_domains = ["www.aliexpress.us"]
    start_urls = ["https://www.aliexpress.us"]

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


    def __init__(self, *args, **kwargs):
        super(AmaassnSpider, self).__init__(*args, **kwargs)
        self.included = {}

        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

    def parse(self, response, **kwargs):
        pass

    def read_text_file(self):
        file_path = 'input/city_names.txt'

        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)