import hashlib
import json
import os
from urllib.parse import urljoin

import scrapy

from ..items import ModsaustraliaProjItem


class A4x4modSpider(scrapy.Spider):
    name = "modsaustralia"  # just web name
    start_urls = ["https://www.4x4modsaustralia.com.au/export/cs/partsfinder.json"]
    base_url = 'https://www.4x4modsaustralia.com.au/'
    counter = 0

    custom_settings = {
        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEED_FORMAT': 'xlsx',
        'FEED_URI': 'output/%(name)s_%(time)s.xlsx',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_EXPORT_FIELDS': ['product_name', 'SKU', 'Make', 'Model', 'Year', 'Price', 'Category',
                               'Availability', 'image_urls', 'Product_URL', 'Description', 'Specifications',
                               'Img1', 'Img2', 'Img3', 'Img4', 'Img5'],
    }

    headers = {
        'authority': 'www.4x4modsaustralia Products Scraper',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'N040477_main_sess=42945aab58d7e48ba3fcd92ab43943b0; new_cache_lookup=0; ninfo_geoloc=%7B%22ship_pobox%22%3A%22n%22%2C%22ship_state%22%3Anull%2C%22ship_country%22%3A%22AU%22%2C%22ship_zip%22%3Anull%2C%22ship_city%22%3Anull%7D; ninfo_view=NSD1%3B%231%7C%245%7Cnview%240%7C; __cfruid=461c35fa2be3d85fcc6f82457c789674ad92fe6e-1684304838; _gid=GA1.3.1433886202.1684304838; mc_lc=https://www.4x4modsaustralia.com.au/; _fbp=fb.2.1684304848359.1172573334; wcsid=XPBJW7d2eZQCTwnR5579T0K0kBrABU6o; hblid=FQZh0WMqtuOwDusw5579T0KrjBB6Uko0; olfsk=olfsk8705477859730364; _okbk=cd4%3Dtrue%2Cvi5%3D0%2Cvi4%3D1684304865984%2Cvi3%3Dactive%2Cvi2%3Dfalse%2Cvi1%3Dfalse%2Ccd8%3Dchat%2Ccd6%3D0%2Ccd5%3Daway%2Ccd3%3Dfalse%2Ccd2%3D0%2Ccd1%3D0%2C; _ok=6873-297-10-7055; MCPopupClosed=yes; _okdetect=%7B%22token%22%3A%2216843179950470%22%2C%22proto%22%3A%22about%3A%22%2C%22host%22%3A%22%22%7D; __cf_bm=HPbRbKuwCcqY9xHEOGDdNTeSfGWr32_taBcDv6pxlhE-1684318792-0-AXoO61gyB7gQyMP1L2CJ+83cAO+WAn2/0sIN48BfnLWkCc6d3zR59cRP52ul1hH7LKquV8Fibt6PrQeIv63Ua+0=; _oklv=1684318790637%2CXPBJW7d2eZQCTwnR5579T0K0kBrABU6o; ninfo_search=NSD1%3B%231%7C%242%7Ccn%233%7C%243%7Ckey%247%7Ccontent%245%7Corder%241%7C0%245%7Cvalue%401%7C%244%7C7207; _ga_GRH5B5ZCCQ=GS1.1.1684304838.1.1.1684318824.0.0.0; _ga=GA1.3.1281813569.1684304838',
        'referer': 'https://www.4x4modsaustralia.com.au/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    def parse(self, response):
        data = self.response_json(response)
        model_ids = [key for key, record in data.items() if record.get("level") == 3]
        ids = model_ids

        for car_id in model_ids[:10]:
            if car_id not in ids:
                break

            model = data.get(car_id, {}).get('label', '')
            make_id = data.get(car_id, {}).get('parent', '')
            make = data.get(make_id, {}).get('label', '')
            year_id = data.get(make_id, {}).get('parent', '')
            year = data.get(year_id, {}).get('label', '')

            url = f'https://www.4x4modsaustralia.com.au/?rf=cn&cn={car_id}&pf=1'

            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.next_page,
                meta={'car_id': car_id, 'car_model': model, 'car_make': make, 'year': year},
                dont_filter=False
            )

    def next_page(self, response):
        product_links = response.css('.card-title a::attr(href)').getall()  # rename products

        for url in product_links:
            self.counter += 1

            yield scrapy.Request(
                url=url,
                callback=self.parts_detail,
                meta=response.meta,
                dont_filter=True,
            )

        next_page_url = response.css('.page-item.active + li.page-item a::attr(href)').get()

        if next_page_url:
            full_next_page_url = urljoin(self.base_url, next_page_url)
            yield scrapy.Request(
                url=full_next_page_url,
                callback=self.next_page,
                meta=response.meta
            )

    def parts_detail(self, response):
        item = ModsaustraliaProjItem()

        item['product_name'] = response.css('.pb-4 h1::text').get('').strip()
        item['SKU'] = response.css('.justify-content-between.w-100 span::text').get('')
        item['Year'] = response.meta.get('year')
        item['Make'] = response.meta.get('car_model')
        item['Model'] = response.meta.get('car_make')
        item['Price'] = response.css('[aria-label="Store Price [@save@"]::text').get('')  # used attribue with value
        desc = response.css('div#accordionDescription ::text').getall()
        item['Description'] = [text.replace('\n', '') for text in desc if text.strip()]
        item['Specifications'] = [text.strip() for text in response.css('div.n-responsive-content ::text').getall() if
                                  text.strip()]
        item['Category'] = ', '.join([text.strip() for text in response.css('.breadcrumb li ::text').getall()[3:-4] if text.strip()])
        item['Availability'] = 'In stock' if response.css('.fa-cart-plus') else 'Out of stock'
        imgs = list(set(response.css('#_jstl__images_r div a::attr(href)').getall()))[:5]
        item['image_urls'] = [urljoin(self.base_url, img) for img in imgs]

        for index, img in enumerate(item['image_urls']):
            image_url_hash = hashlib.shake_256(img.encode()).hexdigest(5)
            image_perspective = img.split("/")[-2]
            image_filename = f"{image_url_hash}_{image_perspective}.jpg"
            image_path = os.path.normpath(os.path.join('images_output', image_filename))
            item[f'Img{index + 1}'] = image_path

        yield item

    def response_json(self, response):
        try:
            json_data = json.loads(response.text) or {}
        except json.JSONDecodeError as e:
            print("Error decoding JSON: ", e)
            json_data = {}

        return json_data

    def closed(self, reason):
        print('Total requests made in next_page:', self.counter)
