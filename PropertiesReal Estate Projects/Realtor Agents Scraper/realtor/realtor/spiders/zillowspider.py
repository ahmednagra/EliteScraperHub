import glob
import re
from datetime import datetime
from math import ceil

from scrapy import Spider, Request, Selector
from urllib.parse import urljoin
import json
from collections import OrderedDict


class ZillowSpider(Spider):
    name = "zillow"
    start_urls = ["https://www.zillow.com/professionals/real-estate-agent-reviews/"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/{name} Agents Detail {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Name', 'Office', 'Screen Name','Last Activity', 'Description', 'Experience', 'Areas Served',
                           'Specializations', 'Phone Numbers', 'Website', 'Address','For Sale', 'For Rent',
                           'Sold','Total Listings Count', 'Member Since', 'Real Estate Licenses', 'Other Licenses', 'Languages', 'URL'],
            }
        }
    }

    headers = {
        'authority': 'www.zillow.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'x-amz-continuous-deployment-state=AYABeKbffu8gIO1Ah51t0YVfEhcAPgACAAFEAB1kM2Jsa2Q0azB3azlvai5jbG91ZGZyb250Lm5ldAABRwAVRzA3MjU1NjcyMVRZRFY4RDcyVlpWAAEAAkNEABpDb29raWUAAACAAAAADExLs9sxfKNCWP0aBQAwirKTY7S5AEX4wzAo3cRTJlG2iaqD2f2WPDf25X2LDWw2OSwTuPz5cUx6Hf8jO%2FpJAgAAAAAMAAQAAAAAAAAAAAAAAAAAAGlvz3tMfOkTl4h%2F39PGfGP%2F%2F%2F%2F%2FAAAAAQAAAAAAAAAAAAAAAQAAAAyg%2FW94l3Hu3F1NgFF6YOndsmHQSbxPzxydJHP8; zguid=24|%244fd12644-df47-4d53-99d8-894e53e3a9b9; _ga=GA1.2.1437035690.1695199675; _gid=GA1.2.2131505753.1695199675; zjs_anonymous_id=%224fd12644-df47-4d53-99d8-894e53e3a9b9%22; zjs_user_id=null; zg_anonymous_id=%22f7707ae6-ce4a-4f5a-9e09-6c7b76e8de6b%22; _pxvid=64a41185-5792-11ee-b7ba-6b2611484fb5; x-amz-continuous-deployment-state=AYABeJ1Wt4qs9x1OdMJK6oAwnB8APgACAAFEAB1kM2Jsa2Q0azB3azlvai5jbG91ZGZyb250Lm5ldAABRwAVRzA3MjU1NjcyMVRZRFY4RDcyVlpWAAEAAkNEABpDb29raWUAAACAAAAADAHQia8k+xw96Rj+SgAwNK%2FzdAzxg6G+AmfjyFDRo%2FVO4fGhr396dCjeF8nCPrmdhtyEmsLaLzah3usW4ix8AgAAAAAMAAQAAAAAAAAAAAAAAAAAADX4uZMzUQZ6CcfrTVkdW93%2F%2F%2F%2F%2FAAAAAQAAAAAAAAAAAAAAAQAAAAxiYn83eTKTHcduQbZ494TkgHevej2WZhk8nEKX; _gcl_au=1.1.331045279.1695199683; _cs_c=0; _fbp=fb.1.1695199684095.1692327930; __pdst=a14516ef091249eba40b627f65871cb9; _pin_unauth=dWlkPVl6UXlPVGxpTmpFdFlUbGxOaTAwTnpoaExXRm1NamN0WlRVMVl6RXpabVprWWpNdw; zgsession=1|4b5fb759-ad21-435c-a900-549707a013f4; pxcts=83b530f4-5845-11ee-b3d9-dd676d0f5707; JSESSIONID=7215F725AF787C1EC73418FC52DB851A; AWSALB=FIKuQ6bzjaXyv5BJXZuvEtfkv3l1zIZjfDWZDrYGhqNuDeVs833vm+GV3XpoNjnzheFqrOGLCb1pNtzDgXpfvaDn/L7cwawjBeGY5HLMLiYoloXDHQKfe/yV8LGo; AWSALBCORS=FIKuQ6bzjaXyv5BJXZuvEtfkv3l1zIZjfDWZDrYGhqNuDeVs833vm+GV3XpoNjnzheFqrOGLCb1pNtzDgXpfvaDn/L7cwawjBeGY5HLMLiYoloXDHQKfe/yV8LGo; DoubleClickSession=true; _uetsid=699ff900579211ee84f88d2ab3acf495; _uetvid=69a07d60579211ee8c0f652fc463c10c; _hp2_id.1215457233=%7B%22userId%22%3A%224279320693285157%22%2C%22pageviewId%22%3A%224197633526265325%22%2C%22sessionId%22%3A%223692922086238034%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%224.0%22%7D; _clck=e15hf7|2|ff7|0|1358; _cs_id=5079043f-4b48-afb4-e24c-838bb27ee01f.1695199686.3.1695276612.1695276612.1.1729363686833; _clsk=iur4d|1695276613296|1|0|v.clarity.ms/collect; tfpsi=90d0c4de-c106-411b-bfb9-bb75e233e5aa; _cs_s=1.5.0.1695278413584; _hp2_ses_props.1215457233=%7B%22ts%22%3A1695276612135%2C%22d%22%3A%22www.zillow.com%22%2C%22h%22%3A%22%2Fprofessionals%2Freal-estate-agent-reviews%2F%22%7D; g_state={"i_p":1695363177409,"i_l":2}; _px3=a23d5ebbf82cdbdc1aa37ad015d41e97580242dd8e2613d8d60e340811f6469a:khi4hM9yqkf5ouh4D2TapDnRZCq9nJRlXrwRgWodEMbPhsxOj7dv1gLMdw/VZtd6Q6IYNgOax0fJBA4LeF5ssw==:1000:NSUWbPYZ6mwH5yaQ5h8lUKz8ffDnEfsW+IjQp6/KZlmPziaEVOjCS6si9+G0G0x2DuEEdxh8N/VeUMBMsb5hpX2WHwuF3DNRANVoRxHscEfoSD070gMQt4hQQf0RRBgVrKqd9H1ycp2zbId4T3AmS4puGDg1U1jTAsIEvD/tg08Xr9bKEgQO9QTlWALfGtX0eQwS50Jt8mBKeEgXzf/twY/ieYMIaOjNZ7iYvxUZ2yk=; _gat=1',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    def __init__(self):
        self.zipcodes = self.read_zipcode_file()
        # self.proxy = 'http://scraperapi:1d7ee6593c0d292c2dd20abae4825a43@proxy-server.scraperapi.com:8001'

    def start_requests(self):
        if not self.zipcodes:
            return

        for zipcode in self.zipcodes:
            url = f'https://www.zillow.com/professionals/real-estate-agent-reviews/{zipcode}/'
            yield Request(url=url, headers=self.headers, callback=self.pagination)

    def pagination(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__ ::text').re_first(r'.*')).get('props', {}).get('pageProps',{}).get('proResults', {})
        except:
            data = {}
            return
        specialties_filter = response.css('[data-testid="specialty-search"] ::attr(value)').getall() or []
        language_filter = response.css('[data-testid="language-search"] ::attr(value)').getall() or []
        total_rows = int(data.get('results', {}).get('total', ''))
        zip_code = data.get('search', {}).get('userInput', {}).get('locationText', '')

        if total_rows >= 250:
            for speciality in specialties_filter[:1]:
                for language in language_filter[:1]:
                    for page_no in range(1, 25)[:1]:
                        url = f'https://www.zillow.com/professionals/api/v2/search/?profileType=2&page={page_no}&locationText={zip_code}&language={language}&specialty={speciality}'
                        yield Request(url=url,
                                      callback=self.parse)
        else:
            total_pages = ceil(total_rows / 10)
            for page_no in range(1, total_pages + 1):
                url = f'https://www.zillow.com/professionals/api/v2/search/?profileType=2&page={page_no}&locationText={zip_code}&language=English'
                yield Request(url=url,
                              callback=self.parse)

    def parse(self, response, **kwargs):
        try:
            data = response.json()
        except:
            data = {}
            return
        agent_urls = [x.get('profileLink', []) for x in data.get('results', {}).get('professionals', [])]

        for url in agent_urls:
            yield Request(url=response.urljoin(url), callback=self.parse_agent)

    def parse_agent(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__ ::text').get()).get('props', {}).get('pageProps', {})
        except:
            data = {}

        screenname = ['\n '.join(x.get('description') for x in data.get('professionalInformation', []) if x.get('term') == 'Screenname')]
        # address = ['\n '.join(x.get('lines', [])) for x in data.get('professionalInformation', []) if x.get('term') == 'Broker address']
        address = [x.get('lines', []) for x in data.get('professionalInformation', []) if x.get('term') == 'Broker address']
        member_since = ['\n '.join(x.get('description', []) for x in data.get('professionalInformation', []) if x.get('term') == 'Member since')]
        other_licenses = [''.join(x.get('lines', [])) for x in data.get('professionalInformation', []) if x.get('term') == 'Other Licenses']
        real_estate_licenses = [x.get('lines', []) for x in data.get('professionalInformation', []) if x.get('term') == 'Real Estate Licenses']
        website_urls = [x for x in data.get('professionalInformation', []) if x.get('term') == 'Websites']
        website_urls = '\n'.join([item['url'] for data in website_urls for item in data.get('links', [])]) if website_urls else ''
        phone_numbers = ['\n '.join(x.get('description', []) for x in data.get('professionalInformation', []) if x.get('term') == 'Cell phone')]
        languages = [x.get('description', []) for x in data.get('professionalInformation', []) if x.get('term') == 'Languages']
        description = data.get('about', {}).get('description', '')
        item = OrderedDict()

        item['Name'] = response.css('.ctcd-title h1::text').get('')
        item['Office'] = response.css('.ctcd-title div::text').get('')
        item['Screen Name'] = screenname[0] if screenname else ''
        item['Last Activity'] = data.get('lastYearPastSalesTotal', {}).get('count', 0)
        item['Description'] = ''.join( (Selector(text=description).css('::text').getall())) if description else ''
        item['Experience'] = ''.join(response.css('section h3::text').getall()) or ''
        item['Areas Served'] = '\n'.join([x.get('text', '') for x in data.get('serviceAreas', [])])
        item['Specializations'] = '\n'.join(data.get('about', {}).get('specialties', []))
        item['Phone Numbers'] = phone_numbers[0] if phone_numbers else ''
        item['Website'] = website_urls if website_urls else ''
        item['Address'] = '\n'.join(address[0][1:2]) if address else ''
        item['Sold'] = data.get('pastSales', {}).get('total', 0)
        item['For Sale'] = data.get('forSaleListings', {}).get('listing_count', 0)
        item['For Rent'] = data.get('forRentListings', {}).get('listing_count', 0)
        item['Total Listings Count'] = int(item['Sold']) + int(item['For Sale']) + int(item['For Rent'])
        item['Member Since'] = member_since[0] if member_since else ''
        item['Real Estate Licenses'] = real_estate_licenses[0] if real_estate_licenses else ''
        item['Other Licenses'] = other_licenses[0] if other_licenses else ''
        item['Languages'] = languages[0] if languages else ''
        item['URL'] = response.url

        yield item

    def read_zipcode_file(self):
        file_name = ''.join(glob.glob('input/zip_codes.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []
