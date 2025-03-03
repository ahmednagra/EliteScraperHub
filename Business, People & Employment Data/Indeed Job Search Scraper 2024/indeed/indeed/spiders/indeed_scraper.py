import glob
import json
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict
from scrapy import Spider, Request, Selector


class IndeedScraperSpider(Spider):
    name = 'indeed'
    start_urls = ['https://www.indeed.com/?r=us']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/{name} Jobs Detail {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Search Keyword', 'Search Location', 'Job Title', 'Company Name', 'Company Url',
                           'Job Location', 'Job Type', 'Salary', 'Description', 'URL'],
            }
        }
    }

    def __init__(self):
        self.keyword_list = self.read_keywords()
        self.location_list = self.read_location()
        self.proxy = self.read_proxykey_file().get('scraperapi_key', '')

    def start_requests(self):
        self.write_logs("Scraping is started", mode='w')

        if not self.keyword_list:
            self.write_logs("No Keyword provided. Spider will stop.")
            return

        if not self.location_list:
            self.write_logs("No Location provided. Spider will stop.")
            return

        for keyword in self.keyword_list:
            for location in self.location_list:
                url = f'https://www.indeed.com/jobs?q={keyword}&l={location}&filter=0'
                yield Request(url=url, callback=self.parse,
                              meta={'proxy': self.proxy,
                                    'keyword': keyword, 'location': location})

    def parse(self, response):
        skill_filter_urls = response.css('#filter-taxo1-menu a::attr(href)').getall() or []
        location_filter_urls = response.css('#filter-loc-menu a::attr(href)').getall() or []
        location_filter_urls = [x.split('rbl=')[-1] for x in location_filter_urls]

        for skillurl in skill_filter_urls:
            for locationurl in location_filter_urls:
                url = f'{urljoin(response.url, skillurl)}&rbl={locationurl}&filter=0'
                yield Request(url=url, callback=self.parse_jobs,
                              meta={'proxy': self.proxy,
                                    'keyword': response.meta.get('keyword'),
                                    'location': response.meta.get('location')})

    def parse_jobs(self, response):
        total_jobs = ''.join(response.css('.jobsearch-JobCountAndSortPane-jobCount span::text').re(r'\d+'))
        total_jobs = int(total_jobs) if total_jobs else 0

        if total_jobs >= 975:
            experience_level_filter_urls = response.css('#filter-explvl-menu a::attr(href)').getall() or []
            for experienceurl in experience_level_filter_urls:
                url = f'{urljoin(response.url, experienceurl)}&filter=0'
                yield Request(url=url, callback=self.pagination,
                              meta={'proxy': self.proxy,
                                    'keyword': response.meta.get('keyword'),
                                    'location': response.meta.get('location'),
                                    })

        else:
            jobs = response.css('.jobsearch-ResultsList .cardOutline, #mosaic-provider-jobcards .css-5lfssm')
            for job in jobs:
                salary = job.css('.salary-snippet-container .attribute_snippet::text').get('')
                job_type = job.css('.metadata:not(.salary-snippet-container) .attribute_snippet::text').get('')
                job_id = job.css('.jobTitle a::attr(data-jk)').get('')
                url = f'https://www.indeed.com/viewjob?jk={job_id}&tk&vjs=3'
                yield Request(url=url,
                              callback=self.parse_job_detail,
                              meta={
                                  'job_type': job_type,
                                  'salary': salary,
                                  'proxy': self.proxy,
                                  'keyword': response.meta.get('keyword'),
                                  'location': response.meta.get('location'),
                              })

        next_page = response.css('[data-testid="pagination-page-next"]::attr(href)').get('')
        if next_page:
            url = urljoin(response.url, next_page)
            yield Request(url=url, callback=self.parse_jobs,
                          meta={'proxy': self.proxy,
                                'keyword': response.meta.get('keyword'),
                                'location': response.meta.get('location'),
                                })

    def parse_job_detail(self, response):
        item = OrderedDict()

        job_type = response.css('.css-tvvxwd::text').getall()
        if job_type:
            job_type_information = job_type[-1]
        else:
            job_type_information = ''

        item['Search Keyword'] = response.meta.get('keyword')
        item['Search Location'] = response.meta.get('location')
        item['Job Title'] = response.css('.jobsearch-JobInfoHeader-title span::text').get('')
        item['Company Name'] = response.css('div[data-testid="inlineHeader-companyName"] a::text').get('')
        item['Company Url'] = response.css('div[data-testid="inlineHeader-companyName"] a::attr(href)').get('')
        item['Job Location'] = response.css('div[data-testid="inlineHeader-companyLocation"] div::text').get('')
        item['Job Type'] = response.meta.get('job_type', '') or job_type_information
        item['Salary'] = response.css('#salaryInfoAndJobType span::text').get('').replace('a month',
                                                                                          '') or response.meta.get(
            'salary', '')
        desc = response.xpath('//div[@id="jobDescriptionText"]//text()').extract() or ''
        item['Description'] = '\n'.join(text.strip() for text in desc if text.strip())
        item['URL'] = response.url
        yield item

    def read_keywords(self):
        file_name = ''.join(glob.glob('input/keywords.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []

    def read_location(self):
        file_name = ''.join(glob.glob('input/location.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []

    def pagination(self, response):
        total_jobs = ''.join(response.css('.jobsearch-JobCountAndSortPane-jobCount span::text').re(r'\d+'))
        total_jobs = int(total_jobs) if total_jobs else 0

        if total_jobs >= 975:
            jobtype_filter_urls = response.css('#filter-jobtype-menu a::attr(href)').getall() or []
            for jobtypeurl in jobtype_filter_urls:
                yield Request(url=urljoin(response.url, jobtypeurl), callback=self.pagination,
                              meta={'proxy': self.proxy,
                                    'keyword': response.meta.get('keyword'),
                                    'location': response.meta.get('location'),
                                    })
        else:
            jobs = response.css('.jobsearch-ResultsList .cardOutline, #mosaic-provider-jobcards .css-5lfssm')
            for job in jobs:
                salary = job.css('.salary-snippet-container .attribute_snippet::text').get('')
                job_type = job.css('.metadata:not(.salary-snippet-container) .attribute_snippet::text').get('')
                job_id = job.css('.jobTitle a::attr(data-jk)').get('')
                url = f'https://www.indeed.com/viewjob?jk={job_id}&tk&vjs=3'

                yield Request(url=url,
                              callback=self.parse_job_detail,
                              meta={
                                  'job_type': job_type,
                                  'salary': salary,
                                  'proxy': self.proxy,
                                  'keyword': response.meta.get('keyword'),
                                  'location': response.meta.get('location'),
                              })

            next_page = response.css('[data-testid="pagination-page-next"]::attr(href)').get('')
            if next_page:
                url = urljoin(response.url, next_page)
                yield Request(url=url, callback=self.pagination,
                              meta={'proxy': self.proxy,
                                    'keyword': response.meta.get('keyword'),
                                    'location': response.meta.get('location'),
                                    })

    def write_logs(self, message, mode='a'):
        with open("logs.txt", mode=mode, encoding='utf-8') as txt_file:
            txt_file.write(f"{datetime.now()} -> {message}\n")

    def read_proxykey_file(self):
        file_path = 'input/proxy_key.txt'
        config = {}

        try:
            with open(file_path, mode='r') as txt_file:
                for line in txt_file:
                    line = line.strip()
                    if line and '==' in line:
                        key, value = line.split('==', 1)
                        config[key.strip()] = value.strip()

            return config

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []
