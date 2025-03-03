import glob
from math import ceil

from collections import OrderedDict
from urllib.parse import unquote, urljoin

from nameparser import HumanName

from scrapy import Request, Spider, FormRequest


class CinandoSpider(Spider):
    name = "cinando"
    base_url = 'https://cinando.com/'
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'output/zCinando Peoples Details.csv',
        'FEED_EXPORT_OVERWRITE': True
    }

    login_headers = {
        'authority': 'cinando.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://cinando.com',
        'pragma': 'no-cache',
        'referer': 'https://cinando.com/?ReturnUrl=%2Fen%2FSearch%2FPeople',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_scraped_urls = []
        config = self.read_input_file(''.join(glob.glob('input/credentials.txt')))

        if config:
            self.email = config.get('email')
            self.password = config.get('password')
        else:
            self.email = None
            self.password = None
            print("Credentials file not found or invalid.")
            raise ValueError("Credentials file not found or invalid.")

    def start_requests(self):
        yield Request(self.base_url, callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            request_token = response.css("input[name='__RequestVerificationToken']::attr(value)").get('')
            form_data = self.get_form_data(request_token)
            yield FormRequest(url=self.base_url, formdata=form_data, callback=self.parse_login_homepage,
                              headers=self.login_headers)
        except Exception as e:
            print(f"Unable to proceed from Parse Method Due to error: {e}")

    def parse_login_homepage(self, response):
        try:
            form_data = self.get_json_formdata(start=0)
            yield FormRequest(url='https://cinando.com/en/People/Search', callback=self.pagination,
                              cookies=self.get_cookies(response), formdata=form_data)
        except Exception as e:
            print(f"Unable to proceed from Parse login Homepage Method Due to error: {e}")

    def pagination(self, response):
        try:
            data = self.get_data_dict(response)

            product = data.get('resultsCount')
            total_pages = ceil(product / 40)

            for page_no in range(0, total_pages + 1):
                start_product = page_no * 40
                form_data = self.get_json_formdata(start=start_product)
                yield FormRequest(url='https://cinando.com/en/People/Search', callback=self.parse_index_json,
                                  cookies=self.get_cookies(response), formdata=form_data, dont_filter=True)
        except Exception as e:
            print(f"Unable to proceed from Pagination Method Due to error: {e}")

    def parse_index_json(self, response):
        data = self.get_data_dict(response)

        try:
            peoples = data.get('results', [])

            for people in peoples:
                item = OrderedDict()
                url = urljoin(self.base_url, unquote(people.get('Link', '')))
                if url in self.current_scraped_urls:
                    print('Duplicate Url Founded :', url)
                    continue

                name_str = people.get('Name', '')
                name = HumanName(name_str) if name_str else ''
                item['Full Name'] = people.get('Name', '')
                item['First Name'] = name.first if name else ''
                item['Last Name'] = name.last if name else ''
                item['Email'] = str(people.get('Email', ''))

                Tel = people.get('Tel', '')
                Mobile = people.get('Mobile', '')

                if Tel or Mobile:
                    if Tel and Mobile:
                        number = set([Tel, Mobile])
                        item['Phone'] = ', '.join(number)
                    else:
                        item['Phone'] = Tel if Tel else Mobile
                else:
                    item['Phone'] = ''

                item['City'] = people.get('City', '')
                item['Country'] = people.get('TxtCountry', '')
                item['Company'] = people.get('CompanyName', '')
                item['Job Title'] = people.get('job', '') or people.get('Job', '')

                activities = people.get('CompanyActivities', [])
                if activities:
                    item['Type of Company'] = activities[0].get('Item1', '')
                else:
                    item['Type of Company'] = ''

                item['URL'] = url

                self.current_scraped_urls.append(url)
                yield item
        except Exception as e:
            print(f"Record not Scraped. error is :{e}")

    def get_form_data(self, key):
        data = {
            '__RequestVerificationToken': key,
            'ReturnURL': '/en/Search/People',
            'ClientId': '',
            'RedirectUri': '',
            'State': '',
            'Email': self.email,
            'Password': self.password,
            'RememberMe': [
                'true',
                'false',
            ],
        }

        return data

    def get_json_formdata(self, start):
        data = {
            'Start': str(start),
            'Length': '40',
            'SortColumn': 'name',
            'SortDir': 'asc',
            'criteria[Query]': '',
            'criteria[Keyword]': '',
            'criteria[CountryAdvanced]': 'false',
            'criteria[CompanyActivityMain]': 'false',
            'criteria[PeopleActivityMain]': 'false',
            'criteria[Cliste]': '',
            'criteria[Editable]': 'false',
            'criteria[OnsiteOnly]': 'false',
            'DontUpdateLength': 'false',
        }

        return data

    def get_cookies(self, response):
        set_cookie_headers = response.headers.getlist('Set-Cookie')

        # Parse the cookies and create a dictionary
        cookies_dict = {}
        for header in set_cookie_headers:
            cookie_parts = header.decode('utf-8').split(';')[0].split('=')
            cookies_dict[cookie_parts[0]] = cookie_parts[1]

        # in cookies previous items are 20 now set to 40
        cookies_dict['ItemsPerPage'] = '40'

        return cookies_dict

    def get_data_dict(self, response):
        try:
            data = response.json()
        except Exception as e:
            data = {}
            print(f" An Error is arise in the pagination Method :{e}")

        return data

    def read_input_file(self, file):
        try:
            data_dict = {}

            with open(file, 'r') as file:
                for line in file:
                    elements = line.strip().split('==')
                    if len(elements) == 2:
                        key = elements[0].strip()
                        value = elements[1].strip()
                        data_dict[key] = value

            if 'email' not in data_dict or 'password' not in data_dict:
                # self.logger.error("Email or password not found in credentials file.")
                print("Email or password not found in credentials file.")
                return {}

            return data_dict
        except Exception as e:
            # self.logger.error(f'Unable to read the credentials file: {e}')
            print(f'Unable to read the credentials file: {e}')
            return {}
