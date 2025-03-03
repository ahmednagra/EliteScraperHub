import re
import json
from collections import OrderedDict
from datetime import datetime
from math import ceil

import requests
from scrapy import Spider, Request, Selector
from scrapy.http import XmlResponse
import xmltodict


class ChemistScraperSpider(Spider):
    name = 'chemist'
    start_urls = ['https://www.chemistwarehouse.com.au/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/ChemistWareHouse Products {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Item ID', 'Product ID', 'Category', 'Brand Name', 'Product Name',
                           'Regular Price', 'Special Price', 'Current Price', 'Short Description',
                           'Long Description', 'Product Information', 'Directions', 'Ingredients',
                           'SKU', 'Image URLs'],
            }
        }
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Cookie': 'BVBRANDID=639b5e50-60c9-4a29-8b9f-dd931ccceeba; _cls_v=86a29eea-8dc1-46bb-80bc-9b273bafc0db; meiro_user_id=9de57d33-2796-4bfc-ae8c-8d94401b7334; __cf_bm=Y4rl45DV2VSyfvMKhrS7aQQj8w2LlanGj0XBg6AxZcg-1703754397-1-AcGWTtmiBqZrr/pqxQqFsjwA1HV0Njp/YxWAbJycL9p9R0+VMfuOKZ9AED2oR39KOgUR1oGLF0SJFzQM5ks0Lwc=; __cflb=02DiuDfFR9ebh77hQy3o3iRnxnF3ZbZdgEADKm7LECgag; BVImplmain_site=13773; country_code=PK; BVBRANDSID=02018b42-f792-47f8-97f5-bbf32d39fb73; ASP.NET_SessionId=zu5wbogqod0yym0op2jbrw4z; CacheUpdater=%5B%7B%22numItemsInCart%22%3A0%2C%22totalAmountInCart%22%3A%22%240.00%22%2C%22boolShowYellowBox%22%3A%22False%22%2C%22needMoreAmountForFreeShipping%22%3A%22%240.00%22%2C%22boolLoggedIn%22%3A%22False%22%2C%22userFName%22%3A%22%22%2C%22country%22%3A284%2C%22shippingfee%22%3A%22%240.00%22%7D%5D; pcf=true; _gcl_au=1.1.2113657204.1703754405; gtm.custom.bot.flag=human; _cls_s=c7ee3c7b-277b-4344-9c14-fe7cb41d544f:1; _gid=GA1.3.273999278.1703754407; meiro_user_id_js=9de57d33-2796-4bfc-ae8c-8d94401b7334; meiro_session_id_js=MTcwMzc1NDQwNzA0MiY5ZGU1N2QzMy0yNzk2LTRiZmMtYWU4Yy04ZDk0NDAxYjczMzQ=; sa-user-id=s%253A0-12ead36a-b928-55a1-438e-aee0baf7f3ae.5%252BdYQIQuZNI9uYE%252FEDJtRXq0%252Badodsb1Qm%252FXEVgK%252BqY; sa-user-id-v2=s%253AEurTarkoVaFDjq7guvfzricjIMA.h8euylktxW9JfyTIH%252F%252F2fVAUafo5BMkGDhgEzROB%252FLc; sa-user-id-v3=s%253AAQAKIPuOwXjlStbY6fFB5HTC6-oRrKa_wmb6ca8Q4YFnd-wwEHwYBCDyhJCpBjABOgT87-jmQgT25IvH.TXOQSAOy3ksE570ilefZYku%252B0AQ%252BzFTDa6gGKnwjHbw; _tt_enable_cookie=1; _ttp=QIRe7q4VbpkkbdhdPSLmwXuhf29; _fbp=fb.2.1703754407926.1708000163; _dc_gtm_UA-43361907-1=1; _pin_unauth=dWlkPU9UbGpaR1E0WkRjdE9EazJaQzAwWVRrekxUa3daalF0TmpFNVpHTm1ZbU0xWTJObA; dicbo_id=%7B%22dicbo_fetch%22%3A1703754408825%7D; meiro_synced_ga_cid=712897924.1703754405; meiro_synced_fb_cid=1703754407926.1708000163; __gads=ID=e0271e5288f91652:T=1703754410:RT=1703754410:S=ALNI_MaDcAYbGXi6hefGGqzOBkHMfsN0YQ; __gpi=UID=00000ce8ec9efc58:T=1703754410:RT=1703754410:S=ALNI_MZp86XYyCVFkDh0c0NlCKpul-rzSA; xyz_cr_536_et_100==NaN&cr=536&wegc=&et=100&ap=; _ga=GA1.3.712897924.1703754405; meiro_session_id_used_ts_js=1703754417440; cto_bundle=1_JJiV9yM1FqMGxqdVJtc0FJRmZpblpBbXdhR0VTJTJGMzhkTmlDMVQ3ZXBiYWVIM0FmeUV6eFU2MVRQTmRQV1BnJTJGYzMlMkJzVG5yVENseUZiQlpZNyUyQlZJOXkxQk1QYkRLRFAwd1UlMkZiVnNPcWQ3Sm1La0lRRFMlMkJBTHZxcHdKR256bm5WcUFBNVp3eWRmQU9YWlJ2S3lBJTJCNFhhVjA0Qzg0dEdSRlNNRHpzdlc0eHhlUk9UNCUzRA; _uetsid=6d59b880a56011ee8f7b690d59e4dbda; _uetvid=169e87806c2b11eeb57e47b3950dedbb; __kla_id=eyJjaWQiOiJaR013WkRJeE5HUXRORFE1T0MwME5HVTFMVGd3TVRjdFlXVTVNalV4WkRBeU16VmsiLCIkcmVmZXJyZXIiOnsidHMiOjE3MDM3NTQ0MDgsInZhbHVlIjoiIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vd3d3LmNoZW1pc3R3YXJlaG91c2UuY29tLmF1LyJ9LCIkbGFzdF9yZWZlcnJlciI6eyJ0cyI6MTcwMzc1NDQxOSwidmFsdWUiOiIiLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cuY2hlbWlzdHdhcmVob3VzZS5jb20uYXUvIn19; cf_clearance=dj.TShJDA0XjQmWXBZRhuecdhtDVbVpPMAhq4wX4Huo-1703754420-0-2-d8acbfc5.bce29351.8fade025-0.2.1703754420; _gat_UA-43361907-1=1; _ga_YZ1YS5R44E=GS1.1.1703754405.1.1.1703754423.42.0.0; _gali=Main',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_urls = self.get_category_urls_from_file()

    def start_requests(self):
        yield Request(url=self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self, response, **kwargs):
        # category_urls = self.category_urls or response.css('.category-tiles li:not(.mob-only) a::attr(href)').getall()
        category_urls = self.category_urls or self.get_categories_urls(response)

        for category_url in category_urls:
            category_id = category_url.split('/')[-2]  # For Example category_id = '257' for Beauty

            if not category_id:
                continue

            category_format = 'chemau{category_id}'.format(category_id=category_id)
            urlp = '{catalog01_chemau}'
            category_json_url = f'https://pds.chemistwarehouse.com.au/search?identifier=AU&fh_start_index=0&fh_view_size=500&fh_location=//catalog01/en_AU/categories%3C{urlp}/categories%3C{category_format}'

            yield Request(url=category_json_url, callback=self.parse_pagination)

    def parse_pagination(self, response):
        data = self.get_json_data(response)
        total_products = (data.get('universes', {}).get('universe', [{}])[0].get('items-section', {}).get('results', {})
                          .get('total-items', ''))

        if not total_products:
            return

        total_products = int(total_products)
        items_per_page = 500
        total_pages = ceil(total_products / items_per_page)

        if not total_pages:
            return

        for page_number in range(1, total_pages + 1):
            start_index = (page_number - 1) * items_per_page
            url = re.sub(r'fh_start_index=\d+', f'fh_start_index={start_index}', response.url)

            yield Request(url=url, callback=self.parse_products, dont_filter=True)

    def parse_products(self, response):
        data = self.get_json_data(response)
        products = data.get('universes', {}).get('universe', [{}])[0].get('items-section', {}).get('items', {}).get(
            'item', [])

        for product in products:
            attributes = product.get('attribute', [])
            item_id = self.get_attribute(attributes, 'secondid')  # For Example  item_id = '112982'
            url = self.get_attribute(attributes, 'producturl')
            brand_name = self.get_attribute(attributes, 'brand')
            product_url = f'https://www.chemistwarehouse.com.au/webapi/products/{item_id}/details' if 'ultra-beauty' in url else url

            yield Request(url=product_url, callback=self.parse_product_detail, meta={'brand_name': brand_name})

    def parse_product_detail(self, response):
        item = OrderedDict()

        try:
            # Get json from the Ultrabeauty type products. Example: https://www.chemistwarehouse.com.au/ultra-beauty/buy/112982/
            xml = xmltodict.parse(response.text, )
            ultra_beauty_product_json = xml.get('ProductDetailsModel', {})  # ulta_beauty category
            ultra_beauty_product_desc_json = ultra_beauty_product_json.get('Description', {}).get('ProductDescription',
                                                                                                  {})
        except Exception as e:
            ultra_beauty_product_json = {}
            ultra_beauty_product_desc_json = {}

        try:
            # Get JSON from page source. Will be emtpy for ultrabeauty type products
            product_page_json = json.loads(
                response.css('script[type="text/javascript"]:contains("analyticsProductData")').re_first(
                    r'({.*})').replace('\\', ''))
        except Exception as e:
            product_page_json = {}

        product_id = response.css('.product-id::text').get('').split(':')[-1]

        price = product_page_json.get('price', '') or ultra_beauty_product_json.get('Price', '')  # Current price
        was_price = response.css('.retailPrice span::text').re_first(r'[0-9.]+') or ultra_beauty_product_json.get('RRP',
                                                                                                                  '')

        regular_price = was_price if was_price else price  # Original price
        special_price = price if was_price else ''  # Discounted price
        current_price = special_price or regular_price  # Current price of the product.

        item_id = ultra_beauty_product_json.get('Id', '')
        product_name = product_page_json.get('name', '') or ultra_beauty_product_json.get('Name', '')

        item[
            'Product URL'] = f'https://www.chemistwarehouse.com.au/ultra-beauty/buy/{item_id}/' if 'webapi' in response.url else response.url  # webapi used in the Ultrabeauty request. Example: https://www.chemistwarehouse.com.au/webapi/products/112982/details
        item['Item ID'] = product_page_json.get('id', '') or item_id
        item['Product ID'] = product_id
        item['Category'] = response.css('.breadcrumbs ::text').getall()[3]
        item['Brand Name'] = response.meta.get('brand_name', '') or product_name.split()[0]
        item['Product Name'] = product_name
        item['Regular Price'] = regular_price
        item['Special Price'] = special_price
        item['Current Price'] = current_price
        item['Short Description'] = '\n\n'.join(
            [''.join(p.css('::text').getall()).strip() for p in response.css('.extended-row p')]) or ''
        item['Long Description'] = self.get_long_description(response) or self.get_ultra_beauty_long_desc(
            ultra_beauty_product_desc_json)
        item['Product Information'] = ''
        item['Directions'] = '\n'.join(
            response.css('.product-info-section.directions:contains("Directions") div ::text').getall()) or ''
        item['Ingredients'] = self.get_ingredients(response) or self.get_ultra_beauty_ingredients(
            ultra_beauty_product_desc_json)
        item['SKU'] = product_page_json.get('id', '') or ultra_beauty_product_json.get('Id', '')
        item['Image URLs'] = self.get_img_urls(response) or self.get_ultra_beauty_images(ultra_beauty_product_json)

        yield item

    def get_long_description(self, response):
        general_information = '\n'.join([x.strip() for x in response.css(
            '.product-info-section:contains("General Information") [itemprop="description"] ::text').getall()]).strip()

        warnings = '\n'.join(response.css('.product-info-section.warnings ::text').getall()).strip()
        warnings = warnings if len(warnings) > 15 else ''

        return f'{general_information}\n\n{warnings}'.strip()

    def get_ultra_beauty_long_desc(self, product_json):
        product_info = self.get_json_value_by_name(product_json, 'Product info')
        warnings = self.get_json_value_by_name(product_json, 'Warnings')

        if not product_info and not warnings:
            return ''

        long_description = f'{product_info}\n\nWarnings:\n{warnings}'.strip()

        return '\n'.join(Selector(text=long_description).css('::text').getall())

    def get_json_value_by_name(self, json_dict, name_text):
        return ''.join([general_info.get('Content', '') or '' for general_info in json_dict if
                        general_info.get('Name', '') == name_text]).strip()

    def get_json_data(self, response):
        try:
            return response.json() or {}
        except json.JSONDecodeError as e:
            return {}

    def get_attribute(self, attributes, value):
        return '\n'.join([url.get('value', [{}])[0].get('value') for url in attributes if url.get('name') == value])

    def get_ingredients(self, response):
        if isinstance(response, XmlResponse):
            return ''

        return '\n'.join(
            response.css('.product-info-section.ingredients:contains("Ingredients") div ::text').getall()) or ''

    def get_ultra_beauty_ingredients(self, product_json):
        ingredients = self.get_json_value_by_name(product_json, 'Ingredients')
        return ingredients

    def get_img_urls(self, response):
        if isinstance(response, XmlResponse):
            return []

        image_urls = response.css('[u="slides"] .image_enlarger::attr(href)').getall() or response.css(
            '.empty_image::attr(src)').getall()
        return image_urls

    def get_ultra_beauty_images(self, product_json):
        product_image = product_json.get('Images', {}).get('ProductImage', [{}])

        try:
            if isinstance(product_image, list):
                image_urls = [image_dict.get('Large', '') for image_dict in product_image]
            else:
                image_urls = [product_image.get('Large', '')]
        except Exception:
            image_urls = []

        return image_urls

    def get_category_urls_from_file(self):
        file_name = 'input/categories_urls.txt'

        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            return [line.strip() for line in lines]

        except FileNotFoundError:
            return []

    def get_categories_urls(self, response):
        try:
            # Extract URLs from the response
            urls = response.css('.category-tiles li:not(.mob-only) a::attr(href),'
                                ' .unstyled.inline.first li a::attr(href)').getall()

            # Hardcoded URLs
            hardcode = ['/shop-online/256/health', '/shop-online/257/beauty', '/shop-online/259/personal-care',
                        '/shop-online/260/medical-aids', '/shop-online/651/pet-care',
                        '/shop-online/694/confectionery-drinks', '/shop-online/3000/promotions']

            # Combine and deduplicate URLs, then filter based on the second-to-last segment
            categories = [category for category in list(set(urls + hardcode)) if category.split('/')[-2]]

            return categories

        except Exception as e:
            print(f"Unexpected Exception: {e}")
            return []
