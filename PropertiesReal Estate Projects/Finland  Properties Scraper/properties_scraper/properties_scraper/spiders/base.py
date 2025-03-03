from collections import OrderedDict
import glob

from scrapy import Spider, signals


class BaseSpider(Spider):
    name = 'base'
    start_urls = ['']

    xlsx_headers = ['Address', 'street number', 'Type', 'Rooms', 'Size (m2)', 'Agency url', 'Agency name']

    data = []
    error_messages = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.handle_error, signal=signals.spider_error)
        return spider

    def handle_error(self, failure, response, spider):
        error_message = str(failure.value)

        # Get the spider name and the function name where the error occurred
        spider_name = spider.name

        formatted_error = f"Spider Name: {spider_name} - Error Message: {error_message}"

        # Append the formatted error to the list
        self.error_messages.append(formatted_error)

    def parse(self, response, **kwargs):
        pass

    def get_item(self, response_sel):
        item = OrderedDict()
        address = self.get_address(response_sel).strip()
        item['Address'] = address.capitalize()
        item['street number'] = self.get_street_number(response_sel)
        item['Type'] = self.get_type(response_sel)  # price
        item['Rooms'] = self.get_rooms(response_sel)
        item['Size (m2)'] = self.get_size(response_sel)
        item['Agency url'] = self.get_agency_url(response_sel)
        item['Agency name'] = self.get_static(response_sel)

        if item['Agency url'] not in [x['Agency url'] for x in self.data]:
            self.data.append(item)
            return item
        else:
            return

    def get_address(self, response):
        pass

    def get_street_number(self, response):
        pass

    def get_type(self, response):
        pass

    def get_rooms(self, response):
        pass

    def get_size(self, response):
        pass

    def get_agency_url(self, response):
        pass

    def get_static(self, response):
        pass

    def read_input_urls(self, filename):
        file_path = ''.join(glob.glob(f'input/{filename}'))
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in file.readlines()]
            return urls
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            return []

    def close(Spider, reason):
        # Append the errors into the errors file for all spiders for this time's run

        with open('ERRORS.txt', 'a') as f:
            for error_message in Spider.error_messages:
                f.write(f"{error_message}\n")
