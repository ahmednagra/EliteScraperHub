import csv
from collections import OrderedDict
from datetime import datetime
from math import ceil
from typing import Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider, Selector, signals


class AdforumSpider(Spider):
    name = 'adforum'
    base_url = 'https://www.adforum.com/'
    talent_search_url = 'https://www.adforum.com/talent/search'
    start_urls = [talent_search_url]

    custom_settings = {
        'DOWNLOAD_DELAY': 0.25,
        'CONCURRENT_REQUESTS': 8,
        'FEEDS': {
            f'output/AdForum Talents {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['Searched Term', 'Searched Location', 'Name', 'Title', 'Location',
                           'Profile URL', 'Company Name', 'Company Website'],
            }
        }
    }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_parameters = self.get_search_parameters_from_file()
        self.config = self.get_config_from_file()
        self.current_items_scraped = 0
        self.scraped_companies = {}
        self.proxy = f'http://{self.config.get('User_name', '')}:{self.config.get('Password', '')}@{self.config.get('Domain_name', '')}:{self.config.get('Proxy_port', '')}'

    # def start_requests(self) -> Iterable[Request]:
    #     yield Request(url='https://www.adforum.com/talent/82210744-andrea-bistany', callback=self.parse_person_profile)

    def parse(self, response, **kwargs):
        try:
            """
            Start the spider by sending a request to the search page with the provided keyword and Location.
            """

            row = self.search_parameters.pop(0)
            keyword = row.get('Keyword', '')
            city = row.get('City', '')
            country = row.get('Country', '')

            location = city or country
            url = self.build_search_url(keyword, city, country)

            yield Request(url, callback=self.pagination, headers=self.headers, dont_filter=True,
                          meta={'keyword': keyword, 'location': location,
                                'handle_httpstatus_list': [404, 410]})

        except Exception as e:
            self.logger.error(f'Error parsing search page: {e}')

    def pagination(self, response):
        """
        Handle pagination to extract talent information from multiple pages.
        """
        try:
            products = response.css('.b-search_result__title ::text').re_first(r'\b(\d+)\b') or 0

            if products and int(products) >= 25:
                total_pages = ceil(int(products) / 100)
                url_part = response.url.split('?')[1]

                for page_no in range(1, total_pages + 1):
                    url = f'{self.base_url}find/loadmore?idx=people&l=100&p={page_no}&{url_part}&o=_score|desc&rtpl=people.list.search'
                    response.meta['page_no'] = page_no

                    yield Request(url, callback=self.parse_talents_listing,
                                  headers=self.headers,
                                  dont_filter=True,
                                  meta=response.meta)
            else:
                yield from self.parse_talents_listing(response)

        except Exception as e:
            self.logger.error(f'Pagination error: {e} URL: {response.url}')

    def parse_talents_listing(self, response):
        """
        Parse the search results page to extract talent information.
        """

        talents = []

        if 'page_no' in response.meta:
            try:
                data = response.json()
                records_html = data.get('html')
                html = Selector(text=records_html)
                talents = html.css('.personResult')
            except Exception as e:
                self.logger.error(f'Error parsing parse method for page {response.meta["page_no"]}: URL: {e}')
        else:
            talents = response.css('.appendable .personResult')

        for talent in talents:
            try:
                response.meta['name'] = talent.css('.talent-grid-name ::text').get('').strip()
                response.meta['title'] = talent.css('.talent-grid-position::text').get('').strip()
                response.meta['person_location'] = talent.css('.talent-grid-country ::text').get('').strip()
                url = talent.css('.talent-grid-company ::attr(href), .media-body a::attr(href)').get('')
                person_url = urljoin(self.base_url, url) if url else ''
                response.meta['person_url'] = person_url

                yield Request(url=person_url, callback=self.parse_person_profile,dont_filter=True,
                              headers=self.headers, meta=response.meta)

            except Exception as e:
                self.logger.error(f'Error Parsing item: {e}')

    def parse_person_profile(self, response):
        """
        Parse individual talent profiles.
        """
        try:
            # Extracting URL of the agency
            agency_name = self.get_agency_name(response)
            agency_url = self.get_agency_url(response)
            response.meta['company_name'] = agency_name

            if not agency_url:
                item = self.parse_item(response)
                yield item

            elif agency_url in self.scraped_companies:
                company_url = self.scraped_companies.get(agency_url)
                response.meta['agency_url'] = agency_url
                response.meta['company_url'] = company_url
                item = self.parse_item(response)
                yield item

            else:
                response.meta['agency_url'] = agency_url
                yield Request(url=agency_url, callback=self.parse_agency_detail, headers=self.headers,
                              meta=response.meta, dont_filter=True)
        except Exception as e:
            self.logger.error(f'Error parsing person profile: {e}, URL: {response.url}')

    def parse_agency_detail(self, response):
        """
        Parse agency details.
        """
        try:
            company_url = response.css(
                '.agency-info__text--alt:contains("Website") a::attr(href), .contact__link--site::attr(href)').get('')
            response.meta['company_url'] = company_url

            # add company Website Url in scraped_companies
            self.scraped_companies[response.meta.get('agency_url', '')] = company_url
            item = self.parse_item(response)
            yield item
        except Exception as e:
            self.logger.error(f'Error parsing agency detail: {e}, URL: {response.url}')

    def parse_item(self, response):
        """
        Parse individual items (talent information).
        """
        try:
            item = OrderedDict()

            # Extract talent information
            item['Searched Term'] = response.meta.get('keyword', '')
            item['Searched Location'] = response.meta.get('location', '')
            item['Name'] = response.meta.get('name', '')
            item['Title'] = response.meta.get('title', '')
            item['Company Name'] = response.meta.get('company_name', '')
            item['Company Website'] = response.meta.get('company_url', '')
            item['Location'] = response.meta.get('person_location', '')
            item['Profile URL'] = response.meta.get('person_url', '')
            self.current_items_scraped += 1
            print('Items are Scrapped = ', self.current_items_scraped)
            return item
        except Exception as e:
            self.logger.error(f'Error Parsing item: {e}')

    def get_search_parameters_from_file(self):
        """
        Load search parameters from a CSV file.
        """
        try:
            input_csv_filename = 'input/search_parameters.csv'

            with open(input_csv_filename, mode='r', encoding='utf-8') as csv_file:
                return list(csv.DictReader(csv_file))
        except Exception as e:
            self.logger.error(f'Error loading search parameters: {e}')
            return []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AdforumSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next Row from CSV if available.
        """

        if not self.search_parameters:
            return

        req = Request(url=self.base_url,
                      callback=self.parse, dont_filter=True,
                      meta={'handle_httpstatus_all': True})

        try:
            self.crawler.engine.crawl(req)  # For latest Python version
        except TypeError:
            self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def get_config_from_file(self):
        """
        Load Proxy Information from a text file.
        """
        try:
            config_filename = 'input/proxy_config.txt'

            with open(config_filename, mode='r', encoding='utf-8') as file:
                return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file}
        except Exception as e:
            self.logger.error(f'Error loading search parameters: {e}')
            return []

    def build_search_url(self, keyword, city, country):
        """
        Build the search URL based on search parameters.
        """
        if not city:
            return f'{self.talent_search_url}?worktitle={keyword}&location=country:{country}'
        else:
            return f'{self.talent_search_url}?worktitle={keyword}&location=city:{city},country:{country}'

    def get_agency_name(self, response):
        return response.css('.m-position-company a::text').get('') or ''.join(response.css('.m-position-company::text').getall())

    def get_agency_url(self, response):
        return response.css('.tab-content .card dt:contains("AGENCY:") + dd a::attr(href)').get('') or response.css('.card-title + dl dt:contains("AGENCY:") + dd a::attr(href)').get('')
