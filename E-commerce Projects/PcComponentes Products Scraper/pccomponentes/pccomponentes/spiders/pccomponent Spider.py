import csv
import glob
import json
import re
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Spider, Request


class PCScraperSpider(Spider):
    name = 'pc'
    base_url = 'https://www.pccomponentes.com/'
    start_urls = ['https://www.pccomponentes.com/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,

        'FEEDS': {
            f'output/Pc Components Products details.csv': {
                'format': 'csv',
                'fields': ['Title', 'EAN', 'Price', 'Description', 'Description HTML', 'Image1 URL', 'Image2 URL', 'Image3 URL', 'Image4 URL', 'URL'],
            }
        },
        'MEDIA_ALLOW_REDIRECTS': True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.previous_scraped_urls = self.get_previous_products_from_csv()

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response, **kwargs):
        json_selector = response.css('script:contains("window.__STATE__ ")')
        if not json_selector:
            return

        data = json.loads(response.css('script:contains("window.__STATE__ ")').re_first(
            r'"menu":(.*"platform":"pccomponentes"})') + ']}')
        categories = data.get('categories', {}).get('byId', {})
        category_items = [category for category in categories.items()]

        for category_id, category_info in category_items:
            sub_category_elements = [cat_element.get('subCategories', []) for elements in category_info.get('columns', []) for cat_element in elements]
            sub_cat_urls = [row.get('href') for elements in sub_category_elements for row in elements]

            for sub_cat in sub_cat_urls:
                url = urljoin(self.base_url, sub_cat) + '?page=1'
                yield Request(url=url, callback=self.parse_products)

    def parse_products(self, response):
        json_selector = response.css('script:contains(" window.__STATE__ ")')
        if not json_selector:
            return

        try:
            data = json.loads(response.css('script:contains(" window.__STATE__ ")').re_first(r'"products":({.*"CF_WORKER":)').replace('undefined', 'null') + ' ""}')
        except Exception as e:
            data = {}

        product_urls = [products.get('slug', '') for products in data.get('articles', {})]

        for product_url in product_urls:
            url = urljoin(self.base_url, product_url)

            try:
                if url.rstrip('/').strip() in self.previous_scraped_urls:
                    print('product already exist')
                    continue
            except Exception as e:
                a=0

            yield Request(url=url, callback=self.parse_product_detail)

        total_pages = data.get('totalPages', '')

        for page_no in range(1, total_pages + 1):
            url = response.url
            pattern = r"\?page="

            if re.search(pattern, url):
                current_page = response.url
                current_page_num_match = re.search(r"\bpage=(\d+)\b", response.url)
                current_page_num = int(current_page_num_match.group(1))
                next_page = current_page.replace(f"?page={current_page_num}", f"?page={current_page_num + 1}")
                yield Request(url=next_page, method='Post', callback=self.parse_products)
            else:
                yield Request(url=urljoin(response.url, '?page=2'), method='Post', callback=self.parse_products)

    def parse_product_detail(self, response):
        item = OrderedDict()

        json_selector = response.css('script:contains("data.ecommerce")')
        if not json_selector:
            return

        try:
            jason_data = json.loads(response.css('script:contains("data.ecommerce")').re_first(r'({.*})'))
        except Exception as e:
            jason_data = {}

        ean = jason_data.get('ean', '')
        if not ean:
            return

        item['Title'] = jason_data.get('name', '')
        item['EAN'] = ean

        item['Price'] = response.css('.precioMain::attr(data-price)').get('') or jason_data.get('price', '')

        image_urls = [response.urljoin(image_url) for image_url in response.css('.fancybox.js-mainImage::attr(href)').getall()][:4]
        field_names = ['Image1 URL', 'Image2 URL', 'Image3 URL', 'Image4 URL']
        item.update({field: url for field, url in zip(field_names, image_urls)})

        item['Description'] = self.get_description(response)
        item['Description HTML'] = self.get_description_html(response)
        item['URL'] = response.url

        # Not call 'Images URLs' because its use only for pipelines.py function
        item['Images URLs'] = image_urls

        yield item

    def get_description(self, response):
        description_text = []

        for tag in response.xpath('//div[@id="ficha-producto-caracteristicas"]/*'):
            if tag.css('style') or tag.css('div.wrapficha') or tag.css('div.ficha-producto-caracteristicas__compra'):  # skip style, image div and bottom Grey text
                continue

            if tag.css('ul li') or tag.css('ol li'):
                li_text = []
                for li in tag.css('ul li, ol li'):
                    li_text.append(''.join(li.css('::text').getall()).strip())

                description_text.append('\n'.join(li_text))
            else:
                description_text.append('\n'.join(tag.css('::text').getall()).strip())

        return '\n\n'.join(description_text)

    def get_description_html(self, response):
        description_html = response.xpath('//div[@id="ficha-producto-caracteristicas"]').get('')
        bottom_grey_text = response.css('div.ficha-producto-caracteristicas__compra').get('')

        return description_html.replace(bottom_grey_text, '')

    def get_previous_products_from_csv(self):
        try:
            file_name = ''.join(glob.glob('output/*.csv'))
            with open(file_name, mode='r', encoding='utf-8') as csv_file:
                products = list(csv.DictReader(csv_file))
                return [product.get('URL', '').rstrip('/').strip() for product in products]

        except FileNotFoundError:
            return []
