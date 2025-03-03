import json
import re
from collections import OrderedDict
from datetime import datetime
from urllib.parse import urljoin, quote

from scrapy import Spider, Request


class AmazonProductsSpider(Spider):
    name = "amazon"

    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'RETRY_TIMES': 7,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],

        'FEEDS': {
            f'output/Amazon Products Detail {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Product URL', 'Brand Name', 'Product Name', 'Special Price', 'Regular Price', 'Sold By', 'Shipped From', 'Shipping Cost', 'Short Description',
                           'Long Description', 'Product Information', 'Directions', 'Ingredients', 'SKU', 'ASIN', 'Barcode', 'Image URLs']
            }
        }
    }

    def __init__(self):
        super().__init__()

        proxy_file_path = 'input/proxy_key.txt'
        urls_file_path = 'input/urls.txt'
        self.urls = self.get_input_rows_from_file(urls_file_path)
        proxy_token = self.get_input_rows_from_file(proxy_file_path)
        cookies = quote('i18n-prefs=AUD; lc-acbau=en_AU')
        self.proxy = f"http://{proxy_token[0]}:setCookies={cookies}@proxy.scrape.do:8080"
        # self.proxy = f"http://cef2263bc9d547608ce8aab5fd735feb1d5c2170fa8:setCookies={cookies}@proxy.scrape.do:8080"

    def start_requests(self):
        for url in self.urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        see_all_results = response.css('.a-cardui-body a::attr(href)').get('')

        if see_all_results:  # convert see all result to simple pagination
            url = urljoin(response.url, see_all_results)
            yield Request(url=url, callback=self.parse)

            return

        category_urls = self.get_sub_category_urls(response)

        for url in category_urls:
            yield Request(url=urljoin(response.url, url),
                          callback=self.parse)

        yield from self.parse_products(response)  # To parse products in the given category itself even if it has sub cats

    def parse_products(self, response):
        product_urls = self.get_product_urls(response)
        urls = list(set(product_urls))
        for url in urls[:10]:
            yield Request(url=urljoin(response.url, url),
                          callback=self.parse_details, dont_filter=True)

        next_page_url = self.get_next_page_url(response)

        if next_page_url:
            yield Request(url=next_page_url, callback=self.parse_products)

    def parse_details(self, response):
        item = OrderedDict()

        current_price = self.get_discounted_price(response)
        was_price = self.get_regular_price(response)

        item['Product URL'] = response.url
        item['Brand Name'] = self.get_brand_name(response)
        item['Product Name'] = response.css('#productTitle::text').get('').strip()

        if was_price:
            item['Special Price'] = current_price
            item['Regular Price'] = was_price
        else:
            item['Regular Price'] = current_price

        item['Sold By'] = self.get_seller_name(response)
        item['Shipped From'] = self.get_shipped_from(response)
        item['Shipping Cost'] = self.get_shipping_cost(response)
        item['Short Description'] = response.css('#feature-bullets .a-list-item::text').getall() or ''
        item['Long Description'] = response.css('#productDescription span::text').getall() or ''
        item['Product Information'] = self.get_product_information(response)
        item['Directions'] = response.css('#important-information div.content:nth-child(3) p:nth-child(2)::text').get(
            '')
        item['Ingredients'] = response.css('#important-information div.content:nth-child(2) p:nth-child(2)::text').get(
            '') or response.css('.a-section.content:nth-child(2) p::text').getall()
        asin = item.get('Product Information', {}).get('ASIN', '') or item['Product URL'].replace('?th=1', '').split("/dp/")[1].split("/")[0] if item.get('Product URL', '').replace('?th=1', '').count('/dp/') == 1 else None
        item['SKU'] = asin
        item['ASIN'] = asin
        item['Barcode'] = ''

        try:
            images_json = json.loads(response.css('script[type="text/javascript"]:contains(ImageBlockATF)').re_first(
                f"'colorImages':(.*)").rstrip(',').replace("'", '"')) or {}
            images_json = images_json.get('initial', [])
        except json.JSONDecodeError:
            images_json = []
        except AttributeError:
            images_json = []

        full_size_images_url = [item.get('hiRes', '') for item in images_json]
        images = [url for url in response.css('.regularAltImageViewLayout .a-list-item .a-button-text img::attr(src)').getall() if
                  'images-na.ssl' not in url] or []

        images_url = [re.sub(r'\._.*', '._AC_SX522_.jpg', url) for url in images]

        item['Image URLs'] = full_size_images_url or images_url

        see_all_options = response.css('#buybox-see-all-buying-choices a::attr(href)')

        if not current_price and see_all_options:
            url = f'https://www.amazon.com.au/gp/product/ajax/ref=dp_aod_unknown_mbc?asin={asin}&m=&qid=&smid=&sourcecustomerorglistid=&sourcecustomerorglistitemid=&sr=&pc=dp&experienceId=aodAjaxMain'
            yield Request(url=url,
                          meta={'handle_httpstatus_all': True},
                          callback=self.get_process_price, cb_kwargs={'item': item})
        else:
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

    def get_sub_category_urls(self, response):
        # bestseller category
        child_category = response.css(
            'div:has(span._p13n-zg-nav-tree-all_style_zg-selected__1SfhQ) ~ div[role="group"]')
        category_urls = response.css(
            'div[role="group"] div[role="treeitem"] a::attr(href)').getall() if child_category else []  # best seller categories url
        category_urls = category_urls or response.css(
            'ul > li > span > a.a-color-base.a-link-normal::attr(href)').getall()
        category_urls = category_urls or response.css('.a-spacing-micro.s-navigation-indent-2 a::attr(href)').getall()

        return category_urls

    def get_product_urls(self, response):
        bestseller_tag = response.css('#gridItemRoot a:nth-child(2)::attr(href)')
        products_url = []

        if bestseller_tag:
            json_data = json.loads(response.css('[data-client-recs-list] ::attr(data-client-recs-list)').get(''))
            products_asins = [item['id'] for item in json_data]

            for asin in products_asins:
                url = f'https://www.amazon.com.au/dp/{asin}'
                products_url.append(url)

        products_url = products_url or response.css(
            '.s-line-clamp-2 a::attr(href), .s-line-clamp-4 a::attr(href)').getall()
        products_url = products_url or response.css(
            '.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-4 a::attr(href)').getall()
        products_url = products_url or [response.url]

        return products_url

    def get_next_page_url(self, response):
        next_page = response.css('.s-pagination-selected + a::attr(href)').get('')
        next_page = next_page or response.css('.a-last a::attr(href)').get('')

        return response.urljoin(next_page)

    def get_product_information(self, response):
        product_information = {}

        rows = response.css('#productDetails_techSpec_section_1 tr') or response.css(
            '.content-grid-block table tr') or ''
        if not rows:
            product_details = response.css('#detailBullets_feature_div li')
        else:
            product_details = []

        for row in rows:
            key = row.css('th::text').get('') or row.css('td strong::text').get('')
            value = row.css('td p::text').get('') or row.css('td::text').get('')
            if key and value:
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key.strip()] = value

        for detail in product_details:
            key = detail.css('.a-text-bold::text').get('')
            value = detail.css('.a-text-bold + span::text').get('')
            if key and value:
                key = key.replace(':', '').replace('\u200e', '').replace(' \u200f', '')
                key = ' '.join(key.strip().split())
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key] = value

        additional_information = response.css('#productDetails_detailBullets_sections1 tr') or ''

        for row in additional_information:
            key = row.css('th::text').get('')
            value = ' '.join(row.css('td *::text').getall()).strip()
            if key and value:
                value = value.split('\n')[-1].strip()
                product_information[key.strip()] = value

        return product_information

    def get_discounted_price(self, response):
        price = response.css('.reinventPricePriceToPayMargin .a-offscreen::text').get('').replace('$', '')
        price = price or response.css('.apexPriceToPay span.a-offscreen::text').get('').replace('$', '')
        price = price or response.css('.priceToPay span::text').get('').replace('$', '')

        return price

    def get_regular_price(self, response):
        price = response.css('.basisPrice .a-offscreen::text').get('').replace('$', '')
        price = price or response.css('.a-price[data-a-color="secondary"] .a-offscreen::text').get('').replace('$', '')
        return price

    def get_process_price(self, response, item):
        item['Regular Price'] = response.css('.a-price-whole::text').get('')
        item['Sold By'] = response.css('#aod-offer-soldBy a[role="link"]::text').get('')
        item['Shipped From'] = response.css('#aod-offer-shipsFrom .a-color-base::text').get('')
        item['Shipping Cost'] = response.css(
            '#mir-layout-DELIVERY_BLOCK span[data-csa-c-delivery-price]::attr(data-csa-c-delivery-price)').get('')

        yield item

    def get_shipped_from(self, response):
        shipped = response.css('.a-section.show-on-unselected .truncate .a-size-small:nth-child(2)::text').get('')
        shipped = shipped or response.css(
            '.a-section.show-on-unselected span.a-size-small:contains(" Dispatched from: ") + span.a-size-small::text').get(
            '')
        shipped = shipped or response.css('[tabular-attribute-name="Ships from"] .tabular-buybox-text-message::text').get('')

        return shipped

    def get_seller_name(self, response):
        sold = response.css(
            '.a-section.show-on-unselected .a-row:nth-child(2) .truncate .a-size-small:nth-child(2)::text').get('')
        sold = sold or response.css(
            '.a-section.show-on-unselected span.a-size-small:contains(" Sold by:") + span.a-size-small::text').get('')
        sold = sold or response.css('.a-profile-descriptor::text').get('')
        sold = sold or response.css('[tabular-attribute-name="Sold by"] .tabular-buybox-text-message a::text').get('')
        sold = sold or response.css('[tabular-attribute-name="Sold by"] .tabular-buybox-text-message span::text').get(
            '')

        return sold

    def get_shipping_cost(self, response):
        # cost = response.css(
        #     'span[data-csa-c-delivery-type="delivery"]:not(:contains("FREE"))::attr(data-csa-c-delivery-price)').get(
        #     '').replace('$', '').replace('fastest', '').replace('FREE', '')
        cost = response.css(
            'span[data-csa-c-delivery-type="delivery"]::attr(data-csa-c-delivery-price)').get(
            '').replace('$', '').replace('FREE', '').replace('fastest', '')

        return cost

    def get_brand_name(self, response):
        brand = response.css('.po-brand .po-break-word::text').get('')
        brand = brand or response.css('#brand::text').get('')
        brand = brand or response.css('a#bylineInfo::text').get('').strip().lstrip('Brand:')

        return brand
