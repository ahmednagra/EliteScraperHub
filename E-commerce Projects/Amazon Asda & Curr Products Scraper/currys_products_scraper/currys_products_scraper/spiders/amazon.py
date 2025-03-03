import os
import re
import json
from datetime import datetime
from difflib import get_close_matches
from urllib.parse import urljoin
from collections import OrderedDict

import requests
from slugify import slugify
from scrapy import Spider, Request


class AmazonSpider(Spider):
    name = "amazon"
    current_dt = datetime.now().strftime("%d%m%Y%H%M")
    start_urls = ['https://www.amazon.co.uk/Best-Sellers-Grocery/zgbs/grocery/ref=zg_bs_nav_grocery_0']
    api_url = "https://phplaravel-1369810-5049628.cloudwaysapps.com/api/push-data"
    api_cat = "https://phplaravel-1369810-5049628.cloudwaysapps.com/api/categories"

    custom_settings = {
        # Zyte API Configuration
        'ZYTE_API_KEY': "bae3c3b2c954411ba6d0d8c0bae1842a",
        'ZYTE_API_TRANSPARENT_MODE': True,

        # Default headers for Zyte API
        'DEFAULT_REQUEST_HEADERS': {
            "zyte_api": {
                "httpResponseBody": True,
                "httpResponseHeaders": True,
            }
        },

        # Download Handlers
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
            "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        },

        # Middlewares
        'DOWNLOADER_MIDDLEWARES': {
            "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 633,
        },
        'SPIDER_MIDDLEWARES': {
            "scrapy_zyte_api.ScrapyZyteAPISpiderMiddleware": 100,
        },

        # Request Fingerprinter
        'REQUEST_FINGERPRINTER_CLASS': "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter",

        # Retry and concurrency settings
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        # 'CONCURRENT_REQUESTS': 3,
        'FEED_EXPORTERS': {
            'json': 'scrapy.exporters.JsonItemExporter',
        },

        'FEEDS': {
            f'output/Amazon Products Detail {current_dt}.json': {
                'format': 'json',
                'encoding': 'utf8',
                'fields': [
                    'retailer_id', 'retailer_name', 'retailer_country', 'retailer_website',
                    'product_id', 'product_title', 'product_description', 'promotion_type',
                    'promotion_description', 'promotion_price', 'promotion_discount',
                    'promotion_conditions', 'promotion_start_date', 'promotion_expiry',
                    'promotion_badge_type', 'rich_content_displayed', 'rich_content_images',
                    'timestamp'
                ]
            }
        }
    }

    def __init__(self):
        super().__init__()
        # Logs
        logs_dir = '/app/logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Generate the log file path with timestamp
        self.current_dt = datetime.now().strftime("%d%m%Y%H%M")
        self.logs_filepath = f'{logs_dir}/Amazon_logs_{self.current_dt}.txt'

        # Record script start time and write to log
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'[INIT] Script started at {self.script_starting_datetime}')

        self.scraped_urls = []
        self.items_scrapped = 0
        self.total_items = 0
        self.duplicates_count = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_categories, meta={'page': 'Indexing Page'})

    def parse_categories(self, response, **kwargs):
        if response.meta.get('page') == 'Indexing Page':
            yield from self.parse_products(response)

        # Get all the categories, sub categories sub_sub categories
        category_urls = self.get_sub_category_urls(response)
        print(f'Category exists: {len(category_urls)}')

        for url in category_urls:
            url = urljoin(response.url, url)
            print(f'Sub Category URl:{url}')
            yield Request(url=url, callback=self.parse_products)

        if not category_urls:
            print('No more Cate Category')
            yield from self.parse_products(response) #nested categories are ended

    def parse_products(self, response):
        category_name = response.css('[class*="_p13n-zg-nav-tree-all_style_zg-selected"] ::text').get('').strip()
        products_urls = list(set(response.css('#gridItemRoot a[role="link"]::attr(href)').getall()))

        if products_urls:
            self.total_items += len(products_urls)

            for product_url in products_urls:
                url = urljoin(response.url, product_url)

                print(f'Product URl:{url}')
                yield Request(url=url, callback=self.parse_details, meta={'category_name':category_name})

        next_page_url = self.get_next_page_url(response)
        if next_page_url: # no need pagination because need only first 50 products.
            a=1
            # yield Request(url=next_page_url, callback=self.parse_products, dont_filter=True)

    def parse_details(self, response):
        try:
            item = OrderedDict()

            # Extract retailer-specific category and MAp
            retailer_category = response.meta.get('category_name', '')
            standard_category = self.category_mapping(retailer_category)
            category_image_url = ''

            asin = response.url.replace('?th=1', '').split("/dp/")[1].split("/")[0] if response.url.replace('?th=1', '').count('/dp/') == 1 else None
            ship_from = self.get_shipped_from(response)
            sold_by = self.get_seller_name(response)
            discount_price = self.get_discounted_price(response)
            regular_price = self.get_regular_price(response)
            promotion_disc = regular_price - discount_price if regular_price > discount_price else 0.0

            item['retailer_id'] = response.css('#merchantID ::attr(value)').get('') or 'amazon_uk'

            item['retailer_category'] = retailer_category
            item['standard_category'] = standard_category
            item['category_image_url'] = category_image_url if category_image_url else None

            item['retailer_name'] = ship_from if ship_from else 'amazon_UK'
            item['retailer_country'] = ship_from if ship_from else 'UK'
            item['retailer_website'] = self.get_retailer_url(response)
            item['product_id'] = response.css('#ASIN ::attr(value)').get('') or asin
            item['product_title'] = response.css('#productTitle::text').get('').strip()
            item['product_description'] = '\n '.join(response.css('#feature-bullets .a-list-item::text').getall()) or ''
            item['promotion_type'] = response.css('[data-card-metrics-id="universal-detail-ilm-card_desktop-dp-atf_0"] img::attr(alt)').get('')
            item['promotion_price'] = discount_price
            item['promotion_discount'] = promotion_disc
            item['promotion_start_date'] = None
            item['promotion_expiry'] = None
            item['promotion_badge_type'] = None
            item['rich_content_displayed'] = False
            item['rich_content_images'] =  self.get_images(response, key='sec_img')
            iso_timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

            # Convert ISO 8601 format to MySQL-compatible format
            item['timestamp'] = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")

            self.post_to_api(item)
        except Exception as e:
            self.write_logs(f'Error Parsing item :{response.url} and error: {e}')

    def get_sub_category_urls(self, response):
        # bestseller category
        child_category = response.css(
            'div:has(span._p13n-zg-nav-tree-all_style_zg-selected__1SfhQ) ~ div[role="group"]')
        category_urls = response.css(
            'div[role="group"] div[role="treeitem"] a::attr(href)').getall() if child_category else []  # best seller categories url
        category_urls = category_urls or response.css(
            'ul > li > span > a.a-color-base.a-link-normal::attr(href)').getall()
        category_urls = category_urls or response.css(
            '.a-spacing-micro.s-navigation-indent-2 a::attr(href)').getall()

        return category_urls

    def get_product_urls(self, response):
        bestseller_tag = response.css('#gridItemRoot a:nth-child(2)::attr(href)')
        products_url = []

        if bestseller_tag:
            json_data = json.loads(response.css('[data-client-recs-list] ::attr(data-client-recs-list)').get(''))
            products_asins = [item['id'] for item in json_data]

            for asin in products_asins:
                url = f'https://www.amazon.com.au/dp/{asin}'
                products_url.append(url)

        products_url = products_url or response.css(
            '.s-line-clamp-2 a::attr(href), .s-line-clamp-4 a::attr(href)').getall()
        products_url = products_url or response.css(
            '.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-4 a::attr(href)').getall()
        products_url = products_url or [response.url]

        return products_url

    def get_next_page_url(self, response):
        next_page = response.css('.a-pagination .a-last a::attr(href)').get('')
        next_page = next_page or response.css('.s-pagination-selected + a::attr(href)').get('')
        next_page = next_page or response.css('.a-last a::attr(href)').get('')

        return response.urljoin(next_page)

    def get_product_information(self, response):
        product_information = {}

        rows = response.css('#productDetails_techSpec_section_1 tr') or response.css(
            '.content-grid-block table tr') or ''
        if not rows:
            product_details = (response.css('#detailBullets_feature_div li') or response.css('.content-grid-row-wrapper table tr, #productDetails_expanderTables_depthRightSections table tr')
                               or response.css('.content-grid-block table tr').getall())
        else:
            product_details = []

        for row in rows:
            key = row.css('th::text').get('') or row.css('td strong ::text').get('')
            value = '\n '.join(row.css('ul li ::text').getall()) or row.css('td p::text').get('') or row.css('td::text').get('')
            if key and value:
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key.strip()] = value

        for detail in product_details:
            key = detail.css('.a-text-bold::text, td strong ::text, th ::text').get('')
            value = detail.css('.a-text-bold + span::text, td ::text').get('').strip() or '\n '.join(detail.css('td li ::text').getall()) or ''.join(detail.css('td ::text').getall())
            if key and value:
                key = key.replace(':', '').replace('\u200e', '').replace(' \u200f', '')
                key = ' '.join(key.strip().split())
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key] = value

        additional_information = response.css('#productDetails_detailBullets_sections1 tr') or ''

        for row in additional_information:
            key = row.css('th::text').get('')
            value = ' '.join(row.css('td *::text').getall()).strip()
            if key and value:
                value = value.split('\n')[-1].strip()
                product_information[key.strip()] = value

        return product_information

    def get_discounted_price(self, response):
        # Try to get the price from multiple selectors
        price = (
                response.css('#attach-base-product-price::attr(value)').get('') or
                ''.join(response.css('#corePriceDisplay_desktop_feature_div .priceToPay ::text').getall()) or
                response.css('.reinventPricePriceToPayMargin .a-offscreen::text').get('').replace('£', '') or
                response.css('.apexPriceToPay span.a-offscreen::text').get('').replace('£', '')
        )

        if price:
            # Use regex to extract digits and convert to float
            match = re.search(r'\d[\d,]*\.?\d*', price)
            if match:
                price = float(match.group(0).replace(',', ''))
            else:
                price = 0.0  # If regex fails, fallback to 0.0
        else:
            price = 0.0  # If no price is found, return 0.0

        return price

    def get_regular_price(self, response):
        # Try to get the price from multiple selectors
        price = (
                response.css('.aok-relative .a-size-small.aok-offscreen::text').get('') or
                response.css('.a-price[data-a-color="secondary"] ::text').get('') or
                response.css('.basisPrice .a-offscreen::text').get('').replace('£', '')
        )

        if price:
            # Use regex to extract digits
            match = re.search(r'\d[\d,]*\.?\d*', price)
            if match:
                # Convert to float after removing commas
                price = float(match.group(0).replace(',', ''))
            else:
                price = 0.0  # If regex fails, fallback to 0.0
        else:
            price = 0.0  # If no price is found, return 0.0

        return price

    def get_process_price(self, response, item):
        item['Regular Price'] = response.css('.a-price-whole::text').get('')
        item['Sold By'] = response.css('#aod-offer-soldBy a[role="link"]::text').get('')
        item['Shipped From'] = response.css('#aod-offer-shipsFrom .a-color-base::text').get('')
        item['Shipping Cost'] = response.css(
            '#mir-layout-DELIVERY_BLOCK span[data-csa-c-delivery-price]::attr(data-csa-c-delivery-price)').get('')

        yield item

    def get_shipped_from(self, response):
        shipped = response.css('.a-section.show-on-unselected .truncate .a-size-small:nth-child(2)::text').get('')
        shipped = shipped or response.css(
            '.a-section.show-on-unselected span.a-size-small:contains(" Dispatched from: ") + span.a-size-small::text').get('')
        shipped = shipped or response.css('.offer-display-feature-text .offer-display-feature-text-message::text').get('')

        return shipped.strip() if shipped else ''

    def get_seller_name(self, response):
        sold = response.css(
            '.a-section.show-on-unselected .a-row:nth-child(2) .truncate .a-size-small:nth-child(2)::text').get('')
        sold = sold or response.css(
            '.a-section.show-on-unselected span.a-size-small:contains(" Sold by:") + span.a-size-small::text').get(
            '')
        sold = sold or response.css('.a-profile-descriptor::text').get('')
        sold = sold or response.css('[tabular-attribute-name="Sold by"] .tabular-buybox-text-message a::text').get(
            '')
        sold = sold or response.css('[tabular-attribute-name="Sold by"] .tabular-buybox-text-message span::text').get('')
        sold = sold or response.css('#sellerProfileTriggerId::text').get('').strip()

        return sold

    def get_retailer_url(self, response):
        url = response.css('#sellerProfileTriggerId ::attr(href)').get('')
        if url:
            url = urljoin(response.url, url)
            return url
        return None

    def get_shipping_cost(self, response):
        cost = response.css(
            'span[data-csa-c-delivery-type="delivery"]::attr(data-csa-c-delivery-price)').get(
            '').replace('£', '').replace('FREE', '').replace('fastest', '')

        cost = cost or response.css(
            'span[data-csa-c-delivery-type="delivery"]:not(:contains("FREE"))::attr(data-csa-c-delivery-price)').get(
            '').replace('£', '').replace('fastest', '').replace('FREE', '')


        return f'£{cost}' if cost else 'Free Shipping'

    def get_brand_name(self, response):
        brand = response.css('.po-brand .po-break-word::text').get('')
        brand = brand or response.css('#brand::text').get('')
        brand = brand or response.css('a#bylineInfo::text').get('').strip().lstrip('Brand:')

        return brand

    def get_images(self, response, key):
        try:
            images_json = json.loads(
                response.css('script[type="text/javascript"]:contains(ImageBlockATF)').re_first(
                    f"'colorImages':(.*)").rstrip(',').replace("'", '"')) or {}
            images_json = images_json.get('initial', [])
        except json.JSONDecodeError:
            images_json = []
        except AttributeError:
            images_json = []

        full_size_images_url = [item.get('hiRes', '') for item in images_json]
        images = [url for url in
                  response.css('.regularAltImageViewLayout .a-list-item .a-button-text img::attr(src)').getall() if
                  'images-na.ssl' not in url] or []

        # Function to get the ordinal suffix (e.g., '1st', '2nd', '3rd', etc.)
        def ordinal(n):
            suffix = ["th", "st", "nd", "rd"] + ["th"] * 6
            if n % 100 in [11, 12, 13]:  # Handle special cases like 11th, 12th, 13th
                return f"{n}th"
            else:
                return f"{n}{suffix[n % 10]}"

        if key=='primary_img':
            img = ''.join([img_dict.get('hiRes', '') for img_dict in images_json if img_dict.get('variant', '') == 'MAIN'])
            return img

        elif key=='sec_img':
            return full_size_images_url or images

        elif key=='image_seq':
            images_list = full_size_images_url or images
            image_sequence = [ordinal(i + 1) for i, _ in enumerate(images_list)] # get list then join for string
            return ', '.join(image_sequence)

        elif key=='video':
            try:
                video_dict = json.loads(response.css('script:contains("triggerVideoAjax")::text').re_first(r'{.*}'))
                video_list = video_dict.get('videos', [])
                if video_list:
                    url = video_list[0].get('url', '')
                    return url
            except json.JSONDecodeError as e:
                return ''

    def category_mapping(self, retailer_category):
        """
        Map retailer-specific categories to standard categories using a concise approach.
        """
        mapping_table = {
            'Soft Drinks': ['Coca-Cola', 'Pepsi', 'Fanta', 'Schweppes'],
            'Water': ['Evian', 'Volvic', 'Highland Spring'],
            'Juices & Smoothies': ['Tropicana', 'Innocent', 'Capri-Sun'],
            'Dairy & Milk': ['Arla', 'Alpro', 'Cravendale'],
            'Butter & Spreads': ['Lurpak', 'Flora', 'Anchor'],
            'Cheese': ['Cathedral City', 'Babybel', 'Philadelphia'],
            'Yogurts & Desserts': ['Müller', 'Activia', 'Yeo Valley'],
            'Bakery': ['Warburtons', 'Hovis', 'Kingsmill'],
            'Cereal & Breakfast': ['Kellogg’s', 'Weetabix', 'Quaker Oats'],
            'Frozen Foods': ['Birds Eye', 'McCain', 'Aunt Bessie’s'],
            'Meat & Poultry': ['British Chicken', 'Richmond Sausages'],
            'Seafood': ['Young’s', 'John West', 'Fish Fingers'],
            'Fruits & Vegetables': ['Fresh Produce', 'Dole', 'Green Giant'],
            'Pasta & Rice': ['Barilla', 'Tilda', 'Uncle Ben’s'],
            'Canned Goods': ['Heinz', 'Napolina', 'Batchelors'],
            'Snacks': ['Walkers', 'Pringles', 'Doritos'],
            'Confectionery': ['Cadbury', 'Mars', 'Haribo'],
            'Tea & Coffee': ['PG Tips', 'Nescafé', 'Tetley'],
            'Alcoholic Beverages': ['Budweiser', 'Heineken', 'Barefoot Wines'],
            'Pet Food': ['Pedigree', 'Whiskas', 'Felix'],
            'Health & Beauty': ['Dove', 'Colgate', 'Nivea'],
            'Cleaning Supplies': ['Fairy', 'Dettol', 'Persil'],
            'Toiletries': ['Andrex', 'Pampers', 'Always'],
            'Baby Products': ['Aptamil', 'Ella’s Kitchen', 'Huggies'],
            'Home Cleaning': ['Finish', 'Domestos', 'Flash'],
        }

        # Find the standard category for the retailer category
        for standard_category, retailer_categories in mapping_table.items():
            if retailer_category in retailer_categories:
                return standard_category

        # Default to 'Uncategorized' if no match is found
        return 'Uncategorized'

    def check_or_create_category(self, item):
        """
        Checks if a category exists in the database. If not, creates it.
        """
        category_name = item.get('standard_category')
        max_category_id = 0
        try:
            category_image_url = item.get('category_image_url')
            # Query the API to check if the category exists
            check_response = requests.get(url=self.api_cat)

            if check_response.status_code == 200:
                categories = check_response.json()
                if categories:  # Category exists
                    # Extract all category names and find the best match
                    category_names = [cat.get('category_name', '').lower() for cat in categories]
                    exact_match = next(
                        (cat for cat in categories if cat['category_name'].lower() == category_name.lower()), None)
                    if exact_match:
                        return exact_match['category_id']

                    # Use get_close_matches for a near match
                    close_matches = get_close_matches(category_name, category_names, n=1, cutoff=0.6)
                    if close_matches:
                        near_match = next((cat for cat in categories if cat['category_name'] == close_matches[0]), None)
                        if near_match:
                            return near_match['category_id']

            # If the category doesn't exist, create it
            category_ids = [cat.get('category_id') for cat in categories]
            max_category_id = max(category_ids)

            slug = slugify(category_name)
            payload = {
                'category_name': category_name,
                'category_slug': slug,
                'category_description': f'Products under {category_name}',
                'category_image_url': category_image_url,  # Placeholder image URL
                'parent_category_id': None,
                'category_created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'category_updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            cat_post = requests.post(self.api_cat, json=payload, headers={'Content-Type': 'application/json'})

            if cat_post.status_code == 200:  # Category created successfully
                created_category = cat_post.json()
                if 'Category successfully created' in created_category.get('message', ''):
                    new_cat_id = max_category_id + 1
                    return new_cat_id
            else:
                self.write_logs(f'[CHECK_OR_CREATE_CATEGORY] Failed to create category: {category_name}. '
                                f'Status Code: {cat_post.status_code}, Response: {cat_post.text}')
                return None
        except requests.exceptions.RequestException as e:
            self.write_logs(f'[CHECK_OR_CREATE_CATEGORY] Request error while processing category: {category_name}: {e}')
            return None
        except Exception as e:
            self.write_logs(f'[CHECK_OR_CREATE_CATEGORY] Unexpected error: {e}')
            return None


    def post_to_api(self, item):
        """
        Sends a POST request to the API with the item data. Ensures category exists or creates it.
        """
        try:
            # Ensure category exists or create it
            category_id = self.check_or_create_category(item)
            item['category_id'] = category_id

            # Convert item to JSON and send to the API
            api_res = requests.post(self.api_url, json=item, headers={'Content-Type': 'application/json'})

            if api_res.status_code == 200:
                self.items_scrapped += 1
                print('Items Scraped: ', self.items_scrapped)
                self.write_logs(
                    f'[POST_TO_API] Successfully uploaded data for product ID {item.get("product_id")}. Response: {api_res.json()}')
            else:
                self.write_logs(f'[POST_TO_API] Failed to upload data for product ID {item.get("product_id", "")}. '
                                f'Status Code: {api_res.status_code}, Response: {api_res.text}')

        except requests.exceptions.RequestException as e:
            self.write_logs(
                f'[POST_TO_API] Request error while uploading data for product ID {item.get("product_id", "")}: {e}')
        except Exception as e:
            self.write_logs(f'[POST_TO_API] Unexpected error: {e}')

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)


    def close(spider, reason):
        spider.write_logs(f'Spider Started at:{spider.script_starting_datetime}')
        spider.write_logs(f'Spider Stopped at:{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}')

        spider.write_logs(f'Total Items Found:{spider.total_items}')
        spider.write_logs(f'Total Items Scraped:{spider.items_scrapped}')
        spider.write_logs(f'Total Duplicate Items Found:{spider.duplicates_count}')

