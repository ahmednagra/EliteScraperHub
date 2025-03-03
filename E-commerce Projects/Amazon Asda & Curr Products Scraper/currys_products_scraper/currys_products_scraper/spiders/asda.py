import ast
import math
import os
import re
import json
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

import requests
from scrapy import Spider, Request, FormRequest, Selector


class AsdaGroceriesSpider(Spider):
    name = "asda"
    allowed_domains = ["groceries.asda.com"]
    start_urls = ["https://groceries.asda.com/special-offers/all-offers"]
    qraphsql_api_url = 'https://groceries.asda.com/api/bff/graphql'
    api_url = "https://phplaravel-1369810-5049628.cloudwaysapps.com/api/push-data"

    current_dt = datetime.now().strftime("%d%m%Y%H%M")

    custom_settings = {
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        'FEED_EXPORTERS': {
            'json': 'scrapy.exporters.JsonItemExporter',
        },

        'FEEDS': {
            f'output/Asda Groceries Scraper {current_dt}.json': {
                'format': 'json',
                'encoding': 'utf8',
                'fields': ['retailer_id', 'retailer_name', 'retailer_country', 'retailer_category',
                           'retailer_category_id', 'standard_category', 'retailer_website', 'category_id',
                           'product_id', 'product_title', 'product_description',
                           'promotion_type', 'promotion_price', 'promotion_discount', 'promotion_description',
                           'PRICE_SAVING','LOYALTY_DISCOUNT','EXCLUSIVE', 'promotion_start_date',
                            'promotion_expiry', 'promotion_badge_type', 'rich_content_displayed',
                            'brand_logo_url', 'retailer_logo_url', 'rich_content_images', 'timestamp', 'url'
                        ]
                    }
                }
    }

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'content-type': 'application/json',
        'origin': 'https://groceries.asda.com',
        'priority': 'u=1, i',
        'referer': 'https://groceries.asda.com/special-offers/all-offers',
        'request-origin': 'gi',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'wm_svc.env': 'prod',
        'wm_svc.name': 'ASDA-BFF',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items_scrapped = 0
        # Logs
        logs_dir = '/app/logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Generate the log file path with timestamp
        self.current_dt = datetime.now().strftime("%d%m%Y%H%M")
        self.logs_filepath = f'{logs_dir}/asda_logs_{self.current_dt}.txt'

        # Record script start time and write to log
        self.script_starting_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.write_logs(f'[INIT] Script started at {self.script_starting_datetime}')


    def start_requests(self):
        categories= ['super_dept_name', 'Toiletries & Beauty', 'Food Cupboard', 'Home & Entertainment', 'Chilled Food',
                    'Beer, Wine & Spirits', 'Health & Wellness', 'Frozen Food','Pet Food & Accessories','Drinks',
                    'Baby, Toddler & Kids', 'Laundry & Household', 'Bakery', 'Meat, Poultry & Fish', 'World Food',
                    'Fruit, Veg & Flowers', 'Dietary & Lifestyle', 'Christmas'
                ]

        for cat in categories:
            data = self.get_data(category=cat, page_id=False)
            yield Request(self.qraphsql_api_url, headers=self.headers, method='POST', body=json.dumps(data), dont_filter=True,
                          callback=self.pagination, meta={'handle_httpstatus_all': True, 'category':cat})

    def pagination(self, response, **kwargs):
        try:
            data_dict = response.json()
        except json.JSONDecoder as e:
            print('Error :',e)
            data_dict = {}

        category = response.meta.get('category', '')

        listing_items = []
        zones_dict = data_dict.get('data', {}).get('tempo_cms_content', {}).get('zones', [{}])
        product_listing = [dict for dict in zones_dict if dict.get('type', '')=='ProductListing']

        # If product_listing exists and has valid 'configs' and 'products'
        if product_listing:
            listing_items = product_listing[0].get('configs', {}).get('products', None)

            # Proceed only if listing_items is not None and is a list
            if listing_items:
                items = listing_items.get('items', [{}])

                for item in items:
                    item_id = item.get('item_id', '')
                    data = self.get_data(category=category, page_id=item_id)
                    print('Product Called:', item.get('item', {}).get('name', ''))

                    yield Request(self.qraphsql_api_url, headers=self.headers, method='POST', body=json.dumps(data),
                                  callback=self.parse_detail, dont_filter=True, meta={'handle_httpstatus_all': True})
            else:
                # Handle the case where listing_items is None (optional)
                self.write_logs(f"Category:{category}  No listing items found.")
        else:
            # Handle the case where no ProductListing was found in zones (optional)
            self.write_logs(f"Category:{category}  No product listings available.")

        # pagination
        if product_listing and not response.meta.get('pagination'):
            facets = product_listing[0].get('configs', {}).get('facets', [])
            if facets:
                count = [item.get('count', 0) for facet in facets for item  in facet.get('items', []) if item.get('facet', '') == category]
                if count:
                    total_products = sum(count)

    def parse_detail(self, response):
        try:
            data_dict = response.json()
        except json.JSONDecoder as e:
            print('Error :', e)
            data_dict = {}

        listing_items = {}
        zones_dict = data_dict.get('data', {}).get('tempo_cms_content', {}).get('zones', [{}])
        product_listing = [zone for zone in zones_dict if zone.get('configs', {}).get('type', '') == 'PdpPrimaryInfo']

        if product_listing:
            listing_items = product_listing[0].get('configs', {}).get('products', {}).get('items', [])
            if listing_items:
                listing_items = listing_items[0]
        else:
            print('Product Detail not found')
            return
        try:
            promotion_price = listing_items.get('price', {}).get('price_info', {}).get('price', '0.0')
            promotion_price = re.sub(r'[^\d.]', '', promotion_price) if promotion_price else 0.0

            info = listing_items.get('item', {})

            # Extract retailer-specific category and MAp
            retailer_category = info.get('taxonomy_info', {}).get('category_name', '')

            promo_description, promotion_discount, price_save, loyalty_disc, exclusive = self.get_promotion_discount(listing_items)
            # Use regex to extract digits and decimals
            integer_discount = 0
            match = re.search(r'\d+(\.\d+)?', promotion_discount)
            if match:
                integer_discount = int(float(match.group()))
            else:
                integer_discount = 0

            item = OrderedDict()
            item['retailer_id'] = 'Asda'
            item['retailer_name'] = 'ASDA'
            item['retailer_country'] = 'Usa'
            item['retailer_category'] = retailer_category
            item['retailer_category_id'] = info.get('taxonomy_info', {}).get('category_name', '')
            item['standard_category'] = self.category_mapping(retailer_category)
            item['retailer_website'] = ''
            item['category_id'] = info.get('taxonomy_info', {}).get('category_id', '')
            item['product_id'] = info.get('cin', '')
            item['product_title'] = info.get('name', '')
            item['product_description'] = self.get_prod_description(listing_items)
            item['promotion_type'] = self.get_promo_type(listing_items)
            item['promotion_price'] = promotion_price
            # item['promotion_discount'] = promotion_discount
            item['promotion_discount'] = integer_discount
            item['promotion_description'] = promo_description
            item['PRICE_SAVING'] = price_save if price_save else ''
            item['LOYALTY_DISCOUNT'] = loyalty_disc if loyalty_disc else ''
            item['EXCLUSIVE'] = exclusive if exclusive else ''
            item['promotion_start_date'] = ''
            item['promotion_expiry'] = ''
            item['promotion_badge_type'] = ''
            item['rich_content_displayed'] = False
            item['brand_logo_url'] = ''
            item['retailer_logo_url'] = ''
            item['rich_content_images'] = self.get_images(listing_items)

            iso_timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            # Convert ISO 8601 format to MySQL-compatible format
            item['timestamp'] = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
            item['url'] = f"https://groceries.asda.com/product/{listing_items.get('item_id', '')}"

            if item['product_title']:
                # yield item
                self.post_to_api(item)
            else:
                pass
        except Exception as e:
            self.write_logs(f"Error Yield Item = {e} URL={response.url}")

    def get_data(self, category, page_id):
        pay_load = {}
        contract = ''
        if page_id:
            contract = 'web/cms/product-details-page'
            pay_load= {
            # 'page_id': '1000287073916',
            'page_id': page_id,
            'page_type': 'productDetailsPage',
            'page_meta_info': True,
        }
        elif category:
            contract = 'web/cms/offers-new'
            pay_load = {
                    'cacheable': True,
                    'filter_query': [
                        {
                            'field': 'super_dept_name',
                            'value': category,
                        },
                        {
                            'field': 'price_offer',
                            'value': 'Yes',
                        },
                    ],
                    'page_type': 'offersNew',
                    'page_id': 'all-offers',
                }

        json_data = {
            'requestorigin': 'gi',
            # 'contract': 'web/cms/offers-new',
            'contract': contract,
            'variables': {
                'user_segments': [
                    '1007',
                    '1019',
                    '1020',
                    '1023',
                    '1024',
                    '1027',
                    '1038',
                    '1041',
                    '1042',
                    '1043',
                    '1047',
                    '1053',
                    '1055',
                    '1057',
                    '1059',
                    '1067',
                    '1070',
                    '1082',
                    '1087',
                    '1097',
                    '1098',
                    '1099',
                    '1100',
                    '1102',
                    '1105',
                    '1107',
                    '1109',
                    '1110',
                    '1111',
                    '1112',
                    '1116',
                    '1117',
                    '1119',
                    '1123',
                    '1124',
                    '1126',
                    '1128',
                    '1130',
                    '1140',
                    '1141',
                    '1144',
                    '1147',
                    '1150',
                    '1152',
                    '1157',
                    '1159',
                    '1160',
                    '1165',
                    '1166',
                    '1167',
                    '1169',
                    '1170',
                    '1172',
                    '1173',
                    '1174',
                    '1176',
                    '1177',
                    '1178',
                    '1179',
                    '1180',
                    '1182',
                    '1183',
                    '1184',
                    '1186',
                    '1189',
                    '1190',
                    '1191',
                    '1194',
                    '1196',
                    '1197',
                    '1198',
                    '1201',
                    '1202',
                    '1204',
                    '1206',
                    '1207',
                    '1208',
                    '1209',
                    '1210',
                    '1213',
                    '1214',
                    '1216',
                    '1217',
                    '1219',
                    '1220',
                    '1221',
                    '1222',
                    '1224',
                    '1225',
                    '1227',
                    '1231',
                    '1233',
                    '1236',
                    '1237',
                    '1238',
                    '1239',
                    '1241',
                    '1242',
                    '1245',
                    '1247',
                    '1249',
                    '1256',
                    '1259',
                    '1260',
                    '1262',
                    '1263',
                    '1264',
                    '1269',
                    '1271',
                    '1278',
                    '1279',
                    '1283',
                    '1284',
                    '1285',
                    '1288',
                    '1291',
                    'test_4565',
                    '4565_test',
                    '1293',
                    '1294',
                    '1295',
                    '1296',
                    '1298',
                    '1299',
                    '1301',
                    '1302',
                    '1303',
                    '1308',
                    '1304',
                    '1305',
                    '1306',
                    '1309',
                    '1310',
                    '1311',
                    '1312',
                    'dp-false',
                    'wapp',
                    'store_4565',
                    'vp_XL',
                    'anonymous',
                    'clothing_store_enabled',
                    'checkoutOptimization',
                    'NAV_UI',
                    'T003',
                    'T014',
                    'rmp_enabled_user',
                ],
                'is_eat_and_collect': False,
                'store_id': '4565',
                'type': 'offersNew',
                'page_size': 500,
                'page': 1,
                'request_origin': 'gi',
                'ship_date': 1732752000000,
                'payload': pay_load,
            },
        }

        return json_data

    def format_listing_info(self, prod_des_dict):
        result = []

        for key, value in prod_des_dict.items():
        # for key, value in prod_des_dict.get('bb_connect').items():
            if not value:
                continue
            # if key has nested dict
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if not sub_value:
                        continue
                    # Add the key and value to the result list
                    result.append(f"{sub_key.replace('_', ' ').title()}\n{sub_value}")

            # If value is a list or dict, convert to string for display
            if isinstance(value, (dict, list)):
                value = str(value)

            # Add the key and value to the result list
            result.append(f"{key.replace('_', ' ').title()}\n{value}")

        # Join the result into a final description
        description = "\n\n".join(result)
        return description

    def get_images(self, listing_items):
        urls = []
        img_id = listing_items.get('item', {}).get('images', {}).get('scene7_id', '')
        img_host = listing_items.get('item', {}).get('images', {}).get('scene7_host', '')
        for no in range(1, 3): #mean no 1,2
            urls.append(f'{img_host}{img_id}_T{no}?wid=1000&hei=1000')

        return urls

    def get_promo_type(self,listing_items):
        promotion_info = listing_items.get('promotion_info', [])
        base_promotion = promotion_info[0].get('base_promotion', {}) if isinstance(promotion_info, list) and len(
            promotion_info) > 0 else {}
        item_promo_type = base_promotion.get('item_promo_type', '')

        return item_promo_type if item_promo_type else None

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

    def get_promotion_discount(self, listing_items):
        promo_description = ''
        promo_discount = ''
        price_save = ''
        loyalty_disc = ''
        exclusive = ''
        full_items_price = 0.0
        prom_discount = 0.0

        try:
            promotion_price = listing_items.get('price', {}).get('price_info', {}).get('price', '0.0')
            promotion_price = re.sub(r'[^\d.]', '', promotion_price) if promotion_price else 0.0
            promotion_price = float(promotion_price)

            promotion_info = listing_items.get('promotion_info', [{}])
            # linksave = promotion_info[0].get('linksave', {}) if promotion_info else {}
            promo_data = promotion_info[0] if promotion_info else {}

            # Process linksave promotions
            linksave = promo_data.get('linksave', {})
            if linksave:
                promo_description = linksave.get('promo_detail', '')
                promo_quantity = float(linksave.get('promo_quantity', 0.0))
                promo_string = linksave.get('promo_value', '')
                promo_value = float(re.sub(r'[^\d.]', '', promo_string)) if promo_string else 0.0
                # promo quantity * current price to get total price for all items

                if '£' in promo_description:
                    full_items_price = promotion_price * promo_quantity
                    prom_discount = full_items_price - promotion_price
                    promo_discount = f'£{prom_discount} per item' if prom_discount > 0 else None
                    price_save_value = full_items_price - promo_value
                    price_save = f'Save £{price_save_value}' if price_save_value > 0 else None
                else:
                    promo_quantity_full_price = promo_quantity * promotion_price
                    promo_value_full_price = promo_value * promotion_price
                    prom_discount = promo_quantity_full_price - promo_value_full_price
                    promo_discount = f'£{prom_discount} per item' if prom_discount > 0 else None
                    price_save_value = promo_quantity_full_price - promo_value_full_price
                    price_save = f'Save £{price_save_value}' if price_save_value > 0 else None
            else:
                # Process base promotions and rollbacks
                base_promotion = promo_data.get('base_promotion', {}).get('item_promo_type', '')
                rollback = promo_data.get('rollback', {})
                promo_description = listing_items.get('price', {}).get('price_info', {}).get('price_per_uom', '')

                was_price = rollback.get('was_price', '0.0')
                was_price = float(re.sub(r'[^\d.]', '', was_price)) if was_price else '0.0'

                promotion_discount = was_price - promotion_price if was_price > promotion_price else 0.0
                if promotion_discount > 0:
                    promo_discount =f'£{promotion_discount} per item' if promotion_discount > 0 else None

            return promo_description, promo_discount, price_save, loyalty_disc, exclusive
        except Exception as e:
            # Log the error and return defaults
            print(f"Error in get_promotion_discount: {e}")
            return promo_description, prom_discount, price_save, loyalty_disc, exclusive

    def get_prod_description(self, listing_items):
        prod_des_dict = listing_items.get('item_enrichment', {}).get('enrichment_info', {})
        result = "\n\n".join(
            f"{key.replace('_', ' ').title()}\n{value}" for key, value in prod_des_dict.items() if value)

        return result

    def write_logs(self, log_msg):
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{log_msg}\n')
            print(log_msg)

    def post_to_api(self, item):
        """
        Sends a POST request to the API with the item data.
        """
        try:
            # Convert item to JSON
            response = requests.post(self.api_url, json=item, headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                self.items_scrapped += 1
                print('Items ae Scrapped: ', self.items_scrapped)
                self.write_logs(f'[POST_TO_API] Successfully uploaded data for product ID {item.get("product_id")}. Response: {response.json()}')
            else:
                self.write_logs(f'[POST_TO_API] Failed to upload data for product ID {item.get("product_id", "")}. '
                                f'Status Code: {response.status_code}, Response: {response.text}')

        except requests.exceptions.RequestException as e:
            self.write_logs(f'[POST_TO_API] Request error while uploading data for product ID {item.get("product_id", "")}: {e}')
        except Exception as e:
            self.write_logs(f'[POST_TO_API] Unexpected error: {e}')
