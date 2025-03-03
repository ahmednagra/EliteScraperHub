import json
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request, FormRequest


class ExampleSpider(Spider):
    name = "mwk"
    start_urls = ["https://www.mwk-shop.de/Zubehoer"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,

        'FEEDS': {
            f'output/MwkShop Products {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Name', 'Article Number', 'GTIN', 'HAN', 'Category', 'Discounted Price', 'Old Price',
                           'Discount Percentage', 'Item Weight', 'Dimensions', 'Quantity', 'Image Url', 'URL'],
            }
        },
    }

    def parse(self, response, **kwargs):
        categories = response.css('.content-cats-small__item a:not([title])::attr(href)').getall() or []
        for category in categories:
            yield Request(url=category, callback=self.parse_products)

    def parse_products(self, response):
        products_urls = response.css('.productbox-images.list-gallery a::attr(href)').getall() or []
        for product_url in products_urls:
            yield Request(url=product_url, callback=self.parse_product_detail)

        next_page = response.css('.page-link-next::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, callback=self.parse_products)

    def parse_product_detail(self, response):
        variants = response.css('.switch-variations .custom-radio')
        if variants:
            for variant in variants:
                a = response.css('.current_article::attr(value)').get('')
                data_key = int(variant.css('label::attr(data-key)').get('0'))
                data_value = int(variant.css('label::attr(data-value)').get('0'))
                jtl_token = response.css('.main-search .jtl_token::attr(value)').get('')

                form_parameters = self.get_form_data(a, data_key, data_value, jtl_token)
                yield FormRequest(url='https://www.mwk-shop.de/io', formdata=form_parameters, callback=self.parse_variant_url)
        else:
            item = self.write_yield_item(response)

            yield item

    def parse_product_varient(self, response):
        item = self.write_yield_item(response)

        yield item

    def get_form_data(self, a, data_key, data_value, jtl_token):
        params = {
            "name": "checkVarkombiDependencies",
            "params": [{
                "jtl_token": jtl_token,
                "inWarenkorb": "1",
                "a": a,
                "wke": "1",
                "show": "1",
                "kKundengruppe": "1",
                "kSprache": "1",
                "eigenschaftwert": {str(data_key): str(data_value)},
                "anzahl": "1",
                "wlPos": "0",
                "wrapper": "#result-wrapper"
            },
                int(data_key), int(data_value)
            ]
        },

        form_data = {
            'io': json.dumps(params).replace('[{"name"', '{"name"').replace(']}]', ']}')
        }
        return form_data

    def write_yield_item(self, response):
        item = OrderedDict()
        try:
            images_json = json.loads(response.css('#slpx-product-detail-gallery').re_first(r'({.*})'))
        except:
            images_json = {}

        item['Name'] = response.css('.product-title::text').get('')
        item['Article Number'] = response.css('#__up_data_qp::attr(data-product-id)').get('')
        item['GTIN'] = response.css('span[itemprop="gtin13"]::text').get('')
        item['HAN'] = response.css('span[itemprop="mpn"]::text').get('')
        item['Category'] = response.css('#__up_data_qp::attr(data-product-category)').get('')
        item['Discounted Price'] = response.css('#__up_data_qp::attr(data-product-price)').get('')
        item['Old Price'] = response.css('#__up_data_qp::attr(data-product-original-price)').get('')
        item['Discount Percentage'] = response.css('.discount.text-nowrap-util::text').get('')
        item['Item Weight'] = ''.join([x.strip().replace(',', '.') for x in response.css('.attr-weight .weight-unit ::text').getall()])
        item['Dimensions'] = response.css('.attr-dimensions .attr-value::text').get('').replace(' ', '').strip()
        item['Quantity'] = response.css('.attr-contents .attr-value::text').get('').strip()
        item['Image Url'] = images_json.get('images', [{}])[0].get('zoom', '')
        item['URL'] = response.url

        return item

    def parse_variant_url(self, response):
        json_data = response.json().get('evoProductCalls', [])
        url = [y for y in [x for x in json_data[0] if '#result-wrapper' in x][0] if
               'https://www.mwk-shop.de/' in str(y)][:1]
        variant_url = ''.join(url)

        yield Request(url=variant_url, callback=self.parse_product_varient, dont_filter=True)
