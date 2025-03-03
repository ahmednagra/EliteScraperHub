import json
from typing import Iterable

from scrapy import Spider, Selector, FormRequest, Request, signals
from urllib.parse import urljoin
from collections import OrderedDict


class CubSpider(Spider):
    name = "old_cub"
    base_url = 'https://online.cub.com.au/'
    start_urls = ["https://online.cub.com.au/"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'log_level': 'WARNING',
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/Online Cub Products Details.xlsx': {
                'format': 'xlsx',
                'fields': ['EAN', 'SKU', 'Name', 'Price', 'Save', 'Deal',
                           'Deal Start Date', 'Deal End Date', 'URL', ],
            }
        }
    }

    headers = {
        'authority': 'online.cub.com.au',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        # 'cookie': 'JSESSIONID=8DF11EC11779D96B10F5F821304C7489.accstorefront-d7766775b-d75r4; ROUTE=.accstorefront-d7766775b-d75r4; visid_incap_2581074=2yMLdW15TnONQ9y5iXnk0fTr1mUAAAAAQUIPAAAAAACyWmtegt4QxIOFdWBOo0xp; incap_ses_956_2581074=RWPZXPz5j0Zzghdx9mVEDfTr1mUAAAAAfUDeN55hy5s28vzklGiazw==; sabmStore-rememberMe=H35QiboK3ZFg2rO2w5Cw5sk9i7m8XLtgFAjPr1havwF99P/W+Vb6wQcEjEk5sH9+BQNmb+cJblmwOWhsmZbOSVlw6I2yoGRS/NkhfLni7GBM8dZu2yiJYOCgKmnDFTVrKY7D1ECRqFUt4aeiC7ulK1xDVK3vSAJ6UiKDLsfFNAjSoXLT; JSESSIONID=8DF11EC11779D96B10F5F821304C7489.accstorefront-d7766775b-d75r4',
        'origin': 'https://online.cub.com.au',
        'pragma': 'no-cache',
        'referer': 'https://online.cub.com.au/sabmStore/en/login',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    current_scraped_items = []
    category_products = {}
    scraped_items = 0
    file_mode = 'w'
    categories_urls = [
        'https://online.cub.com.au/sabmStore/en/c/14',
        'https://online.cub.com.au/sabmStore/en/Beer/c/10',
        'https://online.cub.com.au/sabmStore/en/Cider/c/11',
        'https://online.cub.com.au/sabmStore/en/c/12',
        'https://online.cub.com.au/sabmStore/en/c/13',
        'https://online.cub.com.au/sabmStore/en/deals',
    ]

    def start_requests(self) -> Iterable[Request]:
        yield Request(self.start_urls[0], callback=self.parse)

    def parse(self, response, **kwargs):
        cook = response.headers.getlist(b'Set-Cookie')[0]
        session_id = cook.split(b';')[0].split(b'=')[1].decode()
        route = f".accstorefront{cook.split(b';')[0].split(b'=')[1].split(b'.accstorefront')[1].decode()}"
        cookies = self.get_cookies(session_id, route)
        form_data = self.get_formdata()

        yield FormRequest(url='https://online.cub.com.au/sabmStore/en/j_spring_security_check', formdata=form_data,
                          headers=self.headers, cookies=cookies, callback=self.parse_home_page)

    def parse_home_page(self, response):
        # Pop a URL from the categories_urls list
        self.scraped_items = 0
        if self.categories_urls:
            category_url = self.categories_urls.pop(0)
            yield Request(url=category_url, callback=self.parse_category)

    def parse_category(self, response):
        if 'deals' in response.url:
            category_name = 'Deals'
            category_products = response.css('#d_circle span::text').get('') or response.css('.col-md-6 .num-products label ::text').get('')
            self.category_products[category_name] = category_products

            products = json.loads(response.css('#dealsData ::text').get('').encode().decode('unicode-escape'))
            for product in products:
                product_url = product.get('ranges', [])[0].get('baseProducts', [])[0].get('url', '')
                url = urljoin(self.base_url, product_url)
                print('Deal product url :', url)
                deal = ''.join(Selector(text=product.get('title', '')).css(' ::text').getall())

                yield Request(url=url, callback=self.parse_product_detail,
                              meta={'deal': deal}, dont_filter=True)
        elif 'Beer' in response.url:
            category_name = response.css('meta[name="description"]::attr(content)').get('')
            print('Name ', category_name)
            category_products = response.css('.col-md-6 .num-products label ::text').get('').replace('Products', '')
            print('category_name  ', category_products)
            self.category_products[category_name] = category_products

            all_subcategories_urls = response.css('#Brand li input[name="q"] ::attr(value)').getall() or []
            for subcategory in all_subcategories_urls:
                url = f"{response.url}?q={subcategory}&text=#"
                yield Request(url=url, callback=self.parse_subcategory_index, dont_filter=True)
        else:
            print('url response goto Parse-subcategory Index', response.url)
            yield from self.parse_subcategory_index(response=response)

    def parse_subcategory_index(self, response):
        try:
            category_name = response.css('meta[name="description"]::attr(content)').get('')
            category_products = response.css('.col-md-6 .num-products label ::text').get('')
            if category_products:
                category_products = ''.join([str(s) for s in category_products.split() if s.isdigit()])

            if int(category_products) > 21:
                yield from self.subcategories_filters(response)
                return

            products_urls = response.css('#resultsListRow .productImpressionTag .productMainLink::attr(href)').getall() or []
            for product_url in products_urls:
                url = urljoin(response.url, product_url)
                if url in self.current_scraped_items:
                    print('Url already scraped :', url)
                    continue

                if 'Beer' in self.category_products:
                    yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)
                else:
                    self.category_products[category_name] = category_products
                    yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)

        except Exception as e:
            print('Error form parse_subcategory_index Method : ', e)

    def parse_product_detail(self, response):
        try:
            item = OrderedDict()

            deal = response.meta.get('deal', '')
            if not deal:
                product = response.css('#dealsData ::text').get('').encode().decode('unicode-escape')
                if product:
                    product_data = json.loads(product)
                    if isinstance(product_data, list) and product_data:
                        deal = ''.join(Selector(text=product_data[0].get('title', '')).css(' ::text').getall())

            deal_start_date = response.xpath('//text()').re_first(r"'dimension15':\s*\"([^\"]+)\"")
            deal_start_date = deal_start_date.split('|')[0] if deal_start_date != 'NA' else ''
            deal_end_date = response.xpath('//text()').re_first(r"'dimension16':\s*\"([^\"]+)\"")
            deal_end_date = deal_end_date.split('|')[0] if deal_end_date != 'NA' else ''
            item['EAN'] = response.url.rstrip('/').split('/')[-1]
            item['SKU'] = response.css('h4 + table td:contains(SKU) + td::text').get('')
            item['Name'] = response.css('.last ::text').get('')
            item['Price'] = response.css('.product-summary .price-yourPrice .h1 ::text').get('')
            item['Save'] = response.css('.product-summary .price-save span + span::text').get('')

            if not 'sabmStore' in response.url:
                item['Deal'] = deal if deal else ''
            else:
                item['Deal'] = ''

            item['Deal Start Date'] = deal_start_date if not 'sabmStore' in response.url else ''
            item['Deal End Date'] = deal_end_date if not 'sabmStore' in response.url else ''
            item['URL'] = response.url

            self.current_scraped_items.append(item['URL'])
            self.scraped_items += 1
            print('scraped items are :', self.scraped_items)

            yield item

        except Exception as e:
            print('error from parse_product_detail Method : ', e)
            return

    def get_cookies(self, session_id, route):
        cookies = {
            'JSESSIONID': session_id,
            'ROUTE': route,
            'visid_incap_2581074': '2yMLdW15TnONQ9y5iXnk0fTr1mUAAAAAQUIPAAAAAACyWmtegt4QxIOFdWBOo0xp',
            'incap_ses_956_2581074': 'RWPZXPz5j0Zzghdx9mVEDfTr1mUAAAAAfUDeN55hy5s28vzklGiazw==',
            'sabmStore-rememberMe': 'H35QiboK3ZFg2rO2w5Cw5sk9i7m8XLtgFAjPr1havwF99P/W+Vb6wQcEjEk5sH9+BQNmb+cJblmwOWhsmZbOSVlw6I2yoGRS/NkhfLni7GBM8dZu2yiJYOCgKmnDFTVrKY7D1ECRqFUt4aeiC7ulK1xDVK3vSAJ6UiKDLsfFNAjSoXLT',
            'JSESSIONID': session_id,
        }

        return cookies

    def get_formdata(self):
        data = {
            'j_username': 'joe.iemma@jmshospitality.com.au',
            'j_password': 'Settle2023',
            'targetUrl': '',
            '_spring_security_remember_me': 'on',
            'CSRFToken': '9afa6260-33c3-4a83-88a9-d5cd6e346f89',
        }

        return data

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CubSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        try:
            filename = 'Status.txt'  # Corrected the filename string

            with open(filename, self.file_mode) as f:
                f.write(f"Category {''.join(self.category_products.keys())} \nProducts on web: {''.join(self.category_products.values())} \nProducts Scraped :{self.scraped_items}\n\n")

            if self.file_mode == 'w':
                self.file_mode = 'a'
            self.category_products = {}
            self.scraped_items = 0
        except Exception as e:
            print(f"Error writing to file: {e}")

        if self.categories_urls:
            url = self.categories_urls.pop(0)

            self.crawler.engine.crawl(Request(url=url, callback=self.parse_category))

    def subcategories_filters(self, response):
        filters = response.css('#Package li input[name="q"] ::attr(value)').getall() or []
        for filter_name in filters:
            url = f"{response.url.split('?q=')[0]}?q={filter_name}"
            yield Request(url=url, callback=self.subcategories_filters_index, dont_filter=True)

    def subcategories_filters_index(self, response):
        try:
            products_urls = response.css('#resultsListRow .productImpressionTag .productMainLink::attr(href)').getall() or []
            for product_url in products_urls:
                url = urljoin(response.url, product_url)
                if url in self.current_scraped_items:
                    print('Url already scraped :', url)
                    continue

                yield Request(url=url, callback=self.parse_product_detail, dont_filter=True)
        except Exception as e:
            print('Error form subcategories_filters_index Method : ', e)
