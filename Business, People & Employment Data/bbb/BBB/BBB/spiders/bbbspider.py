import csv
import re
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request


class BBBScraperSpider(Spider):
    name = 'bbb'
    start_urls = ['https://www.bbb.org/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 3
    }

    headers = {
        'authority': 'www.bbb.org',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'iabbb_user_culture=en-us; iabbb_user_location=Cordelia%2520CA%2520USA; iabbb_user_bbb=1116; iabbb_user_postalcode=94534; iabbb_find_location=Surrey%2520BC%2520CAN; _gcl_au=1.1.23101414.1693805428; _fbp=fb.1.1693805433963.108712989; iabbb_ccpa=true; iabbb_session_id=a667b0f5-9923-4c1e-b092-1323d512cb6b; AMCVS_CB586B8557EA40917F000101%40AdobeOrg=1; s_cc=true; GA1.2.856476724.1693805428; iabbb_accredited_search=false; iabbb_accredited_toggle_state=seen; AMCV_CB586B8557EA40917F000101%40AdobeOrg=179643557%7CMCIDTS%7C19605%7CMCMID%7C41477395681760399293122015470100752643%7CMCAAMLH-1694518976%7C3%7CMCAAMB-1694518976%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1693921376s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C5.5.0; _ga_YH69JE08EZ=GS1.1.1693917767.2.0.1693917767.0.0.0; _ga_5LERF8MTEL=GS1.1.1693917776.3.0.1693917776.0.0.0; _gat_gtag_UA_41101326_21=1; __gads=ID=a9c7077c6c42fc01:T=1693805607:RT=1693919773:S=ALNI_MbKzoTtu-JNRUce3KFIxUyzRWpk8Q; __gpi=UID=00000c9548586726:T=1693805607:RT=1693919773:S=ALNI_MYrq5dkmRBcrFk3XRHc08CNp_JH1w; _ga=GA1.1.856476724.1693805428; s_ips=458.4000015258789; _gid=GA1.2.1959806323.1693919814; s_tp=6044; s_ppv=search%2520results%2520%257C%2520search%2C10%2C8%2C591%2C1%2C15; _ga_0XGWYCFVCN=GS1.2.1693919768.6.1.1693919823.5.0.0; gpv_PageUrl=https%3A%2F%2Fwww.bbb.org%2Fsearch%3Ffilter_category%3D10126-200%26filter_distance%3D5%26find_country%3DCAN%26find_entity%3D10126-000%26find_id%3D1362_3100-14100%26find_latlng%3D49.136343%252C-122.820051%26find_loc%3DSurrey%252C%2520BC%26find_text%3DRoofing%2520Contractors%26find_type%3DCategory%26page%3D1%26touched%3D2; s_sq=%5B%5BB%5D%5D; s_nr30=1693919823418-Repeat; _ga_MP6NWVNK4P=GS1.1.1693919767.6.1.1693919824.3.0.0; _ga_PKZXBXGJHK=GS1.1.1693919811.9.1.1693919824.47.0.0',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_scraped_items = []
        self.output_filename = f'output/BBB Products {datetime.now().strftime("%d%m%Y%H%M")}.csv'
        self.output_fieldnames = ['Company Name', 'Phone No 1', 'Phone No 2', 'Phone No 3', 'Phone No 4', 'Phone No 5', 'Address', 'City', 'State', 'Postal Code', 'URL']

    def start_requests(self):
        url = 'https://www.bbb.org/search?find_country=CAN&find_entity=10126-000&find_id=1362_3100-14100&find_latlng=49.136343%2C-122.820051&find_loc=Surrey%2C%20BC&find_text=Roofing%20Contractors&find_type=Category&page=1'
        yield Request(url=url, callback=self.parse, headers=self.headers)

    def parse(self, response, **kwargs):
        distance_selector = response.css('#\\:Rikkbel5aH1\\: input')
        categories_selector = response.css('#\\:Rmkkbel5aH1\\: input')

        for distance in distance_selector:
            distance_value = distance.css('::attr(value)').get('')
            if not distance_value:
                continue

            for category in categories_selector:
                category_value = category.css('::attr(value)').get('')
                if not category_value:
                    continue

                url = f'https://www.bbb.org/api/search?filter_category={category_value}&filter_distance={distance_value}&find_country=CAN&find_entity=10126-000&find_id=1362_3100-14100&find_latlng=49.136343%2C-122.820051&find_loc=Surrey%2C%20BC&find_text=Roofing%20Contractors&find_type=Category&page=1'
                yield Request(url=url, callback=self.parse_products, headers=self.headers)

    def parse_products(self, response):
        data = response.json()

        total_pages = data.get('totalPages', '')
        contractors = data.get('results', [])

        for contractor in contractors:
            url = contractor.get('reportUrl', '')

            if self.alreadyscraped(url):
                self.logger.info('product already scrapped')
                continue

            item = OrderedDict()

            item['Company Name'] = contractor.get('businessName', '')

            phone_numbers = contractor.get('phone', [])
            field_names = ['Phone No 1', 'Phone No 2', 'Phone No 3', 'Phone No 4', 'Phone No 5']

            if phone_numbers:
                item.update({field: phone_no for field, phone_no in zip(field_names, phone_numbers[:5])})

            item['Address'] = contractor.get('address', '')
            item['City'] = contractor.get('city', '')
            item['State'] = contractor.get('state', '')
            item['Postal Code'] = contractor.get('postalcode', '')
            item['URL'] = contractor.get('reportUrl', '')

            self.current_scraped_items.append(item)

        current_url = response.url
        page_pattern = r'page=(\d+)'
        match = re.search(page_pattern, current_url)

        if match:
            current_page = int(match.group(1))
            for page_number in range(current_page + 1, total_pages + 1):
                next_page_url = re.sub(page_pattern, f'page={page_number}', current_url)
                yield Request(url=next_page_url, headers=self.headers, callback=self.parse_products)
        else:
            pass

    def close(spider, reason):
        items = spider.write_items_to_csv()

    def alreadyscraped(self, url):
        for item in self.current_scraped_items:
            if item.get('URL') == url:
                return True

        return False

    def write_items_to_csv(self):
        if not self.current_scraped_items:
            return

        with open(self.output_filename, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.output_fieldnames)

            if csv_file.tell() == 0:
                writer.writeheader()

            writer.writerows(self.current_scraped_items)





