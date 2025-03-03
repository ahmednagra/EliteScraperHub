 import csv
import json
import logging
import re

from scrapy import Spider, Request


class BaseSpider(Spider):
    custom_settings = {
        'CONCURRENT_REQUESTS': 2
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

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.prop_type = 0
        self.location_property_type = ''
        self.homes_url = ''
        self.next_page = []
        self.next_page_url = []

    def start_requests(self):
        zip_codes = self.zip_code_csv()

        for zip_code in zip_codes[89:90]:
            data = {
                "term": zip_code,
                "transactionType": self.prop_type,
                "location": {"lt": 31.53, "ln": 74.35},
                "limitResult": False,
                "includeAgent": True,
                "includeSchools": True,
                "placeOnlySearch": False
            }

            url = 'https://www.homes.com/routes/res/consumer/property/autocomplete/'
            body = json.dumps(data).encode('utf-8')

            yield Request(url=url, headers=self.headers, method='POST', body=body, callback=self.parse, meta={'zip_code': zip_code})

        logging.info(Request)

    def parse(self, response):
        data = self.response_json(response)
        location_url = response.urljoin(data['suggestions']['places'][0].get('u')) + '?' + self.location_property_type

        yield Request(
            url=location_url,
            headers=self.headers,
            callback=self.homes,
            meta={'zip_code': response.meta['zip_code']}
        )

    def homes(self, response):
        homes_url = self.homes_url(response)  # Call the homes_url method

        for home_url in homes_url:
            url = response.urljoin(home_url)

            yield Request(
                url=url,
                headers=self.headers,
                callback=self.home_detail,
                meta={'zip_code': response.meta['zip_code']}
            )

        next_page = self.next_page(response)

        if next_page:
            url = self.next_page_url(response)
            yield Request(
                url=url,
                headers=self.headers,
                callback=self.homes
            )

    def same_selectors(self, response):
        dicitems = {}

        dicitems['SearchTerm'] = response.meta['zip_code']
        dicitems['Address'] = ' '.join(
            filter(None, ''.join(response.css('.property-info-address ::text').getall()).split()))
        dicitems['Street'] = response.css('.property-info-address-main::text').get('').strip()
        dicitems['City'] = response.css('.property-info-address-citystatezip a:first-child::text').get('').split(',')[0]
        dicitems['State'] = response.css('.property-info-address-citystatezip a:first-child::text').get('').split(',')[
            1]
        dicitems['Zipcode'] = response.css('.property-info-address-citystatezip a:last-child::text').get('')
        dicitems['Beds'] = response.css('.beds span::text').get('').replace('-', '')

        selector_patterns = [
            'span.amenities-detail-sentence:contains("Prop. Type:") + .value::text',
            'span.amenities-detail-sentence:contains("Class:") + .value::text',
            'span.amenities-detail-sentence:contains("Property Type:") + .value::text',
            'span.amenities-detail-sentence:contains("Property Sub Type:") + .value::text'
        ]

        for pattern in selector_patterns:
            value = response.css(pattern).get('')
            if value:
                dicitems['Property_Type'] = value
                break

        dicitems['Year_Built'] = re.search(r"built in (\d{4})",
                                           response.css('.breadcrumb-description-text::text').get('')) \
            .group(1) if re.search(r"built in (\d{4})",
                                   response.css('.breadcrumb-description-text::text').get('')) else None
        if not dicitems['Year_Built']:
            dicitems['Year_Built'] = response.css(
                'span.amenities-detail-sentence:contains("Year Built") + .value::text').get('')

        dicitems['Image'] = response.css('[data-attachmenttypeid=PrimaryPhoto]::attr(data-image)').get('')
        # if not dicitems['Image']:
        #     re.search(r'url\(&quot;(.+)&quot;\)', response.css('.js-open-gallery::attr(style)').get()).group(1)
        dicitems['Other_Images'] = str(response.css('.js-open-gallery::attr(data-image)').getall())
        dicitems['URL'] = response.url
        dicitems['Listing_Agent'] = response.css('.agent-information-fullname::text').get('')
        dicitems['Listing_Office'] = response.css('.agent-information-agency-name::text').get('')
        dicitems['Agent_Phone'] = response.css('.agent-information-phone-number::text').get('')
        dicitems['Sqft'] = response.css('.sqft span::text').get('')

        return dicitems


    def zip_code_csv(self):
        zip_code_csv = 'zip_codes.csv'

        with open(zip_code_csv, 'r') as zip_file:
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
