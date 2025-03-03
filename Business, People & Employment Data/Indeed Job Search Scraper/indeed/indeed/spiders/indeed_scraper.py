import glob
import json
import os
from datetime import datetime
from urllib.parse import urljoin

from collections import OrderedDict
from scrapy import Spider, Request, Selector


class IndeedScraperSpider(Spider):
    name = 'indeed'
    start_urls = ['https://www.indeed.com/?r=us']
    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'FEEDS': {
            f'output/{name} Jobs Detail {current_dt}.csv': {
                'format': 'csv',
                'fields': ['Search Keyword', 'Search Location', 'Company Name','Company Website', 'Industry',
                           'Company Size', 'Job Title', 'Job Location', 'Job Type', 'Posted Date',
                           'Job Description Summary', 'LinkedIn Profile', 'URL'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items_scrape = 0
        self.keyword_list = self.read_keywords()
        self.usa_states_list = self.read_usa_states()
        self.proxy = self.read_proxykey_file()

        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

    def start_requests(self):
        if not self.keyword_list:
            self.write_logs("No Keyword provided. Spider will stop.")
            return

        if not self.usa_states_list:
            self.write_logs("No US Zipcode Provided. Spider will stop.")
            return

        for keyword in list(set(self.keyword_list)):
            for state in self.usa_states_list:
                url = f"https://www.indeed.com/jobs?q={keyword}&l={state}&sc=0kf:jt(contract);&filter=0"
                yield Request(url=url,
                              callback=self.parse_jobs, dont_filter=True,
                              meta={
                                  'proxy': self.proxy,
                                    'keyword': keyword,
                                    'location': state})

    def parse_jobs(self, response):
        total_jobs = ''.join(response.css('.jobsearch-JobCountAndSortPane-jobCount span::text').re(r'\d+'))
        total_jobs = int(total_jobs) if total_jobs else 0

        if not response.meta.get('educational_filter') and not response.meta.get('next_page'):
            self.write_logs(f"Key word: {response.meta.get('keyword')}, Total jobs: {total_jobs}, URL: {response.url}")

        if total_jobs ==0:
            self.write_logs(f"Not Job Found URL:{response.url}")
            return

        if total_jobs >= 975:
                edu_filters = response.css('#filter-edulvl-menu a::attr(href)').getall() or []
                experience_level_filter_urls = response.css('#filter-explvl-menu a::attr(href)').getall() or []
                for experience_url in experience_level_filter_urls:
                    for edu_filter in edu_filters:
                        exp_value = experience_url.split('&sc=0kf%3A')[1].split('jt(con')[0]
                        url_1 = f'{urljoin(response.url, edu_filter)}'.split('jt(con')[0]
                        url = f'{url_1}{exp_value}jt(contract);&filter=0'
                        print(f' Education Filter url: {url}')

                        yield Request(url=url, callback=self.parse_jobs,
                                      meta={
                                          'proxy': self.proxy,
                                          'educational_filter': True,
                                          'next_page': True,
                                          'keyword': response.meta.get('keyword'),
                                          'location': response.meta.get('location'),
                                      })
        else:
            # Process job details when total jobs are less than 975
            jobs = response.css('.mainContentTable')
            for job in jobs:
                job_id = job.css('.jobTitle a::attr(href)').get('')
                if job_id and not 'pagead/' in job_id:
                    url = f"https://www.indeed.com{job_id}" if job else ''
                    print('Job Detail Url', url)
                    yield Request(url=url,
                                  callback=self.parse_job_detail,
                                  meta={
                                      'proxy': self.proxy,
                                      'keyword': response.meta.get('keyword'),
                                      'location': response.meta.get('location'),
                                  })

        # Handle pagination
        next_page = response.css('[data-testid="pagination-page-next"]::attr(href)').get('')
        if next_page:

            url = urljoin(response.url, next_page)
            print(f'Next Page is Called Url:{url}')
            yield Request(url=url, callback=self.parse_jobs,
                          meta={
                              'proxy': self.proxy,
                              'next_page': True,
                                'keyword': response.meta.get('keyword'),
                                'location': response.meta.get('location'),
                                })

    def parse_job_detail(self, response):
        item = OrderedDict()
        try:
            desc = response.xpath('//div[@id="jobDescriptionText"]//text()').extract() or ''
            job_type = response.css('#salaryInfoAndJobType ::text').getall()
            if job_type:
                job_type_information = job_type[-1]
            else:
                job_type_information = ''

            try:
                job_dict = json.loads(response.css('script:contains("@context") ::text').get(''))
                desc = job_dict.get('description', '')
                desc_html = Selector(text=desc)
                desc_text =  '\n'.join(text.strip() for text in desc_html.css('::text').getall() if text.strip())
            except json.JSONDecodeError as e:
                job_dict = {}
                desc_text = ''

            company_name = response.css('div[data-testid="inlineHeader-companyName"] a::text').get('')
            company_name = company_name or response.css('div[data-company-name="true"] a::text').get('').strip()
            company_name = company_name or job_dict.get('hiringOrganization', {}).get('name', '')
            company_url = job_dict.get('hiringOrganization', {}).get('sameAs', '')
            company_indeed_url = company_url or response.css('div[data-testid="inlineHeader-companyName"] a::attr(href)').get('')

            item['Search Keyword'] = response.meta.get('keyword')
            item['Search Location'] = response.meta.get('location')
            item['Company Name'] = company_name
            item['LinkedIn Profile'] = company_url
            item['Job Title'] = response.css('.jobsearch-JobInfoHeader-title span::text').get('')
            item['Job Location'] = response.css('div[data-testid="inlineHeader-companyLocation"] div::text').get('')
            item['Job Type'] = ', '.join(job_dict.get('employmentType', [])) or job_type_information
            item['Posted Date'] = datetime.strptime(job_dict.get('datePosted', ''), '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y %I:%M %p') if job_dict.get('datePosted', '') else ''
            item['Job Description Summary'] = desc_text or '\n'.join(text.strip() for text in desc if text.strip())
            item['URL'] = response.css('[rel="canonical"] ::attr(href)').get('') or response.url


            if company_indeed_url:
                yield Request(url=company_indeed_url, callback=self.parse_company_info,
                              meta={'proxy': self.proxy, 'handle_httpstatus_all': True, 'item': item,
                              })
            else:
                self.items_scrape += 1
                print('Item Scraped :', self.items_scrape)
                yield item
        except Exception as e:
            self.write_logs(f'url:{response.url}  Error:{e}')
            return


    def parse_company_info(self, response):
        item = response.meta.get('item', OrderedDict())

        company_size = ''.join(response.css('[data-testid="companyInfo-employee"] ::text').getall()).replace('Company size', '')
        if not company_size:
            company_size = ''.join(response.css('[data-testid="companyInfo-employee"] span ::text').getall()).replace('Company size', '')

        item['Industry'] = response.css('[data-testid="industryInterLink"] ::text').get('').strip()
        item['Company Website'] = response.css('[data-testid="companyInfo-companyWebsite"] a::attr(href)').get('')
        item['Company Size'] = company_size.replace('Company size', '') if company_size else company_size
        item['LinkedIn Profile'] = response.url

        self.items_scrape += 1
        print('Item Scraped with company info:', self.items_scrape)
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

    def read_usa_states(self):
        # file_name = ''.join(glob.glob('input/location.txt'))
        file_name = ''.join(glob.glob('input/usa_states.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def read_proxykey_file(self):
        file_path = 'input/proxy_key.txt'
        # config = {}
        a = 'scraperapi_key==http://scraperapi.country_code=us:dd3a877a7221297538d5270bdd3d13ac@proxy-server.scraperapi.com:8001'
        try:
            with open(file_path, mode='r') as txt_file:
                for line in txt_file:
                    if line:
                        proxy= f"http://scraperapi.country_code=us:{line}@proxy-server.scraperapi.com:8001"
                        return proxy

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def close(spider, reason):
        spider.write_logs(f'\n\nTotal Jobs Scraped : {spider.items_scrape}')
        spider.write_logs(f'Spider Started at: {spider.current_dt}')
        spider.write_logs(f'Spider Stopped at: {datetime.now().strftime("%Y-%m-%d %H%M%S")}')