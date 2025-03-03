from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup
from scrapy import Spider, Request, Selector
from scrapy.http import Response


class SuperaSpider(Spider):
    name = "supera"
    base_url = 'https://www.superatv.com/'

    errors_list = []
    headers = {
        'authority': 'www.superatv.com',
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        # 'cookie': '_dy_ses_load_seq=46510%3A1709110346585; _dy_csc_ses=t; _dy_c_exps=; isVisitorNew=true; UUID=655f2b-a524-801-ab56-3a36641af3f5; datadome=EKoCDUpxwzoQcUT6KU6rIp0QfZXFsG6JqJljTRkNcyXhgbDX41X6C7ugzg1uMGZwK8xEz9yFLImptee9B~ogAKKR50oNPeI7aPhzHqKEA84aAsqNIHrr8dfwYeNcCMwN',
        'pragma': 'no-cache',
        'referer': 'https://www.superatv.com/categories',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="122.0.6261.69", "Not(A:Brand";v="24.0.0.0", "Google Chrome";v="122.0.6261.69"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'store': 'default',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    custom_settings = {
        'FEEDS': {
            f'output/SuperaTv {datetime.now().strftime("%d%m%Y%H%M%S")}.json': {
                'format': 'json',
                'fields': ['Product URL', 'Brand', 'Product Name', 'SKU', 'Price', 'Stock', 'Special Notes',
                           'Installation Instructions', 'Images', 'Videos', 'Description', 'Features', 'Fitment',
                           'Options'],
            }
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.brands_names = []

    def start_requests(self):
        self.errors_list.append(f"scraper Started : {datetime.now().strftime("%d%m%Y%H%M%S")}")
        yield Request(
            'https://www.superatv.com/graphql?query=query%20category(%24id%3AString!%2C%24idNum%3AInt!)%7Bcategory(id%3A%24idNum)%7Bid%20description%20category_information_content%20name%20url_key%20url_path%20product_count%20display_mode%20breadcrumbs%7Bcategory_level%20category_name%20category_url_key%20__typename%7Dmeta_title%20meta_keywords%20meta_description%20canonical_url%20__typename%7DcategoryList(filters%3A%7Bids%3A%7Bin%3A%5B%24id%5D%7D%7D)%7Bchildren_count%20url_key%20url_path%20description%20name%20image%20cms_block%7Bcontent%20identifier%20__typename%7Dchildren%7Bid%20position%20level%20name%20path%20url_path%20url_key%20product_count%20image%20thumbnail%20children%7Bid%20position%20level%20name%20path%20url_path%20url_key%20__typename%7D__typename%7D__typename%7D%7D&operationName=category&variables=%7B%22id%22%3A2129%2C%22idNum%22%3A2129%7D',
            headers=self.headers,
            callback=self.parse_categories
        )

    def parse_categories(self, response):
        try:
            categories_dict = []
            data = response.json().get('data', {})
            if data:
                category_list = data.get('categoryList', [])
                if category_list:
                    children = category_list[0].get('children', [])
                    categories_dict = [cat_name.get('name', '') for cat_name in children]
            self.brands_names.extend(categories_dict)
        except Exception as e:
            print(f"Error: {e}. An unexpected error occurred.")
            self.errors_list.append(f'Error From Categories Method : {e}')
            return

        yield Request(
            'https://www.superatv.com/graphql?query=query%20category(%24id%3AString!%2C%24idNum%3AInt!)%7Bcategory(id%3A%24idNum)%7Bid%20description%20category_information_content%20name%20url_key%20url_path%20product_count%20display_mode%20breadcrumbs%7Bcategory_level%20category_name%20category_url_key%20__typename%7Dmeta_title%20meta_keywords%20meta_description%20canonical_url%20__typename%7DcategoryList(filters%3A%7Bids%3A%7Bin%3A%5B%24id%5D%7D%7D)%7Bchildren_count%20url_key%20url_path%20description%20name%20image%20cms_block%7Bcontent%20identifier%20__typename%7Dchildren%7Bid%20position%20level%20name%20path%20url_path%20url_key%20product_count%20image%20thumbnail%20children%7Bid%20position%20level%20name%20path%20url_path%20url_key%20__typename%7D__typename%7D__typename%7D%7D&operationName=category&variables=%7B%22id%22%3A1453%2C%22idNum%22%3A1453%7D',
            headers=self.headers,
            callback=self.parse
        )

    def parse(self, response: Response, **kwargs):
        try:
            categories = response.json().get('data', {}).get('categoryList', [{}])[0].get('children', [{}])
            categories_names = [cat_url.get('name') for cat_url in categories]
            for category_name in categories_names:
                form_data = self.get_form_data(category_name, page_no=1)
                respo = requests.post('https://alz60h.a.searchspring.io/api/search/search.json', params=form_data)

                if respo.status_code != 200:
                    self.errors_list.append(f"{category_name} ::Response is Not Correct. Pagination cannot proceed.")
                yield from self.pagination(response=respo, cat_url=category_name)

        except Exception as e:
            print('Error from Parse Method:', e)
            self.errors_list.append(f'Error From Parse Method : {e}')
            return

    def pagination(self, response, cat_url):
        try:
            data = response.json()
            products = data.get('results', [])
            for product in products:
                url = product.get('url', '').strip('/')
                yield Request(url=self.get_product_detail_page_url(url), callback=self.parse_product_detail, dont_filter=True)

            # Pagination
            next_page = data.get('pagination', {}).get('nextPage')
            if next_page != 0:
                form_data = self.get_form_data(cat_url, next_page)
                respo = requests.post('https://alz60h.a.searchspring.io/api/search/search.json', params=form_data)
                yield from self.pagination(response=respo, cat_url=cat_url)
            else:
                return

        except Exception as e:
            print('Error from Pagination Method:', e)
            self.errors_list.append(f'Error From Pagination Method : {e}')

    def parse_product_detail(self, response):
        try:
            data = response.json()
        except Exception as e:
            self.errors_list.append(f"Response not in Json Formate , URL:', {response.meta.get('product_url', '')} error: {e}")
            return

        product_dict = data.get('data', {}).get('productDetail', {}).get('items', [])[0]

        if not product_dict:
            return

        try:
            name = product_dict.get('name', '')
            url = urljoin(self.base_url, product_dict.get('url_key', ''))

            description = self.get_text(product_html=product_dict.get('description', {}).get('html', ''))
            features = self.get_text(product_html=product_dict.get('features', {}).get('html', ''))
            fitment = self.get_text(product_html=product_dict.get('fitment', {}).get('html'))

            attachments = product_dict.get('product_attachments', {}).get('product_attachments_data', [])
            installations_instructions = [file_url.get('file_url') for file_url in attachments]
            brand = self.get_brand_name(name)

            stock = product_dict.get('stock_status', '')
            if stock:
                stock = stock.title().replace('_', ' ')

            if product_dict.get('variants', []):
                item = OrderedDict()
                variants = product_dict.get('variants', [])
                for variant in variants:
                    sku = variant.get('product', {}).get('sku', '')
                    options = self.get_product_options(source_list=variant.get('attributes', []),
                                                       code_key='code', label_key='label')

                    item['Product URL'] = f"{url}?sku={sku}&wishlist=null&wishlistItemId=null"
                    item['Brand'] = brand
                    item['Product Name'] = name
                    item['SKU'] = sku
                    item['Price'] = (variant.get('product', {}).get('price_range', {}).get('minimum_price', {}).
                                     get('final_price', {}).get('value', 0.0))
                    item['Stock'] = stock if stock else ''
                    item['Special Notes'] = ''
                    item['Installation Instructions'] = installations_instructions
                    item['Images'] = [img.get('url', '') for img in variant.get('product', {}).get('media_gallery', [])
                                      if not img.get('video_content', {})]

                    video_list = [img.get('video_content', '') for img in product_dict.get('media_gallery', [])
                                  if img.get('video_content')]

                    item['Videos'] = ', '.join([video.get('video_url') for video in video_list])
                    item['Description'] = description
                    item['Features'] = features
                    item['Fitment'] = fitment
                    item['Options'] = options
                    yield item

            else:
                item = OrderedDict()
                item['Product URL'] = url
                item['Brand'] = brand
                item['Product Name'] = name
                item['SKU'] = product_dict.get('sku', '')
                item['Price'] = (
                    product_dict.get('price_range', {}).get('minimum_price', {}).get('final_price', {}).get('value', 0.0))
                item['Stock'] = stock if stock else ''
                item['Special Notes'] = product_dict.get('special_notes', '')
                item['Installation Instructions'] = installations_instructions
                item['Images'] = [img.get('url', '') for img in product_dict.get('media_gallery', []) if
                                            not img.get('video_content', {})]
                video_list = [img.get('video_content', '') for img in product_dict.get('media_gallery', []) if
                              img.get('video_content')]
                item['Videos'] = [video.get('video_url') for video in video_list]
                item['Description'] = description
                item['Features'] = features
                item['Fitment'] = fitment
                item['Options'] = ''
                yield item
        except Exception as e:
            self.errors_list.append(f"Detail page error {e} ::Url:: {response.meta.get('product_url', '')}")

    def get_form_data(self, cat_key, page_no):
        params = {
            'ajaxCatalog': 'v3',
            'resultsFormat': 'native',
            'siteId': 'alz60h',
            'page': page_no,
            'bgfilter.ss_category': f'Shop Make>Categories>{cat_key}',
        }
        return params

    def get_product_detail_page_url(self, product_url):
        url = f'https://www.superatv.com/graphql?query=query%20productDetail(%24urlKey%3AString%2C%24page_size%3AInt)%7BproductDetail%3Aproducts(filter%3A%7Burl_key%3A%7Beq%3A%24urlKey%7D%7D%2CpageSize%3A%24page_size)%7Bitems%7B__typename%20id%20sku%20name%20has_fitment_info%20universal_fit%20url_key%20stock_status%20review_details%7Breview_summary%20review_count%20__typename%7Drating_configurations%7Brating_attributes%20__typename%7Dshort_description%7Bhtml%20__typename%7Dfeatures%7Bhtml%20__typename%7Dfitment%7Bhtml%20__typename%7Ddescription%7Bhtml%20__typename%7Dwarranty%7Btitle%20content%20__typename%7Dspecial_notes%20product_subtitle%20satv_outofstock_note%20price_range%7Bminimum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20currency%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7Dmaximum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20currency%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7D__typename%7Dprice_tiers%7Bfinal_price%7Bvalue%20__typename%7Dquantity%20__typename%7Dmedia_gallery%7Burl%20label%20disabled%20position%20full_grid_width...%20on%20ProductVideo%7Bvideo_content%7Bvideo_url%20video_title%20video_description%20video_metadata%20__typename%7D__typename%7D__typename%7Dimage%7Burl%20label%20__typename%7Dcategories%7Bbreadcrumbs%7Bcategory_id%20category_name%20__typename%7D__typename%7D...%20on%20ConfigurableProduct%7Bconfigurable_options%7Battribute_code%20attribute_id%20id%20label%20position%20values%7Bdefault_label%20label%20store_label%20use_default_value%20value_index%20swatch_data%7Btype%20value...%20on%20ImageSwatchData%7Bthumbnail%20__typename%7D__typename%7D__typename%7D__typename%7Dvariants%7Battributes%7Bcode%20value_index%20attribute_id%20label%20__typename%7Dproduct%7Bhas_fitment_info%20universal_fit%20id%20status%20price_range%7Bminimum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7Dmaximum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20currency%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7D__typename%7Dprice_tiers%7Bfinal_price%7Bvalue%20__typename%7Dquantity%20__typename%7Dproduct_subtitle%20satv_outofstock_note%20short_description%7Bhtml%20__typename%7Dfeatures%7Bhtml%20__typename%7Dfitment%7Bhtml%20__typename%7Ddescription%7Bhtml%20__typename%7Dspecial_notes%20media_gallery%7Burl%20label%20disabled%20position%20full_grid_width...%20on%20ProductVideo%7Bvideo_content%7Bvideo_url%20video_title%20video_description%20video_metadata%20__typename%7D__typename%7D__typename%7Dimage%7Burl%20label%20__typename%7Dsku%20stock_status%20related_products%7Bid%20name%20sku%20url_key%20stock_status%20status%20small_image%7Burl%20__typename%7Dprice_range%7Bminimum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7D__typename%7Dprice_tiers%7Bfinal_price%7Bvalue%20__typename%7Dquantity%20__typename%7D__typename%7D__typename%7D__typename%7D__typename%7D...%20on%20GiftCardProduct%7Ballow_open_amount%20open_amount_min%20open_amount_max%20giftcard_type%20is_redeemable%20lifetime%20allow_message%20message_max_length%20giftcard_amounts%7Bvalue_id%20attribute_id%20value%20__typename%7D__typename%7Dmeta_title%20meta_keyword%20meta_description%20canonical_url%20product_attachments%7Bis_enabled%20is_show_tab%20tab_title%20is_show_icon%20is_show_size%20product_attachments_data%7Bicon_url%20file_url%20file_label%20size%20__typename%7D__typename%7Drelated_products%7Bid%20name%20sku%20url_key%20stock_status%20status%20small_image%7Burl%20__typename%7Dprice_range%7Bminimum_price%7Bregular_price%7Bvalue%20currency%20__typename%7Dfinal_price%7Bvalue%20__typename%7Ddiscount%7Bamount_off%20__typename%7D__typename%7D__typename%7Dprice_tiers%7Bfinal_price%7Bvalue%20__typename%7Dquantity%20__typename%7D__typename%7D%7D__typename%7D%7D&operationName=productDetail&variables=%7B%22page_size%22%3A1%2C%22urlKey%22%3A%22{product_url}%22%2C%22onServer%22%3Afalse%7D'
        return url

    def get_text(self, product_html):
        selector = Selector(text=product_html)
        raw_text = ''.join(selector.xpath('//div//text()').extract())
        soup = BeautifulSoup(raw_text, 'html.parser')
        text_content = soup.get_text()

        return text_content.strip('\n')

    def get_product_options(self, source_list, code_key, label_key):
        result = {}
        try:
            if source_list:
                for options_dict in source_list:
                    option_name = options_dict.get(code_key, '')
                    option_value = options_dict.get(label_key, '')
                    result[option_name] = option_value
        except Exception as ex:
            self.errors_list.append(f"Error processing options_dict: {ex}")
            result = {}

        return result

    def close(spider: Spider, reason):
        try:
            filename = 'Logs.txt'
            with open(filename, 'w') as f:
                for error in spider.errors_list:
                    f.write(f"{error}\n")
            spider.logger.info(f"Errors written to {filename}")
        except Exception as e:
            spider.logger.error(f"Error writing to file: {e}")

    def get_brand_name(self, name):
        for brand_name in self.brands_names:
            if name.startswith(brand_name):
                brand = brand_name
                return brand

        return 'SuperATV'