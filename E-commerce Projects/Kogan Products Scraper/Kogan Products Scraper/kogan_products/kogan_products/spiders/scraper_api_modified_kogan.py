import re
import json
from datetime import datetime
from collections import OrderedDict
from urllib.parse import urljoin, urlencode, unquote

import requests
from scrapy import Request, Spider, Selector


class KoganSpider(Spider):
    name = "scraper_kogan"
    base_url = 'https://www.kogan.com/au/'

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429, 10051],

        'FEEDS': {
            f'output/Kogan Products {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Item ID', 'Product ID', 'Category', 'Brand Name', 'Product Name',
                           'Regular Price', 'Special Price', 'Current Price', 'Stock Status',
                           # 'Size',
                           'Short Description', 'Long Description', 'Product Information',
                           'Directions', 'Ingredients', 'SKU', 'Image URLs'],
            }
        }
    }

    headers = {
        'authority': 'www.kogan.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'device_pixel_ratio=1.125; store_code=au; ab=e53ac8b0-8183-4943-9167-fe1ee7332d93; rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2FCyfJRaMZ15SC3Hn4r7QTUWciGGmOR0qI%3D; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX1%2B3Nypca8p2FpJDDsR5myeCjAQhebu%2BhOc%3D; rskxRunCookie=0; rCookie=16l07zgcwprh64r2ghhdhhlrguor6q; csrftoken=3nPTwDuPB4eWNgUyNubJFqAq8XazTJhu; postcode=3000; lastRskxRun=1707209661164; rl_session=RudderEncrypt%3AU2FsdGVkX1939DjboXVbmsA6SutewjfWU6Jlh%2BNCeT9Jf%2B4Ob94kCg0SQQrnUwUhEE2lEHOiZ0LtMOgBbEDkPTINcWZMlZqi5TMOUlBoJHD8cJMBeI9f%2BFhpoIYyz9ztcqtvuhhcSliP6UoE%2F2CxAQ%3D%3D; rl_user_id=RudderEncrypt%3AU2FsdGVkX19cM1k7TyEITdEggufdlVgRBM0RHpGmAwU%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2BlTP8RN89bsd5zv5kGQlVJaZ74PSnk0kI%3D; rl_group_id=RudderEncrypt%3AU2FsdGVkX19ZVrAkE86DCJheS50raIj9Qqy7rXcGbEM%3D; rl_group_trait=RudderEncrypt%3AU2FsdGVkX1%2BZn9QdYe9BkPQ6gj12ueSPVL7qkkoqXw8%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX18YG4Gt9EaqhyPGg61VVriySkRAO%2Bmgk1R7gIUigNWwFXsuUx67tXw%2Fw5DCcsRh3DmMyHSHD1zPKA%3D%3D; sessionid=tfh5reqvsgmyrr38ixa23owms1b4h1ol; K.ID=9d74a8e6-541e-40ab-b3b8-1bdb2ee4c3c8; banner=banner; k3HideFooterPromo-KA-FOOTER-FOOTBALL-TV-ENDING=dismissed; k3HideFooterPromo-KA-FOOTER-SWITCHWEEK-LAUNCH=dismissed; recently_viewed_au=65042232-3151136-181304510-97198600-168509889-967156-136027446-170717199-165977003; datadome=I9gGUBQY1fBPDg2WqHw4gyiWXOxY6Ob9_Hw~vXCEf711kTxGO11gL0Jat4CtxHPCHyBCpa4c3C67avaNU8oyPsQmb0s_XZzriAuZnkoFP_qL7Sgr0ODSvxjTZC4~MPqz',
        'pragma': 'no-cache',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="122.0.6261.112", "Not(A:Brand";v="24.0.0.0", "Google Chrome";v="122.0.6261.112"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set up proxy key and usage flag
        self.proxy_key = self.get_scrapeops_api_key_from_file()
        self.use_proxy = True if self.proxy_key else False

        # Get search URLs from the input file
        self.categories_search_urls = self.get_category_urls_from_file()

        self.current_scrapped_items = []
        self.items_scrapped = 0

        self.errors_list = []
        self.total_products = 0
        self.meta = {
            "proxy": "http://scraperapi.country_code=au:d29cba09c2f966ad44d24a4f89307ecb@proxy-server.scraperapi.com:8001"
        }

    def start_requests(self):
        if not self.categories_search_urls:
            yield Request(url=self.get_scrapeops_url(self.base_url), callback=self.parse)
        else:
            for url in self.categories_search_urls:
                res = requests.get(url=self.get_scrapeops_url(url), headers=self.headers)
                # yield Request(url=self.get_scrapeops_url(url), callback=self.parse)
                # yield Request(url=url, callback=self.parse, meta=self.meta)
                payload = {'api_key': 'd29cba09c2f966ad44d24a4f89307ecb', 'url': url, 'country_code': 'au', 'keep_headers': 'true'}
                payload = {'api_key': 'd29cba09c2f966ad44d24a4f89307ecb', 'url': 'https://www.kogan.com/au/shop/category/health-beauty-3143', 'country_code': 'au', 'keep_headers': 'true'}
                r = requests.get('http://api.scraperapi.com', params=payload, headers=self.headers)
                yield Request('http://api.scraperapi.com/?api_key=d29cba09c2f966ad44d24a4f89307ecb&url=' + url + 'country_code=au'
                    , callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            start_time = datetime.now().strftime("%d%m%Y%H%M%S")
            self.errors_list.append(f'The spider started at {start_time}')

            categories_urls = self.get_categories_urls(response)

            if not categories_urls:
                yield from self.parse_category(response)

            for subcategory_url in categories_urls:
                url = urljoin(self.base_url, subcategory_url)
                yield Request(url=self.get_scrapeops_url(url), callback=self.parse_category)

        except Exception as e:
            self.errors_list.append(f"Error in parse function: {e}, URL: {self.get_unquoted_url(response.url)}")

    def parse_category(self, response):
        try:
            category_name = self.extract_category_name(response.url)

            categories_urls = self.get_categories_urls(response) or self.get_parse_categories_urls(response)
            categories_names = [name for name in categories_urls if category_name not in name]

            if not categories_names:
                url = f'https://www.kogan.com/au/shop/category/{category_name}/?page=10'
                yield Request(url=self.get_scrapeops_url(url), callback=self.parse_category_pagination)

            else:
                for cat_name in categories_names:
                    # cat_name = cat_name.replace('/?sps=hidden', '').rstrip('/').split('/')[-1]
                    # url = f"https://www.kogan.com/au/shop/category/{cat_name}/?page=10"
                    url = urljoin(self.base_url, cat_name) + '?page=10'
                    yield Request(url=self.get_scrapeops_url(url), callback=self.parse_category_pagination)

        except Exception as e:
            self.errors_list.append(
                f"Error in parse_category function: {e}, URL: {self.get_unquoted_url(response.url)}")

    def parse_category_pagination(self, response):
        try:
            product_elements = response.css('.rs-infinite-scroll .tVqMg')
            products = [product for product in product_elements if "sponsored" not in product.get()]
            urls = [product.css('a::attr(href)').get() for product in products]
            products_urls = [url.split('?ssid')[0] for url in urls]
            category_name = self.extract_category_name(response.url)

            self.total_products += int(len(products))
            print('Still Found Total Products', self.total_products)
            info = f'{category_name.split('?page')[0].strip('/')} has total products = {len(urls)}'
            self.errors_list.append(info)
            print('Category info :', info)

            for product_url in products_urls:
                p_url = urljoin(self.base_url, product_url)
                if p_url.strip('/') in self.current_scrapped_items:
                    continue

                # yield Request(url=self.get_scrapeops_url(p_url), callback=self.parse_product_detail,
                #               meta={'product_url': product_url})

            # pagination
            if len(urls) >= 360:
                api_url = f'https://www.kogan.com/api/v1/products/?category={category_name.split('/')[0]}&group_variants=true&store=au&offset=360&limit=200'
                yield Request(url=self.get_scrapeops_url(api_url), callback=self.category_json)

        except Exception as e:
            self.errors_list.append(
                f"Error in parse_category_pagination function: {e}, URL: {self.get_unquoted_url(response.url)}")

    def category_json(self, response):
        try:
            data = response.json()
            products = data.get('objects', [])
        except Exception as e:
            data = {}
            products = []
            self.errors_list.append(f"Category Json error:{e}  && URL: {self.get_unquoted_url(response.url)}")
            return

        self.total_products += int(len(products))
        print('Still Found Total Products', self.total_products)
        info = f'From Category json CaT {unquote(response.url).split('category=')[1]} has Products= {len(products)}'
        print('Category jason :', info)
        self.errors_list.append(info)

        for product in products:
            url = product.get('url', '').split('?ssid')[0].rstrip('/')
            p_url = urljoin(self.base_url, url)

            if p_url in self.current_scrapped_items:
                continue
            # yield Request(url=self.get_scrapeops_url(p_url), callback=self.parse_product_detail)

        if len(data.get('objects')) >= 200:
            if data.get('meta', {}).get('has_next', ''):
                current_offset = data.get('meta', {}).get('offset', 0)
                new_offset = int(current_offset) + 200
                previous_url = unquote(response.url).split('url=')[1]
                modified_url = previous_url.split('&offset=')[0] + f'&offset={new_offset}&limit=200'
                yield Request(url=self.get_scrapeops_url(modified_url), callback=self.category_json)

    def parse_product_detail(self, response):
        try:
            script_text = response.css('script:contains("bootstrapData = JSON") ::text').re_first(
                r"JSON\.parse\('({.*?})'\)")
            decoded_string = script_text.encode('utf-8').decode('unicode-escape')
            data = json.loads(decoded_string)

            product_data = data.get('product', {}).get('bySlug', {})
            product_dict = {}

            for value in product_data.values():
                product_dict.update(value)

            variants = product_dict.get('variants', [])

            url = urljoin(self.base_url, product_dict.get('url', ''))
            item_id = product_dict.get('id', '')
            product_id = product_dict.get('gtin', '')
            category = ', '.join([cat.get('title', '') for cat in product_dict.get('breadcrumbs', [])])
            brand_name = product_dict.get('brand', '') if product_dict.get('brand') is not None else ''
            product_name = product_dict.get('title', '')
            short_description = ''
            current_price = response.css('[itemprop="price"]::attr(content)').get('')
            was_price = product_dict.get('current_was_price', 0.0) if product_dict.get('current_was_price',
                                                                                       0.0) is not None else ''
            stock_status = product_dict.get('stock', '')
            long_description = self.get_product_long_description(response)
            product_information = self.get_product_information(product_dict)
            directions = ''
            ingredients = self.get_ingredients(response)
            sku = product_dict.get('sku', '')
            images_urls = self.get_images_url(response, product_dict)
            regular_price = self.get_regular_price(product_dict)
            special_price = self.get_special_price(product_dict)

            if not variants:
                item = self.get_item(url, item_id, product_id, category, brand_name, product_name,
                                     short_description, current_price, stock_status, long_description,
                                     product_information, directions, ingredients, sku,
                                     images_urls, regular_price, special_price)
                yield item
                return

            if variants:
                variants = variants[0].get('variants', [])
                for variant in variants:
                    url = urljoin(self.base_url, variant.get('url', '')) if variant.get('url', '') else ''
                    item_id = product_dict.get('id', '')
                    product_id = variant.get('pk', '')
                    product_name = variant.get('title', '')
                    current_price = variant.get('your_price', '')
                    stock_status = 'In Stock' if variant.get('in_stock', '') else 'Out Of Stock'
                    # size = variant.get('facet_value', '')
                    sku = self.get_variant_sku(general_sku=sku, url=url)

                    item = self.get_item(url, item_id, product_id, category, brand_name, product_name,
                                         short_description, current_price, stock_status, long_description,
                                         product_information, directions, ingredients, sku,
                                         images_urls, regular_price, special_price)

                    yield item

        except Exception as e:
            self.errors_list.append(f"Product Detail Method error: {e}  && url = {self.get_unquoted_url(response.url)}")
            print(f"From parse_category Method error: {e}  && url = {self.get_unquoted_url(response.url)}")

    def get_parse_categories_urls(self, response):
        script_tag = response.css('script:contains(bootstrapData)::text').re_first(r"('{.+}')")
        script_tag = script_tag.encode().decode('unicode-escape')

        script_pattern = re.search(r'"servicesMenu":.+?"experiments":', script_tag)

        # Check if the pattern was found
        if script_pattern:
            string = script_pattern.group(0)
            string = string.replace('"servicesMenu": ', '').replace(', "experiments":', '')
        else:
            self.errors_list.append(
                f"From get_parse_categories_urls Method error: && url = {self.get_unquoted_url(response.url)}")
            return

        try:
            # Extract slug from meta
            slug = response.meta.get('slug', '') or unquote(response.url).split('url=')[1].split('category/')[1].rstrip(
                '/').strip()
        except:
            slug = unquote(response.url).split('/')[-2]

        # Parse JSON to get categories dictionary
        categories_dic = json.loads(string)

        sub_categories_urls = []

        # if full website scrape
        if '/au' in slug:
            all_categories = [category.get('categories', [{}]) for category in categories_dic]
            for category in all_categories:
                items = [sub_cat.get('items') for sub_cat in category]
                for item in items:
                    urls = [row.get('href', '') for row in item if row.get('href')]
                    sub_categories_urls.extend(urls)
        else:
            for category_dic in categories_dic:
                sub_categories = category_dic.get('categories', [{}])
                category_url = category_dic.get('href', '')

                if slug in category_url:
                    items_urls = [[item.get('href') for item in row.get('items', [])] for row in
                                  category_dic.get('categories', [{}])]
                    for item_urls in items_urls:
                        sub_categories_urls.extend(item_urls)
                    break

                else:
                    for sub_sub_cat in sub_categories:
                        sub_cat_url = sub_sub_cat.get('href', '')

                        if not sub_cat_url:
                            continue

                        if slug in sub_cat_url:
                            urls = [row.get('href') for row in sub_sub_cat.get('items', [{}]) if row.get('href')]
                            sub_categories_urls.extend(urls)
                            break

                        else:
                            url = [row.get('href', '') for row in sub_sub_cat.get('items', []) if
                                   row.get('href') and slug in row]
                            if url:
                                sub_categories_urls.append(url)
                            continue

        return sub_categories_urls

    def get_categories_urls(self, response):
        try:
            slug = unquote(response.url.split('url=')[1]).split('category/')[1].rstrip('/')
        except:
            slug = ''

        subcat = response.css(
            '[data-filter-group="category"] ul li._1qy5b:not(:first-child) a::attr(href)').getall() or []
        subcat = subcat or response.css(
            '.department-menu__list.L2ZoZ._1njOC li:not(:first-child) a.department-menu__link ::attr(href)').getall() or []

        subcat = [url for url in subcat if not slug in url]

        return subcat

    def get_images_url(self, response, product_dict):
        images = ',\n '.join([img.split('?auto')[0] for img in product_dict.get('images', [])])

        images_urls = response.css('[aria-label="Thumbnail Navigation"] button div img::attr(src)').getall()
        full_images_urls = [img.split('?auto')[0] for img in images_urls]
        full_images_urls = ',\n '.join(full_images_urls)
        full_images_urls = full_images_urls or response.css(
            '.image-gallery-slides .image-gallery-image::attr(src)').get('')

        return images or full_images_urls or ''

    def get_product_information(self, product_dict):
        indo_dict = product_dict.get('facets', {})
        formatted_info = []

        for key, values in indo_dict.items():
            if isinstance(values, list):
                for value in values:
                    formatted_info.append(f"{value['name']} : {value['value']}")
            else:
                formatted_info.append(f"{key} : {values}")

        product_info = '\n'.join(formatted_info)
        return product_info

    def get_product_long_description(self, response):
        try:
            script_tag = response.css('script:contains(slug) ::text').re_first(r"JSON.parse[(]'(.*)'[)];").encode(
                'utf-8').decode('unicode-escape')
            product = json.loads(script_tag).get('product', {})
            slug = product.get('allSlugs', [])[0].strip()
            description_dict = product.get('bySlug', {}).get(slug, {}).get('description')
            html_tag = Selector(text=description_dict)

            tags_list = html_tag.xpath('//html/body/div/div[2]/*') or html_tag.xpath('//html/body/*')
            description_text_list = []

            for tag in tags_list:
                tag_classes = tag.css('::attr(class)').extract()
                if 'radioHideLabel' in tag_classes or 'radioHide' in tag_classes:
                    continue
                if tag.css('style'):
                    continue
                text = ''.join(tag.css(' ::text').getall())
                if text:
                    description_text_list.append(text)
                    if 'SPECIFICATION' in text:
                        break
            # # Join the extracted text into a single string
            text_format = '\n'.join(description_text_list)

            return text_format.replace('SPECIFICATION', '').strip()

        except Exception as e:
            print('get_product_long_description Method err " ', e)
            return ''

    def get_scrapeops_url(self, url):
        if self.use_proxy:
            if 'https://www.kogan.com/api/v1/products/' in url:
                payload = {'api_key': self.proxy_key, 'url': url}
                return 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
            else:
                # payload = {'api_key': self.proxy_key, 'url': url, 'country': 'us', 'Sops-Final-Status-Code': 'true'}
                payload = {'api_key': self.proxy_key, 'url': url}
                url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
                return url
        else:
            return url

    def get_scrapeops_api_key_from_file(self):
        return self.get_input_from_txt('input/scrapeops_proxy_key.txt')[0]

    def get_category_urls_from_file(self):
        return self.get_input_from_txt('input/category_urls.txt')

    def get_input_from_txt(self, file_path):
        with open(file_path, mode='r', encoding='utf-8') as txt_file:
            return [line.strip() for line in txt_file.readlines() if line.strip()] or ['']

    def get_ingredients(self, response):
        try:
            script_tag = response.css('script:contains(slug) ::text').re_first(r"JSON.parse[(]'(.*)'[)];").encode(
                'utf-8').decode('unicode-escape')
            product = json.loads(script_tag).get('product', {})
            slug = product.get('allSlugs', [])[0].strip()
            description_dict = product.get('bySlug', {}).get(slug, {}).get('description')
            html_tag = Selector(text=description_dict)

            tags_list = html_tag.xpath('//html/body/div/div[2]/*') or html_tag.xpath('//html/body/*')
            ingredients_text = ''

            for tag in tags_list:
                tag_classes = tag.css('::attr(class)').extract()
                if 'radioHideLabel' in tag_classes or 'radioHide' in tag_classes:
                    continue
                if tag.css('style'):
                    continue
                text = ''.join(tag.css(' ::text').getall())
                if 'Ingredients:' in text:
                    ingredients_text = text.split('Ingredients:', 1)[-1].strip()
                    break
            if ingredients_text:
                return '\n'.join(['Ingredients:', ingredients_text])
            else:
                return ''
        except Exception as e:
            print(f'Error is up from Ingredients Method :{e}')
            return ''

    def close(spider: Spider, reason):
        try:
            all_products = spider.total_products
            items_scraped = f'Total Rows are inserted :{str(spider.items_scrapped)}'
            spider.errors_list.append(items_scraped)
            spider.error_list.append(all_products)
            filename = 'Scraper Information.txt'  # Corrected the filename string
            with open(filename, 'w') as f:
                for error in spider.errors_list:
                    f.write(f"{error}\n")
            print(f"Scraper Information Successfully write into file: {filename}")
        except Exception as e:
            print(f"Error writing to file: {e}")

    def get_variant_sku(self, general_sku, url):
        sku_part = general_sku.split('-')[0]
        sku = '-'.join([part.capitalize() for part in url.split('-')[-general_sku.count('-'):]]).strip('/')
        final_sku = sku_part + '-' + sku
        return final_sku

    def get_item(self, url, item_id, product_id, category, brand_name, product_name, short_description, current_price,
                 stock_status, long_description, product_information, directions, ingredients, sku, images_urls,
                 regular_price, special_price):
        try:
            item = OrderedDict()

            item['Product URL'] = url
            item['Item ID'] = item_id
            item['Product ID'] = product_id
            item['Category'] = category
            item['Brand Name'] = brand_name
            item['Product Name'] = product_name
            item['Short Description'] = short_description
            item['Current Price'] = current_price
            item['Stock Status'] = stock_status
            # item['Size'] = size
            item['Long Description'] = long_description
            item['Product Information'] = product_information if product_information else ''
            item['Directions'] = directions
            item['Ingredients'] = ingredients
            item['SKU'] = sku.strip() if sku else ''
            item['Image URLs'] = images_urls
            item['Regular Price'] = regular_price
            item['Special Price'] = special_price

            self.current_scrapped_items.append(url.strip('/'))
            self.items_scrapped += 1
            print("Items Scrapped :", self.items_scrapped)
            return item

        except Exception as e:
            print('Error for get item function :', e)
            return

    def extract_category_name(self, url):
        return unquote(url.split('url=')[1]).split('category/')[1].split('&')[0].rstrip('/') or \
            unquote(url.split('url=')[1]).split('/')[-2]

    def get_unquoted_url(self, url):
        return unquote(url.split('url=')[1])

    def get_regular_price(self, product_dict):
        price = product_dict.get('current_was_price', 0.0) if product_dict.get('current_was_price',
                                                                               0.0) is not None else ''
        return price

    def get_special_price(self, product_dict):
        return product_dict.get('future_price', '') if product_dict.get('future_price', '') is not None else ''
