import os
import json
from datetime import datetime
from collections import OrderedDict

from scrapy import Spider, Request, signals, Selector

"""
THIS SPIDER IS SCRAPING THE INFORMATION SECTION FIELDS IN SEPARATE COLUMNS. 
THE REST OF THE WORKING IS THE SAME 
"""


class PerfumeSpider(Spider):
    name = 'goldenscent2'
    start_urls = ['https://www.goldenscent.com/brands.html']  # start url of brands page

    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    post_headers = {
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://www.goldenscent.com',
        'Pragma': 'no-cache',
        'Referer': 'https://www.goldenscent.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'DOWNLOAD_DELAY': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,

        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEEDS': {
            f'output/GoldenScent Perfume Details {current_dt}.xlsx': {
                'format': 'xlsx',
                'fields': ['Title', 'Brand', 'Perfume Id', 'Rating', 'Votes Count', 'Sku', 'Size', 'Price',
                           'Special Price', 'Stock Status', 'Gender', 'Product Type', 'Fragrance Family',
                           'Year of Launch', 'Concentration', 'Base Notes', 'Middle Notes', 'Top Notes',
                           'Ingredients', 'Delivery Time', 'Description', 'URL', 'Images'],
            }
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.brands = []
        self.brand_name = ''
        self.total_brands_count = 0  # found total brands on the website

        self.brand_items_scraped_count = 0  # perfume scraped from detail page
        self.brand_total_listing_page = 0  # Brand Found Total Perfumes at pagination
        self.current_scraped_item_list = []
        self.scraper_items_count = 0  # perfume scraped from scraper
        self.perfume_ids = []  # for avoid duplication
        self.duplicates_count = 0

        # logs
        os.makedirs('logs', exist_ok=True)
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'Script Started at "{self.script_starting_datetime}"\n')

    def parse(self, response, **kwargs):
        """
           Parse the initial page to extract Perfume Brands names and URLs.
        """
        try:
            script = ''.join(''.join(
                response.css('script:contains("__INITIAL_STATE__") ::text').get('').split('__INITIAL_STATE__=')[1:]).split(';(function()')[0:1])
            data = json.loads(script)
        except json.JSONDecodeError as e:
            self.write_logs(f'Error occurred while json in parse function: {str(e)}')
            return

        try:
            brands = data.get('brands', {}).get('filteredBrands', [])
            for brand_dict in brands:
                brand_list = brand_dict.get('data', [])
                for brand in brand_list:
                    name = brand.get('name', '')
                    url = f"https://www.goldenscent.com/en/brands/{name}.html?action=brands&id={brand.get('id', '')}"
                    p_id = brand.get('id', '')

                    if name and p_id:
                        brand_info = {
                            'name': name,
                            'p_id': p_id,
                            'url': url
                        }

                        self.brands.append(brand_info)
            self.total_brands_count = len(self.brands)

        except Exception as e:
            self.write_logs(f'Error occurred while parse function: {str(e)}')

    def parse_brand_pagination(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.write_logs(f'Error occurred while json in parse function: {str(e)} Brand Name:{self.brand_name} Brand_id: {response.meta.get("brand_id", "")}')
            return

        total_perfumes = data.get('results', [])[0].get('nbHits', '')
        self.brand_total_listing_page += int(total_perfumes)

        yield from self.parse_perfume_details(response)

        if total_perfumes >= 1000 and not response.meta.get('filter', ''):
            self.write_logs(f"{self.brand_name} has Total Perfumes {total_perfumes} Brand ID :{response.meta.get('brand_id', '')}  URL:{response.meta.get('brand_url', '')} :{response.meta.get('filter', '')}")
            price = [('0', '100'), ('100', '200'), ('200', '300'), ('300', '400'),
                     ('400', '500'), ('500', '600'), ('600', '700'), ('700', '10000')
                     ]

            for min_price, max_price in price:
                brand_id = response.meta.get('brand_id', '')
                formdata = self.get_formdata(brand_id=brand_id, minimum_price=min_price, maximum_price=max_price)
                response.meta['duplicate_filter'] = True
                response.meta['filter'] = f'Min Price :{min_price}, Max Price:{max_price}'

                yield Request(url=self.get_post_request_url(), headers=self.post_headers, method='POST', body=formdata,
                              callback=self.parse_brand_pagination, meta=response.meta)

    def parse_perfume_details(self, response):
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            self.write_logs(f'Error occurred while json in parse function: {str(e)}')
            return

        perfumes = data.get('results', [])
        if perfumes:
            perfumes = perfumes[0].get('hits', [])

        if not perfumes:
            self.write_logs(f"No perfumes found for brand: {self.brand_name}. URL: {response.meta.get('brand_url', '')}\n")
            return

        # list of multiples perfumes Information
        for perfume in perfumes:
            # Multiple Perfumes Size
            size_options = perfume.get('size_new', [])
            if isinstance(size_options, str):
                size_options = [size_options]

            if not size_options:
                item = self.get_item(perfume=perfume, size_option='', response=response)
                if item:
                    yield item
            else:
                for size_option in size_options:
                    item = self.get_item(perfume=perfume, size_option=size_option, response=response)
                    if item:
                        yield item

    def get_item(self, perfume, size_option, response):
        title = url = perfume_id = ''
        try:
            item = OrderedDict()
            size_dict = {}

            if size_option:
                associate_products = perfume.get('associated_products', [])
                if associate_products:
                    size_dict = [product for product in associate_products if
                                 product.get('option', {}).get('size', '').lower() == size_option.lower()][0]

            perfume_id = size_dict.get('id', '') or perfume.get('objectID', '')

            if perfume_id in self.perfume_ids:
                self.duplicates_count += 1
                return None

            title = size_dict.get('name', '') or perfume.get('name', '')
            url = size_dict.get('url', '') or perfume.get('url', '')
            rating = perfume.get('review', {}).get('average', 0.0)
            reviews_count = perfume.get('review', {}).get('count', 0)
            info_dict = self.get_info_dict(perfume, size_dict)

            item['Title'] = title
            item['Brand'] = perfume.get('brand_value', '')
            item['Perfume Id'] = perfume_id
            item['Rating'] = rating if rating != 0.0 else ''
            item['Votes Count'] = reviews_count if reviews_count != 0 else ''
            item['Description'] = self.get_description(perfume)
            item['Images'] = self.get_images(size_dict, perfume)
            item['Sku'] = size_dict.get('associated_sku', '') or ', '.join(perfume.get('sku', []))
            item['Ingredients'] = perfume.get('ingredients', '')
            item['Size'] = size_option.replace('ml', 'مل')
            item['Price'] = size_dict.get('regular_price', '') or perfume.get('price', {}).get('SAR', {}).get(
                'default', 0)
            item['Special Price'] = size_dict.get('special_price', '') or perfume.get('special_price', '')
            item['Stock Status'] = 'In Stock' if size_dict.get('status', '') or perfume.get('in_stock',
                                                                                            '') else 'Out of Stock'
            item['Delivery Time'] = size_dict.get('delivery_time', '') or perfume.get('delivery_time', '')
            item['URL'] = url

            # Perfume Information
            item['Information'] = self.get_information(perfume, size_dict)

            # for field in info_fields:
            item['Gender'] = info_dict.get('الجنس', '')
            item['Product Type'] = info_dict.get('نوع المنتج', '')
            item['Character'] = info_dict.get('شخصية عطرك', '') or info_dict.get('حسية', '')
            item['Fragrance Family'] = info_dict.get('العائلة العطرية', '')
            item['Year of Launch'] = info_dict.get('سنة الإصدار', '')
            item['Concentration'] = info_dict.get('نسبة التركيز', '')
            item['Base Notes'] = info_dict.get('قاعدة العطر', '')
            item['Middle Notes'] = info_dict.get('قلب العطر', '')
            item['Top Notes'] = info_dict.get('مقدمة العطر', '')

            self.perfume_ids.append(perfume_id)
            self.current_scraped_item_list.append(item)

            self.brand_items_scraped_count += 1
            self.scraper_items_count += 1  # perfume scraped from scraper

            return item
        except Exception as e:
            self.write_logs(f'Perfume: "{title}" ID: "{perfume_id}" URL: "{url}" Detail parsing error :"{e}')
            return None

    def get_images(self, size_dict, perfume):
        dict = size_dict if size_dict else perfume
        main_image = dict.get('imageURL', '') or dict.get('image_url', '')
        if main_image.startswith('//'):
            main_image = 'https:' + main_image

        gallery_images = [image['url'] for image in dict.get('gallery', {}).get('images', [])]

        all_image_urls = [main_image] + gallery_images

        # Join the URLs into a single string separated by commas
        all_image_urls = ', '.join(all_image_urls)
        return all_image_urls

    def get_info_dict(self, perfume, size_dict):
        data_dict = size_dict if size_dict else perfume
        try:
            exempt_keys = ['id', 'regular_price', 'imageURL', 'delivery_time', 'brand_value', 'name', 'description', 'short_name', 'currency', 'attribute_set', 'type_id',
                           'url', 'image_url', 'thumbnail_url', 'product_tier', 'exclusive', 'sku', 'price',
                           'visibility', 'status', 'news_from_date', 'news_to_date', 'gallery', 'template_type',
                           'special_price', 'brand_label', 'brand_id', 'visibility_search', 'visibility_catalog',
                           'categories', 'categories_without_path', 'category_ids', 'rating_summary', 'breadcrumb_mapping',
                           'in_stock', 'associated_products', 'mobile_link', 'date_added', 'algoliaLastUpdateAtCET',
                           'algoliaLastUpdateSource', 'objectID', '_highlightResult', 'swatch']

            info_dict = {details['key']: details['value'] for details in data_dict.get('product_details', {}).values()}
            extracted_data = {}

            if not info_dict:

                def convert_list_to_string(value):
                    """Converts a list to a comma-separated string."""
                    if isinstance(value, list):
                        return ', '.join(str(v) for v in value)
                    return value

                for key, value in data_dict.items():
                    if key not in info_dict and key not in exempt_keys:
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                extracted_data[sub_key] = convert_list_to_string(sub_value)
                        else:
                            extracted_data[key] = convert_list_to_string(value)

                info_dict = {}
                for key, value in extracted_data.items():
                    if not isinstance(value, dict):
                        info_dict[key] = value
                    else:
                        # Extract value from nested dictionary (modify as needed)
                        key = value.get('key', '')
                        value = value.get('value', '')
                        if key:
                            info_dict[key] = value

            return info_dict
        except Exception as e:
            perfume_id = data_dict.get('id', '') or data_dict.get('objectID', '')
            title = data_dict.get('name', '')
            url = data_dict.get('url', '')
            self.write_logs(f'Perfume: "{title}" ID: "{perfume_id}" URL: "{url}" Getting Information parsing error :"{e}')
            return None

    def get_information(self, perfume, size_dict):
        dict = size_dict if size_dict else perfume
        exempt_keys = ['id', 'regular_price', 'imageURL', 'delivery_time', 'brand_value', 'name', 'description',
                       'short_name', 'currency', 'attribute_set', 'type_id',
                       'url', 'image_url', 'thumbnail_url', 'product_tier', 'exclusive', 'sku', 'price',
                       'visibility', 'status', 'news_from_date', 'news_to_date', 'gallery', 'template_type',
                       'special_price', 'brand_label', 'brand_id', 'visibility_search', 'visibility_catalog',
                       'categories', 'categories_without_path', 'category_ids', 'rating_summary', 'breadcrumb_mapping',
                       'in_stock', 'associated_products', 'mobile_link', 'date_added', 'algoliaLastUpdateAtCET',
                       'algoliaLastUpdateSource', 'objectID', '_highlightResult', 'swatch']

        # Create a dictionary with all the details from `product_details` if available
        info_dict = {details['key']: details['value'] for details in dict.get('product_details', {}).values()}

        if not info_dict:
            def convert_list_to_string(value):
                if isinstance(value, list):
                    return ', '.join(str(v) if not isinstance(v, dict) else str(v) for v in value)
                return value

            # Populate info_dict with values from perfume, converting lists to strings
            for key, value in perfume.items():
                if key not in info_dict and key not in exempt_keys:
                    info_dict[key] = convert_list_to_string(value)

        # Create the formatted output string
        formatted_output = []
        for key, value in info_dict.items():
            # Capitalize the first letter and replace underscores with spaces
            formatted_key = key.replace('_', ' ').title()
            formatted_output.append(f"{formatted_key}: {value}")

        # Join all formatted entries with new lines
        info = '\n'.join(formatted_output)
        return info

    def get_description(self, perfume):
        # Extract and clean the description HTML using Scrapy
        description_html = perfume.get('description', '')
        selector = Selector(text=description_html)
        description_text = selector.xpath('string(.)').get('').strip()
        description_text = description_text.replace('Description:', '')

        return description_text

    def get_formdata(self, brand_id, minimum_price, maximum_price):
        if not minimum_price:
            data = f'{{"requests":[{{"indexName":"magento_ar_sa_products","params":"query=%22{brand_id}%22&hitsPerPage=1000&maxValuesPerFacet=20&page=0&typoTolerance=false&restrictSearchableAttributes=%5B%22category_ids%22%5D&advancedSyntax=true&analytics=false&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&clickAnalytics=true&facets=%5B%22gender%22%2C%22brand_new%22%2C%22product_type_new2%22%2C%22fragrance_notes%22%2C%22character%22%2C%22concentration%22%2C%22product_category%22%2C%22makeup_color%22%2C%22makeup_type%22%2C%22area_of_apply%22%5D&tagFilters="}}]}}'
            # eng results
            # data = f'{{"requests":[{{"indexName":"magento_en_sa_products","params":"query={brand_id}&hitsPerPage=1000&maxValuesPerFacet=20&page=0&typoTolerance=false&restrictSearchableAttributes=[\\"category_ids\\"]&advancedSyntax=true&analytics=false&highlightPreTag=__ais-highlight__&highlightPostTag=__/ais-highlight__&clickAnalytics=true&facets=[\\"gender\\",\\"brand_new\\",\\"product_type_new2\\",\\"fragrance_notes\\",\\"character\\",\\"concentration\\",\\"product_category\\",\\"makeup_color\\",\\"makeup_type\\",\\"area_of_apply\\"]&tagFilters="}}]}}'
        else:
            data = f'{{"requests":[{{"indexName":"magento_ar_sa_products","params":"query=%22{brand_id}%22&hitsPerPage=8&maxValuesPerFacet=20&page=0&typoTolerance=false&restrictSearchableAttributes=%5B%22category_ids%22%5D&advancedSyntax=true&analytics=false&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&clickAnalytics=true&facets=%5B%22gender%22%2C%22brand_new%22%2C%22product_type_new2%22%2C%22fragrance_notes%22%2C%22character%22%2C%22concentration%22%2C%22product_category%22%2C%22makeup_color%22%2C%22makeup_type%22%2C%22area_of_apply%22%5D&tagFilters=&numericFilters=%5B%22price.SAR.default%3E%3D{minimum_price}%22%2C%22price.SAR.default%3C%3D{maximum_price}%22%5D"}}]}}'

        return data

    def get_post_request_url(self):
        url = 'https://s7prcq95b5-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia for JavaScript (3.35.1); Browser (lite); instantsearch.js (3.6.0); Vue (2.6.12); Vue InstantSearch (2.7.1); JS Helper (2.28.1)&x-algolia-application-id=S7PRCQ95B5&x-algolia-api-key=bed7f0e03f982f3ff679b25691f03895'
        return url

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def close(spider, reason):
        spider.write_logs(f"\n\nScraper Total Scraped Perfumed Details: {spider.scraper_items_count}")
        spider.write_logs(f"Scraper Total Duplicates Perfumed Found: {spider.duplicates_count}")
        spider.write_logs(f"Scraper started from {spider.script_starting_datetime}")
        spider.write_logs(f'Scraper Stopped at {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PerfumeSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """
        if self.brand_items_scraped_count:
            # Log the success of scraping items from the current brand
            self.write_logs(
                f'Successfully scraped {self.brand_items_scraped_count} out of {self.brand_total_listing_page} Perfumes from the Brand: {self.brand_name}\n'
            )

        if self.brands:
            # Log the initial number of brands left to scrape before popping
            # self.write_logs(f'\n{len(self.brands)}/{self.total_brands_count} Brands left to scrape')
            self.write_logs(f'{len(self.brands) - 1} out of {self.total_brands_count} Brands remaining to scrape.')

            # Log the brand that is about to be scraped
            self.write_logs(f'Starting to scrape the Brand: {self.brands[0]["name"]}')

        self.brand_name = ''
        self.brand_items_scraped_count = 0  # perfume scraped from detail page
        self.brand_total_listing_page = 0  # Category Found Total Products at pagination
        self.current_scraped_item_list = []

        if self.brands:
            brand_dict = self.brands.pop(0)
            self.brand_name = brand_dict.get('name', '')
            brand_id = brand_dict.get('p_id', '')
            brand_url = brand_dict.get('url', '')

            formdata = self.get_formdata(brand_id, minimum_price='', maximum_price='')
            req = Request(url=self.get_post_request_url(), headers=self.post_headers, method='POST', body=formdata,
                          callback=self.parse_brand_pagination,
                          meta={'handle_httpstatus_all': True, 'brand_url': brand_url, 'brand_id': brand_id})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
