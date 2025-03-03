import json
from typing import Iterable
from urllib.parse import urlencode
from collections import OrderedDict

import requests
from scrapy import Request, Spider


class LaikSpider(Spider):
    name = "laik"
    start_urls = ["https://laikamascotas.cl/perros/alimento/seco"]
    errors_list = []

    headers = {
        'authority': 'api-cl.laika.com.co',
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'api-key-client': '$2y$10$DAtaTvXcuyIXd.sWT0gnLueKF0U83Cu49XxAdhQQBg0ytoTR4dd/u',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://laikamascotas.cl',
        'pragma': 'no-cache',
        'referer': 'https://laikamascotas.cl/',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    json_data = {
        'operationName': 'Header',
        'variables': {
            'slug': 'santiago-chile',
            'slugPet': 'dog',
        },
        'query': 'query Header($slug: String, $slugPet: String!) {\n  header(slug: $slug, slug_pet: $slugPet, limit: 7) {\n    user_id\n    percent_membership\n    free_delivery_start\n    slug_error {\n      error\n      city {\n        id\n        name\n        text_cvv\n        phone\n        whatsapp\n        short_name\n        youtube\n        facebook\n        instagram\n        slug\n        logo_web\n        avatar\n        enabled_membership\n        enabled_vetcare\n        enabled_billing\n        required_billing_purchase\n        blog\n        email\n        address_format\n        nacional\n        enabled_municipality\n        free_delivery_no_apply\n        free_delivery_apply\n        before_free_delivery_no_apply\n        membership {\n          id\n          name\n          benefits\n          value\n          image\n          acquired\n          final_date\n          start_date\n          total_monthly_savings_member\n          total_savings_member\n          value\n          value_monthly\n          kit {\n            id\n            name\n            sale_price\n            references {\n              id\n              product_id\n              sale_price\n              price_with_discount\n              kit_membership\n              stock\n              reference_images {\n                url\n                __typename\n              }\n              __typename\n            }\n            brand {\n              id\n              name\n              __typename\n            }\n            subcategory {\n              id\n              name\n              __typename\n            }\n            category {\n              id\n              name\n              __typename\n            }\n            __typename\n          }\n          membership_variables {\n            variable {\n              id\n              name\n              __typename\n            }\n            variable_id\n            value\n            is_primary\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    popular_searches_brands {\n      id\n      brand_slug\n      brand_name\n      pet_id\n      slug_pet\n      __typename\n    }\n    pet {\n      id\n      slug\n      name\n      __typename\n    }\n    countries {\n      id\n      name\n      url_domain\n      logo_web\n      avatar\n      short_name\n      code_country\n      currency\n      cities {\n        name\n        id\n        phone\n        slug\n        nacional\n        enabled_municipality\n        __typename\n      }\n      __typename\n    }\n    categories_dog {\n      id\n      name\n      slug\n      img_web\n      icon\n      show\n      type_products {\n        id\n        name\n        slug\n        __typename\n      }\n      __typename\n    }\n    categories_cat {\n      id\n      name\n      slug\n      img_web\n      icon\n      show\n      type_products {\n        id\n        name\n        slug\n        __typename\n      }\n      __typename\n    }\n    active_membership {\n      id\n      benefits\n      acquired\n      value\n      name\n      image\n      membership_variables {\n        variable {\n          name\n          __typename\n        }\n        status {\n          name\n          __typename\n        }\n        variable_id\n        value\n        is_primary\n        __typename\n      }\n      __typename\n    }\n    free_sample {\n      id\n      reference_id\n      minimum_value\n      buy_membership\n      reference {\n        id\n        sale_price\n        stock\n        product_id\n        reference_images {\n          id\n          url\n          __typename\n        }\n        product {\n          id\n          name\n          description\n          feature\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    brands_dog {\n      id\n      name\n      slug\n      image_app\n      image_web\n      show\n      __typename\n    }\n    brands_cat {\n      id\n      name\n      slug\n      image_app\n      image_web\n      show\n      __typename\n    }\n    services {\n      id\n      name\n      description\n      flow\n      color\n      image_app\n      image_web\n      slug\n      title\n      main_image\n      __typename\n    }\n    __typename\n  }\n}',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.proxy_key = self.get_proxy_key_from_text()

        if not self.proxy_key:
            return

    def start_requests(self) -> Iterable[Request]:
        yield Request(self.get_scrapeops_url(self.start_urls[0]), callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                res = requests.post(self.get_scrapeops_url('https://api-cl.laika.com.co/web'), json=self.json_data,
                                    headers=self.headers)
                if res.status_code == 200:
                    data = res.json()

                    filename = 'output/Laikamascotas.json'
                    with open(filename, 'a') as f:  # Use 'a' for append mode
                        json.dump(data, f, indent=4)

                    self.log(f'Saved JSON data to {filename}')
                    break
                else:
                    print(f'Response is not successful: {res.status_code}. Retrying...')
                    retry_count += 1

            if retry_count == max_retries:
                print('Maximum retries reached. Unable to get successful response.')

        except requests.RequestException as req_ex:
            print(f'RequestException: {req_ex}')
            self.errors_list.append(f'RequestException: {req_ex}')
        except json.JSONDecodeError as json_err:
            print(f'JSONDecodeError: {json_err}')
            self.errors_list.append(f'JSONDecodeError: {json_err}')
        except Exception as e:
            print(f'Error from parse method: {e}')
            self.errors_list.append(f'Error from parse method: {e}')

    def get_scrapeops_url(self, url):
        payload = {'api_key': self.proxy_key, 'url': url, 'keep_headers': True}
        return 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)

    def close(spider: Spider, reason):
        try:
            filename = 'ERRORS.txt'  # Corrected the filename string
            with open(filename, 'w') as f:
                for error in spider.errors_list:
                    f.write(f"{error}\n")
            print(f"Errors written to {filename}")
        except Exception as e:
            print(f"Error writing to file: {e}")

    def get_proxy_key_from_text(self) -> str:
        try:
            file_path = 'input/scrapeops_proxy_key.txt'
            with open(file_path, mode='r', encoding='utf-8') as txt_file:
                proxy_key = txt_file.read().strip()

                if not proxy_key:
                    print('No key found in the input file.')
                    self.errors_list.append(f'No key Exist in the Input file')

            return proxy_key
        except Exception as e:
            print('File not read successfully.')
            self.errors_list.append(f'Key file is not read successfully. Error: {e}')
            return ''
