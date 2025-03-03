import csv
import json
import os

from scrapy import Spider, Request

from ..items import CarvanaCarsItem


class CarvanaSpider(Spider):
    name = "carvana_cars"
    allowed_domains = ["www.carvana.com"]
    start_urls = ['https://www.carvana.com/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2.0,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_DEBUG': True,
        'DOWNLOAD_DELAY': 3,
        'FEEDS': {
            # 'output/%(name)s_%(time)s.csv': {
            'output/all_records.csv': {
                'format': 'csv',
                'overwrite': True,
                'FEED_STORE_EMPTY': True,
                'fields': ['sku', 'Vin_number', 'make', 'model', 'year', 'color',
                           'condition', 'description', 'location', 'mileage', 'price', 'image', 'url']
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.previous_records = self.previous_records()
        self.counter = 0

    def parse(self, response):
        script = json.loads(response.css('script:contains("window.__PRELOADED_STATE__") ::text').re_first(
            'window.__PRELOADED_STATE__ = (.*);'))
        links_dic = script.get("internalLinks", {}).get("topLocations", {}).get("links", {})
        all_locations_links = [item['link'] for item in links_dic]

        for link in all_locations_links[2:5]:
            modify_link = '/cars' + link
            self.counter += 1
            yield Request(response.urljoin(modify_link), callback=self.car_detail)

    def car_detail(self, response):
        cars = response.css('script[data-qa="vehicle-ld"]::text').getall()

        for car in cars:
            try:
                car_detail = json.loads(car)
            except json.JSONDecodeError:
                continue

            item = CarvanaCarsItem()
            item['sku'] = car_detail.get('sku', '')
            item['model'] = car_detail.get('model', '')
            item['color'] = car_detail.get('color', '')
            item['year'] = car_detail.get('modelDate', '')
            item['image'] = car_detail.get('imageUrl', '')
            item['make'] = car_detail.get('manufacturer', '')
            item['description'] = car_detail.get('description', '')
            item['condition'] = car_detail.get('itemCondition', '')
            item['url'] = car_detail.get('offers', '').get('url', '')
            item['mileage'] = car_detail.get('mileageFromOdometer', '')
            item['price'] = car_detail.get('offers', '').get('price', '')
            item['location'] = response.css('span.m-0.truncate::text').get('')
            item['Vin_number'] = car_detail.get('vehicleIdentificationNumber', '')

            yield item

        page = json.loads(
            response.css('#__NEXT_DATA__').get().replace('<script id="__NEXT_DATA__" type="application/json">',
                                                         '').replace('</script>', ''))
        current_page = page.get('props', '').get('pageProps', '').get('initialState', '').get('pagination', '').get(
            'currentPage', '')
        total_pages = page.get('props', '').get('pageProps', '').get('initialState', '').get('pagination', '').get('totalMatchedPages', '')
        # total_pages = 2
        next_page = f'?email-capture=&page={int(current_page) + 1}'
        if int(current_page) < int(total_pages):
            yield Request(response.urljoin(next_page), callback=self.car_detail)

    def previous_records(self):
        try:
            file_path = os.path.join('output', 'all_records.csv')
            all_records = []

            with open(file_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    all_records.append(row)

            print('Total Records Loaded:', len(all_records))
            return all_records
        except Exception as e:
            print('Error occurred while loading Records:', str(e))
            return []

    def closed(self, reason):
        previuous_records = self.previous_records

        file_path = os.path.join('output', 'all_records.csv')
        all_records = []

        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                all_records.append(row)

        # Find the records that are in previous_records but not in all_records
        car_sold = [record for record in previuous_records if record not in all_records]

        # Write the car_sold_records to a new CSV file
        car_sold_file = os.path.join('output', 'car_sold.csv')

        with open(car_sold_file, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(car_sold)

        print('Car_sold.csv file created with the records that were sold.')
        self.logger.info('Total requests made: %s', self.counter)
