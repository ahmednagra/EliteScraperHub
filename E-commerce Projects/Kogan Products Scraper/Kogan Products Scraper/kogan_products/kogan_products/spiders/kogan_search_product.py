import json
from datetime import datetime
from collections import OrderedDict
from urllib.parse import urljoin, urlencode, unquote, quote
from scrapy import Request, Spider, Selector


class KoganSearchSpider(Spider):
    name = "kogan_search"
    base_url = 'https://www.kogan.com/au/'

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429, 10051],

        'FEEDS': {
            f'output/Kogan Search Product {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Item ID', 'Product ID', 'Category', 'Brand Name', 'Product Name',
                           'Regular Price', 'Special Price', 'Current Price', 'Stock Status',
                           'Short Description', 'Long Description', 'Product Information',
                           'Directions', 'Ingredients', 'SKU', 'Image URLs'],
            }
        }
    }
    headers = {
        'authority': 'www.kogan.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'sec-ch-ua': '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set up proxy key and usage flag
        self.search_eans = self.get_input_from_txt('input/eans_numbers.txt')
        self.proxy_key = ''.join(self.get_input_from_txt('input/scrapeops_proxy_key.txt'))
        self.use_proxy = True if self.proxy_key else False

        self.errors_list = []

    def start_requests(self):
        for ean in self.search_eans:
            if 'www.kogan.com' in ean:
                yield Request(url=ean, callback=self.parse_product_detail)
            else:
                url = f'https://www.kogan.com/au/shop/?q={quote(ean)}'
                yield Request(url, callback=self.parse, headers=self.headers, dont_filter=True, meta={'ean': ean})

    def parse(self, response, **kwargs):
        try:
            product_url = response.css('.tVqMg:not(:contains("Sponsored")) ._1A_Xq a::attr(href)').get('')
            if product_url:
                product_url = product_url.split('/?ssid')[0]
                url = urljoin(self.base_url, product_url)
                yield Request(url=url, callback=self.parse_product_detail)
            else:
                if response.meta.get('ean', '') in response.text:
                    yield from self.parse_product_detail(response=response)
                else:
                    return
        except Exception as e:
            self.errors_list.append(
                f"From Parse Method error: {e}  && url = {response.url}")

    def parse_product_detail(self, response):
        try:
            item = OrderedDict()

            script_text = response.css('script:contains("bootstrapData = JSON") ::text').re_first(
                r"JSON\.parse\('({.*?})'\)")
            decoded_string = script_text.encode('utf-8').decode('unicode-escape')

            data = json.loads(decoded_string)
            product_data = data.get('product', {}).get('bySlug', {})
            product_dict = {}

            for value in product_data.values():
                product_dict.update(value)

            item['Product URL'] = self.get_product_url(response, product_dict)
            item['Item ID'] = self.get_item_id(product_dict)
            item['Product ID'] = self.get_product_id(product_dict)
            item['Category'] = self.get_category_name(response, product_dict)
            item['Brand Name'] = self.get_brand_name(response, product_dict)
            item['Product Name'] = self.get_product_name(response, product_dict)
            item['Short Description'] = ''
            item['Current Price'] = self.get_current_price(response, product_dict)
            item['Stock Status'] = self.get_stock_status(response, product_dict)
            item['Long Description'] = self.get_product_long_description(response, product_dict)
            item['Product Information'] = self.get_product_information(product_dict)
            item['Directions'] = ''
            item['Ingredients'] = self.get_product_ingredients(response)
            item['SKU'] = self.get_product_sku(response, product_dict)
            item['Image URLs'] = self.get_images_urls(response, product_dict)
            item['Regular Price'] = self.get_regular_price(product_dict)
            item['Special Price'] = self.get_special_price(product_dict)

            yield item

        except Exception as e:
            self.errors_list.append(
                f"From parse_category Method error: {e}  && url = {response.url}")
            print(f"From parse_category Method error: {e}  && url = {response.url}")

    def get_input_from_txt(self, file_path):
        with open(file_path, mode='r', encoding='utf-8') as txt_file:
            return [line.strip() for line in txt_file.readlines() if line.strip()] or ['']

    def get_product_url(self, response, product_dict):
        url = response.css('[property="og:url"]::attr(content)').get('').strip()
        url = url or urljoin(self.base_url, product_dict.get('url', ''))
        return url

    def get_item_id(self, product_dict):
        return product_dict.get('id', '')

    def get_product_id(self, product_dict):
        return product_dict.get('gtin', '')

    def get_category_name(self, response, product_dict):
        category = ', '.join([cat.get('title', '') for cat in product_dict.get('breadcrumbs', [])])
        category = category or ', '.join(response.css('[itemprop="itemListElement"] [itemprop="name"] ::text').getall())
        return category

    def get_brand_name(self, response, product_dict):
        brand = product_dict.get('brand', '') if product_dict.get('brand') is not None else ''
        brand = brand or response.css('[itemprop="brand"] meta::attr(content)').get('').strip()
        return brand

    def get_product_name(self, response, product_dict):
        name = product_dict.get('title', '')
        name = name or response.css('h1[itemprop="name"] ::text').get('') or response.css(
            '[itemprop="brand"] meta::attr(content)').get('').strip()

        return name

    def get_current_price(self, response, product_dict):
        price = product_dict.get('price', '') or response.css('[itemprop="price"]::attr(content)').get('')
        return price

    def get_stock_status(self, response, product_dict):
        stock = product_dict.get('stock', '')
        stock = stock or product_dict.get('in_stock', '')
        return stock if stock else 'Out Of Stock'

    def get_product_long_description(self, response, product_dict):
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

    def get_product_information(self, product_dict):
        # information = self.get_all_product_information(
        #     response=response.css('#specs-accordion div.text-content-with-links > div'))
        #
        # # If specification is not found, try extracting from the description section
        # if not information:
        #     feature_tag = response.css('section[itemprop="description"] p:contains("Key features") + ul li')
        #     information = []
        #
        #     for row in feature_tag:
        #         row_text = ''.join(row.css(' ::text').getall())
        #         information.append(row_text)
        #
        # return information if information else ''
        try:
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
        except Exception as e:
            print(f"Error in retrieving product information: {e}")
            return ''

    def get_product_ingredients(self, response):
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

    def get_product_sku(self, response, product_dict):
        sku = product_dict.get('sku', '')
        sku = sku or response.css('[itemProp="gtin13"]::text').get('') or response.css(
            '[itemProp="sku"]::attr(content)').get('')

        return sku

    def get_images_urls(self, response, product_dict):
        try:
            images_urls = ',\n '.join([img.split('?auto')[0] for img in product_dict.get('images', [])])
            images = response.css('[aria-label="Thumbnail Navigation"] button div img::attr(src)').getall()
            full_images_urls = [img.split('?auto')[0] for img in images]
            full_images_urls = ',\n '.join(full_images_urls)
            full_images_urls = full_images_urls or response.css(
                '.image-gallery-slides .image-gallery-image::attr(src)').get('')

            return images_urls or full_images_urls
        except Exception as e:
            self.errors_list.append(f"Error in get_images_urls: {e}")
            return ''

    def get_regular_price(self, product_dict):
        price = product_dict.get('current_was_price', 0.0) if product_dict.get('current_was_price', 0.0) is not None else ''
        return price

    def get_special_price(self, product_dict):
        return product_dict.get('future_price', '')

    def close(spider: Spider, reason):
        try:
            filename = 'Search_Product_ERRORS.txt'  # Corrected the filename string
            with open(filename, 'w') as f:
                for error in spider.errors_list:
                    f.write(f"{error}\n")
            print(f"Errors written to {filename}")
        except Exception as e:
            print(f"Error writing to file: {e}")
