import csv
import json
import logging
import re
import time

from scrapy import signals
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.signals import spider_opened
from scrapy.utils.project import get_project_settings


# from ..items import HomesPropertiesItem


class HomesRentSpider(Spider):
    name = "homes_rent"

    custom_settings = {
        'CONCURRENT_REQUESTS': 2
        # 'FEED_FORMAT': 'csv',
        # 'FEED_URI': 'output/%(name)s_%(time)s.csv',
        # 'FEED_EXPORT_FIELDS': ['Address', 'Street', 'City', 'State', 'Zipcode', 'Latitude', 'Longitude', 'Beds',
        #                        'Baths', 'Sqft',
        #                        'Lot_Size', 'Property_Type', 'Property_Style', 'Price', 'Annual_Tax', 'MLS',
        #                        'Year_Built',
        #                        'Agent_Name', 'Broker_Name', 'Agent_Phone', 'Agent_Email', 'Primary_Image',
        #                        'Other_Images', 'URL']
    }

    headers = {
        'authority': 'www.homes.com',
        'accept': 'application/json',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'content-type': 'application/json-patch+json',
        # 'cookie': 'gp=%257b%2522g%2522%253a0%252c%2522v%2522%253a3%252c%2522d%2522%253a%257b%2522lt%2522%253a31.53%252c%2522ln%2522%253a74.35%257d%257d; vr=vr-fNtFNliLrEmouiZ1fl4ayg; _gcl_au=1.1.1779694616.1685603549; _gid=GA1.2.1651964198.1685603550; ln_or=eyIxOTM3ODA0IjoiZCJ9; _uetsid=ab9864b0004b11ee8f6c137e9b1667e4; _uetvid=ab988510004b11ee9150871f2e7999e7; _ga=GA1.1.1570317913.1685603550; cto_bundle=HpIp4l9yaDhyQkR3OTZHRzRlTHJJTmM2bzBVMTE1R3RKd1RBNFJCcllxWDYzMUhYZU5LVWpIbUxQOE1VT2tKeVBxMmo4SHBDNWdMMkRGZW9zMnl2ZXFjRjFoUSUyRkMwYURRQWhHQ2ZKMGlYaGpqOEt1VzZsMmdIZVBQSXdOWjJTU0JDU3NjVURVWllxV0xXMXhlMFJra3U4R0J1ZyUzRCUzRA; _ga_K83KE4D6ED=GS1.1.1685614982.3.0.1685614982.60.0.0; sr=%7B%22h%22%3A675%2C%22w%22%3A494%2C%22p%22%3A1.25%7D',
        'origin': 'https://www.homes.com',
        'referer': 'https://www.homes.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    def __init__(self, filepath, **kwargs):
        super().__init__(**kwargs)
        # filepath =
        # self.file_path = full_file_path
        # print('self File Path is : ', self.file_path)

    def start_requests(self):
        zip_codes = self.zip_code_csv()
        # zip_codes = ['73651']

        for zip_code in zip_codes[15:16]:
            data = {
                "term": zip_code,
                "transactionType": 2,
                "location": {"lt": 31.53, "ln": 74.35},
                "limitResult": False,
                "includeAgent": True,
                "includeSchools": True,
                "placeOnlySearch": False
            }

            url = 'https://www.homes.com/routes/res/consumer/property/autocomplete/'
            body = json.dumps(data).encode('utf-8')

            yield Request(url=url,
                          headers=self.headers,
                          method='POST', body=body,
                          callback=self.parse,
                          meta={'zip_code': zip_code})

        logging.info(Request)

    def parse(self, response):
        data = self.response_json(response)
        location_url = response.urljoin(data['suggestions']['places'][0].get('u')) + '?' + 'property_type=1,2,4'

        yield Request(
            url=location_url,
            headers=self.headers,
            callback=self.rent_homes,
            meta={'zip_code': response.meta['zip_code']}
        )

    def rent_homes(self, response):
        homes_url = response.css('.for-rent-content-container a::attr(href)').getall()

        for home_url in homes_url:
            url = response.urljoin(home_url)

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.detail_home,
                meta={'zip_code': response.meta['zip_code']}
            )

    def detail_home(self, response):
        # item = HomesPropertiesItem()
        item = dict()

        item['Search_Term'] = response.meta['zip_code']
        item['Address'] = ' '.join(
            filter(None, ''.join(response.css('.property-info-address ::text').getall()).split()))
        item['Street'] = response.css('.property-info-address-main::text').get('').strip()
        item['City'] = response.css('.property-info-address-citystatezip a:first-child::text').get('').split(',')[0]
        item['State'] = response.css('.property-info-address-citystatezip a:first-child::text').get('').split(',')[1]
        item['Zip_Code'] = response.css('.property-info-address-citystatezip a:last-child::text').get('')
        item['Latitude'] = ''
        item['Longitude'] = response.css('.amenities-detail-sentence:contains("Longitude:") + .value::text').get('')
        item['Beds'] = response.css('.beds span::text').get('')
        item['Baths'] = response.css('.baths span::text').get('')
        item['Area'] = response.css('.sqft span::text').get('')  # Sqft
        selector_patterns = [
            'span.amenities-detail-sentence:contains("Prop. Type:") + .value::text',
            'span.amenities-detail-sentence:contains("Class:") + .value::text',
            'span.amenities-detail-sentence:contains("Property Type:") + .value::text',
            'span.amenities-detail-sentence:contains("Property Sub Type:") + .value::text'
        ]

        for pattern in selector_patterns:
            value = response.css(pattern).get('')
            if value:
                item['Property_Type'] = value
                break

        item['Price'] = response.css('.rent span::text').get('').replace('$', '').replace(',', '')
        item['Year_Built'] = re.search(r"built in (\d{4})", response.css('.breadcrumb-description-text::text').get('')) \
            .group(1) if re.search(r"built in (\d{4})",
                                   response.css('.breadcrumb-description-text::text').get('')) else ''
        if not item['Year_Built']:
            response.css('span.amenities-detail-sentence:contains("Year Built") + .value::text').get('')
        item['Availability_Date'] = ''
        item['Broker'] = response.css('.agent-information-fullname::text').get('')
        item['Image'] = response.css('[data-attachmenttypeid=PrimaryPhoto]::attr(data-image)').get('')
        item['URL'] = response.url
        item['Broker_Phone'] = response.css('a.agent-information-phone-number::text').get('')
        item['Broker_Email'] = response.css('.agent-information-email::text').get('')
        item['Broker_Company'] = response.css('.agent-information-agency-name::text').get('')
        item['Other_Images'] = str(response.css('.js-open-gallery::attr(data-image)').getall())

        yield item

    # def zip_code_csv(self):
    #     zip_code_csv = 'zip_codes.csv'
    #
    #     with open(zip_code_csv, 'r') as zip_file:
    #         csv_reader = csv.reader(zip_file)
    #         next(csv_reader)  # Skip the header row
    #         zip_codes = [row[0] for row in csv_reader]
    #
    #     return zip_codes
    def zip_code_csv(self):
        with open(self.full_file_path, 'r') as zip_file:
            csv_reader = csv.reader(zip_file)
            next(csv_reader)  # Skip the header row
            zip_codes = [row[0] for row in csv_reader]

        return zip_codes

    def response_json(self, response):
        try:
            json_data = json.loads(response.text) or {}

        except json.JSONDecodeError as e:
            print("Error decoding JSON: ", e)
            json_data = {}

        return json_data

#
# if __name__ == '__main__':
#     process = CrawlerProcess(get_project_settings())
#     process.crawl(HomesRentSpider)
#     process.signals.connect(spider_opened, signal=signals.spider_opened)
#
#     process.start()
