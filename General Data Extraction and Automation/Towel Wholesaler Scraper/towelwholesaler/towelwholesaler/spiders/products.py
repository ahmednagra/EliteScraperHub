import os
import re
import csv
import json
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Spider, Request, signals


class TowelWholesalerSpider(Spider):
    name = "products"
    base_url = 'https://www.towelwholesaler.com/'
    start_urls = ["https://www.towelwholesaler.com/"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.brand_name = ''
        self.brands = []
        self.items_scraped_count = 0
        self.total_brands_count = 0
        self.current_scraped_item = []

        self.fields = ['SKU', 'Type', 'Size', 'Color', 'Options', 'Price Per Each', 'Full Price', 'Stock Status',
                       'Brand', 'Category', 'Sub Category', 'Material', 'Title', 'Description', 'Images', 'Url']

        self.current_dt = datetime.now().strftime("%d%m%Y%H%M%S")
        self.output_directory = f'output/{self.current_dt}'

        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']
        self.logs_filename = f'logs/logs {self.current_dt}.txt'

    def parse(self, response, **kwargs):
        """
        Parse the initial page to extract brand names and URLs.
        """
        brands = response.css('.leftnavbar:contains("Manufacturer") table tr a')
        for brand in brands:
            name = brand.css('a ::text').get('').replace('/', '')
            url = urljoin(self.base_url, brand.css('a::attr(href)').get(''))

            brand_info = {
                'name': name,
                'url': url
            }

            self.brands.append(brand_info)

        self.total_brands_count = len(self.brands)
        self.mandatory_logs.append(f'Total Brands Exist: {self.total_brands_count}')

    def parse_brand_categories(self, response):
        """
        - Parse brand pages to extract categories and all sub categories until the leaf category reached.
        - If there is no categories found, check if it's a products listings page, if yes, send request for each that product
        - if it's not a categories page nor a products page, check if it's a details page of product, if yes, scrape the details of the product
        - At a time, there will be only one type of page. Either Category or products listings page or product details page
        """

        # If there are categories, parse them until the products listings page shows
        # product Detail page :

        if 'valign="bottom"' not in response.text:
            yield Request(url=response.url, callback=self.parse_product_details,
                          headers=self.headers, meta=response.meta, dont_filter=True)
            return

        brand_categories = response.css('.contents tr[valign="top"] a') or response.xpath(
            '//tr[@valign="bottom"]/td/center/a[@href]')

        if not brand_categories:
            self.mandatory_logs.append(f'\nThis Brand "{self.brand_name}" has no Further Subcategories :{response.url}')

        name = ''
        try:
            for category in brand_categories:
                name = category.css('a::text').get('').strip() or category.css('a::attr(title)').get('').strip()
                if not response.meta.get('category', ''):
                    response.meta['category'] = name

                elif not response.meta.get('subcategory', ''):
                    response.meta['subcategory'] = name

                # Extract the URL for the category
                category_url = category.css('a::attr(href)').get('')
                if not category_url:
                    continue

                category_url = urljoin(self.base_url, category_url)
                yield Request(url=category_url, callback=self.parse_brand_categories,
                              headers=self.headers, meta=response.meta)

        except Exception as e:
            self.error.append(f'Error parsing category Name:"{name}" url: {response.url} and Error : {e}')

    def parse_product_details(self, response):
        """
        Parse product detail pages to extract product information.
        """
        try:
            data = {}
            script_selector = response.css('script[type="application/ld+json"]:contains("sku")::text').get(
                '') or response.css('script[type="application/ld+json"]:contains("WebPage")::text').get('')
            if script_selector:
                # Remove double space
                script_selector = re.sub(r'\s+', ' ', script_selector)
                data = json.loads(script_selector)

            variants_choose = response.xpath('//select[contains(@name, "Choose")]/option')
            variants_color = response.xpath('//select[contains(@name, "Color")]/option')
            variants_size = response.xpath('//select[contains(@name, "Size")]/option')
            variants_size_weight = response.xpath('//select[contains(@name, "Choose Size and Weight")]/option')

            title = response.css('.itemimages + font h1::text').get('').strip() or data.get('name', '')
            description = response.css('.itemimages + font li::text').getall() or []
            sku = data.get('sku', '')

            if not variants_choose and not variants_color and not variants_size and not variants_size_weight:
                price_per_unit = ''.join(list(self.price_per_unit(data).values())[:1])
            else:
                price_per_unit = ''

            if not title:
                return

            item = OrderedDict()
            item['SKU'] = sku
            item['Type'] = self.get_value(response, 'Type')
            item['Options'] = {}
            item['Size'] = self.get_value(response, 'Size')
            item['Color'] = self.get_value(response, 'Color')
            item['Price Per Each'] = price_per_unit
            item['Full Price'] = data.get('offers', {}).get('price', '')
            item['Brand'] = self.brand_name
            item['Stock Status'] = 'In Stock' if 'addtocartImg' in response.text else 'Out Of Stock'
            item['Category'] = response.meta.get('category', '')
            item['Sub Category'] = response.meta.get('subcategory', '')
            item['Material'] = self.get_value(response, 'Material')
            item['Title'] = title
            item['Description'] = '\n'.join(
                [item.strip() for item in description if item.strip()]) if description else ''
            item['Images'] = response.css('[rel="gallery"]::attr(href)').getall() or [
                data.get('image', '')] if data.get('image', '') else []
            item['Url'] = data.get('url', '')

            if not variants_choose and not variants_color and not variants_size and not variants_size_weight:
                self.items_scraped_count += 1
                print(f'Current items scraped: {self.items_scraped_count}')
                self.current_scraped_item.append(item)
                return

            if variants_choose:
                for variant in variants_choose:
                    self.extract_variant_items(variant, data, item, key='')
                    continue

            if variants_color:
                for variant in variants_color:
                    self.extract_variant_items(variant, data, item, key='Color')
                    continue

            if variants_size:
                for variant in variants_size:
                    self.extract_variant_items(variant, data, item, key='Size')
                    continue

            if variants_size_weight:
                for variant in variants_size_weight:
                    self.extract_variant_items(variant, data, item, key='Size')
                    continue

        except Exception as e:
            self.error.append(f'Error PArse the Product Detail error: "{e}" Url= "{response.url}"')
            return

    def extract_variant_items(self, variant, data, item, key):
        item = item.copy()
        option = variant.css('::text').get('').strip()
        item['Options'] = {'Size': option}

        if key:
            item[key] = ''.join(variant.css('::text').get('').split('(')[0:1])

        item['Price Per Each'] = self.get_variant_price_per_each(data, option)
        self.items_scraped_count += 1
        print(f'Current items scraped: {self.items_scraped_count}')
        self.current_scraped_item.append(item)
        return

    def price_per_unit(self, data):
        price_raw = data.get('description', '').lower().replace('..', '.').lower().replace('$', '')
        price_dict = {}

        # Check for "per towel"
        if 'per towel' in price_raw:
            try:
                price = re.search(r'\$\d+\.\d+ per towel|\d+\.\d+ per towel', price_raw).group(0)
                price = price.split(' ')[0]  # Extract the price part
                price_dict['per towel'] = price
            except AttributeError:
                pass

        # Check for "per pillowcase"
        elif 'per pillowcase' in price_raw:
            try:
                price = re.search(r'\$\d+\.\d+ per pillowcase|\d+\.\d+ per pillowcase', price_raw).group(0)
                price = price.split(' ')[0]  # Extract the price part
                price_dict['per pillowcase'] = price
            except AttributeError:
                pass

        # Check for "per dozen"
        elif 'per dozen' in price_raw:
            if 'per dozen' in price_raw and 'each' not in price_raw:
                try:
                    string = re.search(r'\$\d+\.\d+ per dozen|\d+\.\d+ per dozen', price_raw).group(0)
                    price = re.search(r'\$\d+\.\d+|\d+\.\d+', string).group(0)
                    price_dict['each'] = '{:.2f}'.format(float(price)/ 12)  # get per_unit price
                except AttributeError:
                    pass
            elif 'each' in price_raw:
                try:
                    price = re.search(r'\$\d+\.\d+ each|\$[\d.]+(?=\seach)|\$\d+\.\d+|\d+\.\d+(?=\s+each)', price_raw).group(0)
                    price = price.split(' ')[0]  # Extract the price part
                    price_dict['each'] = price
                except AttributeError:
                    pass

        # Check for "each"
        elif 'each' in price_raw:
            try:
                price = re.search(r'\d+\.\d+(?=\s+each)', price_raw) or re.search(r'\$[\d.]+(?=\seach)|\$\d+\.\d+', price_raw)
                if price:
                    price = price[0]
                    price_dict['each'] = price
            except AttributeError:
                pass

        # Check for "dozen"
        elif 'dozen' in price_raw:
            try:
                match = re.search(r'\$\d+\.\d+', price_raw.split('dozen')[-1])
                if match:
                    price = match.group(0)
                    price_dict['dozen'] = price
            except Exception as e:
                pass

        # If no specific pattern matches, try to calculate price from 'offers' and 'description'
        if not price_dict:
            try:
                full_price = float(data.get('offers', {}).get('price', '').replace('$', ''))
                description_string = ''.join(data.get('description', '').split('1 case')[1:2])
                if description_string:
                    items = int(re.search(r'\d+', description_string).group(0))
                    calculated_price = '{:.2f}'.format(full_price / items)
                    price_dict['calculated'] = str(calculated_price)
                else:
                    price_dict['default'] = str(full_price)
            except:
                price_dict['default'] = str(data.get('offers', {}).get('price', ''))

        return price_dict

    def get_value(self, response, value):
        description = response.css('.itemimages + font li::text').getall() or []
        values = []

        # Iterate through each description line in the list
        for line in description:
            # Check if the description line contains the key
            if value.lower() in line.lower():
                # Extract digits from the line
                sizes = re.findall(r'\d+"?\s*x\s*\d+"?', line)

                # Check if there are sizes found
                if sizes:
                    # Append the sizes to the list of values
                    values.extend(sizes)
        return '\n'.join(values) if values else ''

    def write_items_to_json(self, brand_name):
        """
        Write items to JSON file.
        """
        os.makedirs(self.output_directory, exist_ok=True)
        output_file = os.path.join(self.output_directory, f'{brand_name}.json')

        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                for item in self.current_scraped_item:
                    fields = {field: item.get(field, '') for field in self.fields}
                    file.write(json.dumps(fields, ensure_ascii=False) + '\n')
        except Exception as e:
            self.error.append(f'Error occurred while writing items to JSON file: "{output_file}", Error: {e}')

    def get_variant_price_per_each(self, data, option):
        """
        Get the variant price per each item.

        Args:
            data: Dictionary containing product data.
            option: Variant option containing the price information.

        Returns:
            The variant price per each item.
        """
        option_variant_price = ''
        try:
            description = data.get('description', '').lower().replace('..', '.').lower()

            option_price_change = ''.join(option.split('$')[1:2])
            option_price_change = float(
                re.findall(r'\d+(?:\.\d+)?', option_price_change)[0]) if option_price_change else 0

            # Default price that show along option
            main_price = data.get('offers', {}).get('price', '')
            option_variant_price = '{:.2f}'.format(float(option_price_change) + float(main_price.replace('$', '')))

            # variant_key from Variant Option
            variant_key = ' '.join(option.split(' ')[0:1]).lower().strip()
            if '/' in variant_key:
                variant_key = ''.join(variant_key.split('/')[0:1])

            # Variant Options [Dozen , Case]
            if 'dozen' in option.lower():
                dozen_count = re.search(r'\b(\d+)\s+dozen\b', option.lower())[1] if re.search(r'\b(\d+)\s+dozen\b',
                                                                                              option.lower()) else 1
                if dozen_count:
                    dozen_count = int(dozen_count) * 12
                    price = '{:.2f}'.format(float(option_variant_price) / dozen_count)
                    return price

            elif ' case' in option.lower() and 'dozen' not in option.lower():
                case_count = re.search(r'case of (\d+)', option.lower()) or re.search(r'case\s+of\s+(\d+)',
                                                                                      option.lower())
                if case_count:
                    case_count = int(case_count.group(1))
                    price = '{:.2f}'.format(float(option_variant_price) / int(case_count))
                    return price

            elif 'per towel' in description and '$' not in option.lower():
                price = re.search(r'\$\d+\.\d+ per towel', description).group(0).split(' ')[0].replace('$',
                                                                                                       '') if re.search(
                    r'\$\d+\.\d+ per towel', description) else ''
                return price

            elif 'per sheet' in description and '$' not in option.lower():
                price = re.search(r'\$\d+\.\d+ per sheet', description).group(0).split(' ')[0].replace('$',
                                                                                                       '') if re.search(
                    r'\$\d+\.\d+ per sheet', description) else ''
                return price

            elif 'dozen' in description and 'each' not in description:
                match = re.search(r'\$[\s\S]*?dozen', description)
                if match:
                    price = ''.join(match[0].split('$')[-1:]).replace('per', '').replace('dozen', '').strip()
                    price = f"{'{:.2f}'.format(float(price) / 12)}"
                    return price

            elif 'each' in description:
                # first match the option key in description for get specific option key each price value
                variant_option = option.lower().split(' ')[:2]
                variant_option_any_match = re.findall(
                    r'\b(?:' + '|'.join(map(re.escape, variant_option)) + r')\b.*?each', description)

                if variant_key and 'each' in description:
                    price = re.findall(rf"{re.escape(variant_key)}.*?\$([\d.]+)\s+each", description)[
                            0:1] or re.findall(rf"{re.escape(variant_key)}.*?\$([\d.]+)", description)[0:1]
                    price = ''.join(price)
                    price = price if price else ''.join(
                        re.search(r'\$[\s\S]*?each', description)[0].split('$')[-1:]).replace('each', '').strip()

                    return price
                elif variant_option_any_match and '$' not in variant_option:
                    for string in variant_option_any_match:
                        if '$' in string and 'each' in string:
                            match = re.search(r'\$[\s\S]*?each', string)
                            if match:
                                price = ''.join(match[0].split('$')[-1:]).replace('each', '').strip()

                                return price

                else:
                    # option not match in description then get price for each
                    match = re.search(r'\$[\s\S]*?each', description)
                    if match:
                        price = ''.join(match[0].split('$')[-1:]).replace('each', '').strip()
                        return price

            else:
                return option_variant_price
        except:
            return option_variant_price

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filename, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                # print(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TowelWholesalerSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """

        print(f'\n\n{len(self.brands)}/{self.total_brands_count} Brands left to Scrape\n\n')

        if self.current_scraped_item:
            print(f'\n\nTotal {self.items_scraped_count} items scraped from Brand {self.brand_name}')
            self.mandatory_logs.append(f'\n\nTotal {self.items_scraped_count} items scraped from Brand {self.brand_name}')
            self.write_items_to_json(self.brand_name)
            self.brand_name = ''
            self.current_scraped_item = []
            self.items_scraped_count = 0

        if self.brands:
            brand = self.brands.pop(0)
            self.brand_name = brand.get('name', '')
            brand_url = brand.get('url', '')

            req = Request(url=brand_url,
                          callback=self.parse_brand_categories, dont_filter=True,
                          meta={'handle_httpstatus_all': True})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10

    def close(spider, reason):
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%Y-%m-%d %H%M%S")}"')
        spider.mandatory_logs.extend(spider.error)
        spider.write_logs()
