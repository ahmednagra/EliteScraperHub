import os
import json
import subprocess
from time import sleep
from datetime import datetime
from collections import OrderedDict

import requests
from scrapy import Spider, Request

# selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ChromeOptions
from selenium import webdriver  # selenium==4.12.0


class PropertiesDetailSpider(Spider):
    name = 'properties_detail'
    base_url = 'https://www.immobilienscout24.de/'
    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 2,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEEDS': {
            f'output/Immobilien Scout24 Properties Details {current_dt}.xlsx': {
                'format': 'xlsx',
                'fields': ['Name', 'Title', 'Purchase Price', 'Basic Rent/Purchase Price', 'Address',
                           'Latitude', 'Longitude', 'No of Apartments', 'No of Rooms', 'Living Space',
                           'Move in Date', 'Property Information', 'Property Cost', 'Property structure & Certificate',
                           'Description', 'URL']
            }
        }
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    }

    def __init__(self):
        super().__init__()
        self.properties_count = 0
        self.cities = self.read_input_file(file_path='input/cities_names.txt', file_type='cities')

        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

        self.config = self.read_input_file(file_path='input/scrapeops_proxy_key.txt', file_type='config')
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('use_proxy', '')

        self.cookies = {}
        self.driver = None

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.parse_start_requests)

    def parse_start_requests(self, response):
        for city_name in self.cities:
            city_url = self.get_city_url(city_name=city_name)

            if not city_url:
                continue

            property_types = [
                f'Suche{city_url}/haus-kaufen',
                f'Suche{city_url}/garage-kaufen',
                f'Suche{city_url}/wohnung-kaufen',
                f'Suche{city_url}/anlageimmobilie',
                f'Suche{city_url}/grundstueck-kaufen',
                f'Suche{city_url}/zwangsversteigerung',
                f'gewerbe-flaechen{city_url}/buero-kaufen',
                f'gewerbe-flaechen{city_url}/gastronomie-kaufen',
                f'gewerbe-flaechen{city_url}/einzelhandel-kaufen',
                f'gewerbe-flaechen{city_url}/spezialgewerbe-kaufen',
                f'gewerbe-flaechen{city_url}/hallenproduktion-kaufen',
                f'gewerbe-flaechen{city_url}/gewerbegrundstuecke-kaufen',
            ]
            cookie_url = f'{self.base_url}{property_types[1]}'
            cookies = self.get_cookies(cookie_url)

            for property_type in property_types:
                if not self.cookies:
                    cookies = self.get_cookies(property_type)

                url = f'{self.base_url}{property_type}'
                response.meta['handle_httpstatus_all'] = True
                yield Request(url=url, headers=self.headers, cookies=cookies,
                              callback=self.parse_city_filters, meta=response.meta)

    def parse_city_filters(self, response):
        if response.status == 401 and not response.meta.get('retry', False):
            response.meta['retry'] = True
            for req in self.block_re_request(url=response.url, callback=self.parse_city_filters, response=response):
                yield req
            return

        if response.status == 301:
            redirect_url = response.css('a::attr(href)').get('').lstrip('/')
            url = f"{self.base_url}{redirect_url}"
            yield Request(url=url, headers=self.headers, cookies=self.cookies,
                          callback=self.parse_city_filters, meta=response.meta)
            return

        properties_urls = response.css(
            'article .result-list-entry__criteria a::attr(href), .result-list-entries > section a.spec-title-link::attr(href)').getall()
        if properties_urls:
            properties_urls = list(set(properties_urls))

        for property_url in properties_urls:
            if 'expose' in property_url.lower():
                url = f"{self.base_url}{property_url.lstrip('/')}#/" if self.base_url not in property_url else property_url
            else:
                url = property_url

            print('detail page requested url', url)
            yield Request(url=url, headers=self.headers, cookies=self.cookies,
                          callback=self.parse_property_detail, meta=response.meta)

        # Pagination
        next_page = response.css('.pagination span.button-secondary:last-child a::attr(href), .reactPagination .p-active + li a ::text').get('')
        if next_page:
            if next_page.isdigit():
                base_url = ''.join(response.url.split('?pagenumber')[0:1])
                url = f'{base_url}?pagenumber={next_page}'
            else:
                url = f"{self.base_url}{next_page.lstrip('/')}"

            yield Request(url=url, headers=self.headers, cookies=self.cookies,
                          callback=self.parse_city_filters, meta=response.meta)

    def parse_property_detail(self, response):
        if response.status == 401 and not response.meta.get('retry', False):
            response.meta['retry'] = True

            for req in self.block_re_request(url=response.url, callback=self.parse_property_detail, response=response):
                yield req
            return

        try:
            geolocation_dict = response.css('script:contains("googlemaps") ::text').get({})
            if geolocation_dict:
                geolocation_dict = json.loads(''.join(geolocation_dict.split('IS24.googlemaps =')[2:]).replace(';', ''))

            address = [value.strip() for value in response.css('.address-with-map-link .address-block ::text').getall()
                       if value.strip()]
            purchase_price = response.css(
                '#projectCriteria .one-whole > p:nth-child(1)::text, .main-criteria-container .is24qa-kaufpreis-main span::text, .is24-preis-value::text').get(
                '').strip()
            item = OrderedDict()
            item['Name'] = response.css('#projectCriteria h1::text, #expose-title ::text').get('')
            item['Title'] = response.css('#projectCriteria h2::text').get('')
            item['Purchase Price'] = purchase_price if purchase_price.lower() != 'auf anfrage' else ''
            item['Basic Rent/Purchase Price'] = self.get_rent_price(response, purchase_price=purchase_price)
            item['Address'] = ' '.join(address) if address else self.get_address(geolocation_dict, response)
            item['Latitude'] = geolocation_dict.get('latitude', 0.0) if geolocation_dict else ''
            item['Longitude'] = geolocation_dict.get('longitude', 0.0) if geolocation_dict else ''
            item['No of Apartments'] = response.css(
                '#projectCriteria .one-whole .project-criteria__availableUnits h5::text').get('').strip()
            item['No of Rooms'] = response.css('.is24qa-zi-main ::text').get('').strip()
            item['Living Space'] = response.css(
                '.is24qa-wohnflaeche-ca-main ::text, .is24qa-vermietbar-ca-main::text, [class^="is24qa-"]:contains("m²").font-semibold::text').get(
                '').strip()
            item['Move in Date'] = response.css('#projectCriteria li:contains("Bezugstermin") p.fineprint ::text').get(
                '').strip()
            item['Property Information'] = self.get_property_info(response)
            item['Property Cost'] = self.get_property_cost(response)
            item['Property structure & Certificate'] = self.get_property_structure(response)
            item['Description'] = '\n '.join(
                response.css('#projectDescription .text-format ::text').getall()) or ', \n'.join(
                response.css('.is24qa-objektbeschreibung ::text').getall())

            item['URL'] = response.css('link[rel="canonical"] ::attr(href)').get('') or response.url

            self.properties_count += 1
            print('Properties Count :', self.properties_count)
            yield item

        except Exception as e:
            self.write_logs(f'Error PArsing Detail Page , Url: {response.url}  Error: {e}')
            return

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def read_input_file(self, file_path, file_type):
        """
        Read URLs or configuration from a text file.
        """
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                if file_type == 'cities':
                    return [line.strip() for line in file.readlines() if line.strip()]
                elif file_type == 'config':
                    return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file if '==' in line}
        except FileNotFoundError:
            self.write_logs(f"File not found: {file_path}")
            return [] if file_type == 'urls' else {}
        except Exception as e:
            self.write_logs(f"An error occurred while reading {file_type} file: {str(e)}")
            return [] if file_type == 'urls' else {}

    def get_city_url(self, city_name):
        try:
            city_headers = {
                'accept': '*/*',
                'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
                'x-is24-gac': '49f5bf376feed3a0f0a52abb46c0dc90',
            }

            params = {
                'i': city_name,
                't': 'country,region,city,quarterOrTown,quarter,district,postcode,trainStation,street,address',
                'f': 'shapeAvailable',
                'dataset': 'nextgen',
            }

            print('Request for City Geo URl')
            res = requests.get(
                'https://www.immobilienscout24.de/geoautocomplete/v4.0/DEU',
                params=params,
                headers=city_headers,
            )

            city_url = res.json()[0].get('entity', {}).get('geopath', {}).get('uri', '')

            return city_url
        except Exception as e:
            self.write_logs(f'City Url Request not Successful Error:{e}')
            return ''

    def get_address(self, geolocation_dict, response):
        address = geolocation_dict.get('address', '')
        if not address:
            address = ', '.join([value.strip() for value in response.css(
                '#projectCriteria .one-whole .project-criteria__address *:not(h5)::text').getall() if value.strip()])

        return address

    def get_property_info(self, response):
        try:
            info = []

            selectors = response.css('.criteriagroup.criteria-group--two-columns:nth-child(1) dl') or response.css(
                '.is24-ex-details.main-criteria-headline-size > div:nth-child(3) dl')
            selectors = selectors or response.css('h4[data-qa^="is24qa-objektinfos-"] + div dl').getall()

            for selector in selectors:
                key = selector.css('dt ::text').get('').strip()
                if key:
                    value = ''.join([text.strip() for text in selector.css('dd ::text').getall() if text.strip()])
                    info.append({key: value})

            return info
        except Exception as e:
            print('Error Parsing Property Information , Error : ', e)
            return []

    def get_property_cost(self, response):
        try:
            info = []

            selectors = response.xpath('//div[@id="is24-expose-premium-stats-widget"]/following-sibling::div[1]//dl')
            selectors = selectors or response.css('h4[data-qa^="is24qa-kosten"] + div dl')
            selectors = selectors or response.css(
                '.is24-ex-details.main-criteria-headline-size div.criteriagroup.print-two-columns:nth-child(2) dl')
            for selector in selectors:
                key = selector.css('dt ::text').get('').strip()
                if key:
                    value = ''.join([text.strip() for text in selector.css('dd::text').getall() if text.strip()])
                    if not value:
                        value = ''.join(
                            [text.strip() for text in selector.css('dd *:not(div) ::text').getall() if text.strip()])
                    info.append({key: value})

            return info
        except Exception as e:
            print('Error Parsing Property Cost , Error : ', e)
            return []

    def get_property_structure(self, response):
        try:
            info = []

            selectors = response.css('h4[data-qa^="is24qa-bausubstanz"] + div dl')
            for selector in selectors:
                key = selector.css('dt ::text').get('').strip()
                if key:
                    value = ''.join([text.strip() for text in selector.css('dd::text').getall() if text.strip()])
                    if not value:
                        value = ''.join(
                            [text.strip() for text in selector.css('dd *:not(div) ::text').getall() if text.strip()])
                    info.append({key: value})

            return info
        except Exception as e:
            print('Error Parsing Property Cost , Error : ', e)
            return []

    def get_rent_price(self, response, purchase_price):
        price = response.css(
            '#projectCriteria .one-whole > p:nth-child(2)::text, .is24qa-kaufpreis-main-label span::text').get(
            '').strip()

        if not price:
            all_prices = list(
                set([price.strip() for price in response.css('[class^="is24qa-"]:contains("€") ::text').getall() if
                     price.strip()][:3]))

            price = [price for price in all_prices if price not in purchase_price]
            price = ''.join(price).strip()
            if len(price) >= 15:
                price = ''
        return price

    def get_cookies(self, url):
        print('Selenium Request is opening')
        # default browser
        # To open Chrome with the script, uncomment these two lines,
        # if you want to attach to an already opened Chrome browser, comment out these two lines
        # If you want to open by the script, then you should have closed all Chrome browsers
        subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222')
        sleep(2)

        # Path to the user profile of Chrome
        user_profile_path = r'C:\Users\Muhammad Ahmed\AppData\Local\Google\Chrome\User Data'
        print("Chrome Launched")
        options = ChromeOptions()
        options.add_argument(rf"--user-data-dir={user_profile_path}")
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(options=options)

        try:
            self.driver.get(url)
            captcha_text = "Du bist ein Mensch aus Fleisch und Blut? Entschuldige bi"

            # Wait for certain elements or captcha text to appear
            def wait_for_elements_or_captcha():
                WebDriverWait(self.driver, 500).until(
                    lambda driver: any([
                        driver.find_elements(By.CSS_SELECTOR, ".saved-search-container"),
                        driver.find_elements(By.CSS_SELECTOR, "pre"),
                        driver.find_elements(By.CSS_SELECTOR, ".topnavigation"),
                        captcha_text in driver.page_source and not driver.find_elements(By.CSS_SELECTOR, ".topnavigation")
                    ])
                )

            wait_for_elements_or_captcha()
            sleep(2)

            # Initialize counter for CAPTCHA solve attempts
            captcha_attempts = 0

            if captcha_text in self.driver.page_source and not self.driver.find_elements(By.CSS_SELECTOR, ".topnavigation"):
                # Loop until CAPTCHA is solved or attempt limit is reached
                while captcha_text in self.driver.page_source and captcha_attempts < 10:
                    print("Captcha detected. Please solve the captcha manually.")
                    sleep(5)
                    # Refresh the page and wait again
                    self.driver.refresh()
                    captcha_attempts += 1  # Increment counter after each attempt

                    if captcha_attempts == 10:
                        print("CAPTCHA solve attempt limit reached.")
                        break

            try:
                poster_element = self.driver.find_element(By.CSS_SELECTOR, '#usercentrics-root')
                shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', poster_element)
                accept_button = shadow_root.find_element(By.CSS_SELECTOR, "[data-testid='uc-accept-all-button']")
                if accept_button:
                    accept_button.click()
                    print("Clicked on 'Alle akzeptieren' button")
                else:
                    print("Accept button not found. Skipping click.")
            except NoSuchElementException:
                print("Accept button not found. Skipping click.")

            # Check for JSON response or Html page element
            if "resultlist.resultlist" in self.driver.page_source:
                print("Found JSON response containing 'resultlist.resultlist'")
            else:
                print("Loaded the page with .saved-search-container")

            sleep(1)
            # Get cookies after the page is loaded
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        except TimeoutException:
            print("Timeout waiting for page to load after solving CAPTCHA.")
            cookies = {}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            cookies = {}
        finally:
            self.driver.close()

        self.cookies = cookies
        return cookies

    def block_re_request(self, url, callback, response):
        self.write_logs(f'Blocked Url :{url}')
        cookies = self.get_cookies(url)

        new_request = Request(url=url, headers=self.headers, cookies=cookies, callback=callback, meta=response.meta)
        # Prioritize this request by setting a high priority value
        new_request.priority = 100
        # Stop any other ongoing requests
        self.crawler.engine.pause()
        # Yield the new prioritized request
        yield new_request
        # Resume other requests after yielding the new one
        self.crawler.engine.unpause()

    def close(spider, reason):
        spider.write_logs(f'Total Properties Scraped : {spider.properties_count}')
        spider.write_logs(f'\n\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.write_logs(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')