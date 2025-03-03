import csv
import json
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request
from slugify import slugify
from usaddress import tag


class CyberbackgroundchecksSpider(Spider):
    name = 'cbc'

    # custom_settings = {
    #     'CONCURRENT_REQUESTS': 8,
    #     'FEEDS': {
    #         f'CyberBackgroundChecks Records.csv': {
    #             'format': 'csv',
    #             'fields': ['Searched_Address', 'Name', 'Age', 'Current_Address', 'Phone_1', 'Phone_2', 'Phone_3', 'Phone_4',
    #                        'Phone_5', 'Phone_6', 'Phone_7', 'Phone_8', 'Phone_9', 'Phone_10', 'Email_1', 'Email_2',
    #                        'Email_3', 'Email_4', 'Email_5', 'URL'],
    #             'overwrite': True,
    #         },
    #     },
    #
    #     'CRAWLERA_ENABLED': True,
    #     'CRAWLERA_APIKEY': '402af928a60746db80c15bbb353560aa',
    #     'DOWNLOADER_MIDDLEWARES': {
    #         'scrapy_crawlera.CrawleraMiddleware': 610,
    #     },
    #
    # }

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'FEED_URI': 'CyberBackgroundChecksRecords.csv',  # Updated feed URI
        'FEEDS': {
            'CyberBackgroundChecksRecords.csv': {
                'format': 'csv',
                'fields': ['Searched_Address', 'Name', 'Age', 'Current_Address', 'Phone_1', 'Phone_2', 'Phone_3',
                           'Phone_4',
                           'Phone_5', 'Phone_6', 'Phone_7', 'Phone_8', 'Phone_9', 'Phone_10', 'Email_1', 'Email_2',
                           'Email_3', 'Email_4', 'Email_5', 'URL'],
                'overwrite': True,
            },
        },
        'CRAWLERA_ENABLED': True,
        'CRAWLERA_APIKEY': '402af928a60746db80c15bbb353560aa',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_crawlera.CrawleraMiddleware': 610,
        },
    }

    headers = {
        'authority': 'www.cyberbackgroundchecks.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'referer': 'https://www.cyberbackgroundchecks.com/address',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    def __init__(self, filepath, **kwargs):
        super().__init__(**kwargs)
        self.csv_path = filepath
        self.file_url = None

    def start_requests(self):
        for address in self.get_search_addresses(self.csv_path)[:5]:
            search_street = address.get('Street', '')
            search_city = address.get('City', '')
            search_state = address.get('State')

            if not search_city and not search_state:
                continue

            print(slugify(search_street))

            url = f'https://www.cyberbackgroundchecks.com/address/{slugify(search_street)}/{slugify(search_city)}/{slugify(search_state)}'

            yield Request(url=url, headers=self.headers, meta={'address': address})

    def parse(self, response, **kwargs):
        input_address = response.meta.get('address', {})
        input_street = input_address.get('Street', '')

        search_street_obj = self.get_address_parts(input_street)
        search_street = self.get_street_address_key(search_street_obj)
        search_city = input_address.get('City', '')
        search_state = input_address.get('State', '')

        searched_address = f'{input_street}, {search_city}, {search_state}'

        try:
            person_contacts = {person.get('@id'): person for person in json.loads(response.css('script:contains("Person")::text').get('').strip())}
        except json.JSONDecodeError:
            person_contacts = {}

        for person in response.css('.card.card-hover'):
            address_string = person.css('.address-current a ::text').get('')
            address_ = self.get_address_parts(address_string)

            street = self.get_street_address_key(address_)
            city = address_.get('PlaceName', '')
            state = address_.get('StateName', '')

            street_matched = street and (search_street in street or street in search_street.lower())
            city_matched = city and (search_city.lower() in city or city in search_city.lower())
            state_matched = state and (search_state.lower() in state or state in search_state.lower())

            if not all([street_matched, city_matched, state_matched]):
                continue

            person_url = response.urljoin(person.css('.btn-primary.btn-block ::attr(href)').get(''))
            person_json = person_contacts.get(person_url, {})

            item = OrderedDict()
            item['Searched_Address'] = searched_address
            item['Name'] = person.css('.name-given ::text').get('').strip()
            item['Age'] = person.css('.age ::text').get('')
            item['Current_Address'] = address_string
            item['URL'] = person_url
            item.update(self.get_phones(person, person_json))
            item.update(self.get_emails(person_json))

            yield item

    def get_street_address_key(self, address_obj):
        return f"{address_obj.get('AddressNumber', '')} {address_obj.get('StreetName', '')}".strip()

    def get_phone_from_html(self, person_html):
        return person_html.css('.phone ::text').getall()

    def get_phones(self, person_html, person_json):
        phones = person_json.get('telephone', []) or self.get_phone_from_html(person_html)

        return self.get_contact_item(phones, 'Phone')

    def get_emails(self, person_json):
        emails = person_json.get('email', [])

        return self.get_contact_item(emails, 'Email')

    def get_contact_item(self, contacts, contact_type):
        contact_item = dict()

        if isinstance(contacts, str):
            contact_item[f'{contact_type}_1'] = contacts

        if isinstance(contacts, list):
            for index, value in enumerate(contacts):
                contact_item[f'{contact_type}_{index + 1}'] = value

        return contact_item

    def get_address_parts(self, address):
        try:
            return tag(address.lower())[0]

        except IndexError:
            return {}

    def get_search_addresses(self, file_path):
        with open(file_path, mode='r', encoding='utf8') as input_file:
            return list(csv.DictReader(input_file))

    def closed(self, reason):
        filename = self.custom_settings['FEED_URI']
        print('filename spider closed:', filename)
        with open('filename.csv', 'w') as f:
            json.dump(filename, f)


