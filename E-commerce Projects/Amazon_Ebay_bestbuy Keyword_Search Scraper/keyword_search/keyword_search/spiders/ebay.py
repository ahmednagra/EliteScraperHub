import json
from collections import OrderedDict

from scrapy import Spider, Request


class EbaySpider(Spider):
    name = 'ebay'
    start_urls = ['https://www.ebay.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 7,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/{name} products scraper.csv': {
                'format': 'csv',
                'fields': ['Brand', 'Model', 'Title', 'Sku', 'GTIN', 'Condition',
                           'Price', 'Discounted Price', 'Description', 'keyword', 'Images', 'Status',
                           'URL'],
                'overwrite': True
            }
        }
    }

    def __init__(self):
        super().__init__()
        search_keyword = 'input/keywords.txt'
        self.keywords = self.get_input_rows_from_file(search_keyword)

    def start_requests(self):
        for keyword in self.keywords:
            yield Request(
                url=f"https://www.ebay.com/sch/i.html?_nkw={keyword.replace(' ', '+')}&_ipg=240&LH_ItemCondition=1000",
                callback=self.parse,
                meta={'keyword': keyword}
            )

    def parse(self, response):
        products = response.css('.s-item__info.clearfix a::attr(href)').getall()
        for product in products:
            yield Request(url=product,
                          callback=self.product_detail,
                          meta=response.meta
                          )

        next_page = response.css('.pagination__next::attr(href)').get('')
        if next_page:
            yield Request(
                url=next_page,
                callback=self.parse,
                meta={'keyword': response.meta['keyword']}
            )

    def product_detail(self, response):
        item = OrderedDict()

        try:
            data = json.loads(response.css('script[type="application/ld+json"]:contains(Product)').re_first(r'({.*})'))
            json_data = data.get('mainEntity', {}).get('offers', {}).get('itemOffered', [{}])[0]
        except (json.JSONDecodeError, AttributeError):
            data = {}
            json_data = {}

        item['Brand'] = data.get('brand', {}).get('name', '') or json_data.get('brand',
                                                                               '') or self.get_value_by_heading(
            response, heading='rand')
        item['Model'] = data.get('model', '') or self.get_value_by_heading(response, heading='odel')
        item['Title'] = data.get('name', '') or response.css('.x-item-title__mainTitle span::text').get('')
        item['Sku'] = response.css('.ux-layout-section__textual-display--itemId .ux-textspans--BOLD::text').get('')
        item['GTIN'] = json_data.get('gtin13')
        item['Condition'] = self.get_condition(response, data, json_data)

        was_price = self.get_price(response, data, json_data)
        if was_price:
            item['Discounted Price'] = self.get_discount_price(response)
            item['Price'] = was_price
        else:
            item['Discounted Price'] = ''
            item['Price'] = was_price

        item['Description'] = self.get_description(response)
        item['keyword'] = response.meta.get('keyword', '')
        item['Images'] = self.get_images(response, data)
        item['URL'] = response.url
        item['Status'] = self.get_status(response, data)

        yield item

    def get_input_rows_from_file(self, file_path):
        try:
            with open(file_path, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def get_images(self, response, data):
        images = ', '.join(response.css(
            '.cc-image-component:not([role="button"]) img[width="64"]::attr(data-originalimg)').getall())
        images = images or ', '.join(response.css(
            '.ux-image-carousel-container img::attr(src), .ux-image-carousel-container img::attr(data-src)').getall()) or []

        images = images or data.get('image', '')

        return images

    def get_condition(self, response, data, json_data):
        condition = response.css('.x-item-condition-label:contains("Condition") + .x-item-condition-value ::text').get(
            '')
        condition = condition or response.css('.x-item-condition-value .clipped::text').get('')
        condition = condition or data.get('offers', {}).get('itemCondition', '').split('/')[-1]
        condition = condition or ''.join([x.get('itemCondition', '').split('/')[-1] for x in json_data.get('offers') if
                                          x.get('itemCondition')][:1])

        return condition

    def get_price(self, response, data, json_data):
        price = data.get('offers', {}).get('price', '')
        price = price or response.css('.x-price-primary span::text').get('')
        price = price or json_data.get('offers', [{}])[0].get('price', '')

        return price

    def get_discount_price(self, response):
        return response.css('.ux-textspans.ux-textspans--STRIKETHROUGH::text').get('').replace('US $', '')

    def get_status(self, response, data):
        stat = response.css('.item-action a:contains("Buy It Now")') or response.css(
            'span.ux-call-to-action__text:contains("Buy It Now")') or \
               data.get('mainEntity', {}).get('offers', {}).get('availability', '').split('/')[
                   -1]
        if stat:
            status = 'In stock'
        else:
            status = 'Out of stock'

        return status

    def get_description(self, response):
        div = response.css('[data-testid=ux-layout-section-evo__item] div.ux-layout-section-evo__row')
        if div:
            string_description = '\n'.join([': '.join(row.css('::text').getall()).strip() for row in response.css(
                '[data-testid=ux-layout-section-evo__item] div.ux-layout-section-evo__row .ux-layout-section-evo__col')])

        else:
            strings = []
            product_description = response.css('.spec-row:contains("Key Features") ul li')
            for description in product_description:
                key = description.css('.s-name::text').get()
                value = description.css('.s-value::text').get()

                # Format the key and value as a string and append to the list
                string = f"{key.strip()}: {value.strip()}"
                strings.append(string)

            string_description = "\n".join(strings)

        return string_description

    def get_value_by_heading(self, response, heading):
        return response.css(f'.ux-labels-values__labels:contains("{heading}") + .ux-labels-values__values ::text').get(
            '').strip()
