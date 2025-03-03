import os
from datetime import datetime
from urllib.parse import unquote
from collections import OrderedDict

from scrapy import Spider, Request


class AsinSearchSpider(Spider):
    name = "asin_search"
    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'device-memory': '8',
        'downlink': '10',
        'dpr': '1.25',
        'ect': '4g',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://www.amazon.ae/',
        'rtt': '100',
        'sec-ch-device-memory': '8',
        'sec-ch-dpr': '1.25',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-ch-viewport-width': '1536',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'viewport-width': '1536',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/Amazon Products Details {current_dt}.csv': {
                'format': 'csv',
                'fields': ['Selling Price', 'Seller Name', 'Fulfilled by', 'Payment', 'Availability', 'URL']
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.asins = set(self.read_input_asins_numbers('input/asins.txt'))

        self.product_count = 0
        self.errors = []
        self.mandatory_logs = []
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']
        self.mandatory_logs.append(f'{len(self.asins)} : Total Input Asins Numbers')

        self.config = self.get_config_from_file('input/scrapeops_proxy_key.txt')
        self.proxy_key = self.config.get('scrapeops_api_key', '')
        self.use_proxy = self.config.get('use_proxy', '')

    def start_requests(self):
        for asin in self.asins:
            url = f'https://www.amazon.ae/dp/{asin}'
            yield Request(url=url, headers=self.headers, callback=self.parse_product_detail, meta={'asin': asin})

    def parse_product_detail(self, response):
        asin = response.meta.get('asin', '')
        try:
            item = OrderedDict()
            see_all_options = response.css('#buybox-see-all-buying-choices a::attr(href)')
            price = self.get_price(response)

            item['Selling Price'] = price.replace('AED', 'AED ') if price else ''
            item['Fulfilled by'] = response.css('#fulfillerInfoFeature_feature_div .offer-display-feature-text span::text').get('')
            item['Seller Name'] = response.css('#merchantInfoFeature_feature_div .offer-display-feature-text span ::text').get('')
            item['Payment'] = response.css('#dynamicSecureTransactionFeature_feature_div .offer-display-feature-text .offer-display-feature-text-message ::text').get('')
            item['Availability'] = '' if price else 'Out of Stock'
            item['URL'] = ''.join(unquote(response.url).split('url=')[1:])

            print(item)
            if see_all_options:
                url = f'https://www.amazon.ae/gp/product/ajax/ref=dp_aod_unknown_mbc?asin={asin}&m=&qid=&smid=&sourcecustomerorglistid=&sourcecustomerorglistitemid=&sr=&pc=dp&experienceId=aodAjaxMain'
                yield Request(url=url, callback=self.get_process_price, headers=self.headers, dont_filter=True,
                              meta={'handle_httpstatus_all': True, 'item': item, 'asin': asin})
            else:
                self.product_count += 1
                print('Items Scraped : ', self.product_count)
                yield item

        except Exception as e:
            self.errors.append(f'Parsing Error the product, Asin: {asin} Error: {e}')

    def get_price(self, response):
        try:
            # amazon Discount price selector
            discount_price = response.css('#snsCaptionAndDiscountPillAbbreviated_feature_div + #apex_offerDisplay_desktop .a-spacing-top-mini .a-offscreen ::text').get('')
            price = discount_price or response.css('#corePrice_feature_div .a-offscreen::text').get('')

            return price.strip() if price else ''
        except Exception as e:
            self.errors.append(f"Parse price error Asin :{response.meta.get('asin', '')} Error: {e}")

    def get_process_price(self, response):
        asin = response.meta.get('asin', '')
        try:
            item = response.meta.get('item')
            options = response.css('#aod-offer')[:1]
            price = options.css('.a-offscreen ::text').get('').strip()
            seller_name = options.css('#aod-offer-soldBy .a-link-normal ::text').get('').strip()

            item['Selling Price'] = price.replace('AED', 'AED ') if price else ''
            item['Fulfilled by'] = options.css('#aod-offer-shipsFrom .a-color-base ::text').get('').strip()
            item['Seller Name'] = seller_name.title() if seller_name else ''
            item['Availability'] = '' if price else 'Out of Stock'

            self.product_count += 1
            print('Items Scraped : ', self.product_count)
            yield item

        except Exception as e:
            self.errors.append(f'Parsing Error the product, Asin: {asin} Error: {e}')

    def read_input_asins_numbers(self, file_path):
        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            self.errors.append(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            self.errors.append(f"An error occurred: {str(e)}")
            return []

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def get_config_from_file(self, config_filename):
        """
        Load Proxy Information from a text file.
        """
        try:
            with open(config_filename, mode='r', encoding='utf-8') as file:
                return {line.split('==')[0].strip(): line.split('==')[1].strip() for line in file}
        except Exception as e:
            self.errors.append(f'Error loading search parameters: {e}')
            return []

    def close(spider, reason):
        spider.mandatory_logs.append(
            f'Spider "{spider.name}" Total Asins Are Scraped: "{spider.product_count}"')
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"\n\n')

        spider.mandatory_logs.append(f'Spider Error:: \n')
        spider.mandatory_logs.extend(spider.errors)
        spider.write_logs()
